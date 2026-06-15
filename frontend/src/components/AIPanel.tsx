import { useRef, useEffect } from 'react'
import { Brain, Loader2, CheckCircle } from 'lucide-react'
import type { StreamChunk } from '../hooks/useIncidentStream'

export default function AIPanel({
  tokens,
  steps,
  investSteps,
}: {
  tokens: string
  steps: StreamChunk[]
  investSteps: StreamChunk[]
}) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [tokens, steps])

  // Extract root cause and confidence from the streamed JSON tokens
  const rootCauseMatch = tokens.match(/"root_cause"\s*:\s*"([^"]+)"/)
  const confidenceMatch = tokens.match(/"confidence_pct"\s*:\s*([\d.]+)/)
  const rootCause = rootCauseMatch?.[1]
  const confidence = confidenceMatch ? parseFloat(confidenceMatch[1]) : null

  const isAnalyzing = tokens.length > 0 && !rootCause
  const isDone = !!rootCause

  return (
    <div className="flex flex-col overflow-hidden">
      <div className="px-3 py-2 border-b border-border flex items-center gap-2 flex-shrink-0">
        <Brain className="w-3.5 h-3.5 text-accent" />
        <span className="text-xs font-semibold text-gray-300 uppercase tracking-widest">AI Investigation</span>
        {isAnalyzing && <Loader2 className="w-3 h-3 text-accent animate-spin ml-auto" />}
        {isDone && <CheckCircle className="w-3 h-3 text-low ml-auto" />}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {investSteps.length === 0 && steps.length === 0 && tokens.length === 0 && (
          <p className="text-gray-700 text-xs py-4">AI reasoning will appear here...</p>
        )}

        {/* Investigation status steps */}
        {investSteps.map((step, i) => (
          <StepLine key={`inv-${i}`} content={step.content} />
        ))}

        {/* RCA reasoning steps */}
        {steps.map((step, i) => (
          <StepLine key={`rca-${i}`} content={step.content} />
        ))}

        {/* Streaming tokens — typewriter display */}
        {tokens.length > 0 && !isDone && (
          <div className="bg-surface/60 rounded border border-border p-2 mt-2">
            <p className="text-xs text-gray-500 mb-1 uppercase tracking-widest">Reasoning...</p>
            <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words font-mono leading-relaxed cursor-blink">
              {tokens}
            </pre>
          </div>
        )}

        {/* Root cause result card */}
        {rootCause && (
          <div className="mt-3 rounded border border-accent/30 bg-accent/5 p-3">
            <p className="text-xs text-accent uppercase tracking-widest font-semibold mb-1.5">Root Cause Identified</p>
            <p className="text-white text-sm font-semibold leading-snug">{rootCause}</p>
            {confidence !== null && (
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-gray-500">Confidence</span>
                  <span className={`font-bold ${confidence >= 85 ? 'text-critical' : confidence >= 65 ? 'text-high' : 'text-medium'}`}>
                    {confidence.toFixed(0)}%
                  </span>
                </div>
                <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-1000 ${confidence >= 85 ? 'bg-critical' : confidence >= 65 ? 'bg-high' : 'bg-medium'}`}
                    style={{ width: `${confidence}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}

function StepLine({ content }: { content: string }) {
  const isDone = content.startsWith('✓')
  return (
    <div className={`text-xs flex items-start gap-2 ${isDone ? 'text-low' : 'text-gray-400'}`}>
      <span className="mt-0.5 flex-shrink-0">{isDone ? '✓' : '⟳'}</span>
      <span>{content.replace(/^✓\s*/, '')}</span>
    </div>
  )
}
