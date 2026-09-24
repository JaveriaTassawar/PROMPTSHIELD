// Example-prompt chips. Choosing one fills the editor; it does not analyze.
function ExamplePrompts({ examples, onSelect, disabled }) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
      <span className="shrink-0 font-mono text-[11px] tracking-widest text-fg-subtle uppercase">Try an example</span>
      <ul className="flex min-w-0 flex-wrap gap-2">
        {examples.map((example) => (
          <li key={example.id} className="min-w-0 max-w-full">
            <button
              type="button"
              onClick={() => onSelect(example.text)}
              disabled={disabled}
              title={example.text}
              className="block max-w-full truncate rounded-full border border-border bg-surface/70 px-3 py-1 font-mono text-xs text-fg-muted transition duration-150 ease-snappy enabled:hover:-translate-y-px enabled:hover:border-accent/50 enabled:hover:text-fg disabled:cursor-not-allowed disabled:opacity-50 sm:max-w-64"
            >
              <span className="sr-only">Use example: </span>
              {example.text}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default ExamplePrompts
