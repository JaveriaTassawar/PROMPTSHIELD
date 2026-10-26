import { useEffect, useState } from 'react'
import { findClassForSubtype } from '../config/detection.js'
import { TRAINING_DIFFICULTY } from '../config/simulation.js'
import { mockFetchScenarios } from '../mocks/simulation.js'

// Scenario catalog for the Simulation Lab. Today it reads the local mock
// catalog; when Backend Task 62 (and its endpoint) exists, only the fetch call
// and toScenario() change — components receive the same normalised scenarios.
//   status: 'loading' | 'success' | 'error'

// Normalises one catalog entry, linking it to the shared taxonomy. Entries with
// a sub-type or difficulty the app doesn't know are dropped rather than guessed.
function toScenario(raw) {
  const detection = findClassForSubtype(raw.subtype)
  const difficulty = TRAINING_DIFFICULTY[raw.difficulty]
  if (!detection || !difficulty) return null

  return {
    id: raw.id,
    code: raw.code,
    title: raw.title,
    summary: raw.summary,
    objective: raw.objective,
    subtype: raw.subtype,
    subtypeDefinition: detection.subtypeDefinitions?.[raw.subtype],
    detection,
    difficulty,
  }
}

export function useSimulationScenarios() {
  const [state, setState] = useState({ status: 'loading', scenarios: [] })

  useEffect(() => {
    let active = true
    mockFetchScenarios()
      .then((catalog) => {
        if (active) setState({ status: 'success', scenarios: catalog.map(toScenario).filter(Boolean) })
      })
      .catch(() => {
        if (active) setState({ status: 'error', scenarios: [] })
      })
    return () => {
      active = false
    }
  }, [])

  return state
}
