import { AlertTriangleIcon } from '../icons.jsx'

// Shown whenever the Profile page displays the ?mock=preview account, so the
// synthetic profile can never be mistaken for a real user.
function ProfilePreviewNotice() {
  return (
    <div
      role="note"
      aria-label="Sample data notice"
      className="flex items-start gap-3 rounded-card border-2 border-dashed border-warning/60 bg-warning/10 px-4 py-3 text-warning"
    >
      <AlertTriangleIcon className="mt-0.5 h-5 w-5 shrink-0" />
      <div>
        <p className="font-mono text-sm font-bold tracking-widest uppercase">Sample data · Local preview</p>
        <p className="text-sm font-semibold">Not a real user account</p>
        <p className="mt-1 text-xs text-warning/80">
          The profile below is a made-up record used only to check this screen’s layout.
        </p>
      </div>
    </div>
  )
}

export default ProfilePreviewNotice
