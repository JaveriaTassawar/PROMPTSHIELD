import { DETECTION_CLASSES, findClassForSubtype, findDetectionClass } from './detection.js'
import { getGeneralGuidance } from './ariaGuidance.js'

// Learning Hub modules (Task 87): Safe Prompting plus one module per attack
// sub-type. All educational text is derived from the approved content in
// config/detection.js and config/ariaGuidance.js — nothing new is claimed here.
// Titles are the existing class/sub-type names.

// Category filters: frontend-only views over the existing taxonomy.
export const LEARNING_CATEGORIES = [
  { id: 'all', label: 'All' },
  ...DETECTION_CLASSES.map((detection) => ({
    id: detection.label,
    label: detection.label === 'Safe' ? 'Safe Prompting' : detection.label,
  })),
]

function safePromptingModule() {
  const detection = findDetectionClass('Safe')
  const guidance = getGeneralGuidance({ classification: 'Safe', subtype: null })
  return {
    id: 'safe-prompting',
    category: detection.label,
    categoryLabel: 'Safe Prompting',
    variant: detection.variant,
    title: 'Safe Prompting',
    summary: guidance.why,
    practice: { label: 'Key practice', text: guidance.do[0] },
  }
}

function attackPatternModule(subtype) {
  const detection = findClassForSubtype(subtype)
  const guidance = getGeneralGuidance({ classification: detection.label, subtype })
  return {
    id: subtype.toLowerCase().replaceAll(' ', '-'),
    category: detection.label,
    categoryLabel: detection.label,
    variant: detection.variant,
    title: subtype,
    summary: detection.subtypeDefinitions[subtype],
    practice: { label: 'Key defence', text: guidance.keyDefence.text },
  }
}

export const LEARNING_MODULES = [
  safePromptingModule(),
  ...DETECTION_CLASSES.flatMap((detection) => detection.subtypes.map(attackPatternModule)),
]
