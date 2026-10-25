# JSP Survey Architecture Review

Oct 24, 2026 · @Daniel Thomas Hawkley

## Summary

The survey organizes the 1,073 JSP entries as readings of reusable leading specifications, connected by dependency edges whose verification state is recorded explicitly. This revision (v2) incorporates the DeepSeek and ChatGPT reviews: the five layers are stated in prose, edges carry one of four verification states, every reach count comes from a documented script, and claims about Mathlib are checked against the pinned commit. Work begins with a specification-only pilot on JSP-000009, JSP-000029 and JSP-000041; the three proposed reading points are in the Reading points tab. GDT, lean-bgp212 and the upstream JSP records stay unchanged.

## Decision and staged plan

Pilot first, shared core second. The pilot settles *what* must connect. Extracting the core later settles *how* the Lean modules connect, so the work is done once. The pilot references existing declarations by fully qualified name and commit, without copying code.

| Stage | Work | Repository changes | Exit condition |
| --- | --- | --- | --- |
| 1 | Inventory existing declarations (names, signatures, commits, verification state) | Read-only | Every declaration a pilot spec cites is pinned to a commit |
| 2 | Specify three reading points: JSP-000009, JSP-000029, JSP-000041 | New survey records only | Each spec complete in SG roles; see the Reading points tab |
| 3 | Identify and validate dependency edges between them | New records and small isolated tests | Each edge reaches Specified; trivial bridges reach Compiled in a scratch project |
| 4 | Extract a shared, namespaced Lean core | GDT, lean-bgp212 and awards, by explicit decision | Import needs from stage 3 written down and agreed |
| 5 | Compile integrated Lean examples on package dependencies | New survey Lean project | Pilot edges reach Verified under Comparator |

The upstream JSP records (`problems/catalog-*.md`) stay unchanged throughout. Survey data lives beside them and is keyed by JSP id.

## Recommended architecture: leading specifications with readings

The architecture has five layers. Each layer below is self-contained in prose; the diagram restates them.

- **L0 Objects.** One Lean definition per shared mathematical object: admissible tuple, residue-class family, unit-distance count, Ramsey number. Each definition carries proved equivalences to the Mathlib or formal-conjectures version where one exists. Seeds: `GDT.Admissible`, `BGP212.Gap.AdmissibleZ`, `BGP212.MultiShift.nu`, formal-conjectures' `unitDistNum`.
- **L1 Leading specifications.** Parametric statements over L0 objects: `H1Le D`, `DHL k m`, prime patterns for an admissible shift set, Dickson over linear forms, the uncovered density of a residue-class family, the maximal unit-distance count in a metric space. Each has an SG record: domain, leading statement, leading constraints, excluded generalizations.
- **L2 Readings.** Each JSP entry as data: the L1 spec it instantiates, its parameter values, a bridge statement from the catalog prose to that instance, and its SG-3 scope boundary. Example: `JSP_000041 := H1Le 186`.
- **L3 Engines.** Verified checkers whose soundness theorems hold for every input. They certify the finite facts that readings and edges need: `checkTree2_sound`, the staged / trie / profile certificates, and the Lemma 12.1 admissibility check.
- **L4 Ledger.** One record per Challenge/Solution pair and per dependency edge: SG result YAML, Comparator config, axiom list, machines, commit. The catalog's columns and the survey's own states sit there as independent axes.

&#91;embedded content: survey architecture · 5 layers\]

### Dependency edges and their verification states

Every relationship between specifications or readings is an edge, and every edge carries exactly one of four states. A development that compiles with `sorry` stays at Compiled until a kernel proof replaces it.

| State | Meaning | Evidence that moves an edge into this state |
| --- | --- | --- |
| Proposed | A mathematical relationship is identified | A cited source: catalog note, paper, or derivation sketch |
| Specified | The exact Lean statement, hypotheses and direction are recorded | Statement text over definitions pinned to named commits |
| Compiled | Lean elaborates the statement and a development for it | Build log and `#print axioms` output, with `sorryAx` presence recorded |
| Verified | Kernel-checked proof with only propext, Quot.sound and Classical.choice, accepted by Comparator against an independently written Challenge | Comparator result, axiom audit, commit and machine |

Edge kinds: reading-of, implies, special case, equivalent formulation, reduces-to-interface, and scope boundary. Reading-of, special case and equivalent formulation edges are PiπΠ lifts and carry a strength (next sections). A scope boundary is a relationship recorded as lying outside a claim, as the catalog does for JSP-001061 and JSP-000491.

Each edge record holds: id, source node, target node, kind, state, Lean statement, hypotheses and named interfaces, mathematical source, verification evidence, and the commits involved. Conditional results (on GRH, EH or DHL) follow the `AnalyticInputs` pattern, with each hypothesis a named structure field. The catalog's 24 prose cross-references enter the graph as Proposed edges.

### Why readings of specifications, rather than one module per conjecture

- The catalog clusters heavily. Its own area tags give Ramsey theory 101 records, primes 53, chromatic number 51 and distance geometry 46, so one specification serves dozens of entries.
- It follows SG-4: the leading statement comes first and specific numbers are its readings, as in GDT and lean-bgp212.
- Each definition lives in one place, and equivalences to outside definitions are proved once in L0.
- It sidesteps the package-composition problem described under Technical constraints.

## Specification Grammar rules used here

Four rules from `SG_0001_SPECIFICATION_ROLES.md` (specification-grammar at `d958b81fc073`) shape the survey. The definitions are paraphrased from that file; the right-hand column is this survey's binding.

| Rule | Definition in SG\_0001 | Binding in this survey |
| --- | --- | --- |
| SG-2 | Independent aspects of a specification's state stay independently gradable, whether held in one multi-axis field or distributed across artifacts. | The catalog's Current status, Lean proof, Solver claim and Lean claim stay separate, and each edge's verification state is a further independent axis. |
| SG-3 | A specification states both what constrains the admissible object and which extensions stay outside the claim (leading constraints and excluded generalizations). | Every L1 spec and L2 reading records its scope boundary, e.g. JSP-000041 covers D = 186 only; Dickson's general forms lie outside `DHL`. |
| SG-4 | Discovery order and specification order differ; a finished specification states the general form first and the specific number as its reading. | L1 states `H1Le D`; JSP-000041 is the reading D = 186. GDT's C(m) = m/φ(m) precedes the 24/25 numeral it explains. |
| SG-6 | Justification (proof) and checking (verification) are distinct roles, and verification has at least two depths: structural (the process ran) and content (the claim matches its source). | Compiled marks structural success; Verified requires kernel proof plus Comparator against an independent Challenge, and each reading's bridge to the catalog prose is a separate content check. |

SG-1 (six roles: Identity, State, Provenance, Specification, Verification, Result) is the record shape the Reading points tab uses.

## PiπΠ: reading-point lifts

PiπΠ is represented as one typed relation, the **lift**, recorded in the SG ledger. It takes no architectural layer of its own: every element it names is already an L0–L2 node or an L4 edge, and a separate layer would hold those same nodes a second time. What PiπΠ adds is the lift record and its strength field.

The roles come from your existing sources. SCOPE.md (mathematical-basis at `e571a609caa7`) defines a reading point as a position specified within an admissible space, and separates *general distinction ≠ structural analogy ≠ direct theorem application*. The readingpoint source records that different objects can share a numerical reading while their specifications stay distinct. The closing line of THEOREMS.md, *Admissible generalizations trail leading specifications · PiπΠ*, fixes the order: a generalization is admitted only after the specification that leads it, and only within that specification's hypotheses. The doc uses PiπΠ verbatim as the name of this relation.

| PiπΠ role | Where it lives | Example |
| --- | --- | --- |
| Reading point: a JSP statement at specific parameter values | L2 reading | JSP-000041 at D = 186 |
| Admissible space of that reading | The L1 spec's domain and leading constraints (SG-3) | Every D : ℕ in `H1Le D` |
| Shared objects and relationships | L0 objects, and lifts among L1 specs | `AdmissibleZ`, `primeGap` |
| General Lean theorem | An L1 statement pinned by name and commit | `BGP212.Gap.dhl_implies_gap` at `14ec5e0` |
| Explicit hypotheses of the lift | The lift's hypothesis list, each a Lean proposition with its own state | `AdmissibleZ {0, 2}`, diameter ≤ 2, `DHL 2 2` |
| Verified implication | Lift state Verified: kernel proof, axiom audit, Comparator | `dhl_implies_gap` itself is Verified; its instance at {0, 2} is Specified |

### Lift strength

Each lift carries one strength, taken from SCOPE.md's scope rule plus the shared-reading principle. Only a direct theorem application can carry conclusions from a general result to a reading.

| Strength | What it carries to the reading | Lean obligation |
| --- | --- | --- |
| Direct theorem application | The theorem's conclusion, within its hypotheses | The theorem instantiated at the reading's parameters, every hypothesis discharged |
| Structural analogy | Shared structure only (period, density, admissibility shape) | A statement of the shared structure, when one is useful |
| General distinction | Membership in a constraint-defined admissible set | The membership proposition |
| Shared reading | The common value alone, kept on record to block a false lift | None |

### Every lift is a proof obligation

A lift opens as an obligation and is discharged only at state Verified; Proposed, Specified and Compiled lifts are open obligations, whatever their source says. A direct-application lift carries SCOPE.md's four conditions as its checklist, each with its own state:

1. the theorem's mathematical objects are specified;
2. the mapping from the JSP problem to those objects is stated (the parameter map);
3. every hypothesis is checked at the mapped parameters;
4. the conclusion claimed is limited to the theorem's own.

A lift record holds: reading point (JSP id and parameter values), generalization (L1 spec, Lean theorem name, commit), parameter map, strength, hypotheses with their states, the Lean obligation statement, overall state, and evidence. The Reading points tab gives three worked records.

## What the existing infrastructure gives the survey

Five kinds of asset carry over: shared definitions, general theorems, certificate engines, a verification procedure, and the Specification Grammar (SG).

**Shared definitions you can use directly**

- **GDT v1.0.0:** `rad`, `d`, `R`, `Tmin`, `Admissible`, `accepted`. Exact-density counting for "n ≡ a (mod m) and coprime to N".
- **Multi-shift GDT (B1/B2):** `nu p H`, `AdmissibleH`, `localCount` = ∏(p − ν\_p(H)), plus minimal period and the W-trick.
- **`BGP212/Gap.lean`:** `PrimeZ`, `AdmissibleZ`, `DHL k m`, `primeGap`, and `H1Le D := ∃ᶠ n, primeGap n ≤ D`.
- **`BGP212/Basic.lean`:** an admissibility predicate in core Lean (no Mathlib) with the omitted-residue table, giving a kernel-checkable test for admissible tuples.

**General theorems, as opposed to Table 3 instances**

- `dhl_implies_gap`: any admissible k-tuple of diameter D, with DHL\[k,2\], gives H₁ ≤ D.
- `gdt_*` / `gdtH_*` (count, period, minimal period, density) and `admissible_iff_local_factors`.
- `beta_integral`, `simplex_integral` and the two-group Dirichlet theorems, stated for bounded measurable integrands.
- `box_poly` (polygon cells).
- `power_sums_algebraically_independent`.
- `placeVal_eq_msVal` and `markProfile_step`, which hold for any ordered field and any class sizes.

**Certificate engines (verified checkers that work for any problem)**

- `checkTree2_sound`: Farkas infeasibility over subdivision trees of rational cells, valid for any capacity data.
- Staged, prefix-trie and marked-profile certificates: kernel computations kept in reusable chunks, each built under a 4 GB budget.
- Moment-oracle linearity (`genPieceWith_eq_keys`): compute each shared quantity once and reuse it.

**Verification procedure**

- Challenge/Solution/Comparator pairs, with `permitted_axioms` limited to propext, Quot.sound and Classical.choice, run under landrun isolation.
- Kernel-only proofs: `native_decide` appears zero times in the repo.
- Per-release result YAML files using the SG roles: identity; a four-axis state; scope split into proved / kernel\_certified / exploratory / outside.
- Python negative controls and data emitters.
- A ledger of inconsistencies found in the source paper (SI-1 to SI-3).
- Imported hypotheses written as named interface structures (`AnalyticInputs`, `SieveInputs`).
- Independent reproduction on two machines.

**Specification Grammar**

- SG-3 (leading constraints and excluded generalizations) fits the catalog's main recurring problem: review notes repeatedly separate a special case, a dimension or a variant from the full scope.
- SG-2's independent state axes fit the catalog's separate columns (status, Lean proof, solver claim, Lean claim).
- SG-6 (proof and verification as separate roles) matches the separation the prize's `lean-verify` skill requires.

## Where it applies in the catalog

Direct statement reuse covers the prime-tuple cluster; the verification procedure covers every entry. All counts below come from `survey/scripts/classify_reach.py` run over all 1,073 records, and the Reach evidence tab lists its keyword sets, method, and the matched records family by family.

The script reads the title, problem description and review notes of each record, and a record matches a family when any of that family's regular expressions matches (some families also match on the area tag). A match is a screen for reading, so counts are upper bounds. Version 1 of this review used ad hoc patterns (\~23, \~60, \~20, \~17, \~300); the figures here replace them.

| Family (script key) | Matches (open / solved / Lean yes) | Precision on reading | Existing asset | Kind of reuse |
| --- | --- | --- | --- | --- |
| `prime_tuples_gaps` | 27 (20 / 7 / 2) | 18 on topic; 9 match on "bounded gaps" in integer sequences, "consecutive primes" in other settings, or "admissib" in review notes (JSP-000027, 000276, 000319, 000731, 000914, 000923, 001018, 001023, 001072) | `H1Le`, `DHL`, `AdmissibleZ`, `dhl_implies_gap` | Direct statement reuse; see the Reading points tab |
| `residue_coprime_sieve` | 58 (40 / 18 / 7) | Pending a manual read | GDT and multi-shift GDT | Counting and density statements for coprimality in residue classes |
| `covering_systems` | 15 (10 / 5 / 3) | Pending a manual read | Multi-shift GDT `localCount`, for prime moduli only | A shared residue-family spec, under the hypotheses in the next section |
| `unit_distance_geometry` | 54 (39 / 15 / 4) | Pending a manual read | formal-conjectures' `unitDistNum`, `distinctDistances` | The worked non-prime example below |
| `graph_ramsey_chromatic` | 264 (150 / 114 / 14) | Area-tag driven | Engine pattern and verification procedure | Statements from the formal-conjectures crosswalk |
| `lp_density_certificates` | 9 (4 / 5 / 2) | Weak: most hits are "fractional parts" | `checkTree2_sound` | Reach still to be measured, by reading the proofs of solved records |
| `simplex_integration` | 1 (0 / 1 / 1) | Off target (JSP-001054, Mahler) | Simplex, Dirichlet, symmetric-function stack | Library and upstream Mathlib candidate; in-catalog use sits inside sieve arguments |
| All records | 1,073 (100 Lean yes) | Exact | Challenge/Comparator, axiom whitelist, SG records | Re-audit of the 100 "Lean proof: Yes" entries |

Families overlap: one record can match several. Precision has been read only for the prime family so far; the other families get the same manual read during stage 1.

## Admissibility and covering systems: the exact hypotheses

The two share one object, a finite family of residue classes and the integers it leaves uncovered. For families whose moduli are primes the connection is a direct theorem application; for composite, overlapping moduli it is a structural analogy (terms from the PiπΠ section below).

**Shared L0 object.** A residue-class family F = {(aᵢ, mᵢ)} has uncovered set U(F) = {n ∈ ℤ : mᵢ ∤ n − aᵢ for every i}. U(F) is periodic with period L = lcm(mᵢ), and its density is #(U(F) ∩ \[0, L)) / L.

|  | Prime-tuple admissibility (`BGP212.Gap.AdmissibleZ H`) | Covering system |
| --- | --- | --- |
| Classes | The same shift set H, reduced modulo each prime p | One family {(aᵢ, mᵢ)}, chosen freely |
| Moduli | One prime at a time; the classes for p all share modulus p | Mixed moduli, often required distinct, odd, or above a bound |
| Quantifiers | ∀ prime p, ∃ residue r, ∀ h ∈ H: p ∤ h − r | ∀ n ∈ ℤ, ∃ i: mᵢ ∣ n − aᵢ |
| Question | Does each single-prime family leave a residue uncovered? | Does the whole family cover ℤ? |
| Finite check | Only primes p ≤ \|H\| can be covered | Residues modulo lcm(mᵢ) |

**Direct theorem application (prime moduli).** For a finite set of primes P with product N, take F\_P(H) = {(−h, p) : h ∈ H, p ∈ P}. An integer n is uncovered by F\_P(H) exactly when gcd(n + h, N) = 1 for every h ∈ H, which is `acceptedH N 1 0 H n`. Then `BGP212.MultiShift.gdtH_count_per_period` at m = 1, a = 0 (where `AdmissibleH` holds vacuously, since d = 1) counts the uncovered integers in each period N as `localCount N 1 H` = ∏ over p ∈ P of (p − ν\_p(H)). Together with `admissible_iff_local_factors` (B2; stated for the core-Lean `BGP212.Admissible` on lists of naturals, via ν\_p(H) < p for every prime p), H is admissible exactly when every F\_P(H) leaves an integer uncovered. A bridge from `BGP212.Admissible` to `AdmissibleZ` is one more Specified obligation. Both theorems are kernel-checked in lean-bgp212 at `14ec5e0`; the specialization to m = 1, a = 0 is a Specified lift.

**Structural analogy (composite moduli).** The product formula rests on Chinese-remainder independence across distinct primes. Covering systems with overlapping composite moduli (for example 2, 3, 4, 6, 12) lose that independence, so their uncovered density needs a count over the lcm period. That count is a new L1 specification; MB\_0001 already lists non-squarefree moduli among its excluded generalizations, which names the same extension.

Readings by fit: JSP-000238 (prime moduli) is the closest candidate for the direct application, after a manual read of its exact statement. JSP-000047 (distinct odd moduli), JSP-000237 (extremal proportion for prescribed moduli), JSP-000993 and JSP-000994 need the lcm-period specification. JSP-000235 (Herzog–Schönheim) concerns cosets in groups, a further generalization.

## Worked non-prime example: distance multiplicities

Seven JSP entries in distance geometry are readings of one L1 specification, and four of the five edges between them are short direct theorem applications. The L0 objects already exist in formal-conjectures (`FormalConjecturesForMathlib/Geometry/Metric.lean` and `Geometry/2d.lean` at `37f0808`): `unitDistNum`, `distanceSet`, `distinctDistances`, `minimalDistinctDistances`, `distinctDistancesFrom` and `ConvexIndep`.

&#91;embedded content: distance-multiplicity cluster · 7 readings, 5 edges\]

| Edge | Statement | Strength | State | Source |
| --- | --- | --- | --- | --- |
| E1 | max over convex-position n-sets ≤ max over all n-sets (sSup over a subset) | Direct application | Specified | formal-conjectures Erdős 96 and 90 definitions |
| E2 | distinct distances D(n) ≥ C(n, 2) / u(n): each distance class is a unit-distance set after rescaling | Direct application | Proposed | Standard counting argument; the rescaling step needs a similarity lemma for ℝ² |
| E3 | `distinctDistancesFrom P x ≤ distinctDistances P`, so a pinned lower bound is a distinct-distance lower bound | Direct application | Specified | Definitions in Metric.lean |
| E4 | JSP-001061 supplies n^(1−ε) for almost all pins, and the n/√log n target of JSP-000491 lies outside it | Scope boundary | Recorded | JSP-000491 review note |
| E5 | Erdős 90's disproof gives Erdős 92's disproof | Direct application | Specified (proof `sorry` in formal-conjectures) | `ErdosProblems/92.lean`; the JSP-000108 ↔ Erdős 92 mapping is Proposed |

JSP-000902 is a reading at X = ℝ^d, with its edges still to be identified. The Erdős numbers attached to these entries are Proposed mappings, matched by statement. One provenance item to reconcile in stage 1: the catalog credits JSP-000106 to Levent Alpöge, while formal-conjectures' Erdős 90 header records a May 2026 disproof (Sawin; Alon et al.).

## Mathlib check at the pinned commit

At Mathlib `85e3a25e006c35636f0e53b0e9296caca2685bc0` (the commit lean-bgp212 pins), the simplex moment formula and power-sum independence are lean-bgp212's own contributions; Farkas exists in Mathlib in a geometric form. Method: a shallow checkout of that commit and text searches over `Mathlib/`. A search finds names and phrases, so a result under an unexpected name would need a further `#find` or `exact?` check inside a build.

| Claim in v1 | Search at 85e3a25 | Finding | Revised claim |
| --- | --- | --- | --- |
| Mathlib lacks a simplex Dirichlet integral | "simplex" in `MeasureTheory/`, `Probability/`, `Analysis/SpecialFunctions/`; "dirichlet" in `Probability/` | Zero hits. Nearest results: `Complex.betaIntegral` (one-variable Beta), `MeasureTheory.volume_sum_rpow_le` (ℓᵖ-ball volume; p = 1 gives the cross-polytope), `stdSimplex` (convexity only) | The monomial moment over the simplex (`BGP212.simplex_integral`) is an upstream candidate |
| Power-sum algebraic independence | `AlgebraicIndependent` in `RingTheory/MvPolynomial/Symmetric/` | Zero hits; Newton's identities are present (`NewtonIdentities.lean`) | `power_sums_algebraically_independent` (Solution/Variational.lean) is an upstream candidate |
| Farkas certificates | "farkas" across `Mathlib/` | Geometric Farkas for cones in `Analysis/Convex/Cone/Dual.lean` and `InnerDual.lean` | Mathlib's form is topological over ℝ; lean-bgp212's exact rational certificate checker (`checkTree2_sound`) is a separate, computable tool |

formal-conjectures, the main statement source for the combinatorics bulk, pins a different stack: Lean v4.33.1 and Mathlib `0df444a360eaa60ab8c11dca51a86af692955474` (at formal-conjectures `37f0808`), against lean-bgp212's v4.34.0-rc2 and `85e3a25`. Stage 2 therefore cites formal-conjectures statements by name and commit, and stage 4 decides how the two stacks meet.

## Technical constraints on reuse

The one blocker is a library-name collision; the rest are pins and policies to keep.

- **Library-name collision.** GDT and bgp212 both name their libraries `Challenge`/`Solution`, so bgp212 copied GDT's code in by hand (`BGP212/GDTv1Basic.lean`, `BGP212/GDTv1.lean`) instead of requiring it as a package. The fix is a shared core package with namespaced library names (GDT, multi-shift, Gap, simplex moments, PackingCert), required as a dependency by bgp212, GDT and awards.
- **Pins.** Use bgp212's pins (Lean v4.34.0-rc2, Mathlib `85e3a25`) so imports work without a port. formal-conjectures pins Lean v4.33.1 and Mathlib 0df444a, so its statements are cited by name and commit until stage 4.
- **Policies to keep:**
  - kernel-only proofs;
  - the three-axiom whitelist;
  - large certificates split into chunks that build under 4 GB;
  - Mac Comparator runs recorded separately from landrun runs.

## Sources

- [translatepi.ai](https://translatepi.ai)
- [main.pdf, Draft v1.2](https://translatepi.ai/main.pdf)
- [thinkthoughts/lean-bgp212](https://github.com/thinkthoughts/lean-bgp212) at `14ec5e0`: [Gap.lean](https://github.com/thinkthoughts/lean-bgp212/blob/14ec5e0c77f9867d97fe394f135d61c349ddd0b1/BGP212/Gap.lean), [MultiShift.lean](https://github.com/thinkthoughts/lean-bgp212/blob/14ec5e0c77f9867d97fe394f135d61c349ddd0b1/BGP212/MultiShift.lean), [THEOREMS.md](https://github.com/thinkthoughts/lean-bgp212/blob/14ec5e0c77f9867d97fe394f135d61c349ddd0b1/specs/paper/THEOREMS.md)
- [thinkthoughts/general-divisor-theorem](https://github.com/thinkthoughts/general-divisor-theorem) at `ec66260` (tag v1.0.0)
- [thinkthoughts/specification-grammar](https://github.com/thinkthoughts/specification-grammar) at `d958b81`: [SG\_0001\_SPECIFICATION\_ROLES.md](https://github.com/thinkthoughts/specification-grammar/blob/d958b81fc073/SG_0001_SPECIFICATION_ROLES.md)
- [thinkthoughts/mathematical-basis](https://github.com/thinkthoughts/mathematical-basis) at `e571a60`: [papers/SCOPE.md](https://github.com/thinkthoughts/mathematical-basis/blob/e571a609caa7/papers/SCOPE.md), [sources/readingpoint/README.md](https://github.com/thinkthoughts/mathematical-basis/blob/e571a609caa7/sources/readingpoint/README.md)
- [google-deepmind/formal-conjectures](https://github.com/google-deepmind/formal-conjectures) at `37f0808`: [TwinPrimes.lean](https://github.com/google-deepmind/formal-conjectures/blob/37f0808b83c56c8cef4ea5816b8329c09b8905a8/FormalConjectures/Wikipedia/TwinPrimes.lean), [Dickson.lean](https://github.com/google-deepmind/formal-conjectures/blob/37f0808b83c56c8cef4ea5816b8329c09b8905a8/FormalConjectures/Wikipedia/Dickson.lean), [Geometry/Metric.lean](https://github.com/google-deepmind/formal-conjectures/blob/37f0808b83c56c8cef4ea5816b8329c09b8905a8/FormalConjecturesForMathlib/Geometry/Metric.lean), [ErdosProblems/92.lean](https://github.com/google-deepmind/formal-conjectures/blob/37f0808b83c56c8cef4ea5816b8329c09b8905a8/FormalConjectures/ErdosProblems/92.lean)
- [leanprover-community/mathlib4](https://github.com/leanprover-community/mathlib4/tree/85e3a25e006c35636f0e53b0e9296caca2685bc0) at `85e3a25`
- [thinkthoughts/awards](https://github.com/thinkthoughts/awards), catalog snapshot from the attached fork
