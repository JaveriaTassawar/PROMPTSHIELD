import Alert from '../Alert.jsx'
import Badge from '../Badge.jsx'
import Card from '../Card.jsx'
import { UserIcon } from '../icons.jsx'

// Read-only personal information (Task 92): User-model fields only. No profile
// update endpoint exists, so nothing here is editable.
const DATE_FORMAT = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })

// "Sample User" → "SU"; a single word gives one letter.
function initialsOf(name) {
  const words = name.split(/\s+/).filter(Boolean)
  return words.length > 1 ? `${words[0][0]}${words.at(-1)[0]}`.toUpperCase() : words[0][0].toUpperCase()
}

function PersonalInfoCard({ status, profile }) {
  let body
  if (status === 'loading') {
    body = (
      <div className="flex items-center gap-4" aria-busy="true">
        <span className="sr-only">Loading profile</span>
        <div className="h-14 w-14 animate-pulse rounded-full bg-surface-raised" />
        <div className="flex flex-1 flex-col gap-2">
          <div className="h-4 w-40 animate-pulse rounded-control bg-surface-raised" />
          <div className="h-3 w-56 animate-pulse rounded-control bg-surface-raised/70" />
        </div>
      </div>
    )
  } else if (status === 'error') {
    body = <Alert variant="error">Your profile could not be loaded. Refresh the page to try again.</Alert>
  } else if (status === 'unavailable' || !profile) {
    body = (
      <div className="flex flex-col items-center gap-3 rounded-control border border-dashed border-border px-5 py-8 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full border border-border bg-surface-raised text-fg-subtle">
          <UserIcon className="h-5 w-5" />
        </span>
        <p className="font-medium text-fg">Profile unavailable</p>
        <p className="max-w-sm text-sm text-fg-muted">
          The authentication/profile API is not connected yet, so no account details can be shown.
        </p>
      </div>
    )
  } else {
    const fields = [
      { label: 'Name', value: profile.name },
      { label: 'Email', value: profile.email },
      { label: 'Role', value: profile.role, mono: true },
      {
        label: 'Joined',
        value: profile.joined && <time dateTime={profile.joined.toISOString()}>{DATE_FORMAT.format(profile.joined)}</time>,
      },
    ]

    body = (
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-4">
          <span
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-linear-to-br from-primary to-indigo text-lg font-bold text-white shadow-glow"
            aria-hidden="true"
          >
            {profile.name ? initialsOf(profile.name) : <UserIcon className="h-6 w-6" />}
          </span>
          <div className="min-w-0">
            <p className="truncate text-lg font-semibold text-fg">{profile.name ?? 'Unnamed account'}</p>
            {profile.email && <p className="truncate text-sm text-fg-muted">{profile.email}</p>}
          </div>
        </div>

        <dl className="grid gap-x-6 gap-y-4 sm:grid-cols-2">
          {fields.map((field) => (
            <div key={field.label} className="min-w-0 rounded-control border border-border/60 bg-canvas/50 px-3 py-2.5">
              <dt className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">{field.label}</dt>
              <dd className={`mt-1 break-words text-sm text-fg ${field.mono ? 'font-mono' : ''}`}>
                {field.value ?? <span className="text-fg-subtle">—</span>}
              </dd>
            </div>
          ))}
        </dl>

        <p className="text-xs text-fg-subtle">These details are read-only — profile editing is not available yet.</p>
      </div>
    )
  }

  return (
    <Card className="p-5">
      <section aria-labelledby="personal-info-heading" className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <h2 id="personal-info-heading" className="font-semibold text-fg">
            Personal information
          </h2>
          {profile?.sample && <Badge variant="info">Sample</Badge>}
        </div>
        {body}
      </section>
    </Card>
  )
}

export default PersonalInfoCard
