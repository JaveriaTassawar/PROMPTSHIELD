import Spinner from './Spinner.jsx'

const VARIANTS = {
  primary:
    'bg-linear-to-r from-primary to-indigo text-white shadow-glow enabled:hover:shadow-glow-strong',
  secondary:
    'border border-border bg-surface/80 text-fg enabled:hover:border-accent/50 enabled:hover:bg-surface-raised',
  ghost: 'text-fg-muted enabled:hover:bg-surface-raised enabled:hover:text-fg',
}

// Buttons get a 1px lift on hover and a press-down on click. `loading` shows a
// spinner and disables the button; pass the loading label as children.
function Button({ variant = 'primary', loading = false, disabled, className = '', children, ...props }) {
  return (
    <button
      disabled={disabled || loading}
      className={`group relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-control px-4 py-2.5 font-semibold transition duration-150 ease-snappy enabled:hover:-translate-y-px enabled:active:translate-y-0 enabled:active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {variant === 'primary' && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -translate-x-full bg-linear-to-r from-transparent via-white/15 to-transparent group-enabled:group-hover:animate-sheen"
        />
      )}
      {loading && <Spinner />}
      <span className="relative inline-flex items-center gap-2">{children}</span>
    </button>
  )
}

export default Button
