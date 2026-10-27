/-
Comparator Challenge for LIFT-GDT-3: `Survey.PrimeBridges.localCount_pos_of_admissibleZ`, with its application `localCount_twin_pos`.

Statements only, written from the registry (survey/registry/edges.json), independently of the
proofs. It imports only `BGP212.Gap` and `BGP212.MultiShift` (lean-bgp212 89b43fa), so
`AdmissibleZ`, `nu`, `localCount` and GDT v1.0.0's `R`, `d`, `rad` are lean-bgp212's own
definitions, compared by Comparator in full; no survey definition occurs in these statements,
so none is restated. The `sorry`s are the challenge.
-/
import BGP212.Gap
import BGP212.MultiShift

namespace Survey.PrimeBridges

open BGP212.Gap

/-- Global admissibility gives a positive per-period count for every `N`, `m`. -/
theorem localCount_pos_of_admissibleZ (N m : ℕ) {H : Finset ℤ} (hH : AdmissibleZ H) :
    0 < BGP212.MultiShift.localCount N m H :=
  sorry

/-- The twin-prime shifts give a positive per-period count for every `N`, `m`. -/
theorem localCount_twin_pos (N m : ℕ) :
    0 < BGP212.MultiShift.localCount N m ({0, 2} : Finset ℤ) :=
  sorry

end Survey.PrimeBridges
