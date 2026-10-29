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
| `lean-bridges/` | Lean project requiring lean-bgp212 at `89b43fa`: `SurveyBridges/H1LeMono.lean`, `SurveyBridges/AdmissibleTwin.lean`, `SurveyBridges/TwinPrimeEquiv.lean`, `SurveyBridges/TwinPrimeTo186.lean` and their audit |
| `scripts/` | Parser, classifier, provenance, registry validator, Lean check |
| `docs/COMPARATOR_RUNS.md` | Verification policy and the pinned macOS and Linux Comparator procedures |
| `evidence/kernel/`, `evidence/comparator/` | Complete kernel-check and Comparator run logs cited by evidence records |
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
survey/scripts/check_bridges.sh ~/lean-bgp212                    # bridge modules, against a built checkout
survey/scripts/compare_bridges.sh ~/lean-bgp212 ~/comparator-v4.34.0-rc2   # Comparator on the pairs
survey/scripts/compare_bridges_linux.sh ~/lean-bgp212 ~/comparator-19e111e   # Linux, landrun, shared read-only builds
```

`compare_bridges.sh` runs Lean Comparator on each config in `lean-bridges/Comparator/`
(`h1le_mono`, `admissibleZ_subset`, `admissibleZ_pair_iff_even`, `admissibleZ_iff_nu_lt`): the Challenge
(`lean-bridges/SurveyChallenge/`, statement only, importing only lean-bgp212) against the Solution
(`lean-bridges/SurveySolution/`, importing the kernel-checked bridge module unchanged). It needs a
Comparator checkout built for Lean 4.34.0-rc2 (commit `19e111e`, lean4export `cacf989`), assembles a
temporary workspace from copies of the existing lean-bgp212 build, and prints `isolation:
landrun-linux` or `isolation: non-isolating`. Only acceptance under landrun on Linux moves a lift to
Verified; procedures for both cases are in [`docs/COMPARATOR_RUNS.md`](docs/COMPARATOR_RUNS.md).

`check_bridges.sh` requires the lean-bgp212 checkout to sit at the pinned commit with a clean tree
and existing builds; it downloads and rebuilds nothing. `lake build` inside `survey/lean-bridges`
is the from-scratch route: it fetches lean-bgp212 and Mathlib at their pinned commits (several GB
with the Mathlib cache). `survey/lean` stays core-only, so its check needs only the toolchain.

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
| verification | unverified, upstream-reported, kernel-checked, comparator-nonisolated, comparator-accepted | What checking stands behind it, with evidence |

An edge's lift state summarizes these: Proposed (prose), Specified, Compiled, and Verified.

| Check | Verification value | Lift state |
| --- | --- | --- |
| Kernel acceptance and axiom audit | `kernel-checked` | Compiled |
| Comparator acceptance without sandbox isolation (e.g. macOS, `landrun-noisolate.sh`) | `comparator-nonisolated` | Compiled |
| Comparator acceptance under landrun on Linux, audited (`landrun-linux` on Landlock ABI ≥ 4, `landrun-fs-systemd` on ABI 2–3; ABI 1 rejected) | `comparator-accepted` | Verified |

Comparator evidence records `isolation` (`landrun-linux` or `non-isolating`), the Comparator and
lean4export commits and binary hashes, the runner and its hash, and the exact Comparator output;
the validator admits `comparator-accepted` only with `landrun-linux` evidence. Every lift is an open proof
obligation until it is Verified;
`upstream-reported` records a source repository's own verification and keeps the obligation open
until the check is re-run for the survey. Analogy and scope-boundary edges carry obligation
`recorded`: they transfer no conclusion.

Edge strengths follow mathematical-basis `papers/SCOPE.md`: direct application (side conditions only),
conditional implication (at least one named assumption, such as `DHL 2 2`), structural analogy,
general distinction, shared reading, and boundary.

## Current registry

- Foundational reading point RP-0001, `1 + 1 = 2`: statement, Lean declaration
  `Survey.Foundation.one_add_one`, proof term `rfl`, kernel check EV-0001 (no axioms), and its
  generalization SPEC-nat-add-one through LIFT-0001 (Compiled; Comparator pending).
- First prime-gap bridge: `Survey.PrimeBridges.h1Le_mono` (LIFT-041-2), kernel-checked against
  lean-bgp212 `89b43fa` with axioms propext, Classical.choice, Quot.sound (EV-0002), and accepted
  by Comparator `19e111e` against the independent Challenge on macOS without sandbox isolation
  (EV-0006, `comparator-nonisolated`; log in `evidence/comparator/`). Compiled; the landrun run on
  Linux remains. Earlier evidence keeps the `14ec5e0` pin (source `lean-bgp212`).
- Second bridge: `Survey.PrimeBridges.admissible_twin : AdmissibleZ ({0, 2} : Finset ℤ)`
  (LIFT-009-5, a general distinction: membership of {0, 2} in the admissible shift sets).
  Kernel-checked on the user's MBP against lean-bgp212 `89b43fa` (EV-0003, axioms propext,
  Classical.choice, Quot.sound; Compiled, Comparator pending). The same run reproduces EV-0002.
- Third bridge: `Survey.PrimeBridges.twin_primes_iff_h1Le_two : InfinitelyManyTwinPrimes ↔
  BGP212.Gap.H1Le 2` (LIFT-009-3, `SurveyBridges/TwinPrimeEquiv.lean`), kernel-checked on the user's
  MBP (EV-0004, axioms propext, Classical.choice, Quot.sound; Compiled, Comparator pending).
- Fourth bridge: `Survey.PrimeBridges.twin_primes_implies_h1Le_186 : InfinitelyManyTwinPrimes →
  BGP212.Gap.H1Le 186` (LIFT-041-3, `SurveyBridges/TwinPrimeTo186.lean`), kernel-checked on the user's
  MBP (EV-0005; Compiled, Comparator pending). It is the implication JSP-000009 ⇒ JSP-000041 and
  proves neither conjecture.
- Admissibility, general results, kernel-checked on the user's MBP against lean-bgp212 `89b43fa`
  (EV-0007, axioms propext, Classical.choice, Quot.sound; Compiled, Comparator pending):
  `Survey.PrimeBridges.admissibleZ_subset` (LIFT-ADM-2, relation `closure`: AdmissibleZ is closed
  downward under `K ⊆ H`) and
  `Survey.PrimeBridges.admissibleZ_pair_iff_even` (LIFT-ADM-3, SPEC-admissible-pair:
  `AdmissibleZ {a, b} ↔ Even (b - a)`), with corollaries `admissibleZ_pair_self`,
  `admissibleZ_singleton`, `not_admissibleZ_zero_one` and `admissible_twin_of_pair` (LIFT-009-6,
  `{0, 2}` from the classification; the kernel-checked `admissible_twin` stays as it is).
- Admissibility in `ZMod p`, kernel-checked on the user's MBP (EV-0008; Compiled, Comparator
  pending): `residueImage p H`
  (OBJ-residue-image, the image of `H` in `ZMod p`), `admissibleZ_iff_omits_residue`
  (LIFT-ADM-4, SPEC-admissible-omits-residue: an omitted residue for every prime) and
  `admissibleZ_iff_card_lt` (LIFT-ADM-5, SPEC-admissible-card-lt: `(residueImage p H).card < p`),
  applied to the empty set, singletons, duplicate shifts, `{0, 2}`, `{0, 1}` and `{-3, -1}` through
  the kernel-checked results.
- Residue image and the multi-shift local factor, kernel-checked on the user's MBP (EV-0009;
  Compiled, Comparator pending): `residueImage_card_eq_nu_of_modulus` (LIFT-ADM-6, relation
  `cardinality-equality`: `(residueImage p H).card = ν_p(H)` for every
  natural `p`, through `negRep p : x ↦ ZMod.cast (-x)`), its prime form `residueImage_card_eq_nu`,
  and `admissibleZ_iff_nu_lt` (LIFT-ADM-7, an equivalence characterizing OBJ-admissible-z:
  `AdmissibleZ H ↔ ∀ p prime, ν_p(H) < p`).
- Local factors and the per-period count, kernel-checked on the user's MBP (EV-0010; Compiled,
  Comparator pending): `admissibleZ_iff_local_factor_pos`
  (LIFT-ADM-8: `AdmissibleZ H ↔ ∀ p prime, 0 < p - ν_p(H)`), `localCount_pos_iff` (LIFT-GDT-2:
  `0 < localCount N m H ↔ ∀ p ∣ R N m, ν_p(H) < p`, no hypothesis on `N`, `m`),
  `localCount_pos_of_admissibleZ` (LIFT-GDT-3), and `localCount_singleton` (LIFT-GDT-4:
  `localCount N m {a} = ∏ p ∣ R N m, (p - 1)`; its totient side condition discharged by LIFT-GDT-5).
- Single-shift compatibility, kernel-checked on the user's MBP (EV-0011; Compiled, Comparator
  pending): `localCount_singleton_eq_totient`
  (LIFT-GDT-5: `0 < N → localCount N m {a} = φ(R N m)`), through `R_eq_prod_sdiff`
  (`R N m = ∏ p ∈ N.primeFactors \ (gcd m N).primeFactors, p`) and `totient_prod_primes`;
  `localCount_singleton_at_zero` shows `0 < N` is needed.
- Comparator without sandbox isolation on macOS (EV-0012, `comparator-nonisolated`): `admissibleZ_subset`,
  `admissibleZ_pair_iff_even` and `admissibleZ_iff_nu_lt` accepted against independent Challenges;
  LIFT-ADM-2, LIFT-ADM-3 and LIFT-ADM-7 stay Compiled pending the landrun run on Linux.
- Pilot readings RP-JSP-000009, RP-JSP-000029, RP-JSP-000041, with 34 edges in total.
  Lift states: Compiled 18, Specified 13, Proposed 3; Verified 0.

## RPI onboarding foundation

[RPI-1: Reading Point Identifiers](docs/RPI.md) extends L2 reading points to
source-backed readings from arXiv, news and repositories without renumbering JSP
or legacy RP identifiers. Onboarding validates against existing specifications.
