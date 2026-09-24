import { ShieldCheckIcon } from './icons.jsx'

// Decorative "prompt → analysis → defense → classification" scene for the auth
// branding panel. Prompt signals travel toward the AI core: clean ones (cyan)
// pass through, a direct jailbreak (red) and an indirect injection (amber) are
// stopped at the violet shield boundary. Sizes scale from --viz; the signal
// keyframes live in index.css. Purely visual, so hidden from assistive tech.

// Each arm is rotated about the centre; its signal moves along the arm's -x axis.
// 0° arrives from the left, 90° from the top, 180° from the right, 270° from below.
const SIGNALS = [
  { angle: 90, kind: 'pass', delay: '0s' },
  { angle: 270, kind: 'pass', delay: '-3s' },
  { angle: 0, kind: 'threat', delay: '1s' },
  { angle: 180, kind: 'suspicious', delay: '5.5s' },
]

const BLOCKED_COLORS = {
  threat: { trail: 'to-danger', ring: 'border-danger' },
  suspicious: { trail: 'to-warning', ring: 'border-warning' },
}

function Signal({ angle, kind, delay }) {
  if (kind === 'pass') {
    return (
      <div className="absolute top-1/2 left-1/2" style={{ transform: `rotate(${angle}deg)` }}>
        <span
          className="absolute -mt-px block h-0.5 w-6 rounded-full bg-linear-to-r from-transparent to-cyan"
          style={{ animation: `signal-pass 6s linear ${delay} infinite both` }}
        />
      </div>
    )
  }

  const colors = BLOCKED_COLORS[kind]
  return (
    <div className="absolute top-1/2 left-1/2" style={{ transform: `rotate(${angle}deg)` }}>
      <span
        className={`absolute -mt-px block h-0.5 w-7 rounded-full bg-linear-to-r from-transparent ${colors.trail}`}
        style={{ animation: `signal-blocked 9s ease-in ${delay} infinite both` }}
      />
      {/* Impact pulse where the shield stops the signal */}
      <div className="absolute" style={{ transform: 'translateX(calc(var(--viz) * -0.26))' }}>
        <span
          className={`absolute -mt-3 -ml-3 block h-6 w-6 rounded-full border-2 ${colors.ring}`}
          style={{ animation: `threat-hit 9s ease-out ${delay} infinite both` }}
        />
      </div>
    </div>
  )
}

function DefenseVisualization({ className = '' }) {
  return (
    <div
      aria-hidden="true"
      className={`relative aspect-square w-(--viz) shrink-0 font-mono select-none [--viz:16.5rem] xl:[--viz:18.75rem] short:[--viz:14.5rem] shorter:[--viz:13rem] ${className}`}
    >
      {/* Outer scan field: dot grid, slow rotating dashed ring, cyan sweep */}
      <div className="absolute inset-0 overflow-hidden rounded-full bg-grid opacity-70" />
      <div className="absolute inset-0 animate-spin-slow rounded-full border border-dashed border-cyan/20" />
      <div className="absolute inset-0 animate-sweep rounded-full bg-[conic-gradient(from_0deg,transparent_0deg,rgb(34_211_238/0.16)_45deg,transparent_70deg)]" />
      <div className="absolute inset-[15%] rounded-full border border-border/70" />

      {/* Prompt signals */}
      {SIGNALS.map((signal) => (
        <Signal key={signal.angle} {...signal} />
      ))}

      {/* Shield boundary (radius 0.26 × --viz) and its flash when a threat is stopped */}
      <div className="absolute inset-[24%] rounded-full border-2 border-accent/50 shadow-[0_0_24px_-6px_rgb(167_139_250/0.6)]" />
      {['1s', '5.5s'].map((delay) => (
        <div
          key={delay}
          className="absolute inset-[24%] rounded-full border-2 border-accent shadow-[0_0_28px_rgb(167_139_250/0.55),inset_0_0_18px_rgb(34_211_238/0.25)]"
          style={{ animation: `shield-flash 9s ease-out ${delay} infinite both` }}
        />
      ))}

      {/* AI core */}
      <div className="absolute inset-[35%] flex animate-breathe items-center justify-center rounded-full border border-accent/40 bg-linear-to-br from-primary/45 to-indigo/30 shadow-[0_0_40px_-4px_rgb(124_58_237/0.7)]">
        <ShieldCheckIcon className="h-1/2 w-1/2 text-fg" />
      </div>

      {/* Telemetry labels */}
      <span className="absolute top-0 left-0 flex items-center gap-1.5 text-[10px] tracking-widest text-fg-muted uppercase">
        <span className="h-1.5 w-1.5 animate-blink rounded-full bg-safe" />
        Shield online
      </span>
      <span className="absolute top-0 right-0 text-[10px] tracking-widest text-cyan/80 uppercase">Scanning</span>
      <span className="absolute right-0 bottom-0 text-[10px] tracking-widest text-fg-subtle uppercase">Prompt stream</span>

      <span
        className="absolute top-[36%] left-0 -translate-x-1/4 rounded border border-danger/40 bg-canvas/90 px-1.5 py-0.5 text-[10px] tracking-wider text-danger uppercase"
        style={{ animation: 'threat-label 9s linear 1s infinite both' }}
      >
        Injection blocked
      </span>
      <span
        className="absolute top-[58%] right-0 translate-x-1/4 rounded border border-warning/40 bg-canvas/90 px-1.5 py-0.5 text-[10px] tracking-wider text-warning uppercase"
        style={{ animation: 'threat-label 9s linear 5.5s infinite both' }}
      >
        Flagged
      </span>
    </div>
  )
}

export default DefenseVisualization
