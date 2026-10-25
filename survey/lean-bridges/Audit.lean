/-
Axiom and statement audit for the survey's bridge lemmas over lean-bgp212.
Run by survey/scripts/check_bridges.sh after the SurveyBridges modules are compiled.
-/
import SurveyBridges.AdmissibleTwin
import SurveyBridges.H1LeMono
import SurveyBridges.TwinPrimeEquiv
import SurveyBridges.TwinPrimeTo186

#check @Survey.PrimeBridges.h1Le_mono
#print axioms Survey.PrimeBridges.h1Le_mono
#check @Survey.PrimeBridges.admissible_twin
#print axioms Survey.PrimeBridges.admissible_twin
#print Survey.PrimeBridges.InfinitelyManyTwinPrimes
#check @Survey.PrimeBridges.twin_primes_iff_h1Le_two
#print axioms Survey.PrimeBridges.twin_primes_iff_h1Le_two
#print axioms Survey.PrimeBridges.h1Le_two_of_twin_primes
#print axioms Survey.PrimeBridges.twin_primes_of_h1Le_two
#check @Survey.PrimeBridges.twin_primes_implies_h1Le_186
#print axioms Survey.PrimeBridges.twin_primes_implies_h1Le_186
