/-
Axiom and statement audit for the survey's bridge lemmas over lean-bgp212.
Run by survey/scripts/check_bridges.sh after the SurveyBridges modules are compiled.
-/
import SurveyBridges.AdmissibleTwin
import SurveyBridges.H1LeMono
import SurveyBridges.TwinPrimeEquiv
import SurveyBridges.TwinPrimeTo186
import SurveyBridges.AdmissibleSubset
import SurveyBridges.AdmissiblePair
import SurveyBridges.ResidueImage
import SurveyBridges.AdmissibleZMod
import SurveyBridges.ResidueNu
import SurveyBridges.LocalFactor
import SurveyBridges.SingleShiftTotient
import SurveyBridges.GDTSingleShift

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
#check @Survey.PrimeBridges.admissibleZ_subset
#print axioms Survey.PrimeBridges.admissibleZ_subset
#check @Survey.PrimeBridges.admissibleZ_pair_iff_even
#print axioms Survey.PrimeBridges.admissibleZ_pair_iff_even
#check @Survey.PrimeBridges.admissibleZ_pair_self
#print axioms Survey.PrimeBridges.admissibleZ_pair_self
#check @Survey.PrimeBridges.admissibleZ_singleton
#print axioms Survey.PrimeBridges.admissibleZ_singleton
#check @Survey.PrimeBridges.admissible_twin_of_pair
#print axioms Survey.PrimeBridges.admissible_twin_of_pair
#check @Survey.PrimeBridges.not_admissibleZ_zero_one
#print axioms Survey.PrimeBridges.not_admissibleZ_zero_one
#print Survey.PrimeBridges.residueImage
#check @Survey.PrimeBridges.mem_residueImage
#print axioms Survey.PrimeBridges.mem_residueImage
#check @Survey.PrimeBridges.dvd_sub_iff_intCast_eq
#print axioms Survey.PrimeBridges.dvd_sub_iff_intCast_eq
#check @Survey.PrimeBridges.intCast_cast_residue
#print axioms Survey.PrimeBridges.intCast_cast_residue
#check @Survey.PrimeBridges.admissibleZ_iff_omits_residue
#print axioms Survey.PrimeBridges.admissibleZ_iff_omits_residue
#check @Survey.PrimeBridges.omits_residue_iff_card_lt
#print axioms Survey.PrimeBridges.omits_residue_iff_card_lt
#check @Survey.PrimeBridges.admissibleZ_iff_card_lt
#print axioms Survey.PrimeBridges.admissibleZ_iff_card_lt
#check @Survey.PrimeBridges.card_lt_residueImage_empty
#print axioms Survey.PrimeBridges.card_lt_residueImage_empty
#check @Survey.PrimeBridges.card_lt_residueImage_singleton
#print axioms Survey.PrimeBridges.card_lt_residueImage_singleton
#check @Survey.PrimeBridges.omits_residue_pair_self
#print axioms Survey.PrimeBridges.omits_residue_pair_self
#check @Survey.PrimeBridges.card_lt_residueImage_twin
#print axioms Survey.PrimeBridges.card_lt_residueImage_twin
#check @Survey.PrimeBridges.not_card_lt_residueImage_zero_one
#print axioms Survey.PrimeBridges.not_card_lt_residueImage_zero_one
#check @Survey.PrimeBridges.omits_residue_neg_three_neg_one
#print axioms Survey.PrimeBridges.omits_residue_neg_three_neg_one
#print BGP212.MultiShift.nu
#print Survey.PrimeBridges.negRep
#check @Survey.PrimeBridges.negRep_intCast
#print axioms Survey.PrimeBridges.negRep_intCast
#check @Survey.PrimeBridges.negRep_injective
#print axioms Survey.PrimeBridges.negRep_injective
#check @Survey.PrimeBridges.image_neg_emod_eq_image_negRep
#print axioms Survey.PrimeBridges.image_neg_emod_eq_image_negRep
#check @Survey.PrimeBridges.residueImage_card_eq_nu_of_modulus
#print axioms Survey.PrimeBridges.residueImage_card_eq_nu_of_modulus
#check @Survey.PrimeBridges.residueImage_card_eq_nu
#print axioms Survey.PrimeBridges.residueImage_card_eq_nu
#check @Survey.PrimeBridges.admissibleZ_iff_nu_lt
#print axioms Survey.PrimeBridges.admissibleZ_iff_nu_lt
#check @Survey.PrimeBridges.nu_twin_lt
#print axioms Survey.PrimeBridges.nu_twin_lt
#print BGP212.MultiShift.localCount
#check @Survey.PrimeBridges.admissibleZ_iff_local_factor_pos
#print axioms Survey.PrimeBridges.admissibleZ_iff_local_factor_pos
#check @Survey.PrimeBridges.localCount_pos_iff
#print axioms Survey.PrimeBridges.localCount_pos_iff
#check @Survey.PrimeBridges.localCount_pos_of_admissibleZ
#print axioms Survey.PrimeBridges.localCount_pos_of_admissibleZ
#check @Survey.PrimeBridges.localCount_twin_pos
#print axioms Survey.PrimeBridges.localCount_twin_pos
#check @Survey.PrimeBridges.nu_singleton
#print axioms Survey.PrimeBridges.nu_singleton
#check @Survey.PrimeBridges.localCount_singleton
#print axioms Survey.PrimeBridges.localCount_singleton
#print GDT.R
#print GDT.d
#print GDT.rad
#check @Survey.PrimeBridges.totient_prod_primes
#print axioms Survey.PrimeBridges.totient_prod_primes
#check @Survey.PrimeBridges.R_eq_prod_sdiff
#print axioms Survey.PrimeBridges.R_eq_prod_sdiff
#check @Survey.PrimeBridges.totient_R_eq_prod
#print axioms Survey.PrimeBridges.totient_R_eq_prod
#check @Survey.PrimeBridges.localCount_singleton_eq_totient
#print axioms Survey.PrimeBridges.localCount_singleton_eq_totient
#check @Survey.PrimeBridges.localCount_zero_eq_totient
#print axioms Survey.PrimeBridges.localCount_zero_eq_totient
#check @Survey.PrimeBridges.localCount_singleton_at_zero
#print axioms Survey.PrimeBridges.localCount_singleton_at_zero
#check @BGP212.Challenge.gdtH_single_shift
#print axioms BGP212.Challenge.gdtH_single_shift
#check @BGP212.Challenge.gdt_count_per_period_via_multishift
#print axioms BGP212.Challenge.gdt_count_per_period_via_multishift
