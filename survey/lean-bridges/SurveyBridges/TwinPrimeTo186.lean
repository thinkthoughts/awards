import SurveyBridges.H1LeMono
import SurveyBridges.TwinPrimeEquiv

/-!
# Twin primes imply the 186 gap bound (LIFT-041-3)

An implication between two open statements, JSP-000009 ⇒ JSP-000041. It proves neither
conjecture: it composes `twin_primes_iff_h1Le_two` (gap 2 infinitely often) with
`h1Le_mono` at 2 ≤ 186.
-/

namespace Survey.PrimeBridges

/-- Infinitely many twin primes give `H1Le 186` (JSP-000009 ⇒ JSP-000041). -/
theorem twin_primes_implies_h1Le_186
    (h : InfinitelyManyTwinPrimes) :
    BGP212.Gap.H1Le 186 :=
  h1Le_mono (by norm_num)
    (twin_primes_iff_h1Le_two.mp h)

#print axioms twin_primes_implies_h1Le_186

end Survey.PrimeBridges
