import Logo from '../components/Logo.jsx'

// Minimal root landing page (/): the PromptShield logo and tagline. No landing
// page is specified in the frontend task plan; the app itself starts at /login.
function HomePage() {
  return (
    <main className="flex min-h-screen animate-fade-up flex-col items-center justify-center gap-3 p-6 text-center">
      <h1 className="sr-only">PromptShield</h1>
      <Logo />
      <p className="text-fg-muted">
        Secure prompting and simulation-based learning through avatar guidance.
      </p>
    </main>
  )
}

export default HomePage
