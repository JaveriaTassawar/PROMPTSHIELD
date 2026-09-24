// Offline evaluation result of the PromptShield classifier (ML Task 31).
// Copied from ml/results/metrics_real.json → overall.accuracy, the headline
// score on the real-world held-out test set (see ml/MODEL_CARD.md).
//
// This is a fixed training-time figure, not live analytics: it says nothing
// about the current user's analyses. Update it only if ML re-runs Task 31.
export const OFFLINE_MODEL_ACCURACY = {
  value: 0.9910751932536894,
  source: 'Held-out real-world test set · not live analytics',
}

// 0.99107… → "99.11%"
export function formatAccuracy(fraction) {
  return `${(fraction * 100).toFixed(2)}%`
}
