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


def main() -> int:
    vols = sorted(PROBLEMS.glob("catalog-*.md"))
    records = [r for v in vols for r in parse_volume(v)]
    ids = [r["id"] for r in records]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print(f"duplicate ids: {sorted(dupes)}", file=sys.stderr)
        return 1
    expected = {f"JSP-{i:06d}" for i in range(1, 1074)}
    missing, extra = expected - set(ids), set(ids) - expected
    if missing or extra:
        print(f"catalog id mismatch: missing={sorted(missing)}, extra={sorted(extra)}", file=sys.stderr)
        return 1
    unknown = [r["id"] for r in records if r["status"] == "Unknown"]
    if unknown:
        print(f"unrecognized status in: {unknown}", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(records)} records -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
