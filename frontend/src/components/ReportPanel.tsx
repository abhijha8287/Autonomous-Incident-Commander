import { Download, FileText, CheckCircle } from 'lucide-react'
import type { StreamChunk } from '../hooks/useIncidentStream'

export default function ReportPanel({
  steps,
  investigationId,
  metadata,
}: {
  steps: StreamChunk[]
  investigationId: string
  metadata: Record<string, unknown>
}) {
  const hasPdf = metadata.pdf_path || steps.some(s => s.content.includes('PDF ready'))
  const rootCause = metadata.root_cause as string | undefined
  const confidence = metadata.confidence_pct as number | undefined
  const severity = metadata.severity as string | undefined

  const SEV_CLASSES: Record<string, string> = {
    CRITICAL: 'text-critical border-critical',
    HIGH: 'text-high border-high',
    MEDIUM: 'text-medium border-medium',
    LOW: 'text-low border-low',
  }
  const sevCls = severity ? (SEV_CLASSES[severity] ?? 'text-gray-400 border-gray-600') : 'text-gray-400 border-gray-600'

  return (
    <div className="border-t border-border bg-panel px-4 py-3 flex items-center gap-6 flex-shrink-0">
      <div className="flex items-center gap-2">
        <CheckCircle className="w-4 h-4 text-low" />
        <span className="text-xs text-gray-300 font-semibold">Investigation Complete</span>
      </div>

      {rootCause && (
        <div className="flex-1 min-w-0">
          <span className="text-xs text-gray-500">Root Cause: </span>
          <span className="text-xs text-white">{rootCause}</span>
          {confidence !== undefined && (
            <span className="text-xs text-gray-500 ml-2">({confidence.toFixed(0)}% confidence)</span>
          )}
        </div>
      )}

      {severity && (
        <span className={`text-xs border rounded px-2 py-0.5 font-bold flex-shrink-0 ${sevCls}`}>
          {severity}
        </span>
      )}

      <div className="flex items-center gap-2 flex-shrink-0 ml-auto">
        {steps.map((s, i) => (
          <span key={i} className="text-xs text-gray-500">{s.content.replace('✓ ', '')}</span>
        ))}
        {hasPdf && (
          <a
            href={`/api/reports/${investigationId}/pdf`}
            download
            className="flex items-center gap-2 px-3 py-1.5 bg-accent text-white text-xs rounded hover:bg-accent/80 transition-colors font-semibold"
          >
            <Download className="w-3.5 h-3.5" />
            Download PDF Report
          </a>
        )}
        {!hasPdf && (
          <span className="flex items-center gap-1.5 text-xs text-gray-500">
            <FileText className="w-3.5 h-3.5" />
            Generating report...
          </span>
        )}
      </div>
    </div>
  )
}
