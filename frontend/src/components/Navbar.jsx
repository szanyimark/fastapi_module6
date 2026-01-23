import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Navbar() {
  const { user, logout } = useAuth()

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
