import { useState, useEffect } from 'react'

function App() {
  const [health, setHealth] = useState<{ status?: string; service?: string } | null>(null)

  useEffect(() => {
    // Fetch health from backend
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error('Failed to fetch health:', err))
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to test_frontend_project_v2
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Your development environment is ready!
          </p>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">System Status</h2>
            
            {health ? (
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">Backend: {health.status || 'Unknown'}</span>
                </div>
                <div className="text-sm text-gray-500">
                  Service: {health.service || 'N/A'}
                </div>
              </div>
            ) : (
              <div className="text-gray-500">Connecting to backend...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
