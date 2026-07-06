import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { authApi } from '../api/api.js'

const AuthContext = createContext(null)
const STORAGE_KEY = 'uedcl_auth_user'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : null
  })
  const [resetState, setResetState] = useState({ email: '', code: '', verified: false, resetToken: null })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
  }, [user])

  const normalizeRole = roleValue => {
    const normalized = String(roleValue || '').trim().toLowerCase() 
    if (normalized === 'admin' || normalized === 'administrator') return 'admin'
    if (normalized === 'manager') return 'manager'
    return 'staff'
  }

  // Verify user session with backend - invalidates stale sessions
  const verifySession = async () => {
    try {
      const payload = await authApi.current()
      const userData = payload?.user || payload
      if (userData?.email) {
        return {
          id: userData.id ?? Date.now(),
          username: userData.username || userData.name || userData.email,
          email: userData.email,
          first_name: userData.first_name || '',
          last_name: userData.last_name || '',
          phone: userData.phone || '',
          image: userData.image || null,
          role: normalizeRole(userData.role || userData.role_name),
          role_name: userData.role_name || userData.role || '',
        }
      }
      // No valid user returned - clear stale session
      return null
    } catch {
      // API error - session invalid, clear local storage
      return null
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadCurrentUser() {
      // Only verify session if we have a stored user (meaning they logged in before)
      const savedUser = localStorage.getItem(STORAGE_KEY)
      if (!savedUser) return

      // Verify session with backend to ensure it's still valid
      const verifiedUser = await verifySession()
      if (!mounted) return

      if (verifiedUser) {
        setUser(verifiedUser)
      } else {
        // Session invalid - clear all auth data
        localStorage.removeItem(STORAGE_KEY)
        localStorage.removeItem('uedcl_access_token')
        localStorage.removeItem('uedcl_refresh_token')
      }
    }

    loadCurrentUser()
    return () => {
      mounted = false
    }
  }, [])

  // Handle browser back button - logout when navigating back from protected pages
  useEffect(() => {
    const handlePopState = async () => {
      // User pressed back button - verify session and log out if invalid
      const savedUser = localStorage.getItem(STORAGE_KEY)
      if (savedUser && user) {
        // Verify session with backend
        const verifiedUser = await verifySession()
        if (!verifiedUser) {
          // Session invalid - force logout
          localStorage.removeItem(STORAGE_KEY)
          localStorage.removeItem('uedcl_access_token')
          localStorage.removeItem('uedcl_refresh_token')
          setUser(null)
          // Redirect to login
          window.location.href = '/login'
        }
      }
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [user])

  // Handle page show - verify session when page is restored from cache
  useEffect(() => {
    const handlePageShow = async (event) => {
      if (event.persisted) {
        // Page is being restored from cache (back button scenario)
        const savedUser = localStorage.getItem(STORAGE_KEY)
        if (savedUser && user) {
          // Verify session with backend
          const verifiedUser = await verifySession()
          if (!verifiedUser) {
            // Session invalid - force logout
            localStorage.removeItem(STORAGE_KEY)
            localStorage.removeItem('uedcl_access_token')
            localStorage.removeItem('uedcl_refresh_token')
            setUser(null)
          }
        }
      }
    }

    window.addEventListener('pageshow', handlePageShow)
    return () => window.removeEventListener('pageshow', handlePageShow)
  }, [user])

  const register = async ({ username, name, phone, email, password }) => {
    if (import.meta.env.DEV) {
      console.debug('[Auth] Register attempt:', { username, email, phone })
    }
    try {
      const result = await authApi.register({ username, email, phone, password, password2: password, first_name: name || '', last_name: '' })
      if (import.meta.env.DEV) {
        console.debug('[Auth] Register result:', result)
      }
      // Check for backend errors - the backend returns { success: false, errors: {...} }
      if (result?.success === false) {
        const errorMsg = result.errors ? JSON.stringify(result.errors) : result.message || 'Registration failed'
        // Helpful debugging: surface backend errors even if the structure differs
        const fallbackMsg = result?.message
        return { ok: false, message: errorMsg || fallbackMsg }
      }
      // Check for success - backend returns { success: true, user: {...} }
      if (result?.success === true && result?.user) {
        const backendUser = result.user
        setUser({ id: backendUser.id, name: backendUser.username, email: backendUser.email, role: 'staff' })
        return { ok: true }
      }
      // Legacy: handle case where backend returns user without success flag
      if (result?.user) {
        const backendUser = result.user
        setUser({ id: backendUser.id, name: backendUser.username, email: backendUser.email, role: 'staff' })
        return { ok: true }
      }
    } catch (err) {
      console.warn('Backend register failed', err)
      return { ok: false, message: err.message || 'Network error. Is the backend running?' }
    }

    // Only reach here if something unexpected happened
    return { ok: false, message: 'Registration failed. Please try again.' }
  }

  const login = async ({ email, password }) => {
    if (import.meta.env.DEV) {
      console.debug('[Auth] Login attempt:', { email })
    }
    try {
      const result = await authApi.login({ email, password })
      if (import.meta.env.DEV) {
        console.debug('[Auth] Login result:', result)
      }

      if (result?.access_token) {
        // api.js already stores tokens in localStorage, but keep this in sync
        localStorage.setItem('uedcl_access_token', result.access_token)

        const userData = result.user || { email }
        setUser({
          id: userData.id ?? Date.now(),
          username: userData.username || userData.first_name || userData.email || email,
          email: userData.email || email,
          first_name: userData.first_name || '',
          last_name: userData.last_name || '',
          phone: userData.phone || '',
          image: userData.image || null,
          role: normalizeRole(userData.role || userData.role_name),
          role_name: userData.role_name || userData.role || '',
        })
        return { ok: true }
      }

      const message =
        result?.errors
          ? typeof result.errors === 'string'
            ? result.errors
            : JSON.stringify(result.errors)
          : result?.message || 'Login failed'
      return { ok: false, message }
    } catch (err) {
      const payload = err?.payload
      const message =
        payload?.detail ||
        payload?.message ||
        payload?.error ||
        payload?.errors ||
        err?.message ||
        'Login failed'
      return { ok: false, message }
    }
  }

  const logout = async () => {
    try {
      // Invalidate server-side auth (and stop refresh race conditions)
      await authApi.logout()
    } catch (err) {
      // Even if backend logout fails, still clear local tokens to force re-login
      if (import.meta.env.DEV) console.warn('[Auth] backend logout failed', err)
    } finally {
      localStorage.removeItem('uedcl_access_token')
      localStorage.removeItem('uedcl_refresh_token')
      setUser(null)
    }
  }

  const requestPasswordReset = async ({ email }) => {
    // Keep only backend-driven behavior (no local seed fallback)
    try {
      const result = await authApi.passwordReset(email)

      // Backend returns different shapes depending on DEBUG / SMTP status.
      const message = result?.message || result?.detail

      if (result?.success === false) {
        return {
          ok: false,
          message: result?.error || result?.send_mail_error || message || 'Failed to send verification email.',
        }
      }

      if (result?.success === true) {
        return {
          ok: true,
          message: message || 'A verification code has been sent.',
          code: result?.code || null,
        }
      }

      if (message) return { ok: true, message }

      return { ok: false, message: result?.error || result?.send_mail_error || 'Password reset failed' }
    } catch (err) {
      const payload = err?.payload
      const message =
        payload?.detail ||
        payload?.message ||
        payload?.error ||
        payload?.send_mail_error ||
        err?.message ||
        'Password reset failed'
      return { ok: false, message }
    }
  }

  const verifyResetCode = async ({ email, code }) => {
    try {
      const result = await authApi.passwordVerify(email, code)
      if (result?.success && result?.reset_token) {
        setResetState(prev => ({ ...prev, email, resetToken: result.reset_token, verified: true }))
        return { ok: true, message: result.message || 'Code verified. Set your new password.' }
      }
      return { ok: false, message: result?.error || 'Invalid verification code.' }
    } catch (err) {
      return { ok: false, message: err?.payload?.error || 'Verification failed.' }
    }
  }

  const changePassword = async ({ email, password }) => {
    const resetToken = resetState.resetToken
    if (!resetToken) return { ok: false, message: 'No active reset session.' }
    try {
      const result = await authApi.passwordChange(email, resetToken, password)
      if (result?.success) {
        setResetState({ email: '', code: '', verified: false, resetToken: null })
        return { ok: true, message: result.message || 'Password reset successfully.' }
      }
      return { ok: false, message: result?.error || 'Password change failed.' }
    } catch (err) {
      return { ok: false, message: err?.payload?.error || 'Password change failed.' }
    }
  }

  const refreshUser = async () => {
    try {
      const payload = await authApi.current()
      const userData = payload?.user || payload
      if (userData?.email) {
        setUser({
          id: userData.id ?? Date.now(),
          username: userData.username || userData.name || userData.email,
          email: userData.email,
          first_name: userData.first_name || '',
          last_name: userData.last_name || '',
          phone: userData.phone || '',
          image: userData.image || null,
          role: normalizeRole(userData.role || userData.role_name),
          role_name: userData.role_name || userData.role || '',
        })
      }
    } catch (err) {
      console.warn('Failed to refresh user', err)
    }
  }

  const value = useMemo(
    () => ({ user, login, register, logout, requestPasswordReset, verifyResetCode, changePassword, refreshUser }),
    [user, resetState]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)

