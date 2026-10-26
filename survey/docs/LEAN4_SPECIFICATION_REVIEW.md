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
