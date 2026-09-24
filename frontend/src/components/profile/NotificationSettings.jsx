import Card from '../Card.jsx'
import SettingToggle from './SettingToggle.jsx'

// The three notification concepts from the SDS Profile prototype (Task 92).
// No preferences model or endpoint exists, so every toggle is disabled with no
// on/off value, and nothing is saved anywhere. Descriptions deliberately omit
// undefined details (severity thresholds, delivery schedules).
const NOTE_ID = 'notifications-note'

const NOTIFICATIONS = [
  { id: 'notify-critical-attack', label: 'Critical attack detected', description: 'Alert when a critical attack is detected' },
  { id: 'notify-weekly-summary', label: 'Weekly summary', description: 'A weekly digest of your activity' },
  { id: 'notify-new-tutorials', label: 'New tutorials', description: 'Notify when new learning material is published' },
]

function NotificationSettings() {
  return (
    <Card className="p-5">
      <section aria-labelledby="notifications-heading" className="flex flex-col gap-4">
        <div>
          <h2 id="notifications-heading" className="font-semibold text-fg">
            Notifications
          </h2>
          <p id={NOTE_ID} className="mt-0.5 text-sm text-fg-muted">
            Notification preferences are not supported by the current PromptShield backend, so these settings are
            unavailable and nothing is saved.
          </p>
        </div>
        <div className="flex flex-col gap-2.5">
          {NOTIFICATIONS.map((item) => (
            <SettingToggle key={item.id} {...item} disabled describedBy={NOTE_ID} />
          ))}
        </div>
      </section>
    </Card>
  )
}

export default NotificationSettings
