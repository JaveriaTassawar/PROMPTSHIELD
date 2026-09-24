import { useEffect, useState } from 'react'
import { DETECTION_CLASSES } from '../config/detection.js'
import { mockFetchDashboard } from '../mocks/dashboard.js'

// Analytics statistics for the Analytics screen (Task 88). Today it reads the
// local mock; Task 89 swaps mockFetchDashboard() for GET /api/dashboard and
// adjusts toStats() to the real response — components keep the same shape.
//   status: 'loading' | 'unavailable' (API not connected) | 'success' | 'error'

// Every sub-type in the shared taxonomy, in taxonomy order.
export const ALL_SUBTYPES = DETECTION_CLASSES.flatMap((detection) =>
  detection.subtypes.map((name) => ({ name, detection })),
)

// Share of all attacks, to one decimal place. 0 when there are no attacks.
function toPercent(count, total) {
  return total > 0 ? Math.round((count / total) * 1000) / 10 : 0
}

function toCount(value) {
  return Number.isInteger(value) && value >= 0 ? value : null
}

// Normalises a dashboard response. All 8 sub-types are always listed (missing
// ones count 0) and unknown sub-type names are ignored rather than guessed.
// Values the response doesn't provide stay null and are shown as unavailable.
function toStats(raw) {
  const counted = ALL_SUBTYPES.map((subtype) => ({ ...subtype, count: toCount(raw.countsBySubtype?.[subtype.name]) ?? 0 }))
  const totalAttacks = counted.reduce((sum, subtype) => sum + subtype.count, 0)

  return {
    sample: raw.sample === true,
    totalAnalyses: toCount(raw.totalAnalyses),
    totalAttacks,
    // Highest count first; equal counts keep taxonomy order (sort is stable).
    subtypes: counted
      .map((subtype) => ({ ...subtype, percent: toPercent(subtype.count, totalAttacks) }))
      .sort((a, b) => b.count - a.count),
    frequency: Array.isArray(raw.attackFrequency) ? raw.attackFrequency : null,
    avgResponseTimeMs: typeof raw.avgResponseTimeMs === 'number' ? raw.avgResponseTimeMs : null,
  }
}

export function useDashboardStats() {
  const [state, setState] = useState({ status: 'loading', stats: null })

  useEffect(() => {
    let active = true
    mockFetchDashboard()
      .then((raw) => {
        if (active) setState(raw ? { status: 'success', stats: toStats(raw) } : { status: 'unavailable', stats: null })
      })
      .catch(() => {
        if (active) setState({ status: 'error', stats: null })
      })
    return () => {
      active = false
    }
  }, [])

  return state
}
