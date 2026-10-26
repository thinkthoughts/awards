import BGP212.Gap

/-!
# Admissibility passes to subsets

`AdmissibleZ H` asks, for every prime `p`, for one residue class `r` that no shift in `H` meets
modulo `p`. The same class serves every subset of `H`, so admissibility is inherited downward.
-/

namespace Survey.PrimeBridges

open BGP212.Gap

/-- Every subset of an admissible shift set is admissible: the omitted class for `H` modulo `p`
is also omitted by `K ⊆ H`. -/
theorem admissibleZ_subset {H K : Finset ℤ}
    (hKH : K ⊆ H)
    (hH : AdmissibleZ H) :
    AdmissibleZ K := by
  intro p hp
  obtain ⟨r, hr⟩ := hH p hp
  exact ⟨r, fun h hh => hr h (hKH hh)⟩

#print axioms admissibleZ_subset

end Survey.PrimeBridges
