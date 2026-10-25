# JSP survey: initial architecture and catalog reach

This ZIP is a **repository-relative overlay** for `thinkthoughts/awards`, not a replacement for the upstream prize repository. Extract its contents at the root of your fork, review changes, and commit on a survey branch.

## Included

- `survey/docs/ARCHITECTURE_REVIEW.md`: Claude's v2 assessment, including GDT, SG, PiπΠ, five layers, and proposed pilots. Embedded diagram and Reading points/Reach evidence tabs from the original authored environment are represented as placeholders; the standalone Markdown does not contain those tabs.
- `survey/scripts/parse_catalog.py`: extracts catalog records keyed by JSP ID. This package adds strict contiguous-ID and recognized-status checks.
- `survey/scripts/classify_reach.py`: keyword-based screening of catalog records.
- `survey/data/reach.json` and `survey/data/reach.csv`: supplied classification output. These are preliminary keyword matches, not verified theorem coverage.

## Rebuild the data in the fork

From repository root:

```bash
python3 survey/scripts/parse_catalog.py
python3 survey/scripts/classify_reach.py
```

`parse_catalog.py` expects the existing `problems/catalog-*.md` files, and generates `survey/data/records.json`. That generated file is intentionally **not** included in this package because the source catalog is not part of the attachments. The classifier regenerates `reach.json` and `reach.csv`.

Before committing results, compare freshly generated reach counts to the packaged snapshot. Record the fork and upstream commit SHAs used for extraction. The parser's source-text interpretation should be tested against representative volume records before the entire corpus is treated as authoritative.

## Scope / next actions

1. Keep existing `problems/`, `awards/`, and `candidates/` unchanged.
2. Validate record count (1,073), source statuses, IDs, and sample records.
3. Define machine-readable SG/PiπΠ edge and reading-point schemas after reviewing the architecture.
4. Specify JSP-000009, JSP-000029, JSP-000041 by referencing pinned Lean declarations; no hand-copied Lean modules.
5. Audit every proposed lift separately for proof status and mathematical statement fidelity.

This package does **not** contain compiled Lean code, a new core package, finished JSP reading-point records, or eligibility claims. No PR or deployment is included.
