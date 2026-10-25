/-
Axiom and proof-term audit for the survey's foundational declarations.
Run by survey/scripts/check_lean.sh after SurveyFoundation/OnePlusOne.lean is compiled.
-/
import SurveyFoundation.OnePlusOne

#check @Survey.Foundation.one_add_one
#print Survey.Foundation.one_add_one
#print axioms Survey.Foundation.one_add_one
#print axioms Survey.Foundation.add_one_eq_succ
#print axioms Survey.Foundation.one_add_one_of_spec
