/-
Comparator Challenge for LIFT-009-6: `Survey.PrimeBridges.admissible_twin_of_pair`.

Statement only, written from the registry statement of LIFT-009-6 (survey/registry/edges.json),
independently of the proof. It imports only `BGP212.Gap` (lean-bgp212 89b43fa), so `AdmissibleZ`
is lean-bgp212's own definition, compared by Comparator in full; the statement uses no survey
definition, so none is restated. The step it cites, `admissibleZ_pair_iff_even` (LIFT-ADM-3), has
its own config (admissibleZ_pair_iff_even.json, accepted in EV-0014). The `sorry` is the challenge.
-/
import BGP212.Gap

namespace Survey.PrimeBridges

open BGP212.Gap

/-- The twin-prime shifts `{0, 2}`, from the pair classification. -/
theorem admissible_twin_of_pair :
    AdmissibleZ ({0, 2} : Finset ℤ) :=
  sorry

end Survey.PrimeBridges
