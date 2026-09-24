import { Link } from 'react-router-dom'
import Card from '../components/Card.jsx'
import Logo from '../components/Logo.jsx'
import { ArrowRightIcon, ShieldIcon } from '../components/icons.jsx'

function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-6 text-center">
      <title>Page not found · PromptShield</title>
      <Logo className="animate-fade-in" />

      <Card glow className="flex w-full max-w-md animate-fade-up flex-col items-center gap-4 px-6 py-10">
        <span className="relative flex h-16 w-16 items-center justify-center rounded-full border border-accent/40 bg-primary/15 text-accent shadow-[0_0_28px_-4px_rgb(124_58_237/0.6)]">
          <ShieldIcon className="h-7 w-7" />
        </span>
        <p className="bg-linear-to-r from-fg to-accent bg-clip-text font-mono text-5xl font-bold tracking-tight text-transparent">404</p>
        <div>
          <p className="font-mono text-xs tracking-widest text-cyan/80 uppercase">Error 404</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-fg">Page not found</h1>
          <p className="mt-2 text-fg-muted">The page you are looking for does not exist.</p>
        </div>
        <Link
          to="/"
          className="group mt-2 inline-flex items-center gap-2 rounded-control border border-border bg-surface/80 px-4 py-2.5 text-sm font-semibold text-fg transition duration-150 ease-snappy hover:-translate-y-px hover:border-accent/50 hover:bg-surface-raised"
        >
          Back to home
          <ArrowRightIcon className="h-4 w-4 transition-transform duration-150 ease-snappy group-hover:translate-x-0.5" />
        </Link>
      </Card>
    </main>
  )
}

export default NotFoundPage
