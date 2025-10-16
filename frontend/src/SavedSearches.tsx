import { useState, useEffect } from 'react'
import { useAuth } from './AuthContext'

interface SavedSearch {
  id: number
  name: string
  job_title: string
  experience_level: string
  count: number
  is_active: boolean
  notification_email?: string
  last_run_at?: string
  created_at: string
  new_results_count: number
}

interface SavedSearchCreate {
  name: string
  job_title: string
  experience_level: string
  count: number
  notification_email?: string
}

export default function SavedSearches() {
  const { user, session } = useAuth()
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingSearch, setEditingSearch] = useState<SavedSearch | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Form state
  const [formData, setFormData] = useState<SavedSearchCreate>({
    name: '',
    job_title: '',
    experience_level: '',
    count: 25,
    notification_email: ''
  })

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (user && session) {
      fetchSavedSearches()
    }
  }, [user, session])

  const fetchSavedSearches = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${apiUrl}/saved-searches/`, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch saved searches')
      }

      const data = await response.json()
      setSavedSearches(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load saved searches')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Debug logging
    console.log('Form submission started')
    console.log('Form data:', formData)
    console.log('Session:', session)
    console.log('User:', user)

    // Validation
    if (!formData.name || !formData.job_title || !formData.experience_level) {
      setError('Please fill in all required fields')
      return
    }

    if (!session?.access_token) {
      setError('Authentication required. Please sign in again.')
      return
    }

    try {
      setSubmitting(true)
      
      const url = editingSearch 
        ? `${apiUrl}/saved-searches/${editingSearch.id}`
        : `${apiUrl}/saved-searches/`
      
      const method = editingSearch ? 'PUT' : 'POST'
      
      console.log('Making request to:', url)
      console.log('Method:', method)
      console.log('Headers:', {
        'Authorization': `Bearer ${session?.access_token}`,
        'Content-Type': 'application/json',
      })

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      console.log('Response status:', response.status)
      console.log('Response ok:', response.ok)

      if (!response.ok) {
        const errorText = await response.text()
        console.log('Error response:', errorText)
        
        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch {
          errorData = { detail: errorText }
        }
        
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to save search`)
      }

      const result = await response.json()
      console.log('Success response:', result)

      // Reset form and refresh list
      setFormData({
        name: '',
        job_title: '',
        experience_level: '',
        count: 25,
        notification_email: ''
      })
      setShowCreateForm(false)
      setEditingSearch(null)
      fetchSavedSearches()
    } catch (err) {
      console.error('Submit error:', err)
      setError(err instanceof Error ? err.message : 'Failed to save search')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = (search: SavedSearch) => {
    setFormData({
      name: search.name,
      job_title: search.job_title,
      experience_level: search.experience_level,
      count: search.count,
      notification_email: search.notification_email || ''
    })
    setEditingSearch(search)
    setShowCreateForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this saved search?')) {
      return
    }

    try {
      const response = await fetch(`${apiUrl}/saved-searches/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to delete search')
      }

      fetchSavedSearches()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete search')
    }
  }

  const handleToggleActive = async (search: SavedSearch) => {
    try {
      const response = await fetch(`${apiUrl}/saved-searches/${search.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: !search.is_active })
      })

      if (!response.ok) {
        throw new Error('Failed to update search')
      }

      fetchSavedSearches()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update search')
    }
  }

  const handleRunNow = async (id: number) => {
    try {
      setError('')
      const response = await fetch(`${apiUrl}/saved-searches/${id}/run`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to run search')
      }

      const result = await response.json()
      alert(`Search completed! Found ${result.total_results} total results, ${result.new_results} new.`)
      fetchSavedSearches()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run search')
    }
  }

  const handleMarkSeen = async (id: number) => {
    try {
      const response = await fetch(`${apiUrl}/saved-searches/${id}/mark-seen`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to mark results as seen')
      }

      fetchSavedSearches()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to mark results as seen')
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="loading-container">
        <span className="spinner" aria-label="Loading" />
        <p>Loading saved searches...</p>
      </div>
    )
  }

  return (
    <div className="saved-searches-container">
      <div className="saved-searches-header">
        <h2>Saved Searches</h2>
        <button 
          className="create-search-button"
          onClick={() => {
            setShowCreateForm(true)
            setEditingSearch(null)
            setFormData({
              name: '',
              job_title: '',
              experience_level: '',
              count: 25,
              notification_email: ''
            })
          }}
        >
          + Create New Search
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {showCreateForm && (
        <div className="create-form-overlay">
          <div className="create-form">
            <h3>{editingSearch ? 'Edit Search' : 'Create New Saved Search'}</h3>
            <form onSubmit={handleSubmit}>
              <div className="field">
                <label htmlFor="name">Search Name</label>
                <input
                  id="name"
                  type="text"
                  placeholder="e.g., Senior Frontend Jobs"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="job_title">Job Title</label>
                <input
                  id="job_title"
                  type="text"
                  placeholder="e.g., Frontend Developer"
                  value={formData.job_title}
                  onChange={(e) => setFormData({...formData, job_title: e.target.value})}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="experience_level">Experience Level</label>
                <select
                  id="experience_level"
                  value={formData.experience_level}
                  onChange={(e) => setFormData({...formData, experience_level: e.target.value})}
                  required
                >
                  <option value="">Select experience level</option>
                  <option value="intern">Intern</option>
                  <option value="new grad">New Grad</option>
                  <option value="associate level">Associate Level</option>
                  <option value="senior level">Senior Level</option>
                  <option value="manager">Manager</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="count">Number of Results</label>
                <input
                  id="count"
                  type="number"
                  min="1"
                  max="100"
                  value={formData.count}
                  onChange={(e) => setFormData({...formData, count: parseInt(e.target.value)})}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="notification_email">Notification Email (Optional)</label>
                <input
                  id="notification_email"
                  type="email"
                  placeholder="Get notified when new results are found"
                  value={formData.notification_email}
                  onChange={(e) => setFormData({...formData, notification_email: e.target.value})}
                />
              </div>

              <div className="form-actions">
                <button type="button" onClick={() => {
                  setShowCreateForm(false)
                  setEditingSearch(null)
                }}>
                  Cancel
                </button>
                <button type="submit" className="primary" disabled={submitting}>
                  {submitting ? (
                    <>
                      <span className="spinner" aria-label="Loading" />
                      {editingSearch ? 'Updating...' : 'Creating...'}
                    </>
                  ) : (
                    editingSearch ? 'Update Search' : 'Create Search'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="saved-searches-list">
        {savedSearches.length === 0 ? (
          <div className="empty-state">
            <p>No saved searches yet. Create your first automated job search!</p>
          </div>
        ) : (
          savedSearches.map((search) => (
            <div key={search.id} className={`search-card ${!search.is_active ? 'inactive' : ''}`}>
              <div className="search-header">
                <h3>{search.name}</h3>
                <div className="search-actions">
                  <button onClick={() => handleRunNow(search.id)} className="run-button">
                    Run Now
                  </button>
                  <button onClick={() => handleEdit(search)} className="edit-button">
                    Edit
                  </button>
                  <button onClick={() => handleDelete(search.id)} className="delete-button">
                    Delete
                  </button>
                </div>
              </div>

              <div className="search-details">
                <p><strong>Job Title:</strong> {search.job_title}</p>
                <p><strong>Experience Level:</strong> {search.experience_level}</p>
                <p><strong>Results Count:</strong> {search.count}</p>
                {search.notification_email && (
                  <p><strong>Notifications:</strong> {search.notification_email}</p>
                )}
              </div>

              <div className="search-status">
                <div className="status-item">
                  <label>
                    <input
                      type="checkbox"
                      checked={search.is_active}
                      onChange={() => handleToggleActive(search)}
                    />
                    Active (runs every 30 minutes)
                  </label>
                </div>

                {search.new_results_count > 0 && (
                  <div className="new-results">
                    <span className="new-count">{search.new_results_count} new results!</span>
                    <button onClick={() => handleMarkSeen(search.id)} className="mark-seen-button">
                      Mark as Seen
                    </button>
                  </div>
                )}

                <div className="last-run">
                  <strong>Last Run:</strong> {search.last_run_at ? formatDate(search.last_run_at) : 'Never'}
                </div>

                <div className="created">
                  <strong>Created:</strong> {formatDate(search.created_at)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
