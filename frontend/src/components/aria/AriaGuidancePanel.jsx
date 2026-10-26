import AriaAvatar from './AriaAvatar.jsx'
import Card from '../Card.jsx'
import { CheckIcon, InfoIcon, ShieldIcon, XIcon } from '../icons.jsx'
import { findDetectionClass } from '../../config/detection.js'

// Aria's guidance (Task 81): Aria as a floating character with a speech bubble,
// followed by a separate security briefing. Presentation only: it renders a
// guidance object (see config/ariaGuidance.js) plus the classification it
// applies to. Only the "Classified as …" line comes from the
// analysis; everything else is the guidance object's content. The dialogue
// intro is fixed UI copy per class — not generated, and adds nothing about
// the prompt itself.
const INTRO = {
  Safe: 'This prompt was classified Safe. Here’s what that result covers, and how to keep your prompts safe.',
  'Direct Jailbreak': 'I’ll help you understand this attack and what to do next.',
  'Indirect Injection': 'I’ll help you understand this injection attack and how to defend against it.',
}

// Result colour: used only for status accents, never to recolour Aria.
const TONE = {
  safe: { text: 'text-safe', bar: 'bg-safe' },
  danger: { text: 'text-danger', bar: 'bg-danger' },
  warning: { text: 'text-warning', bar: 'bg-warning' },
}

// One stop on Aria's walkthrough: a numbered node joined to the next by a line.
function GuideStep({ number, title, last = false, children }) {
  return (
    <li className="relative flex gap-4">
      {!last && (
        <span
          className="absolute top-10 bottom-0 left-[18px] w-px bg-linear-to-b from-accent/50 to-accent/10"
          aria-hidden="true"
        />
      )}
      <span className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-accent/50 bg-canvas font-mono text-xs font-semibold text-accent shadow-[0_0_14px_-4px_rgb(124_58_237/0.8)]">
        {number}
      </span>
      <div className={`min-w-0 flex-1 pt-1.5 ${last ? '' : 'pb-6'}`}>
        <h3 className="text-sm font-semibold text-fg">{title}</h3>
        <div className="mt-1.5">{children}</div>
      </div>
    </li>
  )
}

function RuleCard({ title, items, tone }) {
  const isDo = tone === 'do'
  const Icon = isDo ? CheckIcon : XIcon
  return (
    <div className={`overflow-hidden rounded-card border ${isDo ? 'border-safe/30 bg-safe/[0.04]' : 'border-danger/30 bg-danger/[0.04]'}`}>
      <h3
        className={`flex items-center gap-2.5 border-b px-4 py-2.5 text-sm font-semibold ${
          isDo ? 'border-safe/20 bg-safe/10 text-safe' : 'border-danger/20 bg-danger/10 text-danger'
        }`}
      >
        <span className={`flex h-6 w-6 items-center justify-center rounded-full ${isDo ? 'bg-safe/20' : 'bg-danger/20'}`}>
          <Icon className="h-3.5 w-3.5" strokeWidth="2.75" />
        </span>
        {title}
      </h3>
      <ul className="flex flex-col gap-2.5 px-4 py-3.5">
        {items.map((item) => (
          <li key={item} className="flex gap-2.5 text-sm text-fg-muted">
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
  const detection = findDetectionClass(result.classification)
  const tone = TONE[detection?.variant]
  const intro = INTRO[result.classification]

  return (
    <section
      aria-labelledby="aria-guidance-heading"
      className={`animate-fade-up transition-opacity duration-200 ${isStale ? 'opacity-60' : ''}`}
      style={{ animationDelay: '700ms' }}
    >
      {/* ── Aria herself: a floating character beside her speech bubble ───────
          Not inside a card. On desktop she sits past the report's left edge and
          her base overlaps its top border. */}
      <div className="relative z-10 flex flex-col items-center gap-5 md:flex-row md:items-start md:gap-3 lg:-ml-6">
        <div className="relative shrink-0 md:-mb-14">
          <AriaAvatar
            tone={detection?.variant}
            animated
            label="Aria, PromptShield’s AI security guide"
            className="w-40 md:w-60 lg:w-72"
          />
        </div>

        {/* Speech bubble — its tail points at Aria (up on mobile, left on desktop) */}
        <div className="relative w-full max-w-2xl rounded-3xl border border-accent/35 bg-surface-raised px-5 py-4 shadow-glow sm:px-6 sm:py-5 md:mt-12 md:flex-1 lg:mt-14">
          <span
            className="absolute -top-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 border-t border-l border-accent/35 bg-surface-raised md:top-10 md:-left-2 md:translate-x-0 md:border-t-0 md:border-b"
            aria-hidden="true"
          />
          <p className="absolute -top-3 left-5 inline-flex items-center gap-1.5 rounded-full border border-cyan/40 bg-canvas px-2.5 py-0.5 font-mono text-[10px] font-semibold tracking-widest whitespace-nowrap text-cyan uppercase shadow-[0_0_16px_-4px_rgb(34_211_238/0.7)] sm:left-6">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan shadow-[0_0_6px_rgb(34_211_238/1)] motion-safe:animate-blink" aria-hidden="true" />
            Aria online
          </p>
          <h2 id="aria-guidance-heading" ref={headingRef} tabIndex={-1} className="relative rounded text-2xl font-bold tracking-tight text-fg">
            Hi, I’m Aria<span className="sr-only"> — security guidance</span>
          </h2>
          <p className="relative mt-0.5 font-mono text-[11px] tracking-widest text-cyan/85 uppercase">Your AI security guide</p>
          {intro && <p className="relative mt-3 text-base leading-relaxed text-fg sm:text-lg">{intro}</p>}
        </div>
      </div>

      {/* ── Aria's security briefing: a separate report ─────────────────── */}
      <Card borderClassName="border-accent/25" className="relative mt-4 overflow-hidden p-5 sm:p-7 md:mt-0">
        {tone && <span className={`absolute inset-x-0 top-0 h-0.5 opacity-70 ${tone.bar}`} aria-hidden="true" />}

        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 md:min-h-8 md:pl-48">
          <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase">Aria’s security briefing</p>
          {guidance.source === 'general' && (
            <p className="flex items-center gap-1.5 text-[11px] text-fg-subtle">
              <InfoIcon className="h-3.5 w-3.5 shrink-0" />
              General guidance · {guidance.scope} · Not generated from your prompt
            </p>
          )}
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-8">
          <div className="flex flex-col gap-6">
            <ol className="flex flex-col">
              <GuideStep number="01" title="What happened">
                <p className="text-sm font-medium text-fg">
                  Classified as <span className={tone?.text ?? 'text-fg'}>{result.classification}</span>
                  {result.subtype && ` · ${result.subtype}`}
                </p>
                <p className="mt-1 text-sm text-fg-muted">{guidance.summary}</p>
              </GuideStep>
              <GuideStep number="02" title={guidance.whyTitle}>
                <p className="text-sm text-fg-muted">{guidance.why}</p>
              </GuideStep>
              <GuideStep number="03" title="What you should do next" last>
                <ol className="flex flex-col gap-1.5">
                  {guidance.nextSteps.map((step, index) => (
                    <li key={step} className="flex gap-2.5 text-sm text-fg-muted">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-accent/40 font-mono text-[11px] text-accent">
                        {index + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                </ol>
              </GuideStep>
            </ol>

            {guidance.keyDefence && (
              <div className="relative flex items-start gap-4 overflow-hidden rounded-card border border-cyan/40 bg-linear-to-br from-cyan/10 via-primary/10 to-transparent p-4 shadow-[0_0_28px_-10px_rgb(34_211_238/0.6)]">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-cyan/40 bg-cyan/10 text-cyan shadow-[0_0_18px_-4px_rgb(34_211_238/0.7)]">
                  <ShieldIcon className="h-5 w-5" />
                </span>
                <div className="min-w-0">
                  <p className="font-mono text-[11px] tracking-widest text-cyan uppercase">
                    Aria’s key defence · {guidance.keyDefence.subtype}
                  </p>
                  <p className="mt-1.5 text-sm font-medium text-fg sm:text-base">{guidance.keyDefence.text}</p>
                </div>
              </div>
            )}
          </div>

          <div className="flex flex-col gap-4">
            <RuleCard title="Do" items={guidance.do} tone="do" />
            <RuleCard title="Don’t" items={guidance.dont} tone="dont" />
          </div>
        </div>
      </Card>
    </section>
  )
}

export default AriaGuidancePanel
