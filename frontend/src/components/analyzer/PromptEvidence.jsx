// The submitted prompt, shown as analysed. The current analysis response has
// no span-level evidence, so nothing inside the prompt is highlighted — the
// classification applies to the prompt as a whole. When the API provides
// flagged spans, render them here instead of the plain text.
function PromptEvidence({ prompt, label = 'Submitted prompt' }) {
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <span className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">{label}</span>
      <div
        tabIndex={0}
        aria-label={label}
        className="max-h-44 overflow-y-auto rounded-control border border-border/70 bg-canvas/70 px-3 py-2.5"
      >
        <p className="font-mono text-xs leading-relaxed break-words whitespace-pre-wrap text-fg">{prompt}</p>
      </div>
      <p className="text-xs text-fg-subtle">
        The classification applies to the whole prompt. Individual words are not highlighted.
      </p>
    </div>
  )
}

export default PromptEvidence
