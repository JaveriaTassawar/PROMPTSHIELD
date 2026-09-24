import PromptEvidence from './PromptEvidence.jsx'
import { AlertTriangleIcon, ArrowRightIcon, BotIcon, FileTextIcon, InfoIcon, LayersIcon } from '../icons.jsx'

// Indirect Injection detail beneath the shared ResultSummary (Task 79): the
// injection vector (sub-type) with its fixed definition, a small general
// concept diagram of the attack path, the category-level explanation, and the
// analysed input. The response carries only classification + subtype, so no
// source, document, URL, tool or span is shown — all explanatory text is fixed
// content from config/detection.js.
const STEP_ICONS = [FileTextIcon, BotIcon, AlertTriangleIcon]

function ConceptFlow({ concept }) {
  return (
    <figure className="rounded-control border border-border/70 bg-canvas/50 p-4">
      <figcaption className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="text-sm font-semibold text-fg">{concept.title}</span>
        <span className="text-xs text-fg-subtle">General illustration, not a trace of this analysis</span>
      </figcaption>
      <ol className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-stretch sm:gap-0">
        {concept.steps.map((step, index) => {
          const StepIcon = STEP_ICONS[index]
          const isLast = index === concept.steps.length - 1
          return (
            <li
              key={step.title}
              className="flex animate-fade-up flex-col items-center sm:flex-1 sm:flex-row"
              style={{ animationDelay: `${550 + index * 140}ms` }}
            >
              {index > 0 && (
                <ArrowRightIcon className="my-1 h-4 w-4 shrink-0 rotate-90 text-fg-subtle sm:mx-2 sm:my-0 sm:rotate-0" />
              )}
              <div
                className={`flex w-full items-center gap-3 rounded-control border px-3 py-2.5 sm:h-full ${
                  isLast ? 'border-warning/40 bg-warning/10' : 'border-border/70 bg-surface/60'
                }`}
              >
                <StepIcon className={`h-5 w-5 shrink-0 ${isLast ? 'text-warning' : 'text-fg-muted'}`} />
                <div className="min-w-0">
                  <p className={`text-sm font-medium ${isLast ? 'text-warning' : 'text-fg'}`}>{step.title}</p>
                  <p className="text-xs text-fg-muted">{step.text}</p>
                </div>
              </div>
            </li>
          )
        })}
      </ol>
    </figure>
  )
}

function IndirectInjectionResultDetails({ result, detection, prompt }) {
  const { explanation } = detection
  const vectorDefinition = detection.subtypeDefinitions[result.subtype]
  const isKnownVector = detection.subtypes.includes(result.subtype)

  return (
    <div className="mt-5 flex flex-col gap-6 border-t border-border/70 pt-5">
      <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:gap-8">
        <div className="flex flex-col gap-5">
          {result.subtype && (
            <div className="flex gap-3">
              <span
                className="flex h-10 w-10 shrink-0 animate-scale-in items-center justify-center rounded-full border border-warning/40 bg-warning/10 text-warning"
                style={{ animationDelay: '150ms' }}
              >
                <LayersIcon className="h-5 w-5" />
              </span>
              <div className="min-w-0 animate-fade-up" style={{ animationDelay: '250ms' }}>
                <p className="font-mono text-[11px] tracking-widest text-warning uppercase">
                  Injection vector
                  {isKnownVector && <span className="text-fg-subtle"> · one of {detection.subtypes.length}</span>}
                </p>
                <p className="mt-0.5 text-lg font-semibold text-fg">{result.subtype}</p>
                {vectorDefinition && <p className="mt-1 text-sm text-fg-muted">{vectorDefinition}</p>}
              </div>
            </div>
          )}

          <div className="animate-fade-up" style={{ animationDelay: '350ms' }}>
            <h3 className="text-sm font-semibold text-fg">{explanation.title}</h3>
            <ul className="mt-2.5 flex flex-col gap-2">
              {explanation.points.map((point) => (
                <li key={point} className="flex gap-2.5 text-sm text-fg-muted">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-warning" aria-hidden="true" />
                  {point}
                </li>
              ))}
            </ul>
            <p className="mt-3 flex gap-2.5 text-xs text-fg-subtle">
              <InfoIcon className="mt-px h-4 w-4 shrink-0" />
              {explanation.caveat}
            </p>
          </div>
        </div>

        <div className="animate-fade-up" style={{ animationDelay: '450ms' }}>
          <PromptEvidence prompt={prompt} label="Analysed input" />
        </div>
      </div>

      <ConceptFlow concept={detection.concept} />
    </div>
  )
}

export default IndirectInjectionResultDetails
