/-
Comparator Challenge for LIFT-ADM-4: `Survey.PrimeBridges.admissibleZ_iff_omits_residue`.

Statement only, written from the registry statement of LIFT-ADM-4 (survey/registry/edges.json),
independently of the proof. It imports only `BGP212.Gap` (lean-bgp212 89b43fa), whose import
closure already contains Mathlib's `ZMod` (Mathlib.Data.ZMod.Basic, via Mathlib.Data.Nat.Totient).
The statement mentions the survey definition `residueImage`, so the Challenge states that
definition too. Comparator checks every constant the statement uses: names, types and values
must be identical in Challenge and Solution (no definition holes are declared). The `sorry` is
the challenge.
-/
import BGP212.Gap

namespace Survey.PrimeBridges

/-- The residue classes modulo `p` occupied by the shifts in `H`. Restated verbatim from
`SurveyBridges.ResidueImage` (sha256 91e79f6b088e32d6c228d3de9e11130fc12dcd2b5c4bd0e5fdc86ec51c48d91a): Comparator compares this definition, body
included, with the Solution's constant of the same name and rejects any difference. -/
def residueImage (p : ℕ) (H : Finset ℤ) : Finset (ZMod p) :=
  H.image (fun (h : ℤ) => (h : ZMod p))

open BGP212.Gap

/-- Omitted residues: admissibility as an omitted residue class modulo every prime. -/
theorem admissibleZ_iff_omits_residue (H : Finset ℤ) :
    AdmissibleZ H ↔
      ∀ p : ℕ, p.Prime → ∃ r : ZMod p, r ∉ residueImage p H :=
  sorry

end Survey.PrimeBridges
