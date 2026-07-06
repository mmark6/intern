import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function ForgotPassword() {
  const navigate = useNavigate()
  const { requestPasswordReset, verifyResetCode, changePassword, login } = useAuth()
  const [step, setStep] = useState(1)
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleEmailSubmit = async e => {
    e.preventDefault()
    const res = await requestPasswordReset({ email })
    if (!res.ok) return setError(res.message)
    setError('')
    setMessage(res.message)
    setStep(2)
  }

  const handleCodeSubmit = async e => {
    e.preventDefault()
    const res = await verifyResetCode({ email, code })
    if (!res.ok) return setError(res.message)
    setError('')
    setMessage(res.message)
    setStep(3)
  }

  const handlePasswordSubmit = async e => {
    e.preventDefault()
    if (!password || !confirmPassword) {
      setError('Please enter and confirm your new password.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    const res = await changePassword({ email, password })
    if (!res.ok) return setError(res.message)

    const loginRes = await login({ email, password })
    setError('')
    setMessage(loginRes.ok ? 'Password updated successfully. You are signed in.' : res.message)

    if (loginRes.ok) {
      setTimeout(() => navigate('/'), 600)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={step === 1 ? handleEmailSubmit : step === 2 ? handleCodeSubmit : handlePasswordSubmit}>
        <h1>Forgot Password</h1>
        <p>Verify your email, then set a new password.</p>
        {error && <div className="alert">{error}</div>}
        {message && <div className="alert success" style={{ color: '#22c55e' }}>{message}</div>}


        {step >= 1 && (
          <input
            className="auth-input"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="Enter your email"
            inputMode="email"
            autoComplete="email"
          />
        )}

        {step >= 2 && (
          <input
            className="auth-input"
            value={code}
            onChange={e => setCode(e.target.value)}
            placeholder="Enter verification code"
            inputMode="numeric"
            autoComplete="one-time-code"
          />
        )}

        {step >= 3 && (
          <>
            <input
              className="auth-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Create a new password"
              autoComplete="new-password"
            />
            <input
              className="auth-input"
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              autoComplete="new-password"
            />
          </>
        )}

        <button className="btn primary full">{step === 1 ? 'Send code' : step === 2 ? 'Verify code' : 'Change password'}</button>
        <Link to="/login">Back to login</Link>
      </form>
    </div>
  )
}
