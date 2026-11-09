import { useCallback, useRef, useState } from 'react'

import { analyzePrompt } from '../api/analysis.js'
import { errorMessage } from '../api/client.js'

// Request state for the Prompt Analyzer (Task 76 -- now the real
// POST /api/analyze-prompt, previously mockAnalyzePrompt).
//
// The page's contract is unchanged: { status, result, analyzedPrompt,
// analyze }, plus `errorText` so a 503 can be distinguished from a
// genuine failure.
//
//   status: 'idle' | 'analyzing' | 'success' | 'error'
//
// THE requestId GUARD MATTERS MORE NOW THAN IT DID WITH THE MOCK.
//
// The mock always took 1200ms, so responses arrived in order. A real
// request does not: a short prompt can come back before a long one sent
// earlier, and without this check the earlier, slower response would
// overwrite the newer result -- showing the user a verdict for a prompt
// they have already replaced. Kept from the original implementation and
// worth keeping.
export function usePromptAnalysis() {
  const [state, setState] = useState({
    status: 'idle',
    result: null,
    analyzedPrompt: '',
    errorText: '',
  })
  const latestRequest = useRef(0)

  const analyze = useCallback(async (prompt) => {
    const requestId = ++latestRequest.current
    setState({ status: 'analyzing', result: null, analyzedPrompt: prompt, errorText: '' })

    try {
      const result = await analyzePrompt(prompt)
      if (requestId === latestRequest.current) {
        setState({ status: 'success', result, analyzedPrompt: prompt, errorText: '' })
      }
    } catch (error) {
      if (requestId !== latestRequest.current) return

      // 503 means the model is not loaded on the server. The prompt was
      // still saved, so this is a "try again later", not a failure the
      // user caused or can fix by rewording.
      const unavailable = error?.response?.status === 503
      setState({
        status: 'error',
        result: null,
        analyzedPrompt: prompt,
        errorText: unavailable
          ? 'The classification model is not running on the server. Your prompt was saved and can be analysed later.'
          : errorMessage(error, 'Could not analyse that prompt.'),
      })
    }
  }, [])

  return { ...state, analyze }
}
