import ConfidenceMeter from './ConfidenceMeter.jsx'
import { CheckIcon, InfoIcon, ShieldCheckIcon } from '../icons.jsx'
import { toConfidencePercent } from '../../utils/confidence.js'

// Safe-specific detail beneath the shared ResultSummary (Task 77): scan-complete
// status, confidence meter, and the fixed category-level explanation from
// config/detection.js. Nothing here is prompt-specific model reasoning.
function SafeResultDetails({ result, detection }) {
  const { explanation } = detection

  return (
    <div className="mt-5 grid gap-6 border-t border-border/70 pt-5 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] md:gap-8">
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-3">
          <span
            className="flex h-10 w-10 shrink-0 animate-scale-in items-center justify-center rounded-full border border-safe/40 bg-safe/10 text-safe"
            style={{ animationDelay: '150ms' }}
          >
            <ShieldCheckIcon className="h-5 w-5" />
          </span>
          <div>
            <p className="font-mono text-[11px] tracking-widest text-safe uppercase">Scan complete</p>
            <p className="text-sm text-fg-muted">Checked against every attack class PromptShield supports.</p>
          </div>
        </div>
        <ConfidenceMeter percent={toConfidencePercent(result.confidenceScore)} variant={detection.variant} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-fg">{explanation.title}</h3>
        <ul className="mt-3 flex flex-col gap-2.5">
          {explanation.points.map((point, index) => (
            <li
              key={point}
              className="flex animate-fade-up gap-2.5 text-sm text-fg-muted"
              style={{ animationDelay: `${350 + index * 80}ms` }}
            >
              <CheckIcon className="mt-0.5 h-4 w-4 shrink-0 text-safe" />
              {point}
            </li>
          ))}
        </ul>
        <p
          className="mt-3 flex animate-fade-up gap-2.5 border-t border-border/60 pt-3 text-xs text-fg-subtle"
          style={{ animationDelay: `${350 + explanation.points.length * 80}ms` }}
        >
          <InfoIcon className="mt-px h-4 w-4 shrink-0" />
          {explanation.caveat}
        </p>
      </div>
    </div>
  )
}

export default SafeResultDetails
