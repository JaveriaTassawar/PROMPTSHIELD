// Aria's emblem: a violet guide mark with a cyan "insight" node — related to
// the PromptShield logo but distinct from it. Decorative.
function AriaAvatar({ className = 'h-10 w-10' }) {
  return (
    <span
      aria-hidden="true"
      className={`relative flex shrink-0 items-center justify-center rounded-full border border-accent/40 bg-linear-to-br from-primary/35 to-indigo/25 shadow-[0_0_18px_-4px_rgb(124_58_237/0.7)] ${className}`}
    >
      <svg viewBox="0 0 24 24" className="h-1/2 w-1/2" fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3.5l6.5 2.4v5c0 4.1-2.8 7.5-6.5 8.6-3.7-1.1-6.5-4.5-6.5-8.6v-5L12 3.5z" stroke="var(--color-accent)" strokeWidth="1.75" />
        <path d="M9 13.2c.8.9 1.8 1.3 3 1.3s2.2-.4 3-1.3" stroke="var(--color-fg)" strokeWidth="1.5" />
        <circle cx="12" cy="9.6" r="1.4" fill="var(--color-cyan)" />
      </svg>
    </span>
  )
}

export default AriaAvatar
