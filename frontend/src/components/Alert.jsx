import { AlertTriangleIcon, InfoIcon } from './icons.jsx'

const VARIANTS = {
  success: 'border-safe/40 bg-safe/10 text-safe',
  error: 'border-danger/40 bg-danger/10 text-danger',
  warning: 'border-warning/40 bg-warning/10 text-warning',
  info: 'border-cyan/40 bg-cyan/10 text-cyan',
}

function SuccessIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12.5l2.5 2.5L16 9.5" strokeDasharray="24" className="animate-draw" />
    </svg>
  )
}

// Errors and warnings are announced immediately (role="alert"); success and
// info are announced politely (role="status").
function Alert({ variant = 'info', className = '', children }) {
  const role = variant === 'error' || variant === 'warning' ? 'alert' : 'status'
  const icon =
    variant === 'success' ? (
      <SuccessIcon />
    ) : variant === 'info' ? (
      <InfoIcon className="h-5 w-5 shrink-0" />
    ) : (
      <AlertTriangleIcon className="h-5 w-5 shrink-0" />
    )

  return (
    <div role={role} className={`flex animate-alert-in items-start gap-2.5 rounded-control border px-3 py-2.5 text-sm ${VARIANTS[variant]} ${className}`}>
      {icon}
      <div className="pt-px">{children}</div>
    </div>
  )
}

export default Alert
