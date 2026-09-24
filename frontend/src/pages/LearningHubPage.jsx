import { useState } from 'react'
import PageHeader from '../components/PageHeader.jsx'
import CategoryFilter from '../components/learning/CategoryFilter.jsx'
import LearningProgressSummary from '../components/learning/LearningProgressSummary.jsx'
import TutorialCard from '../components/learning/TutorialCard.jsx'
import { LEARNING_CATEGORIES, LEARNING_MODULES } from '../config/learningModules.js'
import { findNavItem } from '../config/navigation.js'
import { useLearningProgress } from '../hooks/useLearningProgress.js'

const NAV_ITEM = findNavItem('/learning')
const MODULE_IDS = LEARNING_MODULES.map((module) => module.id)

const COUNTS = Object.fromEntries(
  LEARNING_CATEGORIES.map((category) => [
    category.id,
    category.id === 'all' ? LEARNING_MODULES.length : LEARNING_MODULES.filter((module) => module.category === category.id).length,
  ]),
)

// Learning Hub (Task 87, local preview): tutorial cards, category filters,
// user-driven local progress. XP is not tracked.
function LearningHubPage() {
  const [category, setCategory] = useState('all')
  const { completedIds, toggleComplete } = useLearningProgress(MODULE_IDS)

  const visible = category === 'all' ? LEARNING_MODULES : LEARNING_MODULES.filter((module) => module.category === category)

  return (
    <div className="flex flex-col gap-6 lg:gap-8">
      <PageHeader
        eyebrow={NAV_ITEM.eyebrow}
        title={NAV_ITEM.label}
        description="Short modules on safe prompting and on every attack pattern PromptShield detects. Mark a module complete once you’ve worked through it."
      >
        <div className="flex flex-col gap-0.5 sm:items-end">
          <p className="font-mono text-[11px] tracking-widest text-fg-muted uppercase">
            Learning progress · <span className="text-accent">Local preview</span>
          </p>
          <p className="text-xs text-fg-subtle sm:text-right">Saved in this browser only — not synced to an account</p>
        </div>
      </PageHeader>

      <LearningProgressSummary completed={completedIds.length} total={LEARNING_MODULES.length} />

      <section aria-labelledby="tutorials-heading" className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <h2 id="tutorials-heading" className="font-mono text-xs tracking-widest text-fg-subtle uppercase">
            Tutorials
          </h2>
          <CategoryFilter categories={LEARNING_CATEGORIES} selected={category} counts={COUNTS} onChange={setCategory} />
        </div>

        {visible.length === 0 ? (
          <p className="rounded-card border border-dashed border-border px-5 py-8 text-center text-sm text-fg-muted">
            No tutorials in this category yet.
          </p>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {visible.map((module, index) => (
              <li key={module.id} className="animate-fade-up" style={{ animationDelay: `${index * 50}ms` }}>
                <TutorialCard module={module} completed={completedIds.includes(module.id)} onToggle={toggleComplete} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

export default LearningHubPage
