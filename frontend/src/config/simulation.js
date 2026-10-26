// Simulation Lab presentation config (Task 83).
//
// Training difficulty is a frontend-only label for how demanding a practice
// scenario is. It is NOT attack severity, classifier output or model
// confidence, and it is not backend data — Backend Task 62 may replace it.
export const TRAINING_DIFFICULTY = {
  Beginner: { label: 'Beginner', level: 1 },
  Intermediate: { label: 'Intermediate', level: 2 },
  Advanced: { label: 'Advanced', level: 3 },
}

export const DIFFICULTY_LEVELS = Object.keys(TRAINING_DIFFICULTY).length

// Where a scenario turn comes from (Task 84). `external` marks content the AI
// system consumes rather than something the user typed; it is shown in
// monospace so it can be inspected.
export const TURN_ROLES = {
  user: { label: 'User input', external: false },
  document: { label: 'Document content', external: true },
  tool: { label: 'Tool output', external: true },
}

// Provenance of a turn's text, shown on every turn so authored framing is never
// mistaken for dataset content.
export const TURN_ORIGINS = {
  dataset: 'Sample dataset',
  framing: 'Scenario framing',
}
