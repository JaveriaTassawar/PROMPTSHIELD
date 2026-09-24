import { useEffect, useRef } from 'react'
import { Link, useParams } from 'react-router-dom'
import Alert from '../components/Alert.jsx'
import Card from '../components/Card.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageLoading from '../components/PageLoading.jsx'
import CompletionPanel from '../components/simulation/CompletionPanel.jsx'
import DetectionFeed from '../components/simulation/DetectionFeed.jsx'
import ObjectiveBanner from '../components/simulation/ObjectiveBanner.jsx'
import SessionControls from '../components/simulation/SessionControls.jsx'
import SimulationHeader from '../components/simulation/SimulationHeader.jsx'
import SimulationProgress from '../components/simulation/SimulationProgress.jsx'
import TranscriptPanel from '../components/simulation/TranscriptPanel.jsx'
import { findDetectionClass } from '../config/detection.js'
import { TURN_ROLES } from '../config/simulation.js'
import { useSimulationScenarios } from '../hooks/useSimulationScenarios.js'
import { useSimulationSession } from '../hooks/useSimulationSession.js'

// Active simulation (Task 84): a guided, scripted walkthrough. Each "Send next
// turn" reveals the next scenario turn and its detection entry. Free-text test
// prompts and real detections arrive with Task 85; results with Task 86.
function BackLink() {
  return (
    <Link to="/simulation" className="text-sm font-medium text-accent underline-offset-4 transition-colors hover:text-fg hover:underline">
      Back to scenarios
    </Link>
  )
}

// One polite announcement per sent turn — the transcript and feed themselves
// are not live regions, so nothing is read twice.
function announcement(entries, total) {
  if (entries.length === 0) return ''
  const { turn, detection } = entries[entries.length - 1]
  const label = findDetectionClass(detection.classification).label
  const source = detection.source === 'annotation' ? 'Scenario annotation' : 'Detection'
  return `Turn ${entries.length} of ${total}: ${TURN_ROLES[turn.role].label}. ${source}: ${label}${
    detection.subtype ? `, ${detection.subtype}` : ''
  }.`
}

function SimulationSessionPage() {
  const { scenarioId } = useParams()
  const catalog = useSimulationScenarios()
  const session = useSimulationSession(scenarioId)
  const sendRef = useRef(null)
  const completionRef = useRef(null)

  const scenario = catalog.scenarios.find((item) => item.id === scenarioId)
  const isComplete = session.status === 'complete' && session.total > 0

  useEffect(() => {
    if (isComplete) completionRef.current?.focus()
  }, [isComplete])

  function handleRestart() {
    session.restart()
    requestAnimationFrame(() => sendRef.current?.focus())
  }

  if (catalog.status === 'loading' || (session.status === 'loading' && scenario)) {
    return <PageLoading label="Loading scenario…" />
  }

  if (!scenario) {
    return (
      <div className="flex flex-col gap-6">
        <PageHeader eyebrow="Simulation" title="Scenario not found" description="This training scenario doesn’t exist or couldn’t be loaded." />
        <BackLink />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <SimulationHeader scenario={scenario} />

      {session.status === 'error' ? (
        <div className="flex flex-col gap-4">
          <Alert variant="error">This scenario couldn’t be loaded. Please try again later.</Alert>
          <BackLink />
        </div>
      ) : (
        <>
          <ObjectiveBanner objective={scenario.objective} />
          <SimulationProgress sent={session.entries.length} total={session.total} />

          <div className="grid gap-6 lg:grid-cols-5 lg:gap-8">
            <div className="flex flex-col gap-5 lg:col-span-3">
              <Card className="p-4 sm:p-5">
                <TranscriptPanel entries={session.entries} />
              </Card>
              {isComplete ? (
                <CompletionPanel scenario={scenario} entries={session.entries} headingRef={completionRef} onRestart={handleRestart} />
              ) : (
                <SessionControls
                  scanning={session.status === 'scanning'}
                  canRestart={session.entries.length > 0}
                  onSend={session.advance}
                  onRestart={handleRestart}
                  sendRef={sendRef}
                />
              )}
            </div>

            <aside className="hidden lg:col-span-2 lg:block">
              <Card className="p-4 sm:p-5 lg:sticky lg:top-6">
                <DetectionFeed entries={session.entries} />
              </Card>
            </aside>
          </div>

          <p role="status" className="sr-only">
            {announcement(session.entries, session.total)}
          </p>
        </>
      )}
    </div>
  )
}

export default SimulationSessionPage
