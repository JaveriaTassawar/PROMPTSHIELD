import { useState } from 'react'
import Card from '../Card.jsx'
import { DetectionEntry } from './DetectionFeed.jsx'
import { FileTextIcon, LayersIcon, UserIcon } from '../icons.jsx'
import { TURN_ORIGINS, TURN_ROLES } from '../../config/simulation.js'

// Recap of every turn in the completed run with its annotation. A factual
// breakdown of the scenario — not challenges, and nothing is passed or missed.
// Same role icons as the Task 84 transcript.
const ROLE_ICONS = { user: UserIcon, document: FileTextIcon, tool: LayersIcon }
const LONG_TURN = 140

function BreakdownRow({ entry, number }) {
  const { turn, detection } = entry
  const role = TURN_ROLES[turn.role]
  const RoleIcon = ROLE_ICONS[turn.role]
  const isLong = turn.content.length > LONG_TURN
  const [expanded, setExpanded] = useState(false)
  const contentId = `breakdown-turn-${number}`

  return (
    <li className="grid gap-3 border-t border-border/60 py-4 first:border-t-0 first:pt-0 last:pb-0 md:grid-cols-[minmax(0,1fr)_15rem] md:gap-6">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="flex items-center gap-2 font-mono text-[11px] tracking-widest text-fg-muted uppercase">
            <span className="text-fg-subtle">{String(number).padStart(2, '0')}</span>
            <RoleIcon className={`h-4 w-4 ${role.external ? 'text-warning/80' : 'text-accent'}`} />
            {role.label}
          </span>
          <span className="text-[11px] text-fg-subtle">{TURN_ORIGINS[turn.origin]}</span>
        </div>
        <p
          id={contentId}
          className={`mt-1.5 break-words whitespace-pre-wrap text-fg ${
            role.external ? 'font-mono text-xs leading-relaxed' : 'text-sm leading-relaxed'
          } ${isLong && !expanded ? 'line-clamp-2' : ''}`}
        >
          {turn.content}
        </p>
        {isLong && (
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            aria-expanded={expanded}
            aria-controls={contentId}
            className="mt-1 rounded text-xs font-medium text-accent transition-colors hover:text-fg"
          >
            {expanded ? 'Show less' : 'Show full turn'}
          </button>
        )}
      </div>
      <DetectionEntry detection={detection} turnNumber={number} isLatest={false} compact />
    </li>
  )
}

function TurnBreakdown({ entries }) {
  return (
    <Card className="p-5">
      <section aria-labelledby="turn-breakdown-heading">
        <h2 id="turn-breakdown-heading" className="font-mono text-xs tracking-widest text-fg-subtle uppercase">
          Turn-by-turn breakdown
        </h2>
        <ol className="mt-4">
          {entries.map((entry, index) => (
            <BreakdownRow key={index} entry={entry} number={index + 1} />
          ))}
        </ol>
      </section>
    </Card>
  )
}

export default TurnBreakdown
