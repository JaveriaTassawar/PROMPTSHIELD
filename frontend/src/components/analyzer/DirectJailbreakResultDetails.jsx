import Button from '../Button.jsx'
import PromptEvidence from './PromptEvidence.jsx'
import { AlertTriangleIcon, BotIcon, InfoIcon, SparklesIcon } from '../icons.jsx'

// Direct Jailbreak detail beneath the shared ResultSummary (Task 78): the attack
// pattern (sub-type) with its fixed definition, the category-level finding,
// the submitted prompt, and the defensive actions. All explanatory text comes
// from config/detection.js; nothing here is prompt-specific model reasoning.
//
// Get Safe Rewrite (Backend Task 59) has no working service yet, so it is shown
// disabled with a visible reason. Ask Avatar moves to Aria's guidance panel on
// this page (Task 81) — it makes no request.
const ACTIONS_NOTE_ID = 'jailbreak-actions-note'
const ASK_AVATAR_HINT_ID = 'jailbreak-ask-avatar-hint'

function DirectJailbreakResultDetails({ result, detection, prompt, onAskAria }) {
  const { explanation } = detection
  const subtypeDefinition = detection.subtypeDefinitions[result.subtype]
  const isKnownSubtype = detection.subtypes.includes(result.subtype)

  return (
    <div className="mt-5 flex flex-col gap-6 border-t border-border/70 pt-5">
      <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:gap-8">
        <div className="flex flex-col gap-5">
          {result.subtype && (
            <div className="flex gap-3">
              <span
                className="flex h-10 w-10 shrink-0 animate-scale-in items-center justify-center rounded-full border border-danger/40 bg-danger/10 text-danger"
                style={{ animationDelay: '150ms' }}
              >
                <AlertTriangleIcon className="h-5 w-5" />
              </span>
              <div className="min-w-0 animate-fade-up" style={{ animationDelay: '250ms' }}>
                <p className="font-mono text-[11px] tracking-widest text-danger uppercase">
                  Attack pattern
                  {isKnownSubtype && <span className="text-fg-subtle"> · one of {detection.subtypes.length}</span>}
                </p>
                <p className="mt-0.5 text-lg font-semibold text-fg">{result.subtype}</p>
                {subtypeDefinition && <p className="mt-1 text-sm text-fg-muted">{subtypeDefinition}</p>}
              </div>
            </div>
          )}

          <div className="animate-fade-up" style={{ animationDelay: '350ms' }}>
            <h3 className="text-sm font-semibold text-fg">{explanation.title}</h3>
            <ul className="mt-2.5 flex flex-col gap-2">
              {explanation.points.map((point) => (
                <li key={point} className="flex gap-2.5 text-sm text-fg-muted">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-danger" aria-hidden="true" />
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
          <PromptEvidence prompt={prompt} />
        </div>
      </div>

      <div
        className="flex animate-fade-up flex-col gap-3 border-t border-border/70 pt-4 sm:flex-row sm:items-center"
        style={{ animationDelay: '600ms' }}
      >
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button type="button" variant="secondary" disabled aria-describedby={ACTIONS_NOTE_ID} className="w-full sm:w-auto">
            <SparklesIcon className="h-4.5 w-4.5" />
            Get Safe Rewrite
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={onAskAria}
            disabled={!onAskAria}
            aria-describedby={ASK_AVATAR_HINT_ID}
            className="w-full sm:w-auto"
          >
            <BotIcon className="h-4.5 w-4.5" />
            Ask Avatar
          </Button>
        </div>
        <p className="text-xs text-fg-subtle sm:ml-1">
          <span id={ACTIONS_NOTE_ID}>Safe rewrites are not available in this version yet.</span>{' '}
          <span id={ASK_AVATAR_HINT_ID}>Ask Avatar opens Aria’s guidance below.</span>
        </p>
      </div>
    </div>
  )
}

export default DirectJailbreakResultDetails
