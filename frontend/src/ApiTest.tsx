import { useState } from 'react'
import { useAuth } from './AuthContext'

export default function ApiTest() {
  const { session } = useAuth()
  const [testResult, setTestResult] = useState('')
  const [testing, setTesting] = useState(false)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const testApiConnection = async () => {
    setTesting(true)
    setTestResult('Testing API connection...\n')

    try {
      // Test 1: Basic health check
      setTestResult(prev => prev + '1. Testing basic health check...\n')
      const healthResponse = await fetch(`${apiUrl}/health`)
      setTestResult(prev => prev + `   Health check: ${healthResponse.status} ${healthResponse.ok ? 'OK' : 'FAILED'}\n`)

      // Test 2: Test authentication endpoint
      if (session?.access_token) {
        setTestResult(prev => prev + '2. Testing authentication...\n')
        const authResponse = await fetch(`${apiUrl}/saved-searches/`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        })
        setTestResult(prev => prev + `   Auth test: ${authResponse.status} ${authResponse.ok ? 'OK' : 'FAILED'}\n`)
        
        if (!authResponse.ok) {
          const errorText = await authResponse.text()
          setTestResult(prev => prev + `   Error: ${errorText}\n`)
        }
      } else {
        setTestResult(prev => prev + '2. No authentication token available\n')
      }

      // Test 3: Test create endpoint with sample data
      if (session?.access_token) {
        setTestResult(prev => prev + '3. Testing create endpoint...\n')
        const testData = {
          name: 'Test Search',
          job_title: 'Software Engineer',
          experience_level: 'senior level',
          count: 10,
          notification_email: 'test@example.com'
        }

        const createResponse = await fetch(`${apiUrl}/saved-searches/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(testData)
        })

        setTestResult(prev => prev + `   Create test: ${createResponse.status} ${createResponse.ok ? 'OK' : 'FAILED'}\n`)
        
        if (!createResponse.ok) {
          const errorText = await createResponse.text()
          setTestResult(prev => prev + `   Error: ${errorText}\n`)
        } else {
          const result = await createResponse.json()
          setTestResult(prev => prev + `   Created search ID: ${result.id}\n`)
        }
      }

    } catch (error) {
      setTestResult(prev => prev + `\nERROR: ${error}\n`)
    } finally {
      setTesting(false)
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '600px' }}>
      <h3>API Connection Test</h3>
      <button onClick={testApiConnection} disabled={testing}>
        {testing ? 'Testing...' : 'Test API Connection'}
      </button>
      
      {testResult && (
        <pre style={{ 
          background: '#f5f5f5', 
          padding: '15px', 
          marginTop: '15px',
          fontSize: '12px',
          whiteSpace: 'pre-wrap',
          border: '1px solid #ddd',
          borderRadius: '4px'
        }}>
          {testResult}
        </pre>
      )}
    </div>
  )
}
