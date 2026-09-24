import Button from '../Button.jsx'
import Spinner from '../Spinner.jsx'
import { ArrowRightIcon, LockIcon } from '../icons.jsx'

const TEST_PROMPT_NOTE_ID = 'test-prompt-note'

// Send next turn / Restart, plus the test-prompt field that Task 85 enables.
// Send stays focusable while a turn is scanning (aria-disabled, not disabled),
// so keyboard focus is not lost between turns; repeat presses are ignored.
function SessionControls({ scanning, canRestart, onSend, onRestart, sendRef }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Button type="button" variant="ghost" onClick={onRestart} disabled={!canRestart || scanning}>
          Restart scenario
        </Button>
        <Button
          ref={sendRef}
          type="button"
          onClick={onSend}
          aria-disabled={scanning}
          className="w-full sm:w-auto sm:min-w-48"
        >
          {scanning ? (
            <>
              <Spinner />
              Scanning turn…
            </>
          ) : (
            <>
              Send next turn
              <ArrowRightIcon className="h-4.5 w-4.5" />
            </>
          )}
        </Button>
      </div>

      <div className="rounded-control border border-dashed border-border bg-canvas/40 p-3">
        <label htmlFor="test-prompt" className="flex items-center gap-2 text-sm font-medium text-fg-muted">
          <LockIcon className="h-4 w-4 text-fg-subtle" />
          Test prompt
        </label>
        <textarea
          id="test-prompt"
          disabled
          rows={2}
          aria-describedby={TEST_PROMPT_NOTE_ID}
          placeholder="Write your own prompt to test against this scenario"
          className="mt-2 block w-full resize-none rounded-control border border-border/70 bg-transparent px-3 py-2 font-mono text-sm text-fg-muted placeholder:font-sans placeholder:text-fg-subtle disabled:cursor-not-allowed"
        />
        <p id={TEST_PROMPT_NOTE_ID} className="mt-2 text-xs text-fg-subtle">
          Live test prompts require the simulation service.
        </p>
      </div>
    </div>
  )
}

export default SessionControls
