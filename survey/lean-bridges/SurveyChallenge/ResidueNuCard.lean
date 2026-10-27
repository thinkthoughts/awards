/-
Comparator Challenge for LIFT-ADM-6: `Survey.PrimeBridges.residueImage_card_eq_nu_of_modulus`.

Statement only, written from the registry statement of LIFT-ADM-6 (survey/registry/edges.json),
independently of the proof. It imports only `BGP212.Gap` and `BGP212.MultiShift` (lean-bgp212
89b43fa), so `nu` is lean-bgp212's own definition; `residueImage` is restated verbatim and
compared in full by Comparator. The proof's `negRep` and its lemmas do not appear. The `sorry`
is the challenge.
-/
import BGP212.Gap
import BGP212.MultiShift

namespace Survey.PrimeBridges

/-- The residue classes modulo `p` occupied by the shifts in `H`. Restated verbatim from
`SurveyBridges.ResidueImage` (sha256 91e79f6b088e32d6c228d3de9e11130fc12dcd2b5c4bd0e5fdc86ec51c48d91a): Comparator compares this definition, body
included, with the Solution's constant of the same name and rejects any difference. -/
def residueImage (p : ℕ) (H : Finset ℤ) : Finset (ZMod p) :=
  H.image (fun (h : ℤ) => (h : ZMod p))

open BGP212.Gap

/-- For every natural modulus, the residue image has exactly `ν_p(H)` elements. -/
theorem residueImage_card_eq_nu_of_modulus (p : ℕ) (H : Finset ℤ) :
    (residueImage p H).card = BGP212.MultiShift.nu p H :=
  sorry

end Survey.PrimeBridges
