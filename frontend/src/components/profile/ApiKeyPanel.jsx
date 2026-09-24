import Card from '../Card.jsx'
import { LockIcon } from '../icons.jsx'

// API key section required by Task 92. API keys are not part of the planned
// backend (the API uses JWT sign-in), so no key, key format, masked value or
// copy/regenerate controls are shown.
function ApiKeyPanel() {
  return (
    <Card className="p-5">
      <section aria-labelledby="api-key-heading" className="flex flex-col gap-4">
        <h2 id="api-key-heading" className="font-semibold text-fg">
          API key
        </h2>
        <div className="flex items-start gap-3 rounded-control border border-dashed border-border px-4 py-4">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface-raised text-fg-subtle">
            <LockIcon className="h-4.5 w-4.5" />
          </span>
          <div>
            <p className="text-sm font-medium text-fg">Not available</p>
            <p className="mt-0.5 text-sm text-fg-muted">
              API keys are not part of the currently planned PromptShield backend, so there is no key to display.
            </p>
          </div>
        </div>
      </section>
    </Card>
  )
}

export default ApiKeyPanel
