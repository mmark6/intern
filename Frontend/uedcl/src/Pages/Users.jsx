import { useEffect, useMemo, useState } from 'react'
import { usersApi, authApi, dashboardApi } from '../api/api.js'
import StatCard from '../components/StatCard'
import { Users as UsersIcon, UserCog, UserCheck, Shield, TrendingUp } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts'

const fallbackUsers = [
  { name: 'Admin User', role: 'admin', email: 'admin@uedcl.co.ug' },
  { name: 'Project Manager', role: 'manager', email: 'manager@uedcl.co.ug' },
  { name: 'Staff Member', role: 'staff', email: 'staff@uedcl.co.ug' },
]

const ROLE_LABELS = {
  admin: 'Admin',
  manager: 'Manager',
  staff: 'Staff',
}

const ROLE_COLORS = {
  ADMIN: '#dc2626',
  MANAGER: '#2563eb',
  STAFF: '#16a34a',
}

const COLORS = ['#dc2626', '#2563eb', '#16a34a', '#f59e0b']

function normalizeUserList(payload) {
  if (!payload) return []
  if (Array.isArray(payload)) return payload
  if (payload.results) return payload.results
  if (payload.data) return payload.data
  if (payload.users) return payload.users
  return []
}

function normalizeUser(user) {
  return {
    id: user.id,
    name: user.name || user.username || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email,
    email: user.email,
    role: user.role || user.type || user.role_name || 'staff',
    username: user.username,
  }
}

export default function Users() {
  const [users, setUsers] = useState(fallbackUsers)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [passwordFocused, setPasswordFocused] = useState(false)
  const [userStats, setUserStats] = useState({})
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    phone: '',
    password: '',
    password2: '',
    role: 'STAFF',
    first_name: '',
    last_name: '',
  })

  const passwordStrength = useMemo(() => {
    const password = newUser.password
    if (!password) return { strength: 0, label: '', color: '#6b7280' }
    let score = 0
    if (password.length >= 6) score++
    if (password.length >= 8) score++
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++
    if (/\d/.test(password)) score++
    if (/[^a-zA-Z0-9]/.test(password)) score++
    if (score <= 1) return { strength: score, label: 'Weak', color: '#dc2626' }
    if (score <= 2) return { strength: score, label: 'Fair', color: '#f59e0b' }
    if (score <= 3) return { strength: score, label: 'Good', color: '#22c55e' }
    return { strength: score, label: 'Strong', color: '#16a34a' }
  }, [newUser.password])

  const passwordsMatch = newUser.password && newUser.password2 && newUser.password === newUser.password2
  const canSubmit = newUser.username && newUser.email && newUser.password && newUser.password.length >= 6 && passwordsMatch

  // Stats calculations
  const userStatsData = useMemo(() => {
    const total = users.length
    const admins = users.filter(u => u.role === 'ADMIN' || u.role === 'admin').length
    const managers = users.filter(u => u.role === 'MANAGER' || u.role === 'manager').length
    const staff = users.filter(u => u.role === 'STAFF' || u.role === 'staff').length
    return { total, admins, managers, staff }
  }, [users])

  // Role distribution data for pie chart
  const roleDistribution = useMemo(() => [
    { name: 'Admins', value: userStatsData.admins },
    { name: 'Managers', value: userStatsData.managers },
    { name: 'Staff', value: userStatsData.staff },
  ], [userStatsData])

  // User task performance data for bar chart
  const userPerformanceData = useMemo(() => {
    return users.map(u => {
      const stats = userStats[u.id] || {}
      const total = stats.total_tasks || 0
      const done = stats.done || 0
      return {
        name: u.name?.split(' ')[0] || u.username || 'User',
        'To Do': stats.todo || 0,
        'In Progress': stats.in_progress || 0,
        'Done': done,
        'Overdue': stats.overdue || 0,
        total,
        completionRate: total > 0 ? Math.round((done / total) * 100) : 0,
      }
    })
  }, [users, userStats])

  const loadUserTaskStats = async userId => {
    try {
      const stats = await dashboardApi.userTasks(userId)
      setUserStats(prev => ({ ...prev, [userId]: stats }))
    } catch (err) {
      console.error('Failed to load user task stats', err)
    }
  }

  const loadUsers = async () => {
    setLoading(true)
    setError('')

    const attempt = async () => {
      const result = await usersApi.list()
      const list = normalizeUserList(result)

      if (list.length) {
        setUsers(list.map(normalizeUser))
        setError('')
        list.forEach(user => {
          if (user.id) loadUserTaskStats(user.id)
        })
      } else {
        setUsers(fallbackUsers)
        setError('No users were returned from backend. Showing fallback data.')
      }
    }

    try {
      await attempt()
    } catch (err) {
      const status = err?.status
      const isGateway = status === 502 || status === 503 || status === 504

      if (isGateway) {
        try {
          await attempt()
          return
        } catch (retryErr) {
          console.error('Gateway retry failed while loading users', retryErr)
          setUsers(fallbackUsers)
          setError('Backend unavailable')
          return
        }
      }

      console.error('Failed to load backend users', err)
      setUsers(fallbackUsers)
      setError('Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const filteredUsers = useMemo(
    () =>
      users.filter(user =>
        `${user.name} ${user.email} ${ROLE_LABELS[user.role] || user.role}`
          .toLowerCase()
          .includes(search.toLowerCase())
      ),
    [users, search]
  )

  const createUser = async e => {
    e.preventDefault()
    if (creating || !canSubmit) return
    setCreating(true)
    setError('')
    setSuccessMsg('')

    try {
      const payload = {
        username: newUser.username,
        email: newUser.email,
        password: newUser.password,
        password2: newUser.password2,
        role: newUser.role,
        first_name: newUser.first_name,
        last_name: newUser.last_name,
      }
      if (newUser.phone && newUser.phone.trim()) {
        payload.phone = newUser.phone.trim()
      }

      const result = await usersApi.create(payload)
      if (result?.success) {
        setSuccessMsg(`User "${newUser.username}" created successfully!`)
        setNewUser({
          username: '',
          email: '',
          phone: '',
          password: '',
          password2: '',
          role: 'STAFF',
          first_name: '',
          last_name: '',
        })
        await loadUsers()
        setTimeout(() => {
          setShowCreate(false)
          setSuccessMsg('')
        }, 2000)
      } else {
        setError(result?.errors ? JSON.stringify(result.errors) : result?.error || 'Failed to create user')
      }
    } catch (err) {
      setError(err?.message || 'Failed to create user')
    } finally {
      setCreating(false)
    }
  }

  useEffect(() => {
    ;(async () => {
      try {
        await loadUsers()
      } catch {
        // loadUsers already sets fallback state + error
      }
    })()
  }, [])

  return (
    <div>
      <div className="page-header">
        <button className="btn primary" onClick={() => setShowCreate(true)}>
          + Create User
        </button>
        <div className="page-title">
          <h3>User Management</h3>
          <p className="subtitle">Manage system users and their roles</p>
        </div>
      </div>

      <div className="filters">
        <input
          placeholder="Search users..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <button className="btn ghost" onClick={loadUsers} disabled={loading}>
          {loading ? 'Reloading…' : 'Refresh'}
        </button>
      </div>

      {/* User Stats Grid */}
      <div className="stats-grid">
        <StatCard
          label="Total Users"
          value={userStatsData.total}
          accent="#0f3d62"
          icon={UsersIcon}
        />
        <StatCard
          label="Administrators"
          value={userStatsData.admins}
          accent="#dc2626"
          icon={Shield}
        />
        <StatCard
          label="Managers"
          value={userStatsData.managers}
          accent="#2563eb"
          icon={UserCog}
        />
        <StatCard
          label="Staff"
          value={userStatsData.staff}
          accent="#16a34a"
          icon={UserCheck}
        />
      </div>

      {/* Interactive Charts */}
      <div className="grid-2">
        {/* Role Distribution Pie Chart */}
        <div className="panel">
          <div className="panel-head">
            <h3>User Distribution</h3>
            <p className="subtitle">Users by role</p>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={roleDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {roleDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* User Task Performance Bar Chart */}
        <div className="panel">
          <div className="panel-head">
            <h3>Task Performance</h3>
            <p className="subtitle">Tasks per user</p>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={userPerformanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Legend />
                <Bar dataKey="To Do" stackId="a" fill="#64748b" />
                <Bar dataKey="In Progress" stackId="a" fill="#2563eb" />
                <Bar dataKey="Done" stackId="a" fill="#16a34a" />
                <Bar dataKey="Overdue" stackId="a" fill="#dc2626" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="user-modal" onClick={e => e.stopPropagation()}>
            <div className="user-modal-header">
              <h3>Create New User</h3>
              <button className="modal-close" onClick={() => setShowCreate(false)}>&times;</button>
            </div>
            <form onSubmit={createUser} className="user-form">
              <div className="form-section">
                <h4>Account Details</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label>Username <span className="required">*</span></label>
                    <input
                      type="text"
                      placeholder="Enter username"
                      value={newUser.username}
                      onChange={e => setNewUser({ ...newUser, username: e.target.value.trim().toLowerCase() })}
                      required
                      className={newUser.username ? 'valid' : ''}
                    />
                  </div>
                  <div className="form-group">
                    <label>Role <span className="required">*</span></label>
                    <select
                      value={newUser.role}
                      onChange={e => setNewUser({ ...newUser, role: e.target.value })}
                      className="role-select"
                      style={{ borderColor: ROLE_COLORS[newUser.role] }}
                    >
                      <option value="STAFF">Staff Member</option>
                      <option value="MANAGER">Manager</option>
                      <option value="ADMIN">Administrator</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="form-section">
                <h4>Personal Information</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label>First Name</label>
                    <input
                      type="text"
                      placeholder="First name"
                      value={newUser.first_name}
                      onChange={e => setNewUser({ ...newUser, first_name: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Last Name</label>
                    <input
                      type="text"
                      placeholder="Last name"
                      value={newUser.last_name}
                      onChange={e => setNewUser({ ...newUser, last_name: e.target.value })}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Email Address <span className="required">*</span></label>
                  <input
                    type="email"
                    placeholder="email@example.com"
                    value={newUser.email}
                    onChange={e => setNewUser({ ...newUser, email: e.target.value.trim().toLowerCase() })}
                    required
                    className={newUser.email ? 'valid' : ''}
                  />
                </div>
                <div className="form-group">
                  <label>Telephone</label>
                  <input
                    type="tel"
                    placeholder="+256 XXX XXX XXX"
                    value={newUser.phone}
                    onChange={e => setNewUser({ ...newUser, phone: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-section">
                <h4>Security</h4>
                <div className="form-group">
                  <label>Password <span className="required">*</span></label>
                  <input
                    type="password"
                    placeholder="Create a password"
                    value={newUser.password}
                    onChange={e => setNewUser({ ...newUser, password: e.target.value })}
                    onFocus={() => setPasswordFocused(true)}
                    onBlur={() => setPasswordFocused(false)}
                    required
                    minLength={6}
                    className={newUser.password && newUser.password.length >= 6 ? 'valid' : ''}
                  />
                  {newUser.password && (
                    <div className="password-strength">
                      <div className="strength-bar">
                        <div
                          className="strength-fill"
                          style={{
                            width: `${(passwordStrength.strength / 5) * 100}%`,
                            backgroundColor: passwordStrength.color,
                          }}
                        />
                      </div>
                      <span className="strength-label" style={{ color: passwordStrength.color }}>
                        {passwordStrength.label}
                      </span>
                    </div>
                  )}
                </div>
                <div className="form-group">
                  <label>Confirm Password <span className="required">*</span></label>
                  <input
                    type="password"
                    placeholder="Confirm your password"
                    value={newUser.password2}
                    onChange={e => setNewUser({ ...newUser, password2: e.target.value })}
                    required
                    minLength={6}
                    className={
                      newUser.password2
                        ? passwordsMatch
                          ? 'valid match'
                          : 'error'
                        : ''
                    }
                  />
                  {newUser.password2 && !passwordsMatch && (
                    <span className="field-error">Passwords do not match</span>
                  )}
                </div>
              </div>

              {error && <div className="alert error">{error}</div>}
              {successMsg && <div className="alert success">{successMsg}</div>}

              <div className="form-actions">
                <button type="button" className="btn ghost" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn primary"
                  disabled={creating || !canSubmit}
                >
                  {creating ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {error && !showCreate && <div className="alert">{error}</div>}

      <div className="table">
        <div className="row head">
          <span>Name</span>
          <span>Email</span>
          <span>Role</span>
        </div>
        {filteredUsers.map(u => (
          <div className="row" key={u.email}>
            <span>{u.name}</span>
            <span>{u.email}</span>
            <span>
              <span className={`role-chip role-${u.role}`}>
                {ROLE_LABELS[u.role] || u.role}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}