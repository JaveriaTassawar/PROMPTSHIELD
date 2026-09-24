import Badge from '../Badge.jsx'
import { findDetectionClass } from '../../config/detection.js'

// Detection for one sent turn. While detections come from the scenario script
// (source 'annotation'), the entry says so — it is never presented as a model
// classification. Task 85 results (source 'api') drop the annotation label.
export function DetectionEntry({ detection, turnNumber, isLatest, compact = false }) {
  const detectionClass = findDetectionClass(detection.classification)

  return (
    <div
      className={`rounded-control border px-3 py-2.5 transition-colors duration-300 ${
        isLatest ? 'border-accent/50 bg-primary/10' : 'border-border/70 bg-canvas/50'
      } ${compact ? '' : 'animate-fade-up'}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        {!compact && <span className="font-mono text-[11px] tracking-widest text-fg-subtle uppercase">Turn {turnNumber}</span>}
        {isLatest && <span className="font-mono text-[10px] tracking-widest text-accent uppercase">Latest</span>}
      </div>
      <div className={`flex flex-wrap items-center gap-x-2 gap-y-1 ${compact ? '' : 'mt-1.5'}`}>
        <Badge variant={detectionClass.variant}>{detectionClass.label}</Badge>
        {detection.subtype && <span className="font-mono text-xs text-fg-muted">{detection.subtype}</span>}
      </div>
      {detection.source === 'annotation' && (
        <p className="mt-1.5 text-[11px] text-fg-subtle">Scenario annotation · Local preview</p>
      )}
    </div>
  )
}

function DetectionFeed({ entries }) {
  return (
    <section aria-labelledby="detection-feed-heading" className="flex flex-col gap-3">
      <h2 id="detection-feed-heading" className="font-mono text-xs tracking-widest text-fg-subtle uppercase">
        Detection feed
      </h2>
      {entries.length === 0 ? (
        <p className="rounded-control border border-dashed border-border px-3 py-4 text-sm text-fg-muted">
          Detections appear here as each turn is sent.
        </p>
      ) : (
        <ol className="flex flex-col gap-2">
          {entries.map((entry, index) => (
            <li key={index}>
              <DetectionEntry detection={entry.detection} turnNumber={index + 1} isLatest={index === entries.length - 1} />
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

export default DetectionFeed
