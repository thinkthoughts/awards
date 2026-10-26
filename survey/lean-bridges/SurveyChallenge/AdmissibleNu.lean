/-
Comparator Challenge for LIFT-ADM-7: `Survey.PrimeBridges.admissibleZ_iff_nu_lt`.

Statement only, written from the registry statement of LIFT-ADM-7 (survey/registry/edges.json),
independently of the proof. It imports only `BGP212.Gap` and `BGP212.MultiShift`
(lean-bgp212 89b43fa), so `AdmissibleZ` and `nu` are lean-bgp212's own definitions; the survey's
`residueImage`, `negRep` and the ZMod lemmas of the proof do not appear. The `sorry` is the
challenge.
-/
import BGP212.Gap
import BGP212.MultiShift

namespace Survey.PrimeBridges

open BGP212.Gap

/-- Admissibility through the local factor: `ν_p(H) < p` for every prime `p`. -/
theorem admissibleZ_iff_nu_lt (H : Finset ℤ) :
    AdmissibleZ H ↔
      ∀ p : ℕ, p.Prime →
        BGP212.MultiShift.nu p H < p :=
  sorry

end Survey.PrimeBridges
