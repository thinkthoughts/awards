/-
Comparator Challenge for LIFT-GDT-4: `Survey.PrimeBridges.localCount_singleton`, with its step `nu_singleton`.

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

/-- A single shift occupies exactly one class: `ν_p({a}) = 1` for every modulus `p`. -/
theorem nu_singleton (p : ℕ) (a : ℤ) : BGP212.MultiShift.nu p ({a} : Finset ℤ) = 1 :=
  sorry

/-- Single shift: `localCount N m {a} = ∏ p ∈ (R N m).primeFactors, (p - 1)`. -/
theorem localCount_singleton (N m : ℕ) (a : ℤ) :
    BGP212.MultiShift.localCount N m ({a} : Finset ℤ) =
      ∏ p ∈ (GDT.R N m).primeFactors, (p - 1) :=
  sorry

end Survey.PrimeBridges
