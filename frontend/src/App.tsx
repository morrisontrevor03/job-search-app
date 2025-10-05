import { useMemo, useState } from 'react'

export default function App() {
  const [jobTitle, setJobTitle] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('')
  const [count, setCount] = useState<number | ''>('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<string[]>([])
  const [error, setError] = useState<string>('')
  const [touched, setTouched] = useState<{ title: boolean; experienceLevel: boolean; count: boolean }>({ title: false, experienceLevel: false, count: false })

  const errors = useMemo(() => {
    const errs: { title?: string; experienceLevel?: string; count?: string } = {}
    if (touched.title && jobTitle.trim().length < 2) {
      errs.title = 'Enter at least 2 characters.'
    }
    if (touched.experienceLevel && !experienceLevel.trim()) {
      errs.experienceLevel = 'Please select an experience level.'
    }
    if (touched.count) {
      if (count === '' || Number.isNaN(Number(count))) {
        errs.count = 'Enter a number.'
      } else if (Number(count) < 1 || Number(count) > 100) {
        errs.count = 'Choose 1 to 100.'
      }
    }
    return errs
  }, [jobTitle, experienceLevel, count, touched])

  const canSubmit = jobTitle.trim().length >= 2 && experienceLevel.trim().length > 0 && typeof count === 'number' && count >= 1 && count <= 100 && !loading

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setTouched({ title: true, experienceLevel: true, count: true })
    if (!canSubmit) return

    try {
      setLoading(true)
      setError('')
      setResults([])
      
      // Debug: log the data being sent
      const requestData = {
        text: jobTitle,
        level: experienceLevel,
        count: count
      }
      console.log('Sending request data:', requestData)
      
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })

      console.log('Response status:', response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.log('Error response:', errorText)
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
      }

      const data = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while searching')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <h1>Job Search</h1>
        </div>
        <p className="subtitle">Pull the most recent, hidden job postings from anywhere on the internet</p>
      </header>

      <main>
        <form className="card" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="title">Job title</label>
            <input
              id="title"
              name="title"
              type="text"
              inputMode="text"
              placeholder="e.g., Financial Analyst"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, title: true }))}
              aria-invalid={!!errors.title}
              aria-describedby="title-err"
              autoFocus
            />
            {errors.title && (
              <div id="title-err" role="alert" className="error">
                {errors.title}
              </div>
            )}
          </div>

          <div className="field">
            <label htmlFor="experienceLevel">Experience level</label>
            <select
              id="experienceLevel"
              name="experienceLevel"
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, experienceLevel: true }))}
              aria-invalid={!!errors.experienceLevel}
              aria-describedby="experienceLevel-err"
            >
              <option value="">Select experience level</option>
              <option value="intern">Intern</option>
              <option value="new grad">New Grad</option>
              <option value="associate level">Associate Level</option>
              <option value="senior level">Senior Level</option>
              <option value="manager">Manager</option>
            </select>
            {errors.experienceLevel && (
              <div id="experienceLevel-err" role="alert" className="error">
                {errors.experienceLevel}
              </div>
            )}
          </div>

          <div className="field">
            <label htmlFor="count">How many postings?</label>
            <input
              id="count"
              name="count"
              type="number"
              min={1}
              max={100}
              step={1}
              inputMode="numeric"
              placeholder="e.g., 25"
              value={count}
              onChange={(e) => {
                const val = e.target.value
                setCount(val === '' ? '' : Number(val))
              }}
              onBlur={() => setTouched((t) => ({ ...t, count: true }))}
              aria-invalid={!!errors.count}
              aria-describedby="count-err"
            />
            {errors.count && (
              <div id="count-err" role="alert" className="error">
                {errors.count}
              </div>
            )}
          </div>

          <button className="go" type="submit" disabled={!canSubmit}>
            {loading ? (
              <span className="spinner" aria-label="Loading" />
            ) : (
              'Go'
            )}
          </button>
        </form>

        {error && (
          <div className="card error-card">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        )}

        {results.length > 0 && (
          <div className="card results-card">
            <h3>Search Results ({results.length} found)</h3>
            <textarea
              className="results-textbox"
              value={results.join('\n')}
              readOnly
              rows={Math.min(results.length + 2, 15)}
              placeholder="Job posting links will appear here..."
            />
          </div>
        )}
      </main>
    </div>
  )
}
