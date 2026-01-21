import React from 'react'
import { useAuth } from '../context/AuthContext'

export default function Home() {
  const { user } = useAuth()

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Welcome {user ? user.username : 'Guest'}</h1>
      <p>
        {user
          ? 'You are logged in. Click on Users to see the list.'
          : 'Please login or register to access all features.'}
      </p>
    </div>
  )
}
