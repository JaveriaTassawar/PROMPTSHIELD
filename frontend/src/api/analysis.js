// Prompt analysis API call (frontend Task 76).
//
// POST /api/analyze-prompt -> the SDS §6.5 response shape:
//
//   { promptId, classification, subtype, severity, confidenceScore,
//     subtypeConfidence, subtypeReliable, safePromptSuggestion,
//     avatarFeedback }
//
// THREE THINGS THE CALLER MUST HANDLE, ALL BY BACKEND DESIGN:
//
// 1. `subtype` CAN BE NULL FOR AN ATTACK, NOT ONLY FOR SAFE.
//
//    The 8-class sub-type model is a stretch goal and may not be
//    configured on the server. The backend returns subtype: null rather
//    than failing (backend Task 56), so the UI must not assume an attack
//    always names a sub-type.
//
// 2. `subtypeReliable` CAN BE FALSE.
//
//    The sub-type model scores 0.00 F1 on Role Override and never
//    predicts it -- 14 of 18 test cases came back as Policy Evasion
//    instead. When this flag is false the sub-type is a guess, and the
//    UI should say so rather than present it as confidently as the
//    main classification. See ml/MODEL_CARD.md 19.7.
//
// 3. A 503 IS NOT AN ERROR IN THE USUAL SENSE.
//
//    It means the model is not loaded on the server -- the prompt was
//    still saved and can be analysed later. Worth a different message
//    from "something went wrong".

import { api } from './client.js'

export async function analyzePrompt(prompt) {
  const { data } = await api.post('/api/analyze-prompt', { prompt })
  return data
}
