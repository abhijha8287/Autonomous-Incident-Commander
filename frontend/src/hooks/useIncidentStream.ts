import { useState, useCallback, useRef } from 'react'

export interface StreamChunk {
  agent: string
  type: 'step' | 'token' | 'error' | 'done'
  content: string
  metadata?: Record<string, unknown>
}

export interface StreamState {
  investigationSteps: StreamChunk[]
  timelineSteps: StreamChunk[]
  rcaTokens: string
  rcaSteps: StreamChunk[]
  reportSteps: StreamChunk[]
  errors: string[]
  isDone: boolean
  isRunning: boolean
  metadata: Record<string, unknown>
}

const INITIAL_STATE: StreamState = {
  investigationSteps: [],
  timelineSteps: [],
  rcaTokens: '',
  rcaSteps: [],
  reportSteps: [],
  errors: [],
  isDone: false,
  isRunning: false,
  metadata: {},
}

export function useIncidentStream() {
  const [state, setState] = useState<StreamState>(INITIAL_STATE)
  const esRef = useRef<EventSource | null>(null)

  const start = useCallback(async (incidentId: string): Promise<string | null> => {
    setState({ ...INITIAL_STATE, isRunning: true })

    // POST to start the investigation pipeline
    const res = await fetch(`/api/investigate/${incidentId}/start`, { method: 'POST' })
    if (!res.ok) {
      setState(s => ({ ...s, errors: ['Failed to start investigation'], isRunning: false }))
      return null
    }
    const { investigation_id, stream_url } = await res.json()

    // Open SSE stream
    const es = new EventSource(stream_url)
    esRef.current = es

    es.onmessage = (e: MessageEvent) => {
      const chunk: StreamChunk & { type: string } = JSON.parse(e.data)

      if (chunk.type === 'done') {
        setState(s => ({ ...s, isDone: true, isRunning: false }))
        es.close()
        return
      }

      if (chunk.type === 'error') {
        setState(s => ({ ...s, errors: [...s.errors, chunk.content] }))
        return
      }

      setState(s => {
        const next = { ...s }

        if (chunk.agent === 'investigation') {
          next.investigationSteps = [...s.investigationSteps, chunk as StreamChunk]
        } else if (chunk.agent === 'timeline') {
          next.timelineSteps = [...s.timelineSteps, chunk as StreamChunk]
        } else if (chunk.agent === 'root_cause') {
          if (chunk.type === 'token') {
            next.rcaTokens = s.rcaTokens + chunk.content
          } else {
            next.rcaSteps = [...s.rcaSteps, chunk as StreamChunk]
          }
        } else if (chunk.agent === 'report') {
          next.reportSteps = [...s.reportSteps, chunk as StreamChunk]
          if (chunk.metadata) {
            next.metadata = { ...s.metadata, ...chunk.metadata }
          }
        } else if (chunk.agent === 'orchestrator' && chunk.metadata) {
          next.metadata = { ...s.metadata, ...chunk.metadata }
        }

        return next
      })
    }

    es.onerror = () => {
      setState(s => ({ ...s, errors: [...s.errors, 'Stream connection error'], isRunning: false }))
      es.close()
    }

    return investigation_id
  }, [])

  const reset = useCallback(() => {
    esRef.current?.close()
    setState(INITIAL_STATE)
  }, [])

  return { state, start, reset }
}
