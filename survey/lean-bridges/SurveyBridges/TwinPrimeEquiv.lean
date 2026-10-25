import BGP212.Gap

/-!
# Twin primes and `H1Le 2` (JSP-000009)

`BGP212.Gap.H1Le 2` says that infinitely often two consecutive primes differ by at most 2. It
is equivalent to the twin prime conjecture: the only consecutive gap of 1 is the pair (2, 3) at
index 0, and from index 1 on both primes are odd, so a gap of at most 2 is exactly 2.

Mathlib facts used (Mathlib 85e3a25, through `BGP212.Gap`): `Nat.infinite_setOfPred_prime`,
`Nat.nth_strictMono`, `Nat.nth_le_nth`, `Nat.nth_mem_of_infinite`, `Nat.nth_count`,
`Nat.count_monotone`, `Nat.count_succ`, `Nat.frequently_atTop_iff_infinite`,
`Filter.frequently_atTop`, `Nat.Prime.two_le`, `Nat.Prime.eq_two_or_odd`,
`StrictMono.le_apply`.
-/

namespace Survey.PrimeBridges

open BGP212.Gap Filter

/-- Infinitely many natural numbers `p` with `p` and `p + 2` both prime. -/
def InfinitelyManyTwinPrimes : Prop :=
  {p : ℕ | p.Prime ∧ (p + 2).Prime}.Infinite

/-- Two primes `p < q` bound the consecutive gap at index `Nat.count Nat.Prime p` by `q - p`.
The same argument as `BGP212.Gap.gap_le_of_primes` in lean-bgp212's `Solution` library,
restated here because the survey bridges import only `BGP212.Gap`. -/
theorem primeGap_count_le {p q : ℕ} (hp : p.Prime) (hq : q.Prime) (hpq : p < q) :
    primeGap (Nat.count Nat.Prime p) ≤ q - p := by
  have hinf := Nat.infinite_setOfPred_prime
  have h1 : Nat.nth Nat.Prime (Nat.count Nat.Prime p) = p := Nat.nth_count hp
  have hc : Nat.count Nat.Prime p + 1 ≤ Nat.count Nat.Prime q := by
    have := Nat.count_monotone Nat.Prime (Nat.succ_le_of_lt hpq)
    rw [Nat.count_succ] at this
    simpa [hp] using this
  have h2 : Nat.nth Nat.Prime (Nat.count Nat.Prime p + 1) ≤ q := by
    have := (Nat.nth_le_nth hinf).mpr hc
    rwa [Nat.nth_count hq] at this
  unfold primeGap
  omega

/-- From index 1 on, a consecutive prime gap of at most 2 is exactly 2: the gap of 1 occurs
only at index 0, between 2 and 3. -/
theorem nth_succ_eq_add_two {b : ℕ} (hb : 1 ≤ b) (hgap : primeGap b ≤ 2) :
    Nat.nth Nat.Prime (b + 1) = Nat.nth Nat.Prime b + 2 := by
  have hinf := Nat.infinite_setOfPred_prime
  have hmono := Nat.nth_strictMono hinf
  have hp : (Nat.nth Nat.Prime b).Prime := Nat.nth_mem_of_infinite hinf b
  have hq : (Nat.nth Nat.Prime (b + 1)).Prime := Nat.nth_mem_of_infinite hinf (b + 1)
  have hpq : Nat.nth Nat.Prime b < Nat.nth Nat.Prime (b + 1) := hmono (by omega)
  have h0 : 2 ≤ Nat.nth Nat.Prime 0 := (Nat.nth_mem_of_infinite hinf 0).two_le
  have h0b : Nat.nth Nat.Prime 0 < Nat.nth Nat.Prime b := hmono (by omega)
  have hpodd := hp.eq_two_or_odd
  have hqodd := hq.eq_two_or_odd
  unfold primeGap at hgap
  omega

/-- Infinitely many twin primes give `H1Le 2`. -/
theorem h1Le_two_of_twin_primes (h : InfinitelyManyTwinPrimes) : H1Le 2 := by
  have hinf := Nat.infinite_setOfPred_prime
  have h' : {p : ℕ | p.Prime ∧ (p + 2).Prime}.Infinite := h
  have hf := Nat.frequently_atTop_iff_infinite.mpr h'
  rw [H1Le, Filter.frequently_atTop]
  intro N
  obtain ⟨p, hNp, hp, hp2⟩ := Filter.frequently_atTop.mp hf (Nat.nth Nat.Prime N)
  have h1 : Nat.nth Nat.Prime (Nat.count Nat.Prime p) = p := Nat.nth_count hp
  refine ⟨Nat.count Nat.Prime p, ?_, ?_⟩
  · by_contra hlt
    have hlt' := (Nat.nth_strictMono hinf) (lt_of_not_ge hlt)
    rw [h1] at hlt'
    exact not_lt_of_ge hNp hlt'
  · have := primeGap_count_le hp hp2 (by omega)
    omega

/-- `H1Le 2` gives infinitely many twin primes. -/
theorem twin_primes_of_h1Le_two (h : H1Le 2) : InfinitelyManyTwinPrimes := by
  have hinf := Nat.infinite_setOfPred_prime
  have hmono := Nat.nth_strictMono hinf
  rw [H1Le] at h
  show {p : ℕ | p.Prime ∧ (p + 2).Prime}.Infinite
  apply Nat.frequently_atTop_iff_infinite.mp
  rw [Filter.frequently_atTop]
  intro M
  obtain ⟨b, hb, hgap⟩ := Filter.frequently_atTop.mp h (M + 1)
  have hq2 := nth_succ_eq_add_two (by omega) hgap
  have hbp : b ≤ Nat.nth Nat.Prime b := hmono.le_apply
  have hp : (Nat.nth Nat.Prime b).Prime := Nat.nth_mem_of_infinite hinf b
  have hq : (Nat.nth Nat.Prime (b + 1)).Prime := Nat.nth_mem_of_infinite hinf (b + 1)
  refine ⟨Nat.nth Nat.Prime b, by omega, hp, ?_⟩
  rw [← hq2]
  exact hq

/-- **JSP-000009 as a reading of `H1Le`.** Infinitely many twin primes exactly when
infinitely many consecutive primes differ by at most 2. -/
theorem twin_primes_iff_h1Le_two : InfinitelyManyTwinPrimes ↔ H1Le 2 :=
  ⟨h1Le_two_of_twin_primes, twin_primes_of_h1Le_two⟩

#print axioms twin_primes_iff_h1Le_two

end Survey.PrimeBridges
