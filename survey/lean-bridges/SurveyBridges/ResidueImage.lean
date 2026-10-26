import BGP212.Gap
import Mathlib.Data.ZMod.Basic

/-!
# Residue images of shift sets

`residueImage p H` is the set of residue classes modulo `p` met by the shifts in `H`. The bridge
lemma `dvd_sub_iff_intCast_eq` turns the divisibility used in `BGP212.Gap.AdmissibleZ`,
`(p : ℤ) ∣ h - r`, into equality of residues `(h : ZMod p) = (r : ZMod p)`; it holds for every
modulus `p`.
-/

namespace Survey.PrimeBridges

/-- The residue classes modulo `p` occupied by the shifts in `H`. -/
def residueImage (p : ℕ) (H : Finset ℤ) : Finset (ZMod p) :=
  H.image (fun (h : ℤ) => (h : ZMod p))

/-- A residue lies in `residueImage p H` exactly when some shift reduces to it. -/
theorem mem_residueImage {p : ℕ} {H : Finset ℤ} {x : ZMod p} :
    x ∈ residueImage p H ↔ ∃ h ∈ H, (h : ZMod p) = x := by
  unfold residueImage
  exact Finset.mem_image (α := ℤ) (β := ZMod p) (f := fun (h : ℤ) => (h : ZMod p))
    (s := H) (b := x)

/-- Divisibility of a difference by `p` is equality of residues modulo `p`
(`ZMod.intCast_eq_intCast_iff_dvd_sub`, with the sides exchanged). -/
theorem dvd_sub_iff_intCast_eq {p : ℕ} (h r : ℤ) :
    (p : ℤ) ∣ h - r ↔ (h : ZMod p) = (r : ZMod p) :=
  (ZMod.intCast_eq_intCast_iff_dvd_sub r h p).symm.trans eq_comm

/-- Every residue modulo `p` is the reduction of the integer `ZMod.cast r`. -/
theorem intCast_cast_residue {p : ℕ} (r : ZMod p) :
    ((ZMod.cast r : ℤ) : ZMod p) = r :=
  ZMod.intCast_zmod_cast r

#print axioms mem_residueImage
#print axioms dvd_sub_iff_intCast_eq
#print axioms intCast_cast_residue

end Survey.PrimeBridges
