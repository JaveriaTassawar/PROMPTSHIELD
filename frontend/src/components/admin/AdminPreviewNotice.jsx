import { AlertTriangleIcon, LockIcon } from '../icons.jsx'

// Shown on every Admin view: the route is open to anyone in this build, and
// ?mock=preview users are synthetic. Neither may be mistaken for the real thing.
function AdminPreviewNotice({ sample = false }) {
  return (
    <div className="flex flex-col gap-3">
      <div
        role="note"
        aria-label="Access control notice"
        className="flex items-start gap-3 rounded-card border border-danger/50 bg-danger/10 px-4 py-3 text-danger"
      >
        <LockIcon className="mt-0.5 h-5 w-5 shrink-0" />
        <div>
          <p className="font-mono text-sm font-bold tracking-widest uppercase">
            Admin preview · Access control not implemented
          </p>
          <p className="mt-1 text-sm text-fg-muted">
            Anyone can currently open this route in the frontend build. Real admin authorization will be enforced by the
            backend and handled when Task 91 is integrated.
          </p>
        </div>
      </div>

      {sample && (
        <div
          role="note"
          aria-label="Sample data notice"
          className="flex items-start gap-3 rounded-card border-2 border-dashed border-warning/60 bg-warning/10 px-4 py-3 text-warning"
        >
          <AlertTriangleIcon className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-mono text-sm font-bold tracking-widest uppercase">Sample data · Local preview</p>
            <p className="text-sm font-semibold">Not real user accounts</p>
            <p className="mt-1 text-xs text-warning/80">
              The users below are made-up records used only to check this screen’s layout.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminPreviewNotice
