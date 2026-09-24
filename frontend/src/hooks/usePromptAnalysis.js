import { useCallback, useRef, useState } from 'react'
import { mockAnalyzePrompt } from '../mocks/analysis.js'

// Request state for the Prompt Analyzer. Task 76 replaces mockAnalyzePrompt
// with the real POST /api/analyze-prompt call; the rest of the page only sees
// { status, result, analyzedPrompt, analyze }.
//   status: 'idle' | 'analyzing' | 'success' | 'error'
export function usePromptAnalysis() {
  const [state, setState] = useState({ status: 'idle', result: null, analyzedPrompt: '' })
  const latestRequest = useRef(0)

  const analyze = useCallback(async (prompt) => {
    const requestId = ++latestRequest.current
    setState({ status: 'analyzing', result: null, analyzedPrompt: prompt })
    try {
      const result = await mockAnalyzePrompt(prompt)
      if (requestId === latestRequest.current) {
        setState({ status: 'success', result, analyzedPrompt: prompt })
      }
    } catch {
      if (requestId === latestRequest.current) {
        setState({ status: 'error', result: null, analyzedPrompt: prompt })
      }
    }
  }, [])

  return { ...state, analyze }
}
