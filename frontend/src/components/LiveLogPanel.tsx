import { useEffect, useRef } from 'react'
import { Database } from 'lucide-react'
import type { StreamChunk } from '../hooks/useIncidentStream'

const LEVEL_CLASSES: Record<string, string> = {
  INFO:     'text-gray-400',
  WARNING:  'text-medium',
  ERROR:    'text-high',
  CRITICAL: 'text-critical font-semibold',
  ALERT:    'text-critical font-bold',
}

// Extract a simulated log-like line from step content
function parseAsLog(content: string): { time: string; level: string; msg: string } | null {
  // Timeline items like "● 10:00:30 — CRITICAL — database: ..."
  const tlMatch = content.match(/●\s+([\d:]+)\s+—\s+(\w+)\s+—\s+(.+?)\s*:\s*(.+)/)
  if (tlMatch) {
    return { time: tlMatch[1], level: tlMatch[2], msg: `[${tlMatch[3]}] ${tlMatch[4]}` }
  }
  return null
}

export default function LiveLogPanel({ steps }: { steps: StreamChunk[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  // Collect simulated log events from investigation steps and timeline steps
  const logLines: Array<{ time: string; level: string; msg: string; idx: number }> = []
  steps.forEach((step, i) => {
    const parsed = parseAsLog(step.content)
    if (parsed) {
      logLines.push({ ...parsed, idx: i })
    } else if (step.content.includes('events indexed') || step.content.includes('✓')) {
      logLines.push({ time: new Date().toLocaleTimeString('en', { hour12: false }), level: 'INFO', msg: step.content, idx: i })
    }
  })

  return (
    <div className="flex flex-col overflow-hidden bg-panel/30">
      <div className="px-3 py-2 border-b border-border flex items-center gap-2 flex-shrink-0">
        <Database className="w-3.5 h-3.5 text-accent" />
        <span className="text-xs font-semibold text-gray-300 uppercase tracking-widest">Live Logs</span>
        <span className="ml-auto text-xs text-gray-600">{logLines.length} events</span>
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-0.5">
        {steps.length === 0 && (
          <p className="text-gray-700 text-xs py-4">Waiting for Splunk MCP query...</p>
        )}
        {steps.map((step, i) => (
          <LogLine key={i} content={step.content} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

function LogLine({ content }: { content: string }) {
  const time = new Date().toLocaleTimeString('en', { hour12: false })

  // Determine level from content
  let level = 'INFO'
  if (content.includes('CRITICAL') || content.includes('exhausted') || content.includes('HALT')) level = 'CRITICAL'
  else if (content.includes('ERROR') || content.includes('failed') || content.includes('timeout')) level = 'ERROR'
  else if (content.includes('WARNING') || content.includes('HIGH') || content.includes('elevated')) level = 'WARNING'
  else if (content.includes('✓') || content.includes('complete')) level = 'INFO'

  const cls = LEVEL_CLASSES[level] ?? 'text-gray-400'

  return (
    <div className={`text-xs font-mono leading-relaxed ${cls}`}>
      <span className="text-gray-700 mr-2">{time}</span>
      {content}
    </div>
  )
}
