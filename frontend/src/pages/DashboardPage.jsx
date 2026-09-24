import { Link } from 'react-router-dom'
import Badge from '../components/Badge.jsx'
import Card from '../components/Card.jsx'
import PageHeader from '../components/PageHeader.jsx'
import { ArrowRightIcon, ShieldIcon } from '../components/icons.jsx'
import { DETECTION_CLASSES } from '../config/detection.js'
import { findNavItem } from '../config/navigation.js'

// Shell-level overview (Task 74). Everything here is static: no statistics or
// activity are shown until the dashboard API is wired in Task 89.

const QUICK_LINKS = ['/analyzer', '/simulation', '/learning'].map(findNavItem)

function DashboardPage() {
  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        eyebrow="Overview"
        title="Security Overview"
        description="Your PromptShield workspace. Analyse prompts for injection attacks, practise against simulated attacks and build safe-prompting skills."
      />

      <section aria-labelledby="quick-start-heading">
        <h2 id="quick-start-heading" className="sr-only">
          Quick start
        </h2>
        <ul className="grid gap-4 md:grid-cols-3">
          {QUICK_LINKS.map((item, index) => (
            <li key={item.to} className="animate-fade-up" style={{ animationDelay: `${80 + index * 70}ms` }}>
              <Link
                to={item.to}
                className="group glass flex h-full flex-col rounded-card border border-border/80 p-5 shadow-card transition duration-200 ease-snappy hover:-translate-y-0.5 hover:border-accent/50 hover:shadow-glow"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-control bg-primary/20 text-accent transition-colors group-hover:bg-primary/30">
                  <item.icon className="h-5 w-5" />
                </span>
                <span className="mt-4 font-semibold text-fg">{item.label}</span>
                <span className="mt-1 text-sm text-fg-muted">{item.summary}</span>
                <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-accent">
                  Open
                  <ArrowRightIcon className="h-4 w-4 transition-transform duration-150 ease-snappy group-hover:translate-x-1" />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="p-5 lg:col-span-3">
          <h2 className="font-semibold text-fg">What PromptShield detects</h2>
          <p className="mt-1 text-sm text-fg-muted">Every prompt is classified into one of three classes.</p>
          <ul className="mt-4 flex flex-col gap-2.5">
            {DETECTION_CLASSES.map((detection) => (
              <li
                key={detection.label}
                className="flex flex-wrap items-center gap-x-3 gap-y-1.5 rounded-control border border-border/60 bg-canvas/50 px-3 py-2.5"
              >
                <Badge variant={detection.variant}>{detection.label}</Badge>
                <span className="text-sm text-fg-muted">{detection.description}</span>
                {detection.subtypes.length > 0 && (
                  <span className="ml-auto font-mono text-xs text-fg-subtle">
                    {detection.subtypes.length} {detection.subtypeNoun}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </Card>

        <Card className="flex flex-col items-center justify-center gap-3 p-6 text-center lg:col-span-2">
          <span className="flex h-11 w-11 items-center justify-center rounded-full border border-border bg-surface-raised text-fg-subtle">
            <ShieldIcon className="h-5 w-5" />
          </span>
          <h2 className="font-semibold text-fg">Security activity</h2>
          <p className="max-w-xs text-sm text-fg-muted">
            Live scan telemetry and your recent activity will appear here once PromptShield's analysis services are connected.
          </p>
        </Card>
      </div>
    </div>
  )
}

export default DashboardPage
