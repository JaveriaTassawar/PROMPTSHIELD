// Mock stand-in for GET /api/dashboard until Task 89 wires the real endpoint
// (Backend Task 64). Nothing here is measured PromptShield data.
//
// Which response comes back:
//   /analytics                → null: the dashboard API is not connected
//   /analytics?mock=preview   → SAMPLE_DASHBOARD (synthetic, for visual checks only)
//   /analytics?mock=empty     → a connected account with no analyses yet
//   /analytics?mock=error     → the request fails
//
// Response shape is PROVISIONAL. Backend Task 64 defines only "total analyses,
// counts per class, counts per sub-type, recent activity". It defines no
// time series and no response time — `attackFrequency` and `avgResponseTimeMs`
// exist here solely so the UI can be exercised. The hook's toStats() is the
// only place that reads this shape.
const MOCK_DELAY_MS = 600

// SYNTHETIC SAMPLE — made-up numbers that exercise every part of the UI.
// Role Override is deliberately 0 to show a zero-count row.
// Never present these values as PromptShield results.
const SAMPLE_DASHBOARD = {
  sample: true,
  totalAnalyses: 120,
  countsBySubtype: {
    'Policy Evasion': 14,
    'Multi-Turn Manipulation': 6,
    'Role Override': 0,
    'Persona Hijacking': 9,
    'System Prompt Overwrite': 4,
    'Document Embedding': 11,
    'Web Content Injection': 7,
    'Tool Output Injection': 3,
  },
  // Numbered sample points, not dates: there is no real time period behind them.
  attackFrequency: [
    { point: 'Sample 1', directJailbreak: 3, indirectInjection: 1 },
    { point: 'Sample 2', directJailbreak: 5, indirectInjection: 2 },
    { point: 'Sample 3', directJailbreak: 2, indirectInjection: 4 },
    { point: 'Sample 4', directJailbreak: 6, indirectInjection: 3 },
    { point: 'Sample 5', directJailbreak: 4, indirectInjection: 2 },
    { point: 'Sample 6', directJailbreak: 7, indirectInjection: 5 },
    { point: 'Sample 7', directJailbreak: 6, indirectInjection: 4 },
  ],
  avgResponseTimeMs: 420,
}

const EMPTY_DASHBOARD = {
  totalAnalyses: 0,
  countsBySubtype: {},
  attackFrequency: [],
  avgResponseTimeMs: null,
}

export function mockFetchDashboard() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const flag = new URLSearchParams(window.location.search).get('mock')
      if (flag === 'error') reject(new Error('Dashboard request failed.'))
      else if (flag === 'preview') resolve(SAMPLE_DASHBOARD)
      else if (flag === 'empty') resolve(EMPTY_DASHBOARD)
      else resolve(null)
    }, MOCK_DELAY_MS)
  })
}
