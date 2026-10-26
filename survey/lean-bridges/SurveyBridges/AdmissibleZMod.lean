import BGP212.Gap
import Mathlib.Data.Fintype.Card
import SurveyBridges.ResidueImage
import SurveyBridges.AdmissibleTwin
import SurveyBridges.AdmissibleSubset
import SurveyBridges.AdmissiblePair

/-!
# Admissibility as an omitted residue class in `ZMod p`

`BGP212.Gap.AdmissibleZ H` (unchanged) asks for an integer `r` with `¬ (p : ℤ) ∣ h - r` for every
`h ∈ H`. Through `dvd_sub_iff_intCast_eq` this is a residue `(r : ZMod p)` outside
`residueImage p H`; conversely an omitted residue `r : ZMod p` gives the integer `ZMod.cast r`.
For a prime `p`, `ZMod p` has exactly `p` elements, so an omitted residue is the same as
`(residueImage p H).card < p`.

The applications at the end reuse the kernel-checked results `admissible_twin`,
`admissibleZ_subset`, `admissibleZ_singleton`, `admissibleZ_pair_self`,
`admissibleZ_pair_iff_even` and `not_admissibleZ_zero_one`.
-/

namespace Survey.PrimeBridges

open BGP212.Gap

/-- **Omitted residues.** `H` is admissible exactly when, for every prime `p`, some residue
class modulo `p` lies outside the residue image of `H`. -/
theorem admissibleZ_iff_omits_residue (H : Finset ℤ) :
    AdmissibleZ H ↔
      ∀ p : ℕ, p.Prime → ∃ r : ZMod p, r ∉ residueImage p H := by
  constructor
  · intro hH p hp
    obtain ⟨r, hr⟩ := hH p hp
    refine ⟨(r : ZMod p), fun hmem => ?_⟩
    obtain ⟨h, hh, he⟩ := mem_residueImage.mp hmem
    exact hr h hh ((dvd_sub_iff_intCast_eq h r).mpr he)
  · intro hH p hp
    obtain ⟨r, hr⟩ := hH p hp
    refine ⟨(ZMod.cast r : ℤ), fun h hh hd => hr ?_⟩
    have he : (h : ZMod p) = r :=
      ((dvd_sub_iff_intCast_eq h _).mp hd).trans (intCast_cast_residue r)
    exact mem_residueImage.mpr ⟨h, hh, he⟩

/-- For a prime `p`, a residue class is omitted exactly when the residue image has fewer than
`p` elements: a proper subset of `Finset.univ`, whose cardinality is `Fintype.card (ZMod p) = p`. -/
theorem omits_residue_iff_card_lt {p : ℕ} (hp : p.Prime) (H : Finset ℤ) :
    (∃ r : ZMod p, r ∉ residueImage p H) ↔ (residueImage p H).card < p := by
  haveI : NeZero p := ⟨hp.ne_zero⟩
  have key : (residueImage p H).card < p ↔ residueImage p H ≠ Finset.univ := by
    have h := Finset.card_lt_iff_ne_univ (residueImage p H)
    rwa [ZMod.card p] at h
  rw [key]
  constructor
  · rintro ⟨r, hr⟩ he
    apply hr
    rw [he]
    exact Finset.mem_univ r
  · intro hne
    by_contra hall
    apply hne
    exact Finset.eq_univ_iff_forall.mpr fun x => by
      by_contra hx
      exact hall ⟨x, hx⟩

/-- **Residue counting.** `H` is admissible exactly when, for every prime `p`, the shifts of `H`
occupy fewer than `p` residue classes modulo `p`. -/
theorem admissibleZ_iff_card_lt (H : Finset ℤ) :
    AdmissibleZ H ↔
      ∀ p : ℕ, p.Prime → (residueImage p H).card < p := by
  rw [admissibleZ_iff_omits_residue]
  exact forall_congr' fun p => forall_congr' fun hp => omits_residue_iff_card_lt hp H

/-! ### Applications of the general theorems to the existing results -/

/-- Empty shift set, via `admissibleZ_subset` from a singleton. -/
theorem card_lt_residueImage_empty :
    ∀ p : ℕ, p.Prime → (residueImage p (∅ : Finset ℤ)).card < p :=
  (admissibleZ_iff_card_lt ∅).mp
    (admissibleZ_subset (Finset.empty_subset _) (admissibleZ_singleton 0))

/-- Singleton shift sets, via `admissibleZ_singleton`. -/
theorem card_lt_residueImage_singleton (a : ℤ) :
    ∀ p : ℕ, p.Prime → (residueImage p ({a} : Finset ℤ)).card < p :=
  (admissibleZ_iff_card_lt _).mp (admissibleZ_singleton a)

/-- Duplicate shifts, via `admissibleZ_pair_self`. -/
theorem omits_residue_pair_self (a : ℤ) :
    ∀ p : ℕ, p.Prime → ∃ r : ZMod p, r ∉ residueImage p ({a, a} : Finset ℤ) :=
  (admissibleZ_iff_omits_residue _).mp (admissibleZ_pair_self a)

/-- The twin-prime shifts `{0, 2}`, via the kernel-checked `admissible_twin`. -/
theorem card_lt_residueImage_twin :
    ∀ p : ℕ, p.Prime → (residueImage p ({0, 2} : Finset ℤ)).card < p :=
  (admissibleZ_iff_card_lt _).mp admissible_twin

/-- `{0, 1}` occupies every residue class for some prime (in fact `p = 2`), via
`not_admissibleZ_zero_one`. -/
theorem not_card_lt_residueImage_zero_one :
    ¬ ∀ p : ℕ, p.Prime → (residueImage p ({0, 1} : Finset ℤ)).card < p :=
  fun h => not_admissibleZ_zero_one ((admissibleZ_iff_card_lt _).mpr h)

/-- Negative shifts: `{-3, -1}` omits a residue class modulo every prime, via
`admissibleZ_pair_iff_even` (`-1 - (-3) = 1 + 1`). -/
theorem omits_residue_neg_three_neg_one :
    ∀ p : ℕ, p.Prime → ∃ r : ZMod p, r ∉ residueImage p ({-3, -1} : Finset ℤ) :=
  (admissibleZ_iff_omits_residue _).mp ((admissibleZ_pair_iff_even (-3) (-1)).mpr ⟨1, by omega⟩)

#print axioms admissibleZ_iff_omits_residue
#print axioms omits_residue_iff_card_lt
#print axioms admissibleZ_iff_card_lt
#print axioms card_lt_residueImage_empty
#print axioms card_lt_residueImage_singleton
#print axioms omits_residue_pair_self
#print axioms card_lt_residueImage_twin
#print axioms not_card_lt_residueImage_zero_one
#print axioms omits_residue_neg_three_neg_one

end Survey.PrimeBridges
