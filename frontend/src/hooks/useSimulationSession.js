import { useCallback, useEffect, useRef, useState } from 'react'
import { mockFetchScript, mockScanTurn } from '../mocks/simulation.js'

// State for one active simulation (Task 84). The page only sees:
//   { status, turns, entries, total, advance, restart }
//   status:  'loading' | 'ready' | 'scanning' | 'complete' | 'error'
//   entries: the turns sent so far, each { turn, detection }
// Task 85 replaces the two mock calls with the simulation service; detections
// then carry source: 'api' instead of source: 'annotation'.
export function useSimulationSession(scenarioId) {
  const [state, setState] = useState({ status: 'loading', turns: [], entries: [] })
  const busy = useRef(false)

  useEffect(() => {
    let active = true
    mockFetchScript(scenarioId)
      .then((turns) => {
        if (active) setState({ status: turns.length ? 'ready' : 'complete', turns, entries: [] })
      })
      .catch(() => {
        if (active) setState({ status: 'error', turns: [], entries: [] })
      })
    return () => {
      active = false
    }
  }, [scenarioId])

  const advance = useCallback(async () => {
    if (busy.current || state.status !== 'ready') return
    busy.current = true
    const index = state.entries.length
    setState((prev) => ({ ...prev, status: 'scanning' }))

    const detection = await mockScanTurn(scenarioId, index)
    setState((prev) => {
      const entries = [...prev.entries, { turn: prev.turns[index], detection }]
      return { ...prev, entries, status: entries.length === prev.turns.length ? 'complete' : 'ready' }
    })
    busy.current = false
  }, [scenarioId, state.status, state.entries.length])

  const restart = useCallback(() => {
    if (busy.current) return
    setState((prev) => ({ ...prev, entries: [], status: prev.turns.length ? 'ready' : 'complete' }))
  }, [])

  return { ...state, total: state.turns.length, advance, restart }
}
