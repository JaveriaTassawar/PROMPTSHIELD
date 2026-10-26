import { useEffect, useRef, useState } from 'react'
import AriaGuidancePanel from '../components/aria/AriaGuidancePanel.jsx'
import AnalysisPipeline from '../components/analyzer/AnalysisPipeline.jsx'
import AnalysisResult from '../components/analyzer/AnalysisResult.jsx'
import ExamplePrompts from '../components/analyzer/ExamplePrompts.jsx'
import PromptEditor from '../components/analyzer/PromptEditor.jsx'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import PageHeader from '../components/PageHeader.jsx'
import { ScanIcon } from '../components/icons.jsx'
import { EXAMPLE_PROMPTS } from '../config/examplePrompts.js'
import { findNavItem } from '../config/navigation.js'
import { useAriaGuidance } from '../hooks/useAriaGuidance.js'
import { usePromptAnalysis } from '../hooks/usePromptAnalysis.js'

const NAV_ITEM = findNavItem('/analyzer')

// Prompt Analyzer (Task 75, mock response). Layout: inspection workspace, the
// result area, then Aria's guidance for the result (Task 81).
function AnalyzerPage() {
  const [prompt, setPrompt] = useState('')
  const { status, result, analyzedPrompt, analyze } = usePromptAnalysis()
  const guidance = useAriaGuidance(status === 'success' ? result : null)
  const resultRef = useRef(null)
  const ariaHeadingRef = useRef(null)

  const isAnalyzing = status === 'analyzing'
  const canAnalyze = prompt.trim().length > 0 && !isAnalyzing
  const isStale = status === 'success' && prompt !== analyzedPrompt

  function handleSubmit(event) {
    event?.preventDefault()
    if (canAnalyze) analyze(prompt)
  }

  // "Ask Avatar" moves to Aria's guidance on this page — no request is made.
  function focusAria() {
    const heading = ariaHeadingRef.current
    if (!heading) return
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    heading.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' })
    heading.focus({ preventScroll: true })
  }

  // Bring the result into view once it arrives (it is below the fold on phones).
  useEffect(() => {
    if (status !== 'success' && status !== 'error') return
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    resultRef.current?.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'nearest' })
  }, [status])

  return (
    <div className="flex flex-col gap-6 lg:gap-8">
      <PageHeader
        eyebrow={NAV_ITEM.eyebrow}
        title={NAV_ITEM.label}
        description="Paste a prompt to inspect it for jailbreak and prompt-injection attempts before it reaches an AI model."
      />

      <Card glow className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 px-4 py-3 sm:px-5">
          <span className="flex items-center gap-2 font-mono text-xs tracking-widest text-fg-muted uppercase">
            <ScanIcon className={`h-4 w-4 transition-colors ${isAnalyzing ? 'text-cyan' : 'text-accent'}`} />
            Prompt inspection
          </span>
          <AnalysisPipeline status={status} />
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5 p-4 sm:p-5" aria-busy={isAnalyzing}>
          <PromptEditor
            id="prompt-input"
            value={prompt}
            onChange={setPrompt}
            onSubmitShortcut={handleSubmit}
            scanning={isAnalyzing}
          />

          <ExamplePrompts examples={EXAMPLE_PROMPTS} onSelect={setPrompt} disabled={isAnalyzing} />

          <div className="flex flex-col-reverse gap-3 border-t border-border/70 pt-4 sm:flex-row sm:items-center sm:justify-end">
            {prompt && !isAnalyzing && (
              <Button type="button" variant="ghost" onClick={() => setPrompt('')} className="sm:mr-auto">
                Clear
              </Button>
            )}
            <Button type="submit" loading={isAnalyzing} disabled={!canAnalyze} className="w-full sm:w-auto sm:min-w-44">
              {isAnalyzing ? (
                'Analyzing…'
              ) : (
                <>
                  <ScanIcon className="h-4.5 w-4.5" />
                  Analyze Prompt
                </>
              )}
            </Button>
          </div>
        </form>
      </Card>

      <div ref={resultRef} className="scroll-mt-20">
        <AnalysisResult
          status={status}
          result={result}
          analyzedPrompt={analyzedPrompt}
          isStale={isStale}
          onAskAria={guidance ? focusAria : undefined}
        />
      </div>

      {guidance && (
        <div className="scroll-mt-20">
          <AriaGuidancePanel guidance={guidance} result={result} headingRef={ariaHeadingRef} isStale={isStale} />
        </div>
      )}
    </div>
  )
}

export default AnalyzerPage
