import { DetectionEntry } from './DetectionFeed.jsx'
import { FileTextIcon, LayersIcon, UserIcon } from '../icons.jsx'
import { TURN_ORIGINS, TURN_ROLES } from '../../config/simulation.js'

// Ordered transcript of the turns sent so far. User input reads as normal text;
// external content (documents, tool output) is shown in monospace on a dashed
// surface so it is visibly something the AI consumes, not something typed.
// Below lg, each turn's detection sits directly beneath it.
const ROLE_ICONS = { user: UserIcon, document: FileTextIcon, tool: LayersIcon }

function TurnItem({ entry, number, isLatest }) {
  const { turn, detection } = entry
  const role = TURN_ROLES[turn.role]
  const RoleIcon = ROLE_ICONS[turn.role]

  return (
    <li className={isLatest ? 'animate-fade-up' : undefined}>
      <div
        className={`rounded-control border px-4 py-3 ${
          role.external ? 'border-dashed border-warning/30 bg-canvas/60' : 'border-border/80 bg-surface/70'
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
          <span className="flex items-center gap-2 font-mono text-[11px] tracking-widest text-fg-muted uppercase">
            <span className="text-fg-subtle">{String(number).padStart(2, '0')}</span>
            <RoleIcon className={`h-4 w-4 ${role.external ? 'text-warning/80' : 'text-accent'}`} />
            {role.label}
          </span>
          <span className="text-[11px] text-fg-subtle">{TURN_ORIGINS[turn.origin]}</span>
        </div>
        <p
          className={`mt-2 break-words whitespace-pre-wrap text-fg ${
            role.external ? 'font-mono text-xs leading-relaxed' : 'text-sm leading-relaxed'
          }`}
        >
          {turn.content}
        </p>
      </div>
      <div className="mt-2 lg:hidden">
        <DetectionEntry detection={detection} turnNumber={number} isLatest={isLatest} compact />
      </div>
    </li>
  )
}

function TranscriptPanel({ entries }) {
  return (
    <section aria-labelledby="transcript-heading" className="flex flex-col gap-3">
      <h2 id="transcript-heading" className="font-mono text-xs tracking-widest text-fg-subtle uppercase">
        Scenario transcript
      </h2>
      {entries.length === 0 ? (
        <p className="rounded-control border border-dashed border-border px-4 py-6 text-center text-sm text-fg-muted">
          Send the first turn to begin the scenario.
        </p>
      ) : (
        <ol className="flex flex-col gap-3">
          {entries.map((entry, index) => (
            <TurnItem key={index} entry={entry} number={index + 1} isLatest={index === entries.length - 1} />
          ))}
        </ol>
      )}
    </section>
  )
}

export default TranscriptPanel
