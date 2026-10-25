#!/usr/bin/env python3
"""Parse problems/catalog-*.md into survey/data/records.json.

One record per JSP entry: id, title, volume file, the main field table,
MathDB pilot metadata (when present), review-note rows, every outbound
link, and every JSP cross-reference.  The output is the base layer for
the survey: shared objects, specifications, dependencies and Lean targets
are all keyed by JSP id.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBLEMS = ROOT / "problems"
OUT = ROOT / "survey" / "data" / "records.json"

HEAD = re.compile(r"^## (JSP-\d{6}) · (.+?)\s*$")
ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*$")
LINK = re.compile(r"https?://[^\s)<>|\]]+")
XREF = re.compile(r"JSP-\d{6}")
LEAN_REPO = re.compile(r"github\.com/([^/\s)]+/[^/\s)#]+)")
ERDOS = re.compile(r"erdosproblems\.com/(?:latex/|forum/thread/)?(\d+)")
FC = re.compile(r"FormalConjectures/([A-Za-z]+)/(\w+)\.lean")


def split_area(area: str) -> list[str]:
    return [p.strip() for p in re.split(r"\s*/\s*", area) if p.strip()]


def parse_volume(path: Path) -> list[dict]:
    records, cur, section = [], None, "main"
    for line in path.read_text(encoding="utf-8").splitlines():
        m = HEAD.match(line)
        if m:
            cur = {"id": m[1], "title": m[2], "volume": path.name,
                   "fields": {}, "mathdb": {}, "review_notes": [], "_text": []}
            records.append(cur)
            section = "main"
            continue
        if cur is None:
            continue
        if line.startswith('<a id="JSP-'):
            continue  # anchor for the next record
        cur["_text"].append(line)
        if "BEGIN MathDB pilot metadata" in line:
            section = "mathdb"
        elif "END MathDB pilot metadata" in line:
            section = "main"
        elif line.startswith("### Review notes"):
            section = "notes"
        r = ROW.match(line)
        if not r or set(r[1]) <= set("- ") or r[1].startswith("Field"):
            continue
        key, val = r[1], r[2]
        if section == "notes":
            cur["review_notes"].append({"label": key, "note": val})
        elif section == "mathdb":
            cur["mathdb"][key] = val
        else:
            cur["fields"].setdefault(key, val)
    for rec in records:
        text = "\n".join(rec.pop("_text"))
        f = rec["fields"]
        status = f.get("Current status", "")
        rec["status"] = ("Solved" if status.startswith("Solved") else
                         "Open" if status.startswith("Open") else "Unknown")
        rec["lean_proof"] = f.get("Lean proof", "").startswith("Yes")
        rec["area"] = f.get("Mathematical area", "")
        rec["area_path"] = split_area(rec["area"])
        rec["description"] = f.get("Problem description", "")
        rec["date_proposed"] = f.get("Date proposed", "")
        rec["mathdb_pilot"] = bool(rec["mathdb"])
        rec["links"] = sorted(set(LINK.findall(text)))
        rec["xrefs"] = sorted(set(XREF.findall(text)) - {rec["id"]})
        rec["erdos_numbers"] = sorted({int(n) for n in ERDOS.findall(text)})
        rec["formal_conjectures"] = sorted({f"{a}/{b}" for a, b in FC.findall(text)})
        rec["lean_repos"] = sorted(
            {r.removesuffix(".git") for r in LEAN_REPO.findall(f.get("Lean proof", ""))}
        )
    return records


INDEX_ROW = re.compile(r"^\| (JSP-\d{6}) \| \[(.+?)\]\((catalog-[\d-]+\.md)#(JSP-\d{6})\) \| (\w+) \|")


def read_index(readme: Path) -> list[dict]:
    """Rows of the problem index in problems/README.md: id, title, volume, status."""
    rows = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        m = INDEX_ROW.match(line)
        if m:
            rows.append({"id": m[1], "title": m[2], "volume": m[3], "anchor": m[4], "status": m[5]})
    return rows


def validate(records: list[dict], index: list[dict]) -> list[str]:
    """Return a list of problems; an empty list means the catalog parsed consistently."""
    errors = []
    ids = [r["id"] for r in records]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        errors.append(f"duplicate ids: {dupes}")
    n = len(index)
    expected = [f"JSP-{i:06d}" for i in range(1, n + 1)]
    if [row["id"] for row in index] != expected:
        errors.append("index ids are not contiguous from JSP-000001")
    missing, extra = sorted(set(expected) - set(ids)), sorted(set(ids) - set(expected))
    if missing or extra:
        errors.append(f"catalog id mismatch against the {n}-row index: missing={missing}, extra={extra}")
    unknown = [r["id"] for r in records if r["status"] == "Unknown"]
    if unknown:
        errors.append(f"unrecognized status in: {unknown}")
    by_id = {r["id"]: r for r in records}
    for row in index:
        r = by_id.get(row["id"])
        if r is None:
            continue
        if row["anchor"] != row["id"]:
            errors.append(f"{row['id']}: index anchor points to {row['anchor']}")
        if row["volume"] != r["volume"]:
            errors.append(f"{row['id']}: index volume {row['volume']} vs record volume {r['volume']}")
        if row["status"] != r["status"]:
            errors.append(f"{row['id']}: index status {row['status']} vs record status {r['status']}")
        if row["title"] != r["title"]:
            errors.append(f"{row['id']}: index title differs from record heading")
    return errors


def main() -> int:
    vols = sorted(PROBLEMS.glob("catalog-*.md"))
    records = [r for v in vols for r in parse_volume(v)]
    index = read_index(PROBLEMS / "README.md")
    errors = validate(records, index)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(records)} records -> {OUT.relative_to(ROOT)} (index rows: {len(index)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
