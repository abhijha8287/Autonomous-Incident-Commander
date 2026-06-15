import { useRef, useEffect } from 'react'
import { Clock } from 'lucide-react'
import type { StreamChunk } from '../hooks/useIncidentStream'

const SEV_CLASSES: Record<string, string> = {
  CRITICAL: 'bg-critical text-white',
  HIGH:     'bg-high text-white',
  MEDIUM:   'bg-medium text-white',
  LOW:      'bg-low text-white',
  low:      'bg-low text-white',
  medium:   'bg-medium text-white',
  high:     'bg-high text-white',
  critical: 'bg-critical text-white',
}

const DOT_CLASSES: Record<string, string> = {
  CRITICAL: 'bg-critical',
  HIGH:     'bg-high',
  MEDIUM:   'bg-medium',
  LOW:      'bg-low',
  low:      'bg-low',
  medium:   'bg-medium',
  high:     'bg-high',
  critical: 'bg-critical',
}

interface ParsedEvent {
  time: string
  severity: string
  service: string
  event: string
}

function parseTimelineStep(content: string): ParsedEvent | null {
  // Matches: "● 10:00:00 — CRITICAL — database: message"
  const m = content.match(/●\s*([\d:]+)\s*—\s*(\w+)\s*—\s*(.+?)\s*:\s*(.+)/)
  if (m) return { time: m[1], severity: m[2], service: m[3], event: m[4] }

  // Matches "✓ Timeline built..."
  if (content.startsWith('✓')) return null

  // Skip "Building..." / "Waiting..."
  if (!content.includes('—')) return null
  return null
}

export default function TimelinePanel({ steps }: { steps: StreamChunk[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  const events = steps.map(s => parseTimelineStep(s.content)).filter(Boolean) as ParsedEvent[]

  return (
    <div className="flex flex-col overflow-hidden bg-panel/30">
      <div className="px-3 py-2 border-b border-border flex items-center gap-2 flex-shrink-0">
        <Clock className="w-3.5 h-3.5 text-accent" />
        <span className="text-xs font-semibold text-gray-300 uppercase tracking-widest">Incident Timeline</span>
        <span className="ml-auto text-xs text-gray-600">{events.length} events</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3">
        {steps.length === 0 && (
          <p className="text-gray-700 text-xs py-4">Timeline will build here...</p>
        )}

        {/* Building status */}
        {steps.some(s => s.content.startsWith('Build')) && events.length === 0 && (
          <p className="text-gray-600 text-xs mb-2 animate-pulse">Building timeline...</p>
        )}

        <div className="relative">
          {/* Vertical line */}
          {events.length > 0 && (
            <div className="absolute left-2 top-2 bottom-2 w-px bg-border" />
          )}

          <div className="space-y-3">
            {events.map((ev, i) => (
              <div key={i} className="flex items-start gap-3 pl-1">
                <div className={`w-3 h-3 rounded-full flex-shrink-0 mt-0.5 z-10 ${DOT_CLASSES[ev.severity] ?? 'bg-gray-500'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-gray-500 font-mono">{ev.time}</span>
                    <span className={`text-xs rounded px-1 py-0.5 font-semibold ${SEV_CLASSES[ev.severity] ?? 'bg-gray-700 text-gray-300'}`}>
                      {ev.severity.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-600">{ev.service}</span>
                  </div>
                  <p className="text-xs text-gray-300 mt-0.5 leading-snug">{ev.event}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Done note */}
        {steps.some(s => s.content.startsWith('✓ Timeline built')) && (
          <p className="text-xs text-low mt-3">✓ {steps.find(s => s.content.startsWith('✓ Timeline built'))?.content.replace('✓ ', '')}</p>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
