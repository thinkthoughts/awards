/-
Foundational reading point RP-0001: `1 + 1 = 2` over the natural numbers.

Core Lean only: the prelude is the whole trusted base, and this file adds no axioms.
Registry records: survey/registry/readings.json (RP-0001), specs.json (SPEC-nat-add-one),
edges.json (LIFT-0001), evidence.json (EV-0001).
-/

namespace Survey.Foundation

/-- **Reading point.** The natural-number equation `1 + 1 = 2`.
The proof term is `rfl`: the kernel evaluates both sides to the literal `2`. -/
theorem one_add_one : (1 : Nat) + 1 = 2 := rfl

/-- **Leading specification.** For every natural number `n`, `n + 1 = Nat.succ n`
(core `Nat.add_one`). -/
theorem add_one_eq_succ (n : Nat) : n + 1 = n.succ := Nat.add_one n

/-- **PiπΠ lift (LIFT-0001).** The reading point is the leading specification at `n = 1`;
`Nat.succ 1` and `2` are the same natural number by definitional unfolding. -/
theorem one_add_one_of_spec : (1 : Nat) + 1 = 2 := add_one_eq_succ 1

end Survey.Foundation
