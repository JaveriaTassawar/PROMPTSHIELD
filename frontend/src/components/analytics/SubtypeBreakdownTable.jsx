import Badge from '../Badge.jsx'
import Card from '../Card.jsx'
import { ALL_SUBTYPES } from '../../hooks/useDashboardStats.js'

// All 8 attack sub-types with their class (from config/detection.js). Without
// counts (API not connected, loading or failed) the rows still list the
// taxonomy, with "—" in place of numbers.
// % of total = sub-type count ÷ all attacks counted here, to one decimal place.
function SubtypeBreakdownTable({ subtypes, totalAttacks, loading = false, sample = false }) {
  const rows = subtypes ?? ALL_SUBTYPES
  const hasCounts = subtypes != null

  let footnote = 'Counts appear here once PromptShield’s dashboard API is connected.'
  if (loading) footnote = 'Loading sub-type counts…'
  else if (hasCounts) footnote = `% of total is each sub-type’s share of all ${totalAttacks} attacks listed.`

  return (
    <Card className="p-5">
      <section aria-labelledby="subtype-heading" className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <h2 id="subtype-heading" className="font-semibold text-fg">
            Attack sub-type breakdown
          </h2>
          {sample && <Badge variant="info">Sample</Badge>}
        </div>

        <div className="-mx-5 overflow-x-auto px-5">
          <table className="w-full min-w-[32rem] text-left text-sm" aria-describedby="subtype-footnote" aria-busy={loading}>
            <thead>
              <tr className="border-b border-border font-mono text-[11px] tracking-widest text-fg-subtle uppercase">
                <th scope="col" className="py-2 pr-4 font-medium">
                  Sub-type
                </th>
                <th scope="col" className="py-2 pr-4 font-medium">
                  Category
                </th>
                <th scope="col" className="py-2 pr-4 text-right font-medium">
                  Count
                </th>
                <th scope="col" className="py-2 text-right font-medium">
                  % of total
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.name} className="border-b border-border/50 last:border-b-0">
                  <th scope="row" className="py-2.5 pr-4 font-medium text-fg">
                    {row.name}
                  </th>
                  <td className="py-2.5 pr-4">
                    <Badge variant={row.detection.variant}>{row.detection.label}</Badge>
                  </td>
                  <td className={`py-2.5 pr-4 text-right font-mono tabular-nums ${hasCounts && row.count > 0 ? 'text-fg' : 'text-fg-subtle'}`}>
                    {hasCounts ? row.count : '—'}
                  </td>
                  <td className="py-2.5 text-right font-mono text-fg-muted tabular-nums">
                    {hasCounts ? `${row.percent.toFixed(1)}%` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p id="subtype-footnote" className="text-xs text-fg-subtle">
          {footnote}
        </p>
      </section>
    </Card>
  )
}

export default SubtypeBreakdownTable
