// Labelled text input with an optional error message, shared by the auth forms.
// `icon` is a leading icon component; `trailing` renders inside the right edge
// of the input (e.g. the password visibility toggle).
function FormField({ id, label, error, ref, icon: IconComponent, trailing, ...inputProps }) {
  const errorId = `${id}-error`

  return (
    <div className="flex flex-col gap-1.5" data-field>
      <label htmlFor={id} className="text-sm font-medium text-fg">
        {label}
      </label>
      <div className="group relative">
        {IconComponent && (
          <IconComponent
            className={`pointer-events-none absolute top-1/2 left-3 h-4.5 w-4.5 -translate-y-1/2 transition-colors duration-150 ${
              error ? 'text-danger' : 'text-fg-subtle group-focus-within:text-accent'
            }`}
          />
        )}
        <input
          id={id}
          ref={ref}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={`w-full rounded-control border bg-canvas/60 py-2.5 text-fg transition duration-150 placeholder:text-fg-subtle hover:border-accent/40 focus:bg-canvas/80 focus-visible:outline-none ${
            IconComponent ? 'pl-10' : 'pl-3'
          } ${trailing ? 'pr-11' : 'pr-3'} ${
            error
              ? 'border-danger focus:shadow-[0_0_0_3px_rgb(248_113_113/0.3)]'
              : 'border-border focus:border-accent focus:shadow-[0_0_0_3px_rgb(167_139_250/0.3)]'
          }`}
          {...inputProps}
        />
        {trailing && <div className="absolute inset-y-0 right-1.5 flex items-center">{trailing}</div>}
      </div>
      {error && (
        <p id={errorId} className="animate-alert-in text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  )
}

export default FormField
