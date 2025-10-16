import { useState, useEffect } from 'react'
import { useAuth } from './AuthContext'

interface SchedulerStatus {
  running: boolean
  next_run: string | null
  jobs_count: number
}

export default function SchedulerStatus() {
  const { session } = useAuth()
  const [status, setStatus] = useState<SchedulerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchStatus()
    // Refresh status every 30 seconds
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchStatus = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${apiUrl}/admin/scheduler/status`, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch scheduler status')
      }

      const data = await response.json()
      setStatus(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scheduler status')
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (action: 'start' | 'stop' | 'run-now') => {
    try {
      setActionLoading(action)
      setError('')
      
      const response = await fetch(`${apiUrl}/admin/scheduler/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to ${action} scheduler`)
      }

      const result = await response.json()
      
      if (action === 'run-now') {
        alert(result.message)
      }
      
      // Refresh status after action
      setTimeout(fetchStatus, 1000)
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} scheduler`)
    } finally {
      setActionLoading(null)
    }
  }

  if (loading && !status) {
    return (
      <div className="scheduler-status-container">
        <div className="loading-container">
          <span className="spinner" aria-label="Loading" />
          <p>Loading scheduler status...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="scheduler-status-container">
      <div className="scheduler-status-header">
        <h3>Automated Search Scheduler</h3>
        <button onClick={fetchStatus} className="refresh-button" disabled={loading}>
          {loading ? '⟳' : '↻'} Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {status && (
        <div className="scheduler-status-card">
          <div className="status-grid">
            <div className="status-item">
              <label>Status:</label>
              <span className={`status-badge ${status.running ? 'running' : 'stopped'}`}>
                {status.running ? '🟢 Running' : '🔴 Stopped'}
              </span>
            </div>

            <div className="status-item">
              <label>Active Jobs:</label>
              <span>{status.jobs_count}</span>
            </div>

            {status.next_run && (
              <div className="status-item">
                <label>Next Run:</label>
                <span>{new Date(status.next_run).toLocaleString()}</span>
              </div>
            )}
          </div>

          <div className="scheduler-actions">
            {!status.running ? (
              <button 
                onClick={() => handleAction('start')} 
                className="start-button"
                disabled={actionLoading === 'start'}
              >
                {actionLoading === 'start' ? 'Starting...' : 'Start Scheduler'}
              </button>
            ) : (
              <button 
                onClick={() => handleAction('stop')} 
                className="stop-button"
                disabled={actionLoading === 'stop'}
              >
                {actionLoading === 'stop' ? 'Stopping...' : 'Stop Scheduler'}
              </button>
            )}

            <button 
              onClick={() => handleAction('run-now')} 
              className="run-now-button"
              disabled={actionLoading === 'run-now'}
            >
              {actionLoading === 'run-now' ? 'Running...' : 'Run All Searches Now'}
            </button>
          </div>

          <div className="scheduler-info">
            <h4>How it works:</h4>
            <ul>
              <li>The scheduler runs every <strong>30 minutes</strong> automatically</li>
              <li>Only <strong>active</strong> saved searches are executed</li>
              <li>New results are automatically detected and stored</li>
              <li>Email notifications are sent when new results are found</li>
              <li>Results are deduplicated to avoid duplicates</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
