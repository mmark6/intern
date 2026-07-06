import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Camera, Trash2, Mail, Phone, User, Shield, Save } from 'lucide-react'

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const fileInputRef = useRef(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [phone, setPhone] = useState('')
  const [savingPhone, setSavingPhone] = useState(false)
  const [isEditingPhone, setIsEditingPhone] = useState(false)

  useEffect(() => {
    if (user?.phone) {
      setPhone(user.phone)
    }
  }, [user?.phone])

  const handleImageClick = () => {
    fileInputRef.current?.click()
  }

  const handleImageChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if (!validTypes.includes(file.type)) {
      setError('Invalid file type. Allowed: JPEG, PNG, GIF, WebP')
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Image too large. Max 5MB')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const token = localStorage.getItem('uedcl_access_token')
      const formData = new FormData()
      formData.append('image', file)

      const res = await fetch('/api/users/me/image/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to upload')

      setSuccess('Photo updated successfully')
      refreshUser?.()
    } catch (err) {
      setError(err.message || 'Failed to upload image')
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveImage = async () => {
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const token = localStorage.getItem('uedcl_access_token')
      const res = await fetch('/api/users/me/image/', {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to remove')

      setSuccess('Photo removed')
      refreshUser?.()
    } catch (err) {
      setError(err.message || 'Failed to remove image')
    } finally {
      setLoading(false)
    }
  }

  const handleSavePhone = async () => {
    if (phone === user?.phone) {
      setIsEditingPhone(false)
      return
    }

    setSavingPhone(true)
    setError('')
    setSuccess('')

    try {
      const token = localStorage.getItem('uedcl_access_token')
      const res = await fetch('/api/users/me/', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone }),
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.errors?.phone?.[0] || data.error || 'Failed to update phone')

      setSuccess('Phone updated successfully')
      setIsEditingPhone(false)
      refreshUser?.()
    } catch (err) {
      setError(err.message || 'Failed to update phone')
    } finally {
      setSavingPhone(false)
    }
  }

  const handleCancelPhone = () => {
    setPhone(user?.phone || '')
    setIsEditingPhone(false)
  }

  const imageUrl = user?.image

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h2>My Profile</h2>
        <p className="subtitle">Manage your account settings</p>
      </div>

      <div className="profile-container">
        {/* Left: Profile Photo Card */}
        <div className="profile-photo-card">
          <div className="photo-wrapper" onClick={handleImageClick}>
            {imageUrl ? (
              <img src={imageUrl} alt="Profile" className="profile-img" />
            ) : (
              <div className="profile-avatar">
                <span>{user?.username?.charAt(0).toUpperCase() || 'U'}</span>
              </div>
            )}
            <div className="photo-overlay">
              <Camera size={24} />
              <span>{loading ? 'Uploading...' : 'Change Photo'}</span>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            onChange={handleImageChange}
            style={{ display: 'none' }}
          />
          {imageUrl && (
            <button
              className="btn-remove"
              onClick={handleRemoveImage}
              disabled={loading}
            >
              <Trash2 size={14} /> Remove
            </button>
          )}
        </div>

        {/* Right: Profile Info Card */}
        <div className="profile-info-card">
          <div className="info-header">
            <h3>Account Information</h3>
          </div>

          {error && <div className="alert">{error}</div>}
          {success && <div className="alert success">{success}</div>}

          <div className="info-grid">
            <div className="info-item">
              <div className="info-icon">
                <User size={18} />
              </div>
              <div className="info-content">
                <span className="info-label">Username</span>
                <span className="info-value">{user?.username || '-'}</span>
              </div>
            </div>

            <div className="info-item">
              <div className="info-icon">
                <Mail size={18} />
              </div>
              <div className="info-content">
                <span className="info-label">Email</span>
                <span className="info-value">{user?.email || '-'}</span>
              </div>
            </div>

            <div className="info-item">
              <div className="info-icon">
                <Phone size={18} />
              </div>
              <div className="info-content">
                <span className="info-label">Phone</span>
                {isEditingPhone ? (
                  <div className="phone-edit">
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+256 XXX XXX XXX"
                      className="phone-input"
                    />
                    <div className="phone-edit-actions">
                      <button
                        className="btn-save"
                        onClick={handleSavePhone}
                        disabled={savingPhone || phone === user?.phone}
                      >
                        {savingPhone ? 'Saving...' : <Save size={14} />}
                      </button>
                      <button className="btn-cancel" onClick={handleCancelPhone}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <span
                    className="info-value editable"
                    onClick={() => setIsEditingPhone(true)}
                  >
                    {user?.phone || 'Not provided'}
                  </span>
                )}
              </div>
            </div>

            <div className="info-item">
              <div className="info-icon">
                <Shield size={18} />
              </div>
              <div className="info-content">
                <span className="info-label">Role</span>
                <span className="info-value role">{user?.role_name === 'MEMBER' ? 'Staff' : user?.role_name || 'Staff'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}