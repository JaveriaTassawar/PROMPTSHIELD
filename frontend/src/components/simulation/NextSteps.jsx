import AriaAvatar from '../aria/AriaAvatar.jsx'
import Card from '../Card.jsx'
import { getGeneralGuidance } from '../../config/ariaGuidance.js'

// Recommended next steps for the scenario's attack pattern, reusing Aria's
// general guidance (Task 81). Category-level content — not generated from
// the user's run.
function NextSteps({ scenario }) {
  const guidance = getGeneralGuidance({ classification: scenario.detection.label, subtype: scenario.subtype })
  if (!guidance) return null

  return (
    <Card borderClassName="border-accent/25" className="p-5">
      <section aria-labelledby="next-steps-heading">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <AriaAvatar className="h-9 w-9" />
            <h2 id="next-steps-heading" className="font-semibold text-fg">
              Recommended next steps
            </h2>
          </div>
          <div className="flex flex-col gap-0.5 sm:items-end">
            <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase">
              General guidance · <span className="text-accent">{guidance.scope}</span>
            </p>
            <p className="text-xs text-fg-subtle">Not generated from your run</p>
          </div>
        </header>

        <ol className="mt-4 flex flex-col gap-2">
          {guidance.nextSteps.map((step, index) => (
            <li key={step} className="flex gap-2.5 text-sm text-fg-muted">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-accent/40 font-mono text-[11px] text-accent">
                {index + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>

        {guidance.keyDefence && (
          <div className="mt-4 rounded-control border-l-2 border-cyan/70 bg-cyan/5 px-3.5 py-2.5">
            <p className="font-mono text-[11px] tracking-widest text-cyan/90 uppercase">
              Key defence · {guidance.keyDefence.subtype}
            </p>
            <p className="mt-1 text-sm text-fg">{guidance.keyDefence.text}</p>
          </div>
        )}
      </section>
    </Card>
  )
}

export default NextSteps
