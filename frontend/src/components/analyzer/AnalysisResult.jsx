import Alert from '../Alert.jsx'
import Card from '../Card.jsx'
import DirectJailbreakResultDetails from './DirectJailbreakResultDetails.jsx'
import IndirectInjectionResultDetails from './IndirectInjectionResultDetails.jsx'
import SafeResultDetails from './SafeResultDetails.jsx'
import { AlertTriangleIcon, LayersIcon, ShieldCheckIcon, ShieldIcon } from '../icons.jsx'
import { findDetectionClass } from '../../config/detection.js'

// Result area of the Prompt Analyzer. Renders one of four states from the
// request status. The success state is a shared summary (class, sub-type,
// description) followed by the class-specific detail from DETAILS_BY_CLASS;
// Task 81 places Aria guidance alongside this component.

// Verdict styling per detection variant — the same icons and colours the class
// detail views use. Presentation only; the data shown is unchanged.
const VERDICT = {
  safe: {
    icon: ShieldCheckIcon,
    text: 'text-safe',
    bar: 'bg-safe',
    border: 'border-safe/35',
    wash: 'from-safe/[0.07]',
    badge: 'border-safe/40 bg-safe/10 shadow-[0_0_24px_-6px_rgb(74_222_128/0.6)]',
  },
  danger: {
    icon: AlertTriangleIcon,
    text: 'text-danger',
    bar: 'bg-danger',
    border: 'border-danger/35',
    wash: 'from-danger/[0.07]',
    badge: 'border-danger/40 bg-danger/10 shadow-[0_0_24px_-6px_rgb(248_113_113/0.6)]',
  },
  warning: {
    icon: LayersIcon,
    text: 'text-warning',
    bar: 'bg-warning',
    border: 'border-warning/35',
    wash: 'from-warning/[0.07]',
    badge: 'border-warning/40 bg-warning/10 shadow-[0_0_24px_-6px_rgb(251_191_36/0.6)]',
  },
}

// Class-specific detail views. `showsSubtype` means the view presents the
// sub-type itself, so the summary leaves it out.
const DETAILS_BY_CLASS = {
  Safe: { component: SafeResultDetails },
  'Direct Jailbreak': { component: DirectJailbreakResultDetails, showsSubtype: true },
  'Indirect Injection': { component: IndirectInjectionResultDetails, showsSubtype: true },
}

function EmptyState() {
  return (
    <Card className="flex flex-col items-center gap-3 border-dashed px-6 py-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full border border-border bg-surface-raised text-fg-subtle">
        <ShieldIcon className="h-5 w-5" />
      </span>
      <p className="font-semibold text-fg">No analysis yet</p>
      <p className="max-w-sm text-sm text-fg-muted">
        Enter a prompt or choose an example, then run an analysis to see its security classification.
      </p>
    </Card>
  )
}

function ScanningState() {
  return (
    <Card className="border-cyan/30 p-5">
      <p className="flex items-center gap-2 text-sm font-medium text-cyan">
        <span className="h-2 w-2 rounded-full bg-cyan shadow-[0_0_8px_rgb(34_211_238/0.9)]" aria-hidden="true" />
        Scanning prompt for injection patterns…
      </p>
      <div className="mt-4 flex flex-col gap-2.5" aria-hidden="true">
        <span className="h-6 w-40 animate-shimmer rounded-full bg-surface-raised" />
        <span className="h-3 w-full animate-shimmer rounded bg-surface-raised" style={{ animationDelay: '150ms' }} />
        <span className="h-3 w-2/3 animate-shimmer rounded bg-surface-raised" style={{ animationDelay: '300ms' }} />
      </div>
    </Card>
  )
}

function ResultSummary({ result, prompt, isStale, onAskAria }) {
  const detection = findDetectionClass(result.classification)
  const details = DETAILS_BY_CLASS[detection.label]
  const Details = details?.component
  const verdict = VERDICT[detection.variant]
  const VerdictIcon = verdict.icon

  return (
    <Card
      borderClassName={verdict.border}
      className={`relative animate-fade-up overflow-hidden bg-linear-to-b ${verdict.wash} to-transparent to-50% p-5 transition-opacity duration-200 sm:p-6 ${
        isStale ? 'opacity-60' : ''
      }`}
    >
      <span className={`absolute inset-x-0 top-0 h-0.5 ${verdict.bar}`} aria-hidden="true" />
      <div className="flex items-start gap-4">
        <span
          className={`flex h-12 w-12 shrink-0 animate-scale-in items-center justify-center rounded-full border sm:h-14 sm:w-14 ${verdict.badge} ${verdict.text}`}
          aria-hidden="true"
        >
          <VerdictIcon className="h-6 w-6 sm:h-7 sm:w-7" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
            <span className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">Classification</span>
            {result.mock && (
              <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] tracking-widest text-fg-subtle uppercase">
                Mock response
              </span>
            )}
          </div>
          <h3 className={`mt-1 text-2xl leading-tight font-bold tracking-tight sm:text-3xl ${verdict.text}`}>{detection.label}</h3>
          <p className="mt-1.5 text-sm text-fg-muted">{detection.description}</p>
          {result.subtype && !details?.showsSubtype && (
            <p className="mt-2 text-sm">
              <span className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">Sub-type</span>{' '}
              <span className="font-medium text-fg">{result.subtype}</span>
            </p>
          )}
        </div>
      </div>

      {Details && <Details result={result} detection={detection} prompt={prompt} onAskAria={onAskAria} />}

      {isStale && (
        <p className="mt-4 text-xs text-fg-muted">The prompt has changed since this analysis. Analyze it again to update the result.</p>
      )}
    </Card>
  )
}

function AnalysisResult({ status, result, analyzedPrompt, isStale, onAskAria }) {
  return (
    <section aria-labelledby="analysis-result-heading" aria-live="polite" aria-busy={status === 'analyzing'}>
      <h2 id="analysis-result-heading" className="mb-3 font-mono text-xs tracking-widest text-fg-subtle uppercase">
        Analysis result
      </h2>
      {status === 'idle' && <EmptyState />}
      {status === 'analyzing' && <ScanningState />}
      {status === 'error' && <Alert variant="error">Analysis failed. Please try again.</Alert>}
      {status === 'success' && (
        <ResultSummary result={result} prompt={analyzedPrompt} isStale={isStale} onAskAria={onAskAria} />
      )}
    </section>
  )
}

export default AnalysisResult
