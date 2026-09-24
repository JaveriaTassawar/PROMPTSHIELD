// PromptShield mark: violet shield with a cyan "AI core" node, plus wordmark.
function Logo({ className = '' }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg viewBox="0 0 32 32" className="h-8 w-8 drop-shadow-[0_0_10px_rgb(124_58_237/0.6)]" aria-hidden="true">
        <defs>
          <linearGradient id="logo-shield" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--color-accent)" />
            <stop offset="100%" stopColor="var(--color-indigo)" />
          </linearGradient>
        </defs>
        <path d="M16 3l11 4v8c0 6.4-4.6 11.6-11 13-6.4-1.4-11-6.6-11-13V7l11-4z" fill="url(#logo-shield)" />
        <path d="M16 7.5l7 2.6v5c0 4.2-2.9 7.7-7 8.8-4.1-1.1-7-4.6-7-8.8v-5l7-2.6z" fill="var(--color-canvas)" opacity="0.55" />
        <circle cx="16" cy="15" r="2.6" fill="var(--color-cyan)" />
        <path d="M16 11v1.4M16 17.6V19M12 15h1.4M18.6 15H20" stroke="var(--color-cyan)" strokeWidth="1.3" strokeLinecap="round" />
      </svg>
      <span className="text-lg font-bold tracking-tight text-fg">
        Prompt<span className="text-accent">Shield</span>
      </span>
    </div>
  )
}

export default Logo
