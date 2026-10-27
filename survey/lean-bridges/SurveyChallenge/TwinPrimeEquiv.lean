/-
Comparator Challenge for LIFT-009-3: `Survey.PrimeBridges.twin_primes_iff_h1Le_two`, with the
steps the lift cites: its two directions (`h1Le_two_of_twin_primes`, `twin_primes_of_h1Le_two`)
and its two side conditions (`primeGap_count_le`, `nth_succ_eq_add_two`).

Statements only, written from the registry (survey/registry/edges.json), independently of the
proofs. It imports only `BGP212.Gap` (lean-bgp212 89b43fa), so `H1Le` and `primeGap` are
lean-bgp212's own definitions, compared by Comparator in full. The statements mention the survey
definition `InfinitelyManyTwinPrimes`, so the Challenge states it too, verbatim and in the same
`open` context as in SurveyBridges.TwinPrimeEquiv (sha256
4c269741a5de637d43d26a015aedbb0f2f892db2085095c60c6163f9e0cf72e9): Comparator compares this
definition, body included, with the Solution's constant of the same name and rejects any
difference (no definition holes are declared). The `sorry`s are the challenge.
-/
import BGP212.Gap

namespace Survey.PrimeBridges

open BGP212.Gap Filter

/-- Infinitely many natural numbers `p` with `p` and `p + 2` both prime. -/
def InfinitelyManyTwinPrimes : Prop :=
  {p : ℕ | p.Prime ∧ (p + 2).Prime}.Infinite

/-- Two primes `p < q` bound the consecutive gap at index `Nat.count Nat.Prime p` by `q - p`. -/
theorem primeGap_count_le {p q : ℕ} (hp : p.Prime) (hq : q.Prime) (hpq : p < q) :
    primeGap (Nat.count Nat.Prime p) ≤ q - p :=
  sorry

/-- From index 1 on, a consecutive prime gap of at most 2 is exactly 2. -/
theorem nth_succ_eq_add_two {b : ℕ} (hb : 1 ≤ b) (hgap : primeGap b ≤ 2) :
    Nat.nth Nat.Prime (b + 1) = Nat.nth Nat.Prime b + 2 :=
  sorry

/-- Infinitely many twin primes give `H1Le 2`. -/
theorem h1Le_two_of_twin_primes (h : InfinitelyManyTwinPrimes) : H1Le 2 :=
  sorry

/-- `H1Le 2` gives infinitely many twin primes. -/
theorem twin_primes_of_h1Le_two (h : H1Le 2) : InfinitelyManyTwinPrimes :=
  sorry

/-- JSP-000009 as a reading of `H1Le`: infinitely many twin primes exactly when infinitely many
consecutive primes differ by at most 2. -/
theorem twin_primes_iff_h1Le_two : InfinitelyManyTwinPrimes ↔ H1Le 2 :=
  sorry

end Survey.PrimeBridges
