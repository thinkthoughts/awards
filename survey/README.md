# JSP survey

A connected Lean 4 survey of the problems in this repository's catalog (`problems/`), built on the
General Divisor Theorem (GDT), Specification Grammar (SG) and PiπΠ reading-point lifts. The design
is in [`docs/ARCHITECTURE_REVIEW.md`](docs/ARCHITECTURE_REVIEW.md). The survey reads the prize
catalog and writes only under `survey/`.

Leading specifications first. Admissible generalizations trail leading specifications. PiπΠ.

## Layout

| Path | Content |
| --- | --- |
| `data/records.json` | All catalog records keyed by JSP id (generated) |
| `data/provenance.json` | Catalog commit, sha256 of every catalog file and of `records.json` (generated) |
| `data/renumbering-5b7126a-to-c06d67a.json` | JSP id crosswalk from this catalog to upstream `c06d67a` (generated) |
| `data/reach.json`, `data/reach.csv` | Keyword screening of catalog families (generated) |
| `schemas/` | JSON Schemas for every registry file |
| `registry/sources.json` | Pinned external repositories (lean-bgp212, GDT, formal-conjectures, SG, mathematical-basis, Lean core) |
| `registry/objects.json` | L0 shared mathematical objects |
| `registry/specs.json` | L1 leading specifications |
| `registry/readings.json` | L2 reading points: JSP entries and foundational readings |
| `registry/edges.json` | Typed PiπΠ lifts and other dependency edges |
| `registry/evidence.json` | L4 verification evidence |
| `lean/` | Core-only Lean project: `SurveyFoundation/OnePlusOne.lean` and its axiom audit |
| `scripts/` | Parser, classifier, provenance, registry validator, Lean check |
| `tests/test_survey.py` | Regression tests (standard library only) |

## Commands

From the repository root:

```bash
python3 survey/scripts/parse_catalog.py            # records.json, with id/index/status checks
python3 survey/scripts/classify_reach.py           # reach.json, reach.csv
python3 survey/scripts/catalog_provenance.py --compare <upstream-rev>   # provenance + crosswalk
python3 survey/scripts/validate_registry.py        # schemas, cross-references, lift rules
python3 survey/scripts/validate_registry.py --sources-dir DIR   # also look up cited declarations
python3 -m unittest discover -s survey/tests -v
survey/scripts/check_lean.sh <path-to-lean-4.34.0-rc2>          # kernel check + axiom audit
```

`--sources-dir DIR` expects clones named by source id (`DIR/lean-bgp212`,
`DIR/general-divisor-theorem`, `DIR/formal-conjectures`); each cited declaration is looked up in its
file at the pinned commit.

## Catalog provenance

The survey is pinned to this fork's catalog: 1,073 records, last changed at upstream commit
`5b7126acf3d3` (TheJustinSunPrize/awards #5126). Upstream `c06d67a` (#5135) has since removed
JSP-001029 (smooth four-dimensional Poincaré conjecture; JSP-000007 took its place in the MathDB
pilot) and renumbered
JSP-001030 to JSP-001073 down by one, giving 1,072 records. The crosswalk file maps every id; the
pilot ids are unaffected. Syncing the fork's catalog is a separate decision, after which the
generated files are rebuilt and the crosswalk direction recorded.

## States

Every object, specification, reading and edge carries three independent states:

| Axis | Values | Meaning |
| --- | --- | --- |
| mathematical | objects: defined · specs: parametric, proved, open · readings: proved, open, refuted, independent · edges: established, candidate | Status of the mathematics itself |
| formalization | prose, specified, compiled | How far the Lean statement exists |
| verification | unverified, upstream-reported, kernel-checked, comparator-accepted | What checking stands behind it, with evidence |

An edge's lift state summarizes these: Proposed (prose), Specified, Compiled, Verified (kernel-checked
or comparator-accepted here). Every lift is an open proof obligation until it is Verified;
`upstream-reported` records a source repository's own verification and keeps the obligation open
until the check is re-run for the survey. Analogy and scope-boundary edges carry obligation
`recorded`: they transfer no conclusion.

Edge strengths follow mathematical-basis `papers/SCOPE.md`: direct application (side conditions only),
conditional implication (at least one named assumption, such as `DHL 2 2`), structural analogy,
general distinction, shared reading, and boundary.

## Current registry

- Foundational reading point RP-0001, `1 + 1 = 2`: statement, Lean declaration
  `Survey.Foundation.one_add_one`, proof term `rfl`, kernel check EV-0001 (no axioms), and its
  generalization SPEC-nat-add-one through LIFT-0001 (Verified).
- Pilot readings RP-JSP-000009, RP-JSP-000029, RP-JSP-000041, with 21 edges in total.
  Lift states: Verified 1, Compiled 1, Specified 16, Proposed 3.
