import { Link } from 'react-router-dom'
import Card from '../Card.jsx'
import { LockIcon } from '../icons.jsx'

// The screen a non-admin will see once GET /api/admin/users returns 403
// (Task 91). Today it only appears with ?mock=forbidden — no roles are checked.
function AccessDenied() {
  return (
    <Card className="flex flex-col items-center gap-4 px-6 py-12 text-center" borderClassName="border-danger/40">
      <span className="flex h-14 w-14 items-center justify-center rounded-full border border-danger/40 bg-danger/10 text-danger">
        <LockIcon className="h-6 w-6" />
      </span>
      <div>
        <h2 className="text-lg font-semibold text-fg">Admin access required</h2>
        <p className="mt-1 max-w-md text-sm text-fg-muted">
          Your account doesn’t have permission to view the admin panel. If you think this is a mistake, contact a
          PromptShield administrator.
        </p>
      </div>
      <p className="max-w-md rounded-control border border-dashed border-border px-3 py-2 text-xs text-fg-subtle">
        Preview of the future 403 (Forbidden) state, shown by <span className="font-mono">?mock=forbidden</span>. The
        frontend does not check roles yet.
      </p>
      <Link
        to="/dashboard"
        className="text-sm font-medium text-accent underline-offset-4 transition-colors hover:text-fg hover:underline"
      >
        Back to Security Overview
      </Link>
    </Card>
  )
}

export default AccessDenied
