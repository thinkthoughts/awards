/-
Comparator Challenge for LIFT-ADM-2: `Survey.PrimeBridges.admissibleZ_subset`.

Statement only, written from the registry statement of LIFT-ADM-2 (survey/registry/edges.json),
independently of the proof. It imports only `BGP212.Gap` (lean-bgp212 89b43fa), so
`AdmissibleZ` is lean-bgp212's own definition. The `sorry` is the challenge.
-/
import BGP212.Gap

namespace Survey.PrimeBridges

open BGP212.Gap

/-- Subset closure: every subset of an admissible shift set is admissible. -/
theorem admissibleZ_subset {H K : Finset ℤ}
    (hKH : K ⊆ H)
    (hH : AdmissibleZ H) :
    AdmissibleZ K :=
  sorry

end Survey.PrimeBridges
