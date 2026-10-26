import Alert from '../components/Alert.jsx'
import PageHeader from '../components/PageHeader.jsx'
import AttackFrequencyChart from '../components/analytics/AttackFrequencyChart.jsx'
import MetricTile from '../components/analytics/MetricTile.jsx'
import SampleDataBanner from '../components/analytics/SampleDataBanner.jsx'
import SubtypeBreakdownTable from '../components/analytics/SubtypeBreakdownTable.jsx'
import { OFFLINE_MODEL_ACCURACY, formatAccuracy } from '../config/modelMetrics.js'
import { findNavItem } from '../config/navigation.js'
import { useDashboardStats } from '../hooks/useDashboardStats.js'

const NAV_ITEM = findNavItem('/analytics')

const DATA_STATE = {
  loading: 'Loading',
  unavailable: 'API not connected',
  error: 'Could not load',
}

// Analytics (Task 88, local preview). Only the offline model accuracy is a
// real figure. Everything else comes from useDashboardStats(), which Task 89
// wires to GET /api/dashboard; ?mock=preview shows clearly labelled sample data.
function AnalyticsPage() {
  const { status, stats } = useDashboardStats()
  const loading = status === 'loading'
  const sample = stats?.sample === true

  let dataState = DATA_STATE[status]
  if (status === 'success') dataState = sample ? 'Sample data' : 'Local preview'

  let totalNote = 'Dashboard API not connected yet'
  if (status === 'error') totalNote = 'Could not be loaded'
  else if (sample) totalNote = 'Sample value · not real'
  else if (status === 'success') totalNote = 'Prompts analysed'

  let responseNote = 'No measured source yet'
  if (sample && stats.avgResponseTimeMs != null) responseNote = 'Sample value · not measured'

  return (
    <div className="flex flex-col gap-6 lg:gap-8">
      <PageHeader
        eyebrow={NAV_ITEM.eyebrow}
        title={NAV_ITEM.label}
        description="Attack frequency, headline figures and a breakdown of detected attack sub-types."
      >
        <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase sm:text-right">
          Analytics data · <span className={sample ? 'text-warning' : 'text-accent'}>{dataState}</span>
        </p>
      </PageHeader>

      {sample && <SampleDataBanner />}

      {status === 'error' && (
        <Alert variant="error">Analytics could not be loaded. Refresh the page to try again.</Alert>
      )}

      <section aria-label="Headline figures" className="grid gap-4 sm:grid-cols-3">
        <MetricTile
          label="Total analyses"
          value={stats?.totalAnalyses?.toLocaleString()}
          note={totalNote}
          loading={loading}
          sample={sample}
        />
        <MetricTile
          label="Offline model accuracy"
          value={formatAccuracy(OFFLINE_MODEL_ACCURACY.value)}
          note={OFFLINE_MODEL_ACCURACY.source}
          valueClassName="text-safe"
        />
        <MetricTile
          label="Avg response time"
          value={stats?.avgResponseTimeMs != null ? `${(stats.avgResponseTimeMs / 1000).toFixed(2)}s` : null}
          note={responseNote}
          loading={loading}
          sample={sample}
        />
      </section>

      <AttackFrequencyChart frequency={stats?.frequency ?? null} loading={loading} sample={sample} />

      <SubtypeBreakdownTable
        subtypes={stats?.subtypes ?? null}
        totalAttacks={stats?.totalAttacks ?? 0}
        loading={loading}
        sample={sample}
      />
    </div>
  )
}

export default AnalyticsPage
