import PageHeader from '../components/PageHeader.jsx'
import ApiKeyPanel from '../components/profile/ApiKeyPanel.jsx'
import NotificationSettings from '../components/profile/NotificationSettings.jsx'
import PersonalInfoCard from '../components/profile/PersonalInfoCard.jsx'
import ProfilePreviewNotice from '../components/profile/ProfilePreviewNotice.jsx'
import { findNavItem } from '../config/navigation.js'
import { useProfile } from '../hooks/useProfile.js'

const NAV_ITEM = findNavItem('/profile')

const DATA_STATE = {
  loading: 'Loading',
  unavailable: 'API not connected',
  error: 'Could not load',
}

// Profile & settings (Task 92, local preview): read-only personal information,
// plus notification and API-key sections that the backend does not support
// yet. No task wires GET /api/profile here; useProfile() is the swap point.
function ProfilePage() {
  const { status, profile } = useProfile()
  const sample = profile?.sample === true

  let dataState = DATA_STATE[status]
  if (status === 'success') dataState = sample ? 'Sample data' : 'Local preview'

  return (
    <div className="flex flex-col gap-6 lg:gap-8">
      <PageHeader
        eyebrow={NAV_ITEM.eyebrow}
        title="Profile & Settings"
        description="Your account details, notification preferences and API access."
      >
        <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase sm:text-right">
          Profile data · <span className={sample ? 'text-warning' : 'text-accent'}>{dataState}</span>
        </p>
      </PageHeader>

      <div className="flex w-full max-w-3xl flex-col gap-6">
        {sample && <ProfilePreviewNotice />}
        <PersonalInfoCard status={status} profile={profile} />
        <NotificationSettings />
        <ApiKeyPanel />
      </div>
    </div>
  )
}

export default ProfilePage
