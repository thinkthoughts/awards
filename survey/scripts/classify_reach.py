#!/usr/bin/env python3
"""Reproducible catalog-reach classification for the JSP survey architecture review.

Input : survey/data/records.json (from parse_catalog.py; source = problems/catalog-*.md)
Output: survey/data/reach.json  (per family: keyword set, matched ids, open/solved/Lean counts)
        survey/data/reach.csv   (one row per (family, JSP id) match, with the matched keyword)

Method
------
* Text searched per record: title + problem description + every review-note cell,
  lower-cased.  Area tags are searched separately and only by the families that say so.
* A family matches a record when ANY of its regular expressions matches.  Keywords are
  word-bounded where that avoids false hits (e.g. "sieve" but not "sieved" mis-hits are
  fine; "prime gap" also matches "prime gaps").
* Counts are an upper-bound screen for triage, not a classification.  A match means
  "worth reading for this family", and a record can match several families.  Every
  matched id is written out so any count in the review can be checked record by record.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "survey" / "data"

# family -> (description, text regexes, area-tag regexes)
FAMILIES: dict[str, tuple[str, list[str], list[str]]] = {
    "prime_tuples_gaps": (
        "Prime k-tuples, twin primes, Dickson, prime gaps (bgp212 Gap.lean layer)",
        [r"\bprime gaps?\b", r"\bbounded gaps?\b", r"\bsmall gaps?\b", r"\btwin primes?\b",
         r"\bk-tuples?\b", r"\bprime tuples?\b", r"\bdickson\b", r"\bmaynard\b",
         r"\bhardy.?littlewood\b", r"\bconsecutive primes?\b", r"\badmissib"],
        [],
    ),
    "residue_coprime_sieve": (
        "Residue classes with coprimality, totient densities, sieves (GDT / multi-shift GDT layer)",
        [r"\bcoprime\b", r"\brelatively prime\b", r"\btotient\b", r"\beuler'?s (phi|function)\b",
         r"\bsieve\b", r"\bsieving\b", r"\bresidue class", r"\bcongruence class",
         r"\bprimorial\b"],
        [],
    ),
    "covering_systems": (
        "Covering systems and families of residue classes (shared residue-covering spec)",
        [r"\bcovering system", r"\bcovering congruence", r"\bcover(s|ed)? (all|almost all) integers\b",
         r"\bdistinct (odd )?moduli\b", r"\bdisjoint residue classes\b"],
        [r"covering systems"],
    ),
    "lp_density_certificates": (
        "Density / LP / packing bounds where a finite rational certificate may close a step",
        [r"\blinear program", r"\bpacking\b", r"\bfractional\b", r"\bsemidefinite\b",
         r"\bflag algebra", r"\bmaximum density\b", r"\bupper density\b", r"\blower density\b"],
        [],
    ),
    "simplex_integration": (
        "Integrals over simplices / Dirichlet-type integrals / moment problems",
        [r"\bsimplex\b", r"\bsimplices\b", r"\bdirichlet integral", r"\bmoments?\b",
         r"\bvariational\b"],
        [],
    ),
    "unit_distance_geometry": (
        "Unit and distinct distances in finite point sets (worked non-prime example)",
        [r"\bunit[- ]distances?\b", r"\bdistinct distances?\b", r"\bpinned distance",
         r"\bsame distance\b", r"\brepeated distance"],
        [r"distance geometry"],
    ),
    "graph_ramsey_chromatic": (
        "Graph theory, Ramsey theory and chromatic number (outside the existing definitions)",
        [r"\bramsey\b", r"\bchromatic\b"],
        [r"^graph theory", r"ramsey theory", r"chromatic number"],
    ),
}


def text_of(r: dict) -> str:
    parts = [r["title"], r["description"]] + [n["note"] for n in r["review_notes"]]
    return " ".join(parts).lower()


def main() -> int:
    recs = json.loads((DATA / "records.json").read_text(encoding="utf-8"))
    out, rows = {}, []
    for fam, (desc, pats, area_pats) in FAMILIES.items():
        rx = [re.compile(p) for p in pats]
        ax = [re.compile(p) for p in area_pats]
        hits = []
        for r in recs:
            t = text_of(r)
            m = next((p.pattern for p in rx if p.search(t)), None)
            if m is None:
                area = r["area"].lower()
                m = next((f"area:{p.pattern}" for p in ax if p.search(area)), None)
            if m is not None:
                hits.append(r)
                rows.append({"family": fam, "id": r["id"], "matched": m,
                             "status": r["status"], "lean_proof": r["lean_proof"],
                             "area": r["area"], "title": r["title"]})
        out[fam] = {
            "description": desc, "text_patterns": pats, "area_patterns": area_pats,
            "count": len(hits),
            "open": sum(h["status"] == "Open" for h in hits),
            "solved": sum(h["status"] == "Solved" for h in hits),
            "lean_yes": sum(h["lean_proof"] for h in hits),
            "ids": [h["id"] for h in hits],
        }
    meta = {"records": len(recs), "source": "problems/catalog-*.md via survey/data/records.json"}
    (DATA / "reach.json").write_text(json.dumps({"meta": meta, "families": out},
                                                ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with (DATA / "reach.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for fam, v in out.items():
        print(f"{fam:26s} {v['count']:4d}  open {v['open']:4d}  solved {v['solved']:4d}  lean {v['lean_yes']:3d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
