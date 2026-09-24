// Status pill. safe / danger / warning map to the three detection classes
// (Safe / Direct Jailbreak / Indirect Injection); info is for AI/telemetry labels.
const VARIANTS = {
  neutral: 'border-border bg-surface-raised text-fg-muted',
  safe: 'border-safe/40 bg-safe/10 text-safe',
  danger: 'border-danger/40 bg-danger/10 text-danger',
  warning: 'border-warning/40 bg-warning/10 text-warning',
  info: 'border-cyan/40 bg-cyan/10 text-cyan',
}

function Badge({ variant = 'neutral', className = '', children }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${VARIANTS[variant]} ${className}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {children}
    </span>
  )
}

export default Badge
