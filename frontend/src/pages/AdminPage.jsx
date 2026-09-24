import PageHeader from '../components/PageHeader.jsx'
import AccessDenied from '../components/admin/AccessDenied.jsx'
import AdminPreviewNotice from '../components/admin/AdminPreviewNotice.jsx'
import SystemHealthPanel from '../components/admin/SystemHealthPanel.jsx'
import UserManagementTable from '../components/admin/UserManagementTable.jsx'
import { useAdminUsers } from '../hooks/useAdminUsers.js'

const DATA_STATE = {
  loading: 'Loading',
  unavailable: 'API not connected',
  forbidden: 'Access denied (preview)',
  error: 'Could not load',
}

// Admin panel (Task 90, local preview). Reachable by URL only — it is not in
// the sidebar because the frontend has no authentication or role awareness
// yet. Task 91 wires the users table to GET /api/admin/users and its 403.
function AdminPage() {
  const { status, users, sample } = useAdminUsers()

  let dataState = DATA_STATE[status]
  if (status === 'success') dataState = sample ? 'Sample data' : 'Local preview'

  return (
    <div className="flex flex-col gap-6 lg:gap-8">
      <PageHeader
        eyebrow="Administration"
        title="Admin Panel"
        description="Registered user accounts, their roles and the status of PromptShield’s services."
      >
        <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase sm:text-right">
          Admin data · <span className={sample || status === 'forbidden' ? 'text-warning' : 'text-accent'}>{dataState}</span>
        </p>
      </PageHeader>

      <AdminPreviewNotice sample={sample} />

      {status === 'forbidden' ? (
        <AccessDenied />
      ) : (
        <>
          <UserManagementTable status={status} users={users} sample={sample} />
          <SystemHealthPanel />
        </>
      )}
    </div>
  )
}

export default AdminPage
