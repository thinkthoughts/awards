import BGP212.Gap
import BGP212.MultiShift
import SurveyBridges.ResidueImage
import SurveyBridges.AdmissibleTwin
import SurveyBridges.AdmissibleZMod

/-!
# Residue images and the multi-shift local factor `ν_p(H)`

`BGP212.MultiShift.nu p H` counts the canonical integer remainders `(-h) % p` for `h ∈ H`;
`residueImage p H` collects the residues `(h : ZMod p)`. The two sets correspond through

  `negRep p : ZMod p → ℤ`,  `x ↦ ZMod.cast (-x)`,

the canonical representative of the negated class:

* `negRep p (h : ZMod p) = (-h) % p` (`ZMod.coe_intCast`, with `Int.cast_neg`), so the image of
  `H` under `h ↦ (-h) % p` is the image of `residueImage p H` under `negRep p`;
* `negRep p` is injective: casting back gives `-x` (`ZMod.intCast_zmod_cast`), and negation is a
  permutation of `ZMod p` (`neg_injective`).

Both facts hold for every natural modulus, `p = 0` included (`ZMod 0 = ℤ`, `h % 0 = h`), so the
cardinality equation needs no hypothesis on `p`. The prime form keeps the statement used by the
admissibility specification, and `admissibleZ_iff_nu_lt` joins `admissibleZ_iff_card_lt` to the
local factor.
-/

namespace Survey.PrimeBridges

open BGP212.Gap

/-- The canonical integer representative of the negated residue class: `ZMod.cast (-x)`. -/
def negRep (p : ℕ) (x : ZMod p) : ℤ :=
  ZMod.cast (-x)

/-- On reductions of integers, `negRep` is the remainder used by `BGP212.MultiShift.nu`. -/
theorem negRep_intCast (p : ℕ) (h : ℤ) :
    negRep p (h : ZMod p) = (-h) % (p : ℤ) := by
  unfold negRep
  rw [← Int.cast_neg]
  exact ZMod.coe_intCast (-h)

/-- `negRep p` is injective: negation permutes `ZMod p`, and `ZMod.cast` is a section of the
reduction `ℤ → ZMod p`. -/
theorem negRep_injective (p : ℕ) : Function.Injective (negRep p) := by
  intro x y hxy
  have h := congrArg (fun z : ℤ => (z : ZMod p)) hxy
  simp only [negRep, ZMod.intCast_zmod_cast] at h
  exact neg_injective h

/-- The remainders counted by `nu` are the `negRep`-image of the residue image. -/
theorem image_neg_emod_eq_image_negRep (p : ℕ) (H : Finset ℤ) :
    H.image (fun h => (-h) % (p : ℤ)) = (residueImage p H).image (negRep p) := by
  unfold residueImage
  rw [Finset.image_image]
  apply Finset.image_congr
  intro h _
  exact (negRep_intCast p h).symm

/-- **Residue image and local factor, every modulus.** For every natural `p`, the residue image
of `H` in `ZMod p` has exactly `ν_p(H)` elements. -/
theorem residueImage_card_eq_nu_of_modulus (p : ℕ) (H : Finset ℤ) :
    (residueImage p H).card = BGP212.MultiShift.nu p H :=
  calc (residueImage p H).card
      = ((residueImage p H).image (negRep p)).card :=
        (Finset.card_image_of_injective _ (negRep_injective p)).symm
    _ = (H.image fun h => (-h) % (p : ℤ)).card := by
        rw [image_neg_emod_eq_image_negRep]
    _ = BGP212.MultiShift.nu p H := rfl

/-- **Residue image and local factor, prime modulus**: the form used with admissibility. The
equation holds for every modulus (`residueImage_card_eq_nu_of_modulus`). -/
theorem residueImage_card_eq_nu
    (p : ℕ) (hp : p.Prime) (H : Finset ℤ) :
    (residueImage p H).card =
      BGP212.MultiShift.nu p H :=
  residueImage_card_eq_nu_of_modulus p H

/-- **Admissibility through the local factor.** `H` is admissible exactly when
`ν_p(H) < p` for every prime `p`, i.e. every local factor `p - ν_p(H)` is positive. -/
theorem admissibleZ_iff_nu_lt (H : Finset ℤ) :
    AdmissibleZ H ↔
      ∀ p : ℕ, p.Prime →
        BGP212.MultiShift.nu p H < p := by
  rw [admissibleZ_iff_card_lt]
  exact forall_congr' fun p => forall_congr' fun hp => by
    rw [residueImage_card_eq_nu p hp H]

/-- The twin-prime shifts `{0, 2}` leave a class free at every prime: `ν_p({0, 2}) < p`, via the
kernel-checked `admissible_twin`. -/
theorem nu_twin_lt :
    ∀ p : ℕ, p.Prime → BGP212.MultiShift.nu p ({0, 2} : Finset ℤ) < p :=
  (admissibleZ_iff_nu_lt _).mp admissible_twin

#print axioms negRep_intCast
#print axioms negRep_injective
#print axioms image_neg_emod_eq_image_negRep
#print axioms residueImage_card_eq_nu_of_modulus
#print axioms residueImage_card_eq_nu
#print axioms admissibleZ_iff_nu_lt
#print axioms nu_twin_lt

end Survey.PrimeBridges
