/-
Comparator Challenge for LIFT-ADM-3: `Survey.PrimeBridges.admissibleZ_pair_iff_even`.

Statement only, written from the registry statement of LIFT-ADM-3 (survey/registry/edges.json),
independently of the proof. It imports only `BGP212.Gap` (lean-bgp212 89b43fa), which supplies
`AdmissibleZ` and, through its Mathlib imports (Mathlib 85e3a25), `Even` and `Finset ℤ`.
The `sorry` is the challenge.
-/
import BGP212.Gap

namespace Survey.PrimeBridges

open BGP212.Gap

/-- Admissible pairs: `{a, b}` is admissible exactly when `b - a` is even. -/
theorem admissibleZ_pair_iff_even (a b : ℤ) :
    AdmissibleZ ({a, b} : Finset ℤ) ↔ Even (b - a) :=
  sorry

end Survey.PrimeBridges
