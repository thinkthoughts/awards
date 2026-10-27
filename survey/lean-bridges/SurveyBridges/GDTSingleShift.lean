/-
Bridge for EDGE-GDT-1: the multi-shift General Divisor Theorem at `H = {0}` re-derives GDT
v1.0.0's count per period.

This module adds no declarations. It imports lean-bgp212's own proof module
`Solution.MultiShift` (lean-bgp212 89b43fa, sha256
7f345fe6b4ffe8e21993e658a9233f40efde0ed140e2e5338aea016c6b4f86bd, identical at 14ec5e0)
unchanged, so the survey's Comparator Solution exports exactly the upstream theorems
EDGE-GDT-1 cites, under their upstream names:

* `BGP212.Challenge.gdtH_single_shift`: at `H = {0}`, `AdmissibleH ↔ Admissible`,
  `acceptedH ↔ accepted` for every `n`, and `localCount N m {0} = φ(R N m)`;
* `BGP212.Challenge.gdt_count_per_period_via_multishift`: GDT v1.0.0's `gdt_count_per_period`,
  statement for statement, proved through `gdtH_count_per_period` and `gdtH_single_shift`.

Definitions: `BGP212.MultiShift.{AdmissibleH, acceptedH, localCount}` (BGP212/MultiShift.lean)
and GDT v1.0.0's `GDT.{Admissible, accepted, Tmin, R}` (vendored in BGP212/GDTv1Basic.lean).
-/
import Solution.MultiShift

#print axioms BGP212.Challenge.gdtH_single_shift
#print axioms BGP212.Challenge.gdt_count_per_period_via_multishift
