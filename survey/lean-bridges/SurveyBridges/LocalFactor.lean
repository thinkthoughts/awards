import BGP212.Gap
import BGP212.MultiShift
import Mathlib.Algebra.Order.BigOperators.GroupWithZero.Finset
import SurveyBridges.AdmissibleTwin
import SurveyBridges.ResidueNu

/-!
# Local factors `p - ν_p(H)` and the per-period count `localCount`

`BGP212.MultiShift.localCount N m H = ∏ p ∈ (GDT.R N m).primeFactors, (p - nu p H)` is the
multi-shift GDT's exact count per period (`BGP212.Challenge.gdtH_count_per_period`, upstream).
This module proves its positivity facts directly from the definitions:

* `admissibleZ_iff_local_factor_pos`: `AdmissibleZ H` (global residue coverage, every prime)
  is equivalent to positivity of every local factor `p - ν_p(H)`;
* `localCount_pos_iff`: `0 < localCount N m H` exactly when `ν_p(H) < p` at the primes of
  `R N m`; no hypothesis on `N`, `m` (natural subtraction truncates at `0`, so a zero factor
  is exactly `p ≤ ν_p(H)`);
* `localCount_pos_of_admissibleZ`: global admissibility makes every `localCount N m H` positive.

`AdmissibleZ H` and `BGP212.MultiShift.AdmissibleH N m a H` stay separate: `AdmissibleH`
concerns the fixed class `a` at the primes of `d N m`, while `localCount` ranges over the
primes of `R N m`; neither statement here mentions `a`.

`nu_singleton` and `localCount_singleton` reduce the single-shift case to
`∏ p ∈ (R N m).primeFactors, (p - 1)`, the first step toward `Nat.totient (R N m)`.
-/

namespace Survey.PrimeBridges

open BGP212.Gap

/-- **Local factor positivity.** `H` is admissible exactly when every local factor
`p - ν_p(H)` is positive. -/
theorem admissibleZ_iff_local_factor_pos (H : Finset ℤ) :
    AdmissibleZ H ↔ ∀ p : ℕ, p.Prime → 0 < p - BGP212.MultiShift.nu p H := by
  rw [admissibleZ_iff_nu_lt]
  exact forall_congr' fun p => forall_congr' fun _ => Nat.sub_pos_iff_lt.symm

/-- **Per-period count positivity.** `localCount N m H` is positive exactly when
`ν_p(H) < p` at every prime `p ∣ R N m`. -/
theorem localCount_pos_iff (N m : ℕ) (H : Finset ℤ) :
    0 < BGP212.MultiShift.localCount N m H ↔
      ∀ p ∈ (GDT.R N m).primeFactors, BGP212.MultiShift.nu p H < p := by
  unfold BGP212.MultiShift.localCount
  constructor
  · intro h p hp
    have hne := Finset.prod_ne_zero_iff.mp h.ne' p hp
    exact Nat.sub_pos_iff_lt.mp (Nat.pos_of_ne_zero hne)
  · intro h
    exact Finset.prod_pos fun p hp => Nat.sub_pos_iff_lt.mpr (h p hp)

/-- **Global admissibility gives a positive count for every `N`, `m`.** -/
theorem localCount_pos_of_admissibleZ (N m : ℕ) {H : Finset ℤ} (hH : AdmissibleZ H) :
    0 < BGP212.MultiShift.localCount N m H :=
  (localCount_pos_iff N m H).mpr fun p hp =>
    (admissibleZ_iff_nu_lt H).mp hH p (Nat.prime_of_mem_primeFactors hp)

/-- The twin-prime shifts give a positive per-period count for every `N`, `m`. -/
theorem localCount_twin_pos (N m : ℕ) :
    0 < BGP212.MultiShift.localCount N m ({0, 2} : Finset ℤ) :=
  localCount_pos_of_admissibleZ N m admissible_twin

/-- A single shift occupies exactly one class: `ν_p({a}) = 1` for every modulus `p`. -/
theorem nu_singleton (p : ℕ) (a : ℤ) : BGP212.MultiShift.nu p ({a} : Finset ℤ) = 1 := by
  unfold BGP212.MultiShift.nu
  rw [Finset.image_singleton, Finset.card_singleton]

/-- **Single shift.** `localCount N m {a} = ∏ p ∈ (R N m).primeFactors, (p - 1)`. -/
theorem localCount_singleton (N m : ℕ) (a : ℤ) :
    BGP212.MultiShift.localCount N m ({a} : Finset ℤ) =
      ∏ p ∈ (GDT.R N m).primeFactors, (p - 1) := by
  unfold BGP212.MultiShift.localCount
  exact Finset.prod_congr rfl fun p _ => by rw [nu_singleton]

#print axioms admissibleZ_iff_local_factor_pos
#print axioms localCount_pos_iff
#print axioms localCount_pos_of_admissibleZ
#print axioms localCount_twin_pos
#print axioms nu_singleton
#print axioms localCount_singleton

end Survey.PrimeBridges
