import ariaMascot from '../../assets/aria-mascot.png'

// Aria, PromptShield's security-guide mascot (transparent artwork in
// assets/aria-mascot.png). Size it with `className` on the wrapper — usually a
// width; the image keeps its own aspect ratio.
//
// `tone` (safe / danger / warning) adds a faint result-coloured glow behind
// her; Aria herself is never recoloured. `animated` adds a gentle float of the
// whole image, only when the user hasn't asked for reduced motion.
// Decorative by default; pass `label` where the image should announce Aria.
const TONE_GLOW = {
  safe: 'bg-safe/20',
  danger: 'bg-danger/20',
  warning: 'bg-warning/20',
}

function AriaAvatar({ tone, animated = false, label, className = 'w-12' }) {
  return (
    <span className={`relative inline-flex shrink-0 items-center justify-center ${className}`}>
      {/* Soft glow that settles her into the dark UI */}
      <span className="absolute inset-[18%] rounded-full bg-primary/35 blur-2xl" aria-hidden="true" />
      {TONE_GLOW[tone] && (
        <span className={`absolute inset-x-[15%] top-[25%] bottom-[20%] rounded-full blur-3xl ${TONE_GLOW[tone]}`} aria-hidden="true" />
      )}
      <img
        src={ariaMascot}
        alt={label ?? ''}
        aria-hidden={label ? undefined : true}
        width="1374"
        height="1145"
        decoding="async"
        draggable="false"
        className={`relative h-auto w-full select-none drop-shadow-[0_10px_24px_rgb(79_70_229/0.45)] ${
          animated ? 'motion-safe:animate-aria-float' : ''
        }`}
      />
    </span>
  )
}

export default AriaAvatar
