// Prompt input for the analyzer: monospace text on a faint grid, with a cyan
// scan sweep while an analysis runs. The text is read-only (not disabled) during
// a scan so it stays readable and focusable.
function PromptEditor({ id, value, onChange, onSubmitShortcut, scanning }) {
  const hintId = `${id}-hint`

  function handleKeyDown(event) {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault()
      onSubmitShortcut()
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-medium text-fg">
        Prompt to analyze
      </label>
      <div
        className={`relative overflow-hidden rounded-control border bg-canvas/70 transition duration-150 focus-within:shadow-[0_0_0_3px_rgb(167_139_250/0.3)] ${
          scanning ? 'border-cyan/50' : 'border-border hover:border-accent/40 focus-within:border-accent'
        }`}
      >
        <div className="pointer-events-none absolute inset-0 bg-grid opacity-40" aria-hidden="true" />
        {scanning && (
          <div className="pointer-events-none absolute inset-0 animate-scan-down" aria-hidden="true">
            <div className="absolute inset-x-0 bottom-0 h-16 bg-linear-to-b from-transparent to-cyan/15" />
            <div className="absolute inset-x-0 bottom-0 h-px bg-cyan shadow-[0_0_12px_rgb(34_211_238/0.9)]" />
          </div>
        )}
        <textarea
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          readOnly={scanning}
          aria-describedby={hintId}
          spellCheck={false}
          placeholder="Paste or type a prompt, e.g. an instruction you plan to send to an AI model…"
          className="relative block min-h-44 w-full resize-y bg-transparent px-4 py-3 font-mono text-sm leading-relaxed text-fg placeholder:font-sans placeholder:text-fg-subtle focus-visible:outline-none sm:min-h-52"
        />
      </div>
      <div id={hintId} className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-xs text-fg-subtle">
        <span>
          {value.length} {value.length === 1 ? 'character' : 'characters'}
        </span>
        <span className="hidden sm:inline">
          Press <kbd className="rounded border border-border px-1 font-mono text-fg-muted">Ctrl</kbd> +{' '}
          <kbd className="rounded border border-border px-1 font-mono text-fg-muted">Enter</kbd> to analyze
        </span>
      </div>
    </div>
  )
}

export default PromptEditor
