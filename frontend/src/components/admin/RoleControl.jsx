import Button from '../Button.jsx'

// Per-user role control required by Task 90. No role-update API is defined, so
// it stays disabled; `describedBy` points at the visible reason next to the table.
function RoleControl({ userName, describedBy }) {
  return (
    <Button
      type="button"
      variant="secondary"
      disabled
      aria-describedby={describedBy}
      className="px-3 py-1.5 text-xs whitespace-nowrap"
    >
      Change role
      <span className="sr-only"> for {userName ?? 'this user'}</span>
    </Button>
  )
}

export default RoleControl
