# Lean 4 specification review — prime-gap bridges

**Reading point:** October 2026  
**Public page:** https://translatepi.ai/lean4  
**Survey branch:** https://github.com/thinkthoughts/awards/tree/survey/prime-bridges/survey  
**Purpose:** Record the conclusions of the independent DeepSeek review, the existing Lean evidence, and the next specification questions. This document is a development note, not an official catalog submission.

## 1. Established declarations and evidence

The following claims are grounded in the reported MBP Lean 4.34.0-rc2 runs against `lean-bgp212` commit `89b43fa019337645b4c2c66ae917bcb1fe76450f` and the source hashes recorded in the survey registry.

| Lean declaration | Result | Evidence |
| --- | --- | --- |
| `Survey.PrimeBridges.h1Le_mono` | Monotonicity of `H1Le` in its bound | EV-0002, EV-0003; non-isolating Comparator acceptance EV-0006 |
| `Survey.PrimeBridges.admissible_twin` | `AdmissibleZ ({0, 2} : Finset ℤ)` | EV-0003 |
| `Survey.PrimeBridges.twin_primes_iff_h1Le_two` | `InfinitelyManyTwinPrimes ↔ H1Le 2` | EV-0004 |
| `Survey.PrimeBridges.twin_primes_implies_h1Le_186` | `InfinitelyManyTwinPrimes → H1Le 186` | EV-0005 |

These kernel checks reported the axioms `propext`, `Classical.choice`, and `Quot.sound`. Under the survey's stricter evidence policy, Linux-isolated Comparator acceptance is tracked separately; EV-0006 records a macOS, non-isolating Comparator acceptance for `h1Le_mono`.

### Twin-prime equivalence: review correction

DeepSeek flagged a possible missing treatment of the exceptional prime gap between 2 and 3. The checked source already contains:

```lean
nth_succ_eq_add_two
h1Le_two_of_twin_primes
twin_primes_of_h1Le_two
twin_primes_iff_h1Le_two
```

The first lemma establishes the relevant eventual gap-2 behavior for indices at least one. The two directions and their equivalence were kernel-checked in EV-0004. The reviewer should inspect the source and provide an explicit counterexample or a precise formal discrepancy before reopening that result.

The equivalence concerns two formulations. It makes no assertion that either conjectural proposition has been established unconditionally.

## 2. Leading-specification candidates

### A. Admissibility and residue coverage

The current BGP212 definition is:

```lean
def AdmissibleZ (H : Finset ℤ) : Prop :=
  ∀ p : ℕ, p.Prime → ∃ r : ℤ, ∀ h ∈ H, ¬ ((p : ℤ) ∣ h - r)
```

For a prime `p`, admissibility means the image of the shifts in `ZMod p` omits a residue class. Thus the following is a **mathematical candidate for formalization**:

\[
\operatorname{AdmissibleZ}(H)
\iff \forall p\;\text{prime},\quad
\bigl|\{(h\bmod p):h\in H\}\bigr|<p.
\]

Equivalently, one can use `−h` residue classes; negation is a bijection of `ZMod p`. The precise Lean statement, type casts, `Finset.image` and cardinality lemmas must be tested against the pinned Mathlib. This is not yet a compiled theorem.

Potential declarations:

```lean
admissibleZ_iff_residue_image_card_lt
admissibleZ_iff_omits_residue
```

### B. Admissibility under subsets

Candidate statement:

```lean
theorem admissibleZ_mono {H K : Finset ℤ}
    (hKH : K ⊆ H) (hH : BGP212.Gap.AdmissibleZ H) :
    BGP212.Gap.AdmissibleZ K
```

This follows mathematically by retaining the omitted residue for `H`, then restricting the universal condition to `K`. Exact Lean proof is pending.

### C. Two-shift admissibility

Study `AdmissibleZ ({a,b} : Finset ℤ)` and identify the exact condition on `a-b`. The twin tuple `{0,2}` is one instance. Handle duplicate shifts and the prime `2` explicitly.

### D. DHL and bounded-gap interfaces

`DHL k m` is a parameterized proposition. Separate the hypothesis from applications of `dhl_implies_gap`, the required admissible tuple, and its diameter certificate. The existing `Solution/Gap.lean` general theorem should be reused where possible. Concrete `40`-tuple and `186` claims require an explicit source and kernel-checked tuple certificate.

### E. General linear forms

Dickson-type statements use forms `aᵢ*n+bᵢ`. The monic shift predicate `AdmissibleZ` expresses the `aᵢ=1` case. A general-forms interface needs its own definitions and quantified local conditions before any correspondence is certified.

## 3. Evidence rules for the survey

- Distinguish **definition**, **general theorem**, **instance**, **conditional implication**, and **candidate analogy**.
- Distinguish **mathematical hypotheses** from **proof verification status**.
- Prove typed edges before labeling them established relationships.
- For catalog connections, provide exact statement correspondence; keyword matching supplies candidates for inspection.
- Treat reach estimates as exploratory until supported by reproducible classification output and sampled matches.
- Record source commits, exact Lean signatures, hashes, axioms, and Comparator isolation mode.

## 4. Next questions for DeepSeek

1. Inspect `BGP212/Gap.lean` and `SurveyBridges/TwinPrimeEquiv.lean` at their pinned commits. Does `nth_succ_eq_add_two` settle your gap-1 concern? Quote the relevant theorem statements and explain the logic of each direction. If you find an actual defect, give the exact Lean declaration and failing mathematical step.
2. Specify `AdmissibleZ ↔ residue-image-cardinality < p` with well-typed Lean 4 declarations over `ZMod p`. Provide two candidate formulations: omitted residue and `Finset.image` cardinality. Verify sign and coercion conventions, including `p = 2` and empty `H`.
3. Identify existing Mathlib lemmas at pinned commit `85e3a25e006c35636f0e53b0e9296caca2685bc0` that discharge the `Finset`, `ZMod`, divisibility and cardinality steps. Quote exact declaration names and source paths; mark each as source-checked or candidate.
4. Derive the mathematical classification of two-element shift sets `AdmissibleZ ({a,b} : Finset ℤ)` and propose a general Lean theorem. Explain how `{0,2}` specializes it.
5. Check `dhl_implies_gap` in `Solution/Gap.lean` and distinguish reusable general theorem, concrete tuple certificate, and `DHL` analytic hypothesis. Propose the smallest new bridge for the 186-bound reading.
6. Rank only the next **three** general Lean targets by exact reusable dependencies and proof cost. For each, list a theorem statement, imports, intended proof lemmas, and evidence needed for its verification state. Include catalog IDs only where you have inspected the exact catalog statement.

**Requested output:** A concise technical Markdown response with a `source-checked / inferred / proposed` label for each claim. No repository edits or claims of compiled proofs.

---

## 5. Review 2 — admissibility and residue coverage

**Reading point:** October 2026  
**Input:** DeepSeek's second read-only technical review. Its GitHub retrieval failed, so its Mathlib declaration names and proposed Lean proof terms remain candidates awaiting source inspection and compilation.

### 5.1 Established source definition

The previously inspected `BGP212/Gap.lean` defines:

```lean
def AdmissibleZ (H : Finset ℤ) : Prop :=
  ∀ p : ℕ, p.Prime → ∃ r : ℤ, ∀ h ∈ H, ¬ ((p : ℤ) ∣ h - r)
```

This is the authoritative starting point for the next bridge. A residue omission may be represented by the image of `h` or `-h` in `ZMod p`; negation permutes the residue classes and preserves coverage and image cardinality.

### 5.2 General theorem targets

The following are **Specified in this review**, pending Lean source, kernel compilation, axiom audit, registry entries, and Comparator evidence. They do not yet have recorded proof status in `survey/registry`.

| Candidate declaration | Mathematical content | Dependencies / proof obligations |
| --- | --- | --- |
| `admissibleZ_iff_omits_residue` | Every prime modulus has an omitted residue of `H` | Connect integer divisibility to equality in `ZMod p`; lift the integer witness to `ZMod p` and back |
| `admissibleZ_iff_card_lt` | `AdmissibleZ H ↔ ∀ p, p.Prime → (residueImage p H).card < p` | Finite-type card for `ZMod p`, image versus universal set, prime positivity |
| `admissibleZ_subset` | `K ⊆ H → AdmissibleZ H → AdmissibleZ K` | Reuse each omitted residue for the subset; a direct proof may avoid cardinality lemmas |
| `admissibleZ_pair_iff_even` | `AdmissibleZ ({a,b} : Finset ℤ) ↔ Even (b-a)` | Modulus two covers both classes exactly for opposite-parity shifts; moduli greater than two have more classes than two shifts |

For distinct shifts, the pair classification reduces to a parity condition. The statement also covers `a=b`, where the `Finset` is a singleton and the difference is zero.

The existing `Survey.PrimeBridges.admissible_twin` is the `{a,b}={0,2}` reading of the proposed pair classification. Its existing kernel evidence remains EV-0003; deriving it again from the new general theorem would be an additional corollary.

### 5.3 Mathematical check of two-element admissibility

For `H={a,b}`, the residue image has cardinality at most two. At a prime `p>2`, it omits a class. At `p=2`, it omits a class exactly where `a` and `b` share parity. Thus:

\[
\operatorname{AdmissibleZ}(\{a,b\})\iff 2\mid(b-a).
\]

Examples: `{0,2}`, `{0,4}`, and `{3,9}` are admissible; `{0,1}` and `{7,12}` cover both residues modulo two.

The substitution `h ↦ -h` leaves this classification unchanged. DeepSeek's suggestion that the parity criterion might flip under the sign convention is corrected here.

### 5.4 DHL distinctions retained

1. `DHL k 2` is a parameterized proposition and may appear as a named hypothesis.
2. `dhl_implies_gap` is a general implication requiring a certified admissible tuple and diameter bound.
3. A particular bounded-gap conclusion requires its specific premises and explicit tuple certificate.
4. `twin_primes_implies_h1Le_186` is an independently kernel-checked implication obtained by composing the twin-prime equivalence with `h1Le_mono`. Its proof uses the twin-prime premise.

The next work should reuse the general `dhl_implies_gap` statement already present in `Solution/Gap.lean`; any new package interface should provide a genuine new dependency or reproducibility benefit.

### 5.5 Decisions and source checks

- **Keep** the existing kernel-checked twin-prime equivalence and its gap-one lemma. EV-0004 covers their reported kernel checks.
- **Develop first** the omitted-residue bridge, then cardinality, subset closure, and the two-element classification.
- **Verify exact Mathlib identifiers** against the pinned commit before treating proposed lemma names as existing declarations.
- **Separate exploratory reach estimates** from catalog statement matches established through explicit mathematical reduction.
- **Continue** the current Linux-isolated Comparator milestone independently of these proposed generalizations.

## 6. Next questions for DeepSeek — round 3

1. Using the exact `AdmissibleZ` definition quoted in §5.1, give a Lean proof plan for `admissibleZ_iff_omits_residue`. Specify the intermediate lemma relating `((p:ℤ) ∣ h-r)` to equality of `(h : ZMod p)` and `(r : ZMod p)`. State clearly which lemma names are verified and which are candidates.
2. Specify `residueImage` and `admissibleZ_iff_card_lt` with correct `ZMod p` types. Provide the precise conversion between `Finset.image` being a proper subset of `Finset.univ` and having cardinality less than `p`, including the `p.Prime` hypothesis.
3. Give the shortest direct proof strategy for `admissibleZ_subset` using the original quantifier definition, independent of the proposed cardinality theorem. Identify the exact `Finset` membership step.
4. Develop a structured proof of `admissibleZ_pair_iff_even` with separate `p=2` and `p>2` cases. Cover `a=b`, negative integers, and `ZMod 2` coercions. Give a minimal sequence of supporting lemmas rather than a monolithic tactic proof.
5. Compare two implementation orders: direct subset/pair proofs from `AdmissibleZ`, versus first establishing `ZMod` coverage and cardinality bridges. Identify which produces the smallest reusable dependency graph.
6. Return a three-step handoff for Claude: exact proposed module names, theorem declarations, import requirements, and one local compilation milestone per step. Keep every uncompiled claim explicitly proposed.

**Requested output:** a focused Lean engineering note, with source-checked / inferred / proposed labels. Read-only; omit unrelated catalog reach claims.
