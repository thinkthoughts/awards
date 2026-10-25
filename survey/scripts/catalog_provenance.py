#!/usr/bin/env python3
"""Record where survey/data/records.json came from, and map JSP ids across catalog revisions.

Usage (from the repository root):
    python3 survey/scripts/catalog_provenance.py
    python3 survey/scripts/catalog_provenance.py --compare <git-rev>

The first form writes survey/data/provenance.json: the git commit that last changed the
catalog, the sha256 of every catalog file and of records.json, and the record count.
With --compare it also writes survey/data/renumbering-<base>-to-<rev>.json, a crosswalk
of JSP ids between the working-tree catalog and the catalog at <rev>, matched by title.
The catalog itself is only read.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "survey" / "data"
CATALOG_GLOBS = ["problems/README.md", "problems/catalog-*.md"]


def _parser():
    spec = importlib.util.spec_from_file_location("parse_catalog", ROOT / "survey/scripts/parse_catalog.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def catalog_files(root: Path) -> list[Path]:
    files = []
    for pattern in CATALOG_GLOBS:
        files.extend(sorted(root.glob(pattern)))
    return files


def parse_tree(root: Path) -> dict[str, dict]:
    p = _parser()
    recs = [r for v in sorted((root / "problems").glob("catalog-*.md")) for r in p.parse_volume(v)]
    errors = p.validate(recs, p.read_index(root / "problems" / "README.md"))
    if errors:
        raise SystemExit("catalog at " + str(root) + " fails validation:\n" + "\n".join(errors))
    return {r["id"]: r for r in recs}


def export_rev(rev: str, dest: Path) -> None:
    (dest / "problems").mkdir(parents=True)
    names = git("ls-tree", "--name-only", rev, "problems/").splitlines()
    for name in names:
        if name == "problems/README.md" or (name.startswith("problems/catalog-") and name.endswith(".md")):
            blob = subprocess.run(["git", "show", f"{rev}:{name}"], cwd=ROOT, check=True,
                                  capture_output=True).stdout
            (dest / name).write_bytes(blob)


def write_provenance() -> dict:
    records_path = DATA / "records.json"
    if not records_path.exists():
        raise SystemExit("run survey/scripts/parse_catalog.py first")
    recs = json.loads(records_path.read_text(encoding="utf-8"))
    catalog_commit = git("log", "-1", "--format=%H", "--", *CATALOG_GLOBS)
    dirty = git("status", "--porcelain", "--", "problems/")
    prov = {
        "schema": "survey/provenance@1",
        "catalog": {
            "repository": "thinkthoughts/awards (fork of TheJustinSunPrize/awards)",
            "last_commit_touching_catalog": catalog_commit,
            "last_commit_subject": git("log", "-1", "--format=%s", catalog_commit),
            "working_tree_catalog_clean": dirty == "",
            "files": [{"path": str(f.relative_to(ROOT)), "sha256": sha256(f)} for f in catalog_files(ROOT)],
        },
        "records": {
            "path": "survey/data/records.json",
            "count": len(recs),
            "first_id": recs[0]["id"],
            "last_id": recs[-1]["id"],
            "sha256": sha256(records_path),
            "generator": "survey/scripts/parse_catalog.py",
        },
    }
    out = DATA / "provenance.json"
    out.write_text(json.dumps(prov, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"provenance -> {out.relative_to(ROOT)} (catalog commit {catalog_commit[:12]}, {len(recs)} records)")
    return prov


def write_crosswalk(rev: str, base_commit: str) -> None:
    full = git("rev-parse", rev)
    here = parse_tree(ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        export_rev(full, Path(tmp))
        there = parse_tree(Path(tmp))
    by_title = {}
    for i, r in there.items():
        by_title.setdefault(r["title"], []).append(i)
    rows, unchanged, renumbered, removed = [], 0, 0, []
    for i, r in here.items():
        targets = by_title.get(r["title"], [])
        if there.get(i, {}).get("title") == r["title"]:
            unchanged += 1
            continue
        if len(targets) == 1:
            renumbered += 1
            rows.append({"from": i, "to": targets[0], "title": r["title"]})
        else:
            removed.append({"from": i, "title": r["title"], "matches": targets})
    matched = {row["to"] for row in rows} | {i for i in here if there.get(i, {}).get("title") == here[i]["title"]}
    added = [{"to": i, "title": there[i]["title"]} for i in there if i not in matched]
    out = {
        "schema": "survey/renumbering@1",
        "from_catalog_commit": base_commit,
        "to_catalog_commit": full,
        "from_count": len(here),
        "to_count": len(there),
        "method": "records matched by exact heading title",
        "unchanged_ids": unchanged,
        "renumbered": rows,
        "without_match_in_target": removed,
        "only_in_target": added,
    }
    path = DATA / f"renumbering-{base_commit[:7]}-to-{full[:7]}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"crosswalk -> {path.relative_to(ROOT)}: {unchanged} unchanged, {renumbered} renumbered, "
          f"{len(removed)} without a match, {len(added)} only in target")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compare", help="git revision whose catalog to map ids against")
    args = ap.parse_args()
    prov = write_provenance()
    if args.compare:
        write_crosswalk(args.compare, prov["catalog"]["last_commit_touching_catalog"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
