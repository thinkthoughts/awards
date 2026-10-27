/-
Comparator Challenge for LIFT-GDT-5: `Survey.PrimeBridges.localCount_singleton_eq_totient`, with the steps it cites (`totient_prod_primes`, `R_eq_prod_sdiff`, `totient_R_eq_prod`, `localCount_zero_eq_totient`) and the boundary case `localCount_singleton_at_zero`.

Statements only, written from the registry (survey/registry/edges.json), independently of the
proofs. It imports only `BGP212.Gap` and `BGP212.MultiShift` (lean-bgp212 89b43fa), so
`AdmissibleZ`, `nu`, `localCount` and GDT v1.0.0's `R`, `d`, `rad` are lean-bgp212's own
definitions, compared by Comparator in full; no survey definition occurs in these statements,
so none is restated. The `sorry`s are the challenge.
-/
import BGP212.Gap
import BGP212.MultiShift

namespace Survey.PrimeBridges

-- No `open`: as in the bridge module, these statements use full names.

/-- Euler's product for a product of distinct primes. -/
theorem totient_prod_primes {T : Finset ℕ} (hT : ∀ p ∈ T, p.Prime) :
    Nat.totient (∏ p ∈ T, p) = ∏ p ∈ T, (p - 1) :=
  sorry

/-- `R N m` is the product of the primes of `N` that do not divide `gcd m N`. -/
theorem R_eq_prod_sdiff {N : ℕ} (hN : 0 < N) (m : ℕ) :
    GDT.R N m = ∏ p ∈ N.primeFactors \ (Nat.gcd m N).primeFactors, p :=
  sorry

/-- `φ(R N m)` is the product of the local factors `p - 1` over the primes of `R N m`. -/
theorem totient_R_eq_prod {N : ℕ} (hN : 0 < N) (m : ℕ) :
    Nat.totient (GDT.R N m) = ∏ p ∈ (GDT.R N m).primeFactors, (p - 1) :=
  sorry

/-- Single-shift compatibility: for `0 < N`, one shift gives GDT v1.0.0's count per period. -/
theorem localCount_singleton_eq_totient {N : ℕ} (hN : 0 < N) (m : ℕ) (a : ℤ) :
    BGP212.MultiShift.localCount N m ({a} : Finset ℤ) = Nat.totient (GDT.R N m) :=
  sorry

/-- The shift `0`, the third conjunct of upstream `BGP212.Challenge.gdtH_single_shift`. -/
theorem localCount_zero_eq_totient {N : ℕ} (hN : 0 < N) (m : ℕ) :
    BGP212.MultiShift.localCount N m ({0} : Finset ℤ) = Nat.totient (GDT.R N m) :=
  sorry

/-- `0 < N` is needed: at `N = 0, m = 2`, the count is `1` and `φ(R 0 2) = φ 0 = 0`. -/
theorem localCount_singleton_at_zero :
    BGP212.MultiShift.localCount 0 2 ({0} : Finset ℤ) = 1 ∧ Nat.totient (GDT.R 0 2) = 0 :=
  sorry

end Survey.PrimeBridges
