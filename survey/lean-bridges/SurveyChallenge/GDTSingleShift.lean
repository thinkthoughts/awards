/-
Comparator Challenge for EDGE-GDT-1: `BGP212.Challenge.gdt_count_per_period_via_multishift`,
with the specialization it rests on, `BGP212.Challenge.gdtH_single_shift`.

Statements only, written from the registry statement of EDGE-GDT-1 (survey/registry/edges.json),
which quotes lean-bgp212's statements verbatim, independently of the proofs. The names are the
upstream names in `BGP212.Challenge`, so Comparator judges exactly the theorems the registry
cites. It imports only `BGP212.MultiShift` (lean-bgp212 89b43fa), so `AdmissibleH`, `acceptedH`,
`localCount` and GDT v1.0.0's `Admissible`, `accepted`, `Tmin`, `R` are lean-bgp212's own
definitions, compared by Comparator in full: no survey definition occurs, none is restated, and
no definition holes are declared (lean-bgp212's own Comparator/multishift.json declares twelve;
this pair uses none). The `sorry`s are the challenge.
-/
import BGP212.MultiShift

namespace BGP212.Challenge

open GDT BGP212.MultiShift

/-- **Specialization `H = {0}`.** Admissibility, acceptance and the count reduce to
GDT v1.0.0's `Admissible`, `accepted` and `φ(R)`. -/
theorem gdtH_single_shift {N m : ℕ} (hN : 0 < N) (a : ℤ) :
    (AdmissibleH N m a {0} ↔ Admissible N m a) ∧
    (∀ n : ℕ, acceptedH N m a {0} n ↔ accepted N m a n) ∧
    localCount N m {0} = Nat.totient (R N m) :=
  sorry

/-- **GDT v1.0.0's `gdt_count_per_period`, re-derived.** The statement is
`gdt_count_per_period` verbatim; the proof goes through the multi-shift theorem. -/
theorem gdt_count_per_period_via_multishift {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) (b : ℕ) :
    ((Finset.Ico b (b + Tmin N m)).filter (accepted N m a)).card =
      Nat.totient (R N m) :=
  sorry

end BGP212.Challenge
