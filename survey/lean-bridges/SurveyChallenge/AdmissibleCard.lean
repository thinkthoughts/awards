/-
Comparator Challenge for LIFT-ADM-5: `Survey.PrimeBridges.admissibleZ_iff_card_lt` (the lift's
registry statement) and its prime-wise step `Survey.PrimeBridges.omits_residue_iff_card_lt`.

Statements only, written from the registry (survey/registry/edges.json), independently of the
proofs. It imports only `BGP212.Gap`; `residueImage` is restated verbatim and compared in full
by Comparator, as in SurveyChallenge.AdmissibleOmits. The `sorry`s are the challenge.
-/
import BGP212.Gap

namespace Survey.PrimeBridges

/-- The residue classes modulo `p` occupied by the shifts in `H`. Restated verbatim from
`SurveyBridges.ResidueImage` (sha256 91e79f6b088e32d6c228d3de9e11130fc12dcd2b5c4bd0e5fdc86ec51c48d91a): Comparator compares this definition, body
included, with the Solution's constant of the same name and rejects any difference. -/
def residueImage (p : ℕ) (H : Finset ℤ) : Finset (ZMod p) :=
  H.image (fun (h : ℤ) => (h : ZMod p))

open BGP212.Gap

/-- For a prime `p`, a residue class is omitted exactly when fewer than `p` classes are met. -/
theorem omits_residue_iff_card_lt {p : ℕ} (hp : p.Prime) (H : Finset ℤ) :
    (∃ r : ZMod p, r ∉ residueImage p H) ↔ (residueImage p H).card < p :=
  sorry

/-- Residue counting: admissibility as fewer than `p` occupied classes modulo every prime. -/
theorem admissibleZ_iff_card_lt (H : Finset ℤ) :
    AdmissibleZ H ↔
      ∀ p : ℕ, p.Prime → (residueImage p H).card < p :=
  sorry

end Survey.PrimeBridges
