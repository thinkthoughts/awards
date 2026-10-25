/-
Axiom and statement audit for the survey's bridge lemmas over lean-bgp212.
Run by survey/scripts/check_bridges.sh after the SurveyBridges modules are compiled.
-/
import SurveyBridges.AdmissibleTwin
import SurveyBridges.H1LeMono

#check @Survey.PrimeBridges.h1Le_mono
#print axioms Survey.PrimeBridges.h1Le_mono
#check @Survey.PrimeBridges.admissible_twin
#print axioms Survey.PrimeBridges.admissible_twin
