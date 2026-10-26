import { AlertTriangleIcon } from '../icons.jsx'

// Shown whenever the Analytics screen displays ?mock=preview data, so the
// synthetic numbers can never be mistaken for measured results.
function SampleDataBanner() {
  return (
    <div
      role="note"
      aria-label="Sample data notice"
      className="flex items-start gap-3 rounded-card border-2 border-dashed border-warning/60 bg-warning/10 px-4 py-3 text-warning"
    >
      <AlertTriangleIcon className="mt-0.5 h-5 w-5 shrink-0" />
      <div>
        <p className="font-mono text-sm font-bold tracking-widest uppercase">Sample data · Local preview</p>
        <p className="text-sm font-semibold">Not real analytics</p>
        <p className="mt-1 text-xs text-warning/80">
          Counts, the frequency series and the response time below are made-up values used only to check this screen’s
          layout. Only the offline model accuracy is a real figure.
        </p>
      </div>
    </div>
  )
}

export default SampleDataBanner
