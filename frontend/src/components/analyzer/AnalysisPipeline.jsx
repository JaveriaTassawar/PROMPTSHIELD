import { CheckIcon, XIcon } from '../icons.jsx'

// Three-stage progress for one analysis, driven only by the request status —
// nothing advances on a timer:
//   idle      → all pending
//   analyzing → received done, scan active
//   success   → all done
//   error     → received done, scan failed
const STAGES = [
  { id: 'received', label: 'Prompt received' },
  { id: 'scan', label: 'Security scan' },
  { id: 'classification', label: 'Classification' },
]

const STATE_BY_STATUS = {
  idle: ['pending', 'pending', 'pending'],
  analyzing: ['done', 'active', 'pending'],
  success: ['done', 'done', 'done'],
  error: ['done', 'failed', 'pending'],
}

const STATE_TEXT = { pending: 'pending', active: 'in progress', done: 'complete', failed: 'failed' }

function StageMarker({ state }) {
  if (state === 'done') {
    return (
      <span className="flex h-5 w-5 animate-scale-in items-center justify-center rounded-full bg-primary text-white">
        <CheckIcon className="h-3 w-3" strokeWidth="3" />
      </span>
    )
  }
  if (state === 'failed') {
    return (
      <span className="flex h-5 w-5 animate-scale-in items-center justify-center rounded-full bg-danger/20 text-danger">
        <XIcon className="h-3 w-3" strokeWidth="3" />
      </span>
    )
  }
  if (state === 'active') {
    return (
      <span className="relative flex h-5 w-5 items-center justify-center">
        <span className="absolute inset-0 animate-ping rounded-full bg-cyan/40" />
        <span className="h-2.5 w-2.5 rounded-full bg-cyan shadow-[0_0_10px_rgb(34_211_238/0.9)]" />
      </span>
    )
  }
  return (
    <span className="flex h-5 w-5 items-center justify-center">
      <span className="h-2 w-2 rounded-full border border-fg-subtle" />
    </span>
  )
}

function AnalysisPipeline({ status }) {
  const states = STATE_BY_STATUS[status]

  return (
    <ol aria-label="Analysis progress" className="flex items-center gap-2">
      {STAGES.map((stage, index) => {
        const state = states[index]
        return (
          <li key={stage.id} className="flex items-center gap-2">
            {index > 0 && (
              <span
                aria-hidden="true"
                className={`h-px w-4 transition-colors duration-300 sm:w-6 ${states[index - 1] === 'done' ? 'bg-primary' : 'bg-border'}`}
              />
            )}
            <StageMarker state={state} />
            <span
              className={`hidden font-mono text-[11px] tracking-wide uppercase transition-colors duration-300 md:inline ${
                state === 'active' ? 'text-cyan' : state === 'done' ? 'text-fg-muted' : state === 'failed' ? 'text-danger' : 'text-fg-subtle'
              }`}
            >
              {stage.label}
            </span>
            <span className="sr-only md:hidden">{stage.label}</span>
            <span className="sr-only">: {STATE_TEXT[state]}</span>
          </li>
        )
      })}
    </ol>
  )
}

export default AnalysisPipeline
