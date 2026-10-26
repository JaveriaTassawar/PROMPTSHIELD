import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Alert from '../components/Alert.jsx'
import Card from '../components/Card.jsx'
import PageHeader from '../components/PageHeader.jsx'
import ScenarioBriefing from '../components/simulation/ScenarioBriefing.jsx'
import ScenarioCard from '../components/simulation/ScenarioCard.jsx'
import { TargetIcon } from '../components/icons.jsx'
import { findNavItem } from '../config/navigation.js'
import { useSimulationScenarios } from '../hooks/useSimulationScenarios.js'

const NAV_ITEM = findNavItem('/simulation')

// Simulation Lab scenario picker (Task 83): select a scenario, read its
// briefing, then start it explicitly. The active simulation is Task 84.
function SimulationLabPage() {
  const { status, scenarios } = useSimulationScenarios()
  const [selectedId, setSelectedId] = useState(null)
  const navigate = useNavigate()
  const briefingHeadingRef = useRef(null)
  const pointerSelection = useRef(false)

  const selected = scenarios.find((scenario) => scenario.id === selectedId)

  // A tap/click selection brings the briefing into view (it sits below the
  // cards). Keyboard selection with the arrow keys does not scroll the page.
  function handleSelect(id) {
    setSelectedId(id)
    if (!pointerSelection.current) return
    pointerSelection.current = false
    requestAnimationFrame(() => {
      const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      briefingHeadingRef.current?.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'nearest' })
    })
  }

  return (
    <div className="flex flex-col gap-6 lg:gap-8">
      <PageHeader
        eyebrow={NAV_ITEM.eyebrow}
        title={NAV_ITEM.label}
        description="Practise recognising prompt-injection attacks in a controlled environment. Choose a scenario, review its briefing, then start the simulation."
      >
        <div className="flex flex-col gap-0.5 sm:items-end">
          <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase">
            Training scenarios · <span className="text-accent">Local preview</span>
          </p>
          <p className="text-xs text-fg-subtle sm:text-right">Stored locally until the simulation service is connected</p>
        </div>
      </PageHeader>

      <fieldset
        onPointerDown={() => (pointerSelection.current = true)}
        onKeyDown={() => (pointerSelection.current = false)}
        disabled={status !== 'success'}
      >
        <legend className="mb-3 font-mono text-xs tracking-widest text-fg-subtle uppercase">Select attack scenario</legend>

        {status === 'loading' && (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-busy="true">
            <span className="sr-only">Loading scenarios…</span>
            {[0, 1, 2, 3].map((index) => (
              <div key={index} className="h-56 animate-shimmer rounded-card border border-border/60 bg-surface/50" aria-hidden="true" />
            ))}
          </div>
        )}

        {status === 'error' && <Alert variant="error">The scenario catalog couldn’t be loaded. Please try again later.</Alert>}

        {status === 'success' && scenarios.length === 0 && (
          <Card className="border-dashed px-6 py-10 text-center text-sm text-fg-muted">No training scenarios are available yet.</Card>
        )}

        {status === 'success' && scenarios.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {scenarios.map((scenario, index) => (
              <div key={scenario.id} className="animate-fade-up" style={{ animationDelay: `${index * 70}ms` }}>
                <ScenarioCard
                  scenario={scenario}
                  name="scenario"
                  checked={scenario.id === selectedId}
                  onSelect={handleSelect}
                />
              </div>
            ))}
          </div>
        )}
      </fieldset>

      {status === 'success' &&
        (selected ? (
          <div key={selected.id} className="scroll-mt-20">
            <ScenarioBriefing
              scenario={selected}
              headingRef={briefingHeadingRef}
              onStart={() => navigate(`/simulation/${selected.id}`)}
            />
          </div>
        ) : (
          scenarios.length > 0 && (
            <Card className="flex items-center gap-3 border-dashed px-5 py-4 text-sm text-fg-muted">
              <TargetIcon className="h-5 w-5 shrink-0 text-fg-subtle" />
              Select a scenario above to read its security briefing.
            </Card>
          )
        ))}
    </div>
  )
}

export default SimulationLabPage
