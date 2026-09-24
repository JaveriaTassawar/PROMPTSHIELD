import { useLocation } from 'react-router-dom'
import { useSimulationScenarios } from './useSimulationScenarios.js'

// The completed run shown on /simulation/:scenarioId/results (Task 86).
// Task 84's "View Results" passes the run in router navigation state; nothing
// is stored, so a refresh or a directly opened URL has no run to show.
// Task 85 will read the saved simulation result here instead.
//   status: 'loading' | 'not-found' | 'no-run' | 'ready'
export function useSimulationResult(scenarioId) {
  const { status: catalogStatus, scenarios } = useSimulationScenarios()
  const { state } = useLocation()

  if (catalogStatus === 'loading') return { status: 'loading' }

  const scenario = scenarios.find((item) => item.id === scenarioId)
  if (!scenario) return { status: 'not-found' }

  const run = state?.run
  if (!run || run.scenarioId !== scenarioId || !Array.isArray(run.entries) || run.entries.length === 0) {
    return { status: 'no-run', scenario }
  }

  return { status: 'ready', scenario, entries: run.entries }
}
