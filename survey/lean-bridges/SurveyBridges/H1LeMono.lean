import BGP212.Gap

namespace Survey.PrimeBridges

/--
Monotonicity of the consecutive-prime-gap bound.

A verified bound D₁ implies every weaker bound D₂ ≥ D₁.
-/
theorem h1Le_mono {D₁ D₂ : ℕ}
    (hD : D₁ ≤ D₂)
    (h : BGP212.Gap.H1Le D₁) :
    BGP212.Gap.H1Le D₂ := by
  unfold BGP212.Gap.H1Le at h ⊢
  exact h.mono (fun n hn => le_trans hn hD)

#print axioms h1Le_mono

end Survey.PrimeBridges
