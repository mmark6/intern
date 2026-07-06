import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import downloadImage from '../assets/download.jpg'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ email: 'admin@uedcl.co.ug', password: 'Admin123!' })

  const submit = async e => {
    e.preventDefault()
    if (submitting) return

    setError('')
    setSubmitting(true)

    try {
      const res = await login(form)
      if (!res.ok) {
        const msg = String(res.message || 'Login failed.')

        if (msg.toLowerCase().includes('too many') || msg.includes('429')) {
          return setError('Too many login attempts. Please wait a moment and try again.')
        }

        return setError(msg)
      }
      navigate('/')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card login-card" onSubmit={submit}>
        <div className="auth-branding">
          <img className="auth-logo" src={downloadImage} alt="UEDCL logo" />
          <div>
            <p className="eyebrow">UEDCL</p>
            <h1>Welcome back</h1>
          </div>
        </div>
        <p className="auth-subtitle">Access the task tracking workspace with secure, role-based controls.</p>
        {error && <div className="alert">{error}</div>}
        <input
          className="auth-input"
          value={form.email}
          onChange={e => setForm({ ...form, email: e.target.value })}
          placeholder="Email"
          autoComplete="email"
        />
        <input
          className="auth-input"
          type="password"
          value={form.password}
          onChange={e => setForm({ ...form, password: e.target.value })}
          placeholder="Password"
          autoComplete="current-password"
        />
        <button className="btn primary full" disabled={submitting}>
          {submitting ? 'Logging in…' : 'Login'}
        </button>
        <div className="auth-links">
          <Link to="/forgot-password">Forgot password?</Link>
          <Link to="/register">Create account</Link>
        </div>
      </form>
    </div>
  )
}
