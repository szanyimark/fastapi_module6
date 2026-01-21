import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Users() {
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const { user, token } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!user || !token) {
      navigate('/login')
      return
    }

    const loadUsers = async () => {
      setError('')
      try {
        const res = await fetch(`${API_URL}/users/`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (res.status === 401) {
          navigate('/login')
          return
        }
        
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }
        
        const data = await res.json()
        setUsers(data)
      } catch (e) {
        setError(String(e))
      } finally {
        setLoading(false)
      }
    }

    loadUsers()
  }, [user, token, navigate])

  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading...</div>
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Users List</h1>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {users.length === 0 ? (
        <p>No users found.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f0f0f0' }}>
              <th style={{ padding: '0.75rem', textAlign: 'left', border: '1px solid #ddd' }}>Username</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', border: '1px solid #ddd' }}>Email</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', border: '1px solid #ddd' }}>Full Name</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.username}>
                <td style={{ padding: '0.75rem', border: '1px solid #ddd' }}>{u.username}</td>
                <td style={{ padding: '0.75rem', border: '1px solid #ddd' }}>{u.email}</td>
                <td style={{ padding: '0.75rem', border: '1px solid #ddd' }}>{u.fullname || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
