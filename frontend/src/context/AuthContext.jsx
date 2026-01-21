import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)

  const getSubjectFromToken = (jwt) => {
    try {
      const payload = jwt.split('.')[1]
      const json = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
      return json.sub
    } catch (e) {
      return null
    }
  }

  // Load user and token from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('token')
    const savedUsername = localStorage.getItem('username')
    if (savedToken) {
      const derivedUsername = savedUsername || getSubjectFromToken(savedToken)
      if (derivedUsername) {
        setToken(savedToken)
        setUser({ username: derivedUsername })
        if (!savedUsername) {
          localStorage.setItem('username', derivedUsername)
        }
      }
    }
  }, [])

  const login = (accessToken, usernameHint) => {
    const derivedUsername = getSubjectFromToken(accessToken) || usernameHint
    setToken(accessToken)
    setUser({ username: derivedUsername || '' })
    localStorage.setItem('token', accessToken)
    if (derivedUsername) {
      localStorage.setItem('username', derivedUsername)
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
