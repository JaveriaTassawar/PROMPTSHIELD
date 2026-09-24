// Converts an API confidenceScore to a whole percentage for display.
//
// The only documented example (SDS §6.5) sends a 0–1 fraction, e.g. 0.94.
// The live contract is unconfirmed until Task 76 — if the backend sends 0–100
// instead, change this function only.
//
// Rounding never shows 100% for a score below 1, or 0% for a score above 0,
// so the display doesn't claim certainty the model didn't report.
export function toConfidencePercent(score) {
  if (typeof score !== 'number' || Number.isNaN(score)) return null
  const fraction = Math.min(Math.max(score, 0), 1)
  const percent = Math.round(fraction * 100)
  if (percent === 100 && fraction < 1) return 99
  if (percent === 0 && fraction > 0) return 1
  return percent
}
