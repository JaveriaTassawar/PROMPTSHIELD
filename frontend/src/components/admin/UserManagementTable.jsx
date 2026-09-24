import { useState } from 'react'
import Alert from '../Alert.jsx'
import Badge from '../Badge.jsx'
import Card from '../Card.jsx'
import FormField from '../FormField.jsx'
import { SearchIcon } from '../icons.jsx'
import RoleControl from './RoleControl.jsx'

// User management table (Task 90): User-model fields only — name, email, role
// (shown exactly as the record sends it) and join date. Search filters the rows
// already loaded in the browser; there is no server-side search or paging.
const ROLE_NOTE_ID = 'role-control-note'

const DATE_FORMAT = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

function matches(user, query) {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return [user.name, user.email].some((value) => value?.toLowerCase().includes(needle))
}

function TableMessage({ children }) {
  return (
    <p className="rounded-control border border-dashed border-border px-5 py-8 text-center text-sm text-fg-muted">{children}</p>
  )
}

function UserManagementTable({ status, users, sample = false }) {
  const [query, setQuery] = useState('')
  const visible = users.filter((user) => matches(user, query))
  const hasUsers = status === 'success' && users.length > 0

  let body
  if (status === 'loading') {
    body = (
      <div className="flex flex-col gap-2" aria-busy="true">
        <span className="sr-only">Loading users</span>
        {[0, 1, 2].map((row) => (
          <div key={row} className="h-10 animate-pulse rounded-control bg-surface-raised/60" />
        ))}
      </div>
    )
  } else if (status === 'unavailable') {
    body = <TableMessage>User records are not available — the admin users API is not connected yet.</TableMessage>
  } else if (status === 'error') {
    body = <Alert variant="error">User records could not be loaded. Refresh the page to try again.</Alert>
  } else if (users.length === 0) {
    body = <TableMessage>No user accounts yet.</TableMessage>
  } else {
    body = (
      <div className="-mx-5 overflow-x-auto px-5">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <caption className="sr-only">
            User accounts{sample ? ' (sample data, not real)' : ''}
          </caption>
          <thead>
            <tr className="border-b border-border font-mono text-[11px] tracking-widest text-fg-subtle uppercase">
              <th scope="col" className="py-2 pr-4 font-medium">
                Name
              </th>
              <th scope="col" className="py-2 pr-4 font-medium">
                Email
              </th>
              <th scope="col" className="py-2 pr-4 font-medium">
                Role
              </th>
              <th scope="col" className="py-2 pr-4 font-medium">
                Joined
              </th>
              <th scope="col" className="py-2 text-right font-medium">
                Role control
              </th>
            </tr>
          </thead>
          <tbody>
            {visible.map((user) => (
              <tr key={user.id} className="border-b border-border/50 last:border-b-0">
                <th scope="row" className="py-2.5 pr-4 font-medium text-fg">
                  {user.name ?? '—'}
                </th>
                <td className="py-2.5 pr-4 text-fg-muted">{user.email ?? '—'}</td>
                <td className="py-2.5 pr-4">
                  {user.role ? <span className="font-mono text-xs text-fg">{user.role}</span> : <span className="text-fg-subtle">—</span>}
                </td>
                <td className="py-2.5 pr-4 whitespace-nowrap text-fg-muted">
                  {user.joined ? <time dateTime={user.joined.toISOString()}>{DATE_FORMAT.format(user.joined)}</time> : '—'}
                </td>
                <td className="py-2.5 text-right">
                  <RoleControl userName={user.name} describedBy={ROLE_NOTE_ID} />
                </td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-fg-muted">
                  No loaded users match “{query.trim()}”.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <Card className="p-5">
      <section aria-labelledby="users-heading" className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 id="users-heading" className="font-semibold text-fg">
                User management
              </h2>
              {sample && <Badge variant="info">Sample</Badge>}
            </div>
            <p id={ROLE_NOTE_ID} className="mt-0.5 text-sm text-fg-muted">
              Role updates are unavailable: no role-update API is currently defined.
            </p>
          </div>
          {hasUsers && (
            <div className="md:w-72">
              <FormField
                id="user-search"
                type="search"
                label="Search loaded users"
                placeholder="Name or email"
                icon={SearchIcon}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                autoComplete="off"
              />
            </div>
          )}
        </div>

        {body}

        {hasUsers && (
          <p className="text-xs text-fg-subtle" aria-live="polite">
            Showing {visible.length} of {users.length} loaded {users.length === 1 ? 'user' : 'users'}.
          </p>
        )}
      </section>
    </Card>
  )
}

export default UserManagementTable
