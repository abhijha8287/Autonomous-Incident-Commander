import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Activity, Clock, ChevronRight, Plus, Zap } from 'lucide-react'

interface Incident {
  id: string
  service: string
  title: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN'
  status: string
  detected_at: string
}

const SEVERITY_CLASSES: Record<string, string> = {
  CRITICAL: 'text-critical border-critical bg-critical/10',
  HIGH:     'text-high border-high bg-high/10',
  MEDIUM:   'text-medium border-medium bg-medium/10',
  LOW:      'text-low border-low bg-low/10',
  UNKNOWN:  'text-gray-400 border-gray-600 bg-gray-900',
}

const SEVERITY_DOT: Record<string, string> = {
  CRITICAL: 'bg-critical',
  HIGH:     'bg-high',
  MEDIUM:   'bg-medium',
  LOW:      'bg-low',
  UNKNOWN:  'bg-gray-500',
}

export default function Dashboard() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetchIncidents()
    const timer = setInterval(fetchIncidents, 5000)
    return () => clearInterval(timer)
  }, [])

  async function fetchIncidents() {
    try {
      const res = await fetch('/api/incidents')
      const data = await res.json()
      setIncidents(data)
    } finally {
      setLoading(false)
    }
  }

  async function triggerDemo() {
    await fetch('/api/incidents/trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ service: 'checkout-service', title: 'Critical Error Rate — checkout-service' }),
    })
    fetchIncidents()
  }

  const active = incidents.filter(i => i.status === 'ACTIVE' || i.status === 'INVESTIGATING')
  const critical = incidents.filter(i => i.severity === 'CRITICAL')

  return (
    <div className="min-h-screen bg-surface">
      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center">
            <Zap className="w-4 h-4 text-accent" />
          </div>
          <div>
            <h1 className="text-white font-semibold text-sm tracking-wide">AUTONOMOUS INCIDENT COMMANDER</h1>
            <p className="text-gray-500 text-xs">AI-Powered Incident Response · Splunk MCP</p>
          </div>
        </div>
        <button
          onClick={triggerDemo}
          className="flex items-center gap-2 px-3 py-1.5 text-xs bg-critical/10 text-critical border border-critical/30 rounded hover:bg-critical/20 transition-colors"
        >
          <Plus className="w-3 h-3" />
          Trigger Demo Incident
        </button>
      </header>

      {/* Stats bar */}
      <div className="border-b border-border px-6 py-3 flex items-center gap-8 bg-panel/50">
        <Stat icon={<AlertTriangle className="w-3.5 h-3.5 text-critical" />} label="Active" value={active.length} color="text-critical" />
        <Stat icon={<Activity className="w-3.5 h-3.5 text-high" />} label="Critical" value={critical.length} color="text-high" />
        <Stat icon={<Clock className="w-3.5 h-3.5 text-gray-400" />} label="Total" value={incidents.length} color="text-gray-300" />
        <div className="ml-auto flex items-center gap-2 text-xs text-gray-500">
          <span className="w-1.5 h-1.5 rounded-full bg-low animate-pulse" />
          Live · Splunk MCP Connected
        </div>
      </div>

      {/* Incidents list */}
      <main className="px-6 py-6">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">Incidents</h2>

        {loading && (
          <div className="text-gray-600 text-sm text-center py-12">Loading...</div>
        )}

        {!loading && incidents.length === 0 && (
          <div className="text-center py-16 text-gray-600">
            <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No incidents. Click "Trigger Demo Incident" to begin.</p>
          </div>
        )}

        <div className="space-y-2">
          {incidents.map(inc => (
            <button
              key={inc.id}
              onClick={() => navigate(`/investigate/${inc.id}`)}
              className="w-full text-left bg-panel border border-border rounded-lg px-4 py-3 hover:border-accent/40 transition-colors group flex items-center gap-4"
            >
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${SEVERITY_DOT[inc.severity] ?? 'bg-gray-500'}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <span className="text-white text-sm font-medium truncate">{inc.title}</span>
                  <span className={`text-xs border rounded px-1.5 py-0.5 font-semibold flex-shrink-0 ${SEVERITY_CLASSES[inc.severity]}`}>
                    {inc.severity}
                  </span>
                  <span className="text-xs text-gray-600">{inc.status}</span>
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {inc.service} · {new Date(inc.detected_at).toLocaleTimeString()}
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-accent transition-colors flex-shrink-0" />
            </button>
          ))}
        </div>
      </main>
    </div>
  )
}

function Stat({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      {icon}
      <span className={`text-lg font-bold ${color}`}>{value}</span>
      <span className="text-xs text-gray-600">{label}</span>
    </div>
  )
}
