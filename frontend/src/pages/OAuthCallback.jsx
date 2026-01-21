import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function OAuthCallback() {
  const navigate = useNavigate()
  const { login } = useAuth()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const username = params.get('username')

    if (token && username) {
      login(token, username)
      navigate('/')
    } else {
      navigate('/login')
    }
  }, [login, navigate])

  return (
    <div style={{ padding: '2rem' }}>
      Completing login...
    </div>
  )
}
