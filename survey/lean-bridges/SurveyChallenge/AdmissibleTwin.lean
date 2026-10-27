/-
Comparator Challenge for LIFT-009-5: `Survey.PrimeBridges.admissible_twin`.

Statement only, written from the registry statement of LIFT-009-5 (survey/registry/edges.json),
independently of the proof. It imports only `BGP212.Gap` (lean-bgp212 89b43fa), so `AdmissibleZ`
is lean-bgp212's own definition, compared by Comparator in full; the statement uses no survey
definition, so none is restated. The `sorry` is the challenge.
-/
import BGP212.Gap

namespace Survey.PrimeBridges

open BGP212.Gap

/-- The twin-prime shift tuple {0, 2} is admissible. -/
theorem admissible_twin :
    AdmissibleZ ({0, 2} : Finset ℤ) :=
  sorry

end Survey.PrimeBridges
