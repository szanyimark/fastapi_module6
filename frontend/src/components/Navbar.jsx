import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Navbar() {
  const { user, logout } = useAuth()

  const handleGitHubLogin = async () => {
    console.log("clicked github login")
    // Navigate directly to backend login route so the Set-Cookie is applied
    window.location.href = `${API_URL}/auth/github/login`
  }

  return (
    <nav style={{
      padding: '1rem 2rem',
      backgroundColor: '#333',
      color: 'white',
      display: 'flex',
      gap: '1.5rem',
      alignItems: 'center'
    }}>
      <Link to="/" style={{ color: 'white', textDecoration: 'none', fontWeight: 'bold' }}>
        Home
      </Link>
      <Link to="/users" style={{ color: 'white', textDecoration: 'none' }}>
        Users
      </Link>
      {!user && (
        <>
            <span style={{ marginLeft: 'auto' }}></span>
          <Link to="/register" style={{ color: 'white', textDecoration: 'none' }}>
            Register
          </Link>
          <Link to="/login" style={{ color: 'white', textDecoration: 'none' }}>
            Login
          </Link>
          <button
            onClick={handleGitHubLogin}
            style={{
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              backgroundColor: '#24292e',
              color: 'white',
              border: '1px solid #444',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          >
            GitHub Login
          </button>
        </>
      )}
      {user && (
        <>
          <span style={{ marginLeft: 'auto' }}>Welcome, {user.username}</span>
          <button
            onClick={logout}
            style={{
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              backgroundColor: '#555',
              color: 'white',
              border: 'none',
              borderRadius: '4px'
            }}
          >
            Logout
          </button>
        </>
      )}
    </nav>
  )
}
