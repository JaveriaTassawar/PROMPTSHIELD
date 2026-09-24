import { TargetIcon } from '../icons.jsx'

function ObjectiveBanner({ objective }) {
  return (
    <div className="relative flex gap-3 overflow-hidden rounded-card border border-accent/25 bg-primary/5 py-3.5 pr-4 pl-5">
      <span className="absolute inset-y-0 left-0 w-0.5 bg-accent" aria-hidden="true" />
      <TargetIcon className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
      <div>
        <p className="font-mono text-[11px] tracking-widest text-accent uppercase">Training objective</p>
        <p className="mt-1 text-sm text-fg">{objective}</p>
      </div>
    </div>
  )
}

export default ObjectiveBanner
