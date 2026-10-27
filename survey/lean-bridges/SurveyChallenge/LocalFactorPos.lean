/-
Comparator Challenge for LIFT-ADM-8: `Survey.PrimeBridges.admissibleZ_iff_local_factor_pos`.

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

/-- Local factor positivity: admissibility as `0 < p - ν_p(H)` at every prime. -/
theorem admissibleZ_iff_local_factor_pos (H : Finset ℤ) :
    AdmissibleZ H ↔ ∀ p : ℕ, p.Prime → 0 < p - BGP212.MultiShift.nu p H :=
  sorry

end Survey.PrimeBridges
