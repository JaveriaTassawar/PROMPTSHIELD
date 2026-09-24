// Switch for a single setting. `checked` is true/false for a known saved value.
// With `checked={null}` there is no known value, so it is shown neither on nor
// off (knob centred) and is not announced as a switch state — only as
// unavailable. Pass `describedBy` to point at the visible reason.
function SettingToggle({ id, label, description, checked = null, disabled = false, describedBy, onChange }) {
  const known = typeof checked === 'boolean'
  const descriptionId = `${id}-description`

  const knobPosition = !known ? 'translate-x-2.5' : checked ? 'translate-x-5' : 'translate-x-0'
  const track = known && checked ? 'bg-primary border-primary' : 'bg-surface-raised border-border'

  return (
    <div className="flex items-center justify-between gap-4 rounded-control border border-border/60 bg-canvas/50 px-3 py-3">
      <div className="min-w-0">
        <p id={`${id}-label`} className="text-sm font-medium text-fg">
          {label}
        </p>
        {description && (
          <p id={descriptionId} className="text-xs text-fg-subtle">
            {description}
          </p>
        )}
      </div>
      <button
        type="button"
        id={id}
        role={known ? 'switch' : undefined}
        aria-checked={known ? checked : undefined}
        aria-labelledby={known ? `${id}-label` : `${id}-label ${id}-state`}
        aria-describedby={[description && descriptionId, describedBy].filter(Boolean).join(' ') || undefined}
        disabled={disabled}
        onClick={() => onChange?.(!checked)}
        className="flex shrink-0 items-center gap-2 disabled:cursor-not-allowed"
      >
        {!known && (
          <span id={`${id}-state`} className="text-xs text-fg-subtle">
            Unavailable
          </span>
        )}
        <span
          aria-hidden="true"
          className={`relative inline-flex h-6 w-11 items-center rounded-full border p-0.5 transition-colors ${track} ${
            disabled ? 'opacity-50' : ''
          } ${known ? '' : 'border-dashed'}`}
        >
          <span className={`h-4.5 w-4.5 rounded-full bg-fg-muted transition-transform ${knobPosition}`} />
        </span>
      </button>
    </div>
  )
}

export default SettingToggle
