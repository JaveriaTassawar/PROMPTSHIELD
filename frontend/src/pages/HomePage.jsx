import { Link } from 'react-router-dom'

import Logo from '../components/Logo.jsx'

// Root landing page (/). The logo and tagline, plus the two ways into the
// app.
//
// WHY THE LINKS ARE HERE.
//
// This page previously had no links at all, so anyone who typed the bare
// address landed on a logo with no way forward and had to guess that the
// app lives at /register. That is the first thing a visitor sees, and an
// examiner opening the project will do exactly that.
//
// WHY <Link> AND NOT <Button>.
//
// Button renders a <button>. Wrapping one in a Link nests an interactive
// element inside another, which is invalid HTML and makes screen readers
// announce the control twice. These are navigation, so they are anchors
// styled to match Button's primary and secondary variants — the classes
// are copied from components/Button.jsx rather than imported, because
// that component's are tied to <button> states (enabled:, disabled:)
// which do not apply to an anchor.
const PRIMARY =
  'bg-linear-to-r from-primary to-indigo text-white shadow-glow hover:shadow-glow-strong'
const SECONDARY =
  'border border-border bg-surface/80 text-fg hover:border-accent/50 hover:bg-surface-raised'
const BASE =
  'inline-flex items-center justify-center gap-2 rounded-control px-5 py-2.5 font-semibold transition duration-150 ease-snappy hover:-translate-y-px active:translate-y-0 active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent'

function HomePage() {
  return (
    <main className="flex min-h-screen animate-fade-up flex-col items-center justify-center gap-6 p-6 text-center">
      <div className="flex flex-col items-center gap-3">
        <h1 className="sr-only">PromptShield</h1>
        <Logo />
        <p className="max-w-md text-fg-muted">
          Secure prompting and simulation-based learning through avatar guidance.
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        {/* Create account first: a first-time visitor has no account, and
            this page is mostly seen by first-time visitors. */}
        <Link to="/register" className={`${BASE} ${PRIMARY}`}>
          Create account
        </Link>
        <Link to="/login" className={`${BASE} ${SECONDARY}`}>
          Sign in
        </Link>
      </div>
    </main>
  )
}

export default HomePage
