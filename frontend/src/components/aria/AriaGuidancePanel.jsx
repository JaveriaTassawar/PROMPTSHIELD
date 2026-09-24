import AriaAvatar from './AriaAvatar.jsx'
import Card from '../Card.jsx'
import { CheckIcon, XIcon } from '../icons.jsx'

// Aria's guidance panel (Task 81). Presentation only: it renders a guidance
// object (see config/ariaGuidance.js) plus the classification it applies to.
// Only the "Classified as …" line comes from the analysis; everything else is
// the guidance object's content.
function SectionHeading({ children }) {
  return <h3 className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">{children}</h3>
}

function RuleList({ title, items, tone }) {
  const isDo = tone === 'do'
  const Icon = isDo ? CheckIcon : XIcon
  return (
    <div
      className={`rounded-control border bg-canvas/40 p-3.5 ${isDo ? 'border-safe/15' : 'border-danger/15'}`}
    >
      <h3 className={`flex items-center gap-2 text-sm font-semibold ${isDo ? 'text-safe' : 'text-danger'}`}>
        <Icon className="h-4 w-4" strokeWidth="2.5" />
        {title}
      </h3>
      <ul className="mt-2.5 flex flex-col gap-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-sm text-fg-muted">
            <Icon className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${isDo ? 'text-safe/80' : 'text-danger/80'}`} strokeWidth="2.5" />
            <span>
              <span className="sr-only">{isDo ? 'Do: ' : 'Don’t: '}</span>
              {item}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function AriaGuidancePanel({ guidance, result, headingRef, isStale }) {
  return (
    <Card
      borderClassName="border-accent/25"
      className={`animate-fade-up p-5 transition-opacity duration-200 ${isStale ? 'opacity-60' : ''}`}
      style={{ animationDelay: '700ms' }}
    >
      <section aria-labelledby="aria-guidance-heading">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <AriaAvatar />
            <div>
              <h2 id="aria-guidance-heading" ref={headingRef} tabIndex={-1} className="rounded font-semibold text-fg">
                Aria<span className="sr-only"> — security guidance</span>
              </h2>
              <p className="font-mono text-[11px] tracking-widest text-cyan/80 uppercase">Security guide</p>
            </div>
          </div>
          {guidance.source === 'general' && (
            <div className="flex flex-col gap-0.5 sm:items-end">
              <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase">
                General guidance · <span className="text-accent">{guidance.scope}</span>
              </p>
              <p className="text-xs text-fg-subtle">Not generated from your prompt</p>
            </div>
          )}
        </header>

        <div className="mt-5 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-8">
          <div className="flex flex-col gap-4">
            <div>
              <SectionHeading>What happened</SectionHeading>
              <p className="mt-1.5 text-sm font-medium text-fg">
                Classified as {result.classification}
                {result.subtype && ` · ${result.subtype}`}
              </p>
              <p className="mt-1 text-sm text-fg-muted">{guidance.summary}</p>
            </div>
            <div>
              <SectionHeading>{guidance.whyTitle}</SectionHeading>
              <p className="mt-1.5 text-sm text-fg-muted">{guidance.why}</p>
            </div>
            <div>
              <SectionHeading>Next steps</SectionHeading>
              <ol className="mt-1.5 flex flex-col gap-1.5">
                {guidance.nextSteps.map((step, index) => (
                  <li key={step} className="flex gap-2.5 text-sm text-fg-muted">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-accent/40 font-mono text-[11px] text-accent">
                      {index + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
            {guidance.keyDefence && (
              <div className="rounded-control border-l-2 border-cyan/70 bg-cyan/5 px-3.5 py-2.5">
                <p className="font-mono text-[11px] tracking-widest text-cyan/90 uppercase">
                  Key defence · {guidance.keyDefence.subtype}
                </p>
                <p className="mt-1 text-sm text-fg">{guidance.keyDefence.text}</p>
              </div>
            )}
          </div>

          <div className="grid content-start gap-3 sm:grid-cols-2">
            <RuleList title="Do" items={guidance.do} tone="do" />
            <RuleList title="Don’t" items={guidance.dont} tone="dont" />
          </div>
        </div>
      </section>
    </Card>
  )
}

export default AriaGuidancePanel
