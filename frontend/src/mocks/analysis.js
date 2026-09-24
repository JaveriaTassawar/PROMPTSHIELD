import { EXAMPLE_PROMPTS } from '../config/examplePrompts.js'

// Mock stand-in for POST /api/analyze-prompt until Task 76 wires the real
// endpoint. Nothing is analysed. The response follows the SDS §6.5 shape but
// only includes the fields the UI reads so far:
//   classification, subtype  (Task 75)
//   confidenceScore          (Task 77, Safe results only — 0–1 as in the SDS example)
// Severity, rewrite and guidance are left to Tasks 78–82.
//
// Which classification comes back:
//   1. /analyzer?mock=error                → the request fails
//   2. an example chip's exact text        → that row's label in ml/data/sample_1000.csv
//   3. /analyzer?mock=safe|jailbreak|injection → that class
//   4. anything else                        → the SDS §6.5 sample (Direct Jailbreak / Persona Hijacking)
const MOCK_DELAY_MS = 1200

// Demonstration value for the Task 77 confidence meter. Not a model output.
const MOCK_SAFE_CONFIDENCE = 0.96

const SAFE_RESPONSE = { classification: 'Safe', subtype: null, confidenceScore: MOCK_SAFE_CONFIDENCE }

// Ground-truth labels of the example prompts in the hand-checked sample.
const EXAMPLE_LABELS = {
  'zero-sum': SAFE_RESPONSE,
  dan: { classification: 'Direct Jailbreak', subtype: 'Persona Hijacking' },
  'base64-system-prompt': { classification: 'Direct Jailbreak', subtype: 'System Prompt Overwrite' },
  'stock-quantity': { classification: 'Indirect Injection', subtype: 'Tool Output Injection' },
}

const FLAG_RESPONSES = {
  safe: SAFE_RESPONSE,
  jailbreak: { classification: 'Direct Jailbreak', subtype: 'Persona Hijacking' },
  injection: { classification: 'Indirect Injection', subtype: 'Document Embedding' },
}

function pickResponse(prompt, flag) {
  const example = EXAMPLE_PROMPTS.find((item) => item.text === prompt.trim())
  if (example) return EXAMPLE_LABELS[example.id]
  return FLAG_RESPONSES[flag] ?? FLAG_RESPONSES.jailbreak
}

export function mockAnalyzePrompt(prompt) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const flag = new URLSearchParams(window.location.search).get('mock')
      if (flag === 'error') {
        reject(new Error('Analysis failed.'))
        return
      }
      resolve({ ...pickResponse(prompt, flag), mock: true })
    }, MOCK_DELAY_MS)
  })
}
