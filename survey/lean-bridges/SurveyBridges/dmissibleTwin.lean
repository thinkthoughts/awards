import BGP212.Gap

namespace Survey.PrimeBridges

open BGP212.Gap

/-- The twin-prime shift tuple {0, 2} is admissible. -/
theorem admissible_twin :
    AdmissibleZ ({0, 2} : Finset ℤ) := by
  intro p hp
  refine ⟨1, ?_⟩
  intro h hh
  have hp2 : 2 ≤ p := hp.two_le
  have hnot : ¬ (p ∣ 1) := by
    intro hd
    have hp1 : p = 1 := Nat.dvd_one.mp hd
    omega
  have hcast : ¬ ((p : ℤ) ∣ (1 : ℤ)) := by
    intro hd
    apply hnot
    exact_mod_cast hd
  simp only [Finset.mem_insert, Finset.mem_singleton] at hh
  rcases hh with rfl | rfl
  · intro hd
    apply hcast
    simpa using (dvd_neg.mpr hd)
  · simpa using hcast

#print axioms admissible_twin

end Survey.PrimeBridges
