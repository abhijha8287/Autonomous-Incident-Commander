import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Play, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { useIncidentStream } from '../hooks/useIncidentStream'
import LiveLogPanel from '../components/LiveLogPanel'
import AIPanel from '../components/AIPanel'
import TimelinePanel from '../components/TimelinePanel'
import ReportPanel from '../components/ReportPanel'

interface IncidentDetail {
  id: string
  title: string
  service: string
  severity: string
  status: string
  detected_at: string
}

const SEVERITY_CLASSES: Record<string, string> = {
  CRITICAL: 'text-critical',
  HIGH:     'text-high',
  MEDIUM:   'text-medium',
  LOW:      'text-low',
  UNKNOWN:  'text-gray-400',
}

export default function Investigation() {
  const { incidentId } = useParams<{ incidentId: string }>()
  const navigate = useNavigate()
  const [incident, setIncident] = useState<IncidentDetail | null>(null)
  const [investigationId, setInvestigationId] = useState<string | null>(null)
  const { state, start, reset } = useIncidentStream()

  useEffect(() => {
    if (incidentId) {
      fetch(`/api/incidents/${incidentId}`)
        .then(r => r.json())
        .then(setIncident)
    }
  }, [incidentId])

  async function handleStart() {
    if (!incidentId) return
    reset()
    const invId = await start(incidentId)
    setInvestigationId(invId)
  }

  const sev = incident?.severity ?? 'UNKNOWN'
  const sevClass = SEVERITY_CLASSES[sev] ?? 'text-gray-400'

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      {/* Header */}
      <header className="border-b border-border px-4 py-3 flex items-center gap-3 flex-shrink-0">
        <button onClick={() => navigate('/')} className="text-gray-500 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <span className={`text-xs font-bold ${sevClass} border border-current rounded px-1.5 py-0.5`}>{sev}</span>
            <h1 className="text-white text-sm font-semibold truncate">{incident?.title ?? '...'}</h1>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            {incident?.service} · Detected {incident ? new Date(incident.detected_at).toLocaleTimeString() : '—'}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {state.isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-accent">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Investigating...
            </span>
          )}
          {state.isDone && (
            <span className="flex items-center gap-1.5 text-xs text-low">
              <CheckCircle className="w-3.5 h-3.5" />
              Complete
            </span>
          )}
          {!state.isRunning && (
            <button
              onClick={handleStart}
              className="flex items-center gap-2 px-3 py-1.5 text-xs bg-accent text-white rounded hover:bg-accent/80 transition-colors font-semibold"
            >
              <Play className="w-3.5 h-3.5" />
              {state.isDone ? 'Re-run Investigation' : 'Start AI Investigation'}
            </button>
          )}
        </div>
      </header>

      {/* Error banner */}
      {state.errors.length > 0 && (
        <div className="bg-high/10 border-b border-high/30 px-4 py-2 flex items-center gap-2 text-xs text-high">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          {state.errors[state.errors.length - 1]}
        </div>
      )}

      {/* Empty state */}
      {!state.isRunning && !state.isDone && state.investigationSteps.length === 0 && (
        <div className="flex-1 flex items-center justify-center text-center text-gray-600">
          <div>
            <Play className="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p className="text-sm">Click "Start AI Investigation" to begin autonomous incident analysis.</p>
            <p className="text-xs mt-1 text-gray-700">Splunk MCP will query logs and AI will reason over them.</p>
          </div>
        </div>
      )}

      {/* Main three-panel layout */}
      {(state.isRunning || state.isDone || state.investigationSteps.length > 0) && (
        <div className="flex-1 grid grid-cols-3 divide-x divide-border overflow-hidden" style={{ minHeight: 0 }}>
          <LiveLogPanel steps={state.investigationSteps} />
          <AIPanel tokens={state.rcaTokens} steps={state.rcaSteps} investSteps={state.investigationSteps} />
          <TimelinePanel steps={state.timelineSteps} />
        </div>
      )}

      {/* Report bar — appears when done */}
      {state.isDone && investigationId && (
        <ReportPanel
          steps={state.reportSteps}
          investigationId={investigationId}
          metadata={state.metadata}
        />
      )}
    </div>
  )
}
