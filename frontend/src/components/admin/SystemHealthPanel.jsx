import Badge from '../Badge.jsx'
import Card from '../Card.jsx'

// System health (Task 90): only states this screen can actually verify. The
// web app is available because this page loaded; nothing checks the backend
// or the model yet, so they are never shown as healthy — not even in preview.
const SERVICES = [
  {
    name: 'Web app',
    status: 'Available',
    variant: 'safe',
    detail: 'Verified: this page loaded in your browser.',
  },
  {
    name: 'Backend API',
    status: 'Not connected',
    variant: 'neutral',
    detail: 'No backend health check is connected to this screen yet.',
  },
  {
    name: 'Detection model',
    status: 'Not verified',
    variant: 'neutral',
    detail: 'The classifier’s status cannot be checked from this screen yet.',
  },
]

function SystemHealthPanel() {
  return (
    <Card className="p-5">
      <section aria-labelledby="health-heading" className="flex flex-col gap-4">
        <div>
          <h2 id="health-heading" className="font-semibold text-fg">
            System health
          </h2>
          <p className="mt-0.5 text-sm text-fg-muted">Only statuses this screen can verify are shown.</p>
        </div>
        <ul className="flex flex-col gap-2.5">
          {SERVICES.map((service) => (
            <li
              key={service.name}
              className="flex flex-col gap-1.5 rounded-control border border-border/60 bg-canvas/50 px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between sm:gap-4"
            >
              <div>
                <p className="text-sm font-medium text-fg">{service.name}</p>
                <p className="text-xs text-fg-subtle">{service.detail}</p>
              </div>
              <Badge variant={service.variant} className="self-start sm:self-center">
                {service.status}
              </Badge>
            </li>
          ))}
        </ul>
      </section>
    </Card>
  )
}

export default SystemHealthPanel
