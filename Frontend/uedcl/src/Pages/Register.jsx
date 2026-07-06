import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [form, setForm] = useState({ username: '', name: '', phone: '', email: '', password: '', password2: '' })

  const submit = async e => {
    e.preventDefault()
    setError('')

    if (form.password !== form.password2) {
      return setError('Passwords do not match.')
    }

    // AuthContext.register accepts username, name, phone, email, password
    const username = form.username || form.name.trim().replace(/\s+/g, '_').toLowerCase()
    const res = await register({ username, name: form.name, phone: form.phone, email: form.email, password: form.password })
    if (!res.ok) return setError(res.message)
    navigate('/')
  }

  return (
    <div className="auth-page">
      <form className="auth-card register-card" onSubmit={submit}>
        <h1>Create Account</h1>
        <p className="auth-subtitle">Register for UEDCL task tracking with secure role-based access.</p>

        {error && <div className="alert">{error}</div>}

        <input
          className="auth-input"
          value={form.username}
          onChange={e => setForm({ ...form, username: e.target.value })}
          placeholder="Username"
          autoComplete="username"
        />
        <input
          className="auth-input"
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
          placeholder="Full name"
          autoComplete="name"
        />
        <input
          className="auth-input"
          value={form.email}
          onChange={e => setForm({ ...form, email: e.target.value })}
          placeholder="Email address"
          autoComplete="email"
          inputMode="email"
        />
        <input
          className="auth-input"
          value={form.phone}
          onChange={e => setForm({ ...form, phone: e.target.value })}
          placeholder="Telephone number"
          autoComplete="tel"
          inputMode="tel"
        />
        <input
          className="auth-input"
          type="password"
          value={form.password}
          onChange={e => setForm({ ...form, password: e.target.value })}
          placeholder="Password (min 6 characters)"
          autoComplete="new-password"
        />
        <input
          className="auth-input"
          type="password"
          value={form.password2}
          onChange={e => setForm({ ...form, password2: e.target.value })}
          placeholder="Confirm password"
          autoComplete="new-password"
        />

        <button className="btn primary full" type="submit">
          Register
        </button>

        <div className="auth-links" style={{ marginTop: 2 }}>
          <Link to="/login">Back to login</Link>
        </div>
      </form>
    </div>
  )
}
