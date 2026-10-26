import BGP212.Gap
import SurveyBridges.AdmissibleSubset

/-!
# Admissible pairs

A two-element shift set `{a, b}` is admissible exactly when `b - a` is even.

* `p = 2`: an omitted class `r` makes `a - r` and `b - r` both odd, so `b - a` is even;
  conversely, for even `b - a`, the class `a + 1` is omitted.
* `p ≥ 3`: two shifts meet at most two of the `p` classes. Concretely, `a + 1` is omitted
  unless `p ∣ b - (a + 1)`, and then `a + 2` is omitted, since `p` divides neither `1` nor `2`.

The statement covers duplicate shifts (`a = b`, where `{a, a} = {a}`) and arbitrary integers,
negative ones included. `admissible_twin` in `SurveyBridges.AdmissibleTwin` stays as it is;
`admissible_twin_of_pair` derives the same statement from the classification.
-/

namespace Survey.PrimeBridges

open BGP212.Gap

/-- A prime `p ≥ 3` divides neither `1` nor `2` in `ℤ`. -/
private theorem not_dvd_one_two {p : ℕ} (hp3 : 3 ≤ p) :
    ¬ (p : ℤ) ∣ 1 ∧ ¬ (p : ℤ) ∣ 2 := by
  constructor
  · intro hd
    have h : p ∣ 1 := by exact_mod_cast hd
    have := Nat.le_of_dvd (by decide) h
    omega
  · intro hd
    have h : p ∣ 2 := by exact_mod_cast hd
    have := Nat.le_of_dvd (by decide) h
    omega

/-- **Admissible pairs.** `{a, b}` is admissible exactly when `b - a` is even. -/
theorem admissibleZ_pair_iff_even (a b : ℤ) :
    AdmissibleZ ({a, b} : Finset ℤ) ↔ Even (b - a) := by
  constructor
  · -- p = 2: both shifts avoid the class r, so both differences to r are odd.
    intro hH
    obtain ⟨r, hr⟩ := hH 2 Nat.prime_two
    have ha : ¬ (2 : ℤ) ∣ a - r := by
      exact_mod_cast hr a (Finset.mem_insert_self a {b})
    have hb : ¬ (2 : ℤ) ∣ b - r := by
      exact_mod_cast hr b (Finset.mem_insert_of_mem (Finset.mem_singleton_self b))
    rw [Int.even_iff]
    omega
  · rintro ⟨k, hk⟩ p hp
    have hp2 : 2 ≤ p := hp.two_le
    rcases Nat.lt_or_ge p 3 with hp3 | hp3
    · -- p = 2: the class a + 1 is omitted, as b - a is even.
      obtain rfl : p = 2 := by omega
      refine ⟨a + 1, fun h hh => ?_⟩
      simp only [Finset.mem_insert, Finset.mem_singleton] at hh
      have hodd : ¬ (2 : ℤ) ∣ h - (a + 1) := by
        rcases hh with hh | hh <;> rw [hh] <;> omega
      exact_mod_cast hodd
    · -- p ≥ 3: two shifts leave one of the classes a + 1, a + 2 free.
      obtain ⟨h1, h2⟩ := not_dvd_one_two hp3
      by_cases hc : (p : ℤ) ∣ b - (a + 1)
      · refine ⟨a + 2, fun h hh => ?_⟩
        simp only [Finset.mem_insert, Finset.mem_singleton] at hh
        rcases hh with hh | hh <;> rw [hh] <;> intro hd
        · rw [show a - (a + 2) = -2 by omega] at hd
          exact h2 (dvd_neg.mp hd)
        · have h' := dvd_sub hc hd
          rw [show b - (a + 1) - (b - (a + 2)) = 1 by omega] at h'
          exact h1 h'
      · refine ⟨a + 1, fun h hh => ?_⟩
        simp only [Finset.mem_insert, Finset.mem_singleton] at hh
        rcases hh with hh | hh <;> rw [hh]
        · intro hd
          rw [show a - (a + 1) = -1 by omega] at hd
          exact h1 (dvd_neg.mp hd)
        · exact hc

/-- Duplicate shifts: `{a, a}` is admissible for every integer `a`. -/
theorem admissibleZ_pair_self (a : ℤ) :
    AdmissibleZ ({a, a} : Finset ℤ) :=
  (admissibleZ_pair_iff_even a a).mpr ⟨0, by omega⟩

/-- Every singleton shift set is admissible, as a subset of `{a, a}`. -/
theorem admissibleZ_singleton (a : ℤ) :
    AdmissibleZ ({a} : Finset ℤ) :=
  admissibleZ_subset (Finset.singleton_subset_iff.mpr (Finset.mem_insert_self a {a}))
    (admissibleZ_pair_self a)

/-- The twin-prime shifts `{0, 2}`, from the pair classification. -/
theorem admissible_twin_of_pair :
    AdmissibleZ ({0, 2} : Finset ℤ) :=
  (admissibleZ_pair_iff_even 0 2).mpr ⟨1, by omega⟩

/-- The odd-difference pair `{0, 1}` fails at `p = 2`. -/
theorem not_admissibleZ_zero_one :
    ¬ AdmissibleZ ({0, 1} : Finset ℤ) := by
  intro h
  have he := (admissibleZ_pair_iff_even 0 1).mp h
  rw [Int.even_iff] at he
  omega

#print axioms admissibleZ_pair_iff_even
#print axioms admissibleZ_pair_self
#print axioms admissibleZ_singleton
#print axioms admissible_twin_of_pair
#print axioms not_admissibleZ_zero_one

end Survey.PrimeBridges
