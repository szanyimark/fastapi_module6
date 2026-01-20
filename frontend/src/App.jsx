import React, { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')

  const loadUsers = async () => {
    setError('')
    try {
      const res = await fetch(`${API_URL}/users/`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setUsers(data)
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: 'sans-serif' }}>
      <h1>Module6 Frontend</h1>
      <p>API: {API_URL}</p>
      <button onClick={loadUsers}>Load Users</button>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      <ul>
        {users.map(u => (
          <li key={u.username}>{u.username} - {u.email}</li>
        ))}
      </ul>
    </div>
  )
}
