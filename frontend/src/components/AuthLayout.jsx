import { Outlet, useLocation } from 'react-router-dom'
import Card from './Card.jsx'
import ClassificationPreview from './ClassificationPreview.jsx'
import DefenseVisualization from './DefenseVisualization.jsx'
import Logo from './Logo.jsx'
import { BotIcon, ScanIcon, SparklesIcon } from './icons.jsx'

// Placeholder copy based on the project README — replace with the SDS wording.
const FEATURES = [
  {
    icon: ScanIcon,
    title: 'Real-time detection',
    text: 'Classifies prompts as Safe, Direct Jailbreak or Indirect Injection.',
  },
  {
    icon: SparklesIcon,
    title: 'Safe prompt rewrites',
    text: 'Suggests a safer version of risky prompts.',
  },
  {
    icon: BotIcon,
    title: 'Avatar-guided learning',
    text: 'Practise spotting attacks in a guided simulation sandbox.',
  },
]

// Layout route shared by Login and Register: branding panel on the left (wide
// screens only) and the page's form card on the right. The branding panel stays
// mounted when moving between the two pages; only the form card fades.
function AuthLayout() {
  const location = useLocation()

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Scanner and Sample Analysis take priority: on shorter screens the feature
          descriptions hide first, then the feature cards. */}
      <aside className="relative hidden flex-col gap-5 overflow-hidden border-r border-border/60 bg-canvas/40 px-10 py-9 lg:flex xl:px-12 short:py-7 shorter:gap-4">
        <Logo className="animate-fade-in" />

        <div className="animate-fade-up" style={{ animationDelay: '80ms' }}>
          <p className="font-mono text-xs tracking-widest text-cyan/80 uppercase">AI prompt security</p>
          <p className="mt-2.5 bg-linear-to-r from-fg via-fg to-accent bg-clip-text text-3xl leading-tight font-bold tracking-tight text-transparent xl:text-4xl short:xl:text-3xl">
            Secure Your AI Interactions
          </p>
          <p className="mt-2.5 max-w-lg text-fg-muted">
            Detect prompt injection and jailbreak attempts in real time, and learn to write safer prompts.
          </p>
        </div>

        <div className="flex flex-1 flex-col items-center justify-center gap-5 shorter:gap-4">
          <DefenseVisualization className="animate-fade-in" />
          <ClassificationPreview className="max-w-xl animate-fade-up" />
        </div>

        <ul className="grid grid-cols-3 gap-3 shorter:hidden">
          {FEATURES.map((feature, index) => (
            <li
              key={feature.title}
              className="animate-fade-up rounded-card border border-border/60 bg-surface/40 p-3 transition-colors duration-150 hover:border-accent/40"
              style={{ animationDelay: `${500 + index * 80}ms` }}
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-control bg-primary/20 text-accent" aria-hidden="true">
                <feature.icon className="h-4 w-4" />
              </span>
              <p className="mt-2 text-sm font-semibold text-fg">{feature.title}</p>
              <p className="mt-0.5 text-xs text-fg-muted short:hidden">{feature.text}</p>
            </li>
          ))}
        </ul>
      </aside>

      <main className="flex flex-col items-center justify-center px-4 py-8 sm:px-6">
        <div className="w-full max-w-md">
          <Logo className="mb-6 animate-fade-in lg:hidden" />
          <Card glow key={location.pathname} className="animate-fade-up p-6 sm:p-7">
            <Outlet />
          </Card>
        </div>
      </main>
    </div>
  )
}

export default AuthLayout
