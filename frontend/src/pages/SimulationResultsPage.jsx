import { Link, useParams } from 'react-router-dom'
import Card from '../components/Card.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageLoading from '../components/PageLoading.jsx'
import NextSteps from '../components/simulation/NextSteps.jsx'
import RunSummary from '../components/simulation/RunSummary.jsx'
import SimulationHeader from '../components/simulation/SimulationHeader.jsx'
import TurnBreakdown from '../components/simulation/TurnBreakdown.jsx'
import { ArrowRightIcon, TargetIcon } from '../components/icons.jsx'
import { useSimulationResult } from '../hooks/useSimulationResult.js'

// Simulation Results (Task 86, partial): factual run summary, turn-by-turn
// breakdown and general next steps. Score and challenge results are not shown —
// no scoring or challenge rules are defined yet (see Task 86 / Backend Task 63).
const PRIMARY_LINK =
  'inline-flex items-center justify-center gap-2 rounded-control bg-linear-to-r from-primary to-indigo px-4 py-2.5 font-semibold text-white shadow-glow transition duration-150 ease-snappy hover:-translate-y-px hover:shadow-glow-strong active:translate-y-0'
const TEXT_LINK = 'text-sm font-medium text-accent underline-offset-4 transition-colors hover:text-fg hover:underline'

function SimulationResultsPage() {
  const { scenarioId } = useParams()
  const result = useSimulationResult(scenarioId)

  if (result.status === 'loading') {
    return <PageLoading label="Loading results…" />
  }

  if (result.status === 'not-found') {
    return (
      <div className="flex flex-col gap-6">
        <PageHeader eyebrow="Results" title="Scenario not found" description="This training scenario doesn’t exist or couldn’t be loaded." />
        <Link to="/simulation" className={TEXT_LINK}>
          Back to scenarios
        </Link>
      </div>
    )
  }

  const { scenario } = result

  if (result.status === 'no-run') {
    return (
      <div className="flex flex-col gap-6">
        <SimulationHeader scenario={scenario} eyebrow="Results" />
        <Card className="flex flex-col items-center gap-3 border-dashed px-6 py-10 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-full border border-border bg-surface-raised text-fg-subtle">
            <TargetIcon className="h-5 w-5" />
          </span>
          <h2 className="font-semibold text-fg">No completed run to show</h2>
          <p className="max-w-md text-sm text-fg-muted">
            Results appear after you complete this scenario. Runs aren’t saved, so refreshing this page clears them.
          </p>
          <Link to={`/simulation/${scenario.id}`} className={`mt-2 ${PRIMARY_LINK}`}>
            Run this scenario
            <ArrowRightIcon className="h-4.5 w-4.5" />
          </Link>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <SimulationHeader scenario={scenario} eyebrow="Results" />
      <RunSummary scenario={scenario} entries={result.entries} />

      <div className="grid gap-6 lg:grid-cols-5 lg:gap-8">
        <div className="lg:col-span-3">
          <TurnBreakdown entries={result.entries} />
        </div>
        <div className="lg:col-span-2">
          <NextSteps scenario={scenario} />
        </div>
      </div>

      <div className="flex flex-col-reverse gap-3 border-t border-border/70 pt-5 sm:flex-row sm:items-center sm:justify-between">
        <Link to="/simulation" className={`self-center sm:self-auto ${TEXT_LINK}`}>
          Choose another scenario
        </Link>
        <Link to={`/simulation/${scenario.id}`} className={PRIMARY_LINK}>
          Run again
          <ArrowRightIcon className="h-4.5 w-4.5" />
        </Link>
      </div>
    </div>
  )
}

export default SimulationResultsPage
