import BGP212.MultiShift
import Mathlib.Data.Nat.Totient
import Mathlib.Data.Nat.Squarefree
import SurveyBridges.LocalFactor

/-!
# Single-shift compatibility: `localCount N m {a} = φ(R N m)`

GDT v1.0.0 counts `φ(R N m)` accepted values per period; the multi-shift count at one shift is
`localCount N m {a} = ∏ p ∈ (R N m).primeFactors, (p - 1)` (`localCount_singleton`). The two agree
once `R N m` is a product of distinct primes. With `0 < N`:

* `R_eq_prod_sdiff`: `R N m = ∏ p ∈ N.primeFactors \ (gcd m N).primeFactors, p`, because
  `rad N = ∏ p ∈ N.primeFactors, p` splits over `(gcd m N).primeFactors ⊆ N.primeFactors`
  (`Finset.prod_sdiff`) and the second factor is `d N m`;
* `totient_prod_primes`: for a finite set `T` of primes, `φ(∏ p ∈ T, p) = ∏ p ∈ T, (p - 1)`
  (`Nat.totient_eq_div_primeFactors_mul` with `Nat.primeFactors_prod`).

This route uses the explicit prime product, so squarefreeness of `R N m` enters only through
`Nat.primeFactors_prod`. The hypothesis `0 < N` is necessary: `localCount_singleton_at_zero`
records `N = 0, m = 2`, where the count is `1` and `φ(R 0 2) = φ 0 = 0`.

All statements are about the shift set `{a}` and the definitions `GDT.R`, `GDT.d`, `GDT.rad`;
the class condition `AdmissibleH` (upstream `gdtH_single_shift`, first conjunct) is separate.
-/

namespace Survey.PrimeBridges

/-- Euler's product for a product of distinct primes. -/
theorem totient_prod_primes {T : Finset ℕ} (hT : ∀ p ∈ T, p.Prime) :
    Nat.totient (∏ p ∈ T, p) = ∏ p ∈ T, (p - 1) := by
  have hne : ∏ p ∈ T, p ≠ 0 := Finset.prod_ne_zero_iff.mpr fun p hp => (hT p hp).ne_zero
  rw [Nat.totient_eq_div_primeFactors_mul, Nat.primeFactors_prod hT,
    Nat.div_self (Nat.pos_of_ne_zero hne), one_mul]

/-- `R N m` is the product of the primes of `N` that do not divide `gcd m N`. -/
theorem R_eq_prod_sdiff {N : ℕ} (hN : 0 < N) (m : ℕ) :
    GDT.R N m = ∏ p ∈ N.primeFactors \ (Nat.gcd m N).primeFactors, p := by
  have hsub : (Nat.gcd m N).primeFactors ⊆ N.primeFactors :=
    Nat.primeFactors_mono (Nat.gcd_dvd_right m N) hN.ne'
  have hsplit : (∏ p ∈ N.primeFactors \ (Nat.gcd m N).primeFactors, p) *
      (∏ p ∈ (Nat.gcd m N).primeFactors, p) = ∏ p ∈ N.primeFactors, p :=
    Finset.prod_sdiff hsub
  have hpos : 0 < ∏ p ∈ (Nat.gcd m N).primeFactors, p :=
    Finset.prod_pos fun p hp => (Nat.prime_of_mem_primeFactors hp).pos
  unfold GDT.R GDT.d GDT.rad
  show (∏ p ∈ N.primeFactors, p) / (∏ p ∈ (Nat.gcd m N).primeFactors, p) = _
  rw [← hsplit, Nat.mul_div_cancel _ hpos]

/-- `φ(R N m)` is the product of the local factors `p - 1` over the primes of `R N m`. -/
theorem totient_R_eq_prod {N : ℕ} (hN : 0 < N) (m : ℕ) :
    Nat.totient (GDT.R N m) = ∏ p ∈ (GDT.R N m).primeFactors, (p - 1) := by
  have hT : ∀ p ∈ N.primeFactors \ (Nat.gcd m N).primeFactors, p.Prime :=
    fun p hp => Nat.prime_of_mem_primeFactors (Finset.mem_sdiff.mp hp).1
  rw [R_eq_prod_sdiff hN m, Nat.primeFactors_prod hT, totient_prod_primes hT]

/-- **Single-shift compatibility.** For `0 < N`, one shift gives GDT v1.0.0's count per period. -/
theorem localCount_singleton_eq_totient {N : ℕ} (hN : 0 < N) (m : ℕ) (a : ℤ) :
    BGP212.MultiShift.localCount N m ({a} : Finset ℤ) = Nat.totient (GDT.R N m) := by
  rw [localCount_singleton, totient_R_eq_prod hN m]

/-- The shift `0`, the third conjunct of upstream `BGP212.Challenge.gdtH_single_shift`. -/
theorem localCount_zero_eq_totient {N : ℕ} (hN : 0 < N) (m : ℕ) :
    BGP212.MultiShift.localCount N m ({0} : Finset ℤ) = Nat.totient (GDT.R N m) :=
  localCount_singleton_eq_totient hN m 0

/-- The hypothesis `0 < N` is needed: at `N = 0, m = 2`, `R 0 2 = 0`, the count is `1` and
`φ 0 = 0`. -/
theorem localCount_singleton_at_zero :
    BGP212.MultiShift.localCount 0 2 ({0} : Finset ℤ) = 1 ∧ Nat.totient (GDT.R 0 2) = 0 := by
  have hR : GDT.R 0 2 = 0 := by
    unfold GDT.R GDT.d GDT.rad
    rw [Nat.primeFactors_zero, Nat.gcd_zero_right, Nat.Prime.primeFactors Nat.prime_two,
      Finset.prod_empty, Finset.prod_singleton]
    rfl
  refine ⟨?_, by rw [hR, Nat.totient_zero]⟩
  rw [localCount_singleton, hR, Nat.primeFactors_zero, Finset.prod_empty]

#print axioms totient_prod_primes
#print axioms R_eq_prod_sdiff
#print axioms totient_R_eq_prod
#print axioms localCount_singleton_eq_totient
#print axioms localCount_zero_eq_totient
#print axioms localCount_singleton_at_zero

end Survey.PrimeBridges
