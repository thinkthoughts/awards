/-
Comparator Challenge for LIFT-GDT-2: `Survey.PrimeBridges.localCount_pos_iff`.

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

/-- The per-period count is positive exactly when `ν_p(H) < p` at every prime of `R N m`. -/
theorem localCount_pos_iff (N m : ℕ) (H : Finset ℤ) :
    0 < BGP212.MultiShift.localCount N m H ↔
      ∀ p ∈ (GDT.R N m).primeFactors, BGP212.MultiShift.nu p H < p :=
  sorry

end Survey.PrimeBridges
