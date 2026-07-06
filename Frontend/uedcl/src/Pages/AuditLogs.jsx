import { useEffect, useMemo, useState } from 'react'
import { auditLogsApi } from '../api/api.js'
import { Download } from 'lucide-react'

const ACTION_LABELS = {
  LOGIN: 'logged into the system',
  LOGOUT: 'logged out of the system',
  CREATE: 'created',
  UPDATE: 'updated',
  DELETE: 'deleted',
  VIEW: 'viewed',
  STATUS: 'changed status of',
}

const TARGET_TYPE_LABELS = {
  USER: 'user',
  PROJECT: 'project',
  TASK: 'task',
  COMMENT: 'comment',
}

const fallbackLogs = [
  { id: 1, username: 'admin', action: 'LOGIN', target_type: 'USER', target_name: 'admin@uedcl.co.ug', ip_address: '127.0.0.1', timestamp: new Date().toISOString(), description: 'User logged in' },
  { id: 2, username: 'manager', action: 'CREATE', target_type: 'PROJECT', target_name: 'Website Redesign', ip_address: '127.0.0.1', timestamp: new Date().toISOString(), description: 'Created new project' },
]

function normalizeLogs(payload) {
  if (!payload) return []
  if (Array.isArray(payload)) return payload
  if (payload.results) return payload.results
  if (payload.data) return payload.data
  if (payload.audit_logs) return payload.audit_logs
  if (payload.logs) return payload.logs
  return []
}

function normalizeLog(log) {
  return {
    id: log.id,
    username: log.username || log.user?.username || 'Unknown',
    action: log.action,
    target_type: log.target_type,
    target_id: log.target_id,
    target_name: log.target_name,
    description: log.description,
    ip_address: log.ip_address,
    user_agent: log.user_agent,
    timestamp: log.timestamp || log.created_at,
  }
}

function formatActionStatement(log) {
  const user = log.username || 'Unknown'
  const action = ACTION_LABELS[log.action] || log.action?.toLowerCase() || 'performed an action'
  const targetType = TARGET_TYPE_LABELS[log.target_type] || log.target_type || ''
  const targetName = log.target_name ? ` "${log.target_name}"` : ''
  const target = targetType ? `${targetType}${targetName}` : log.description || ''

  if (log.action === 'LOGIN') {
    return `${user} ${action}`
  } else if (log.action === 'LOGOUT') {
    return `${user} ${action}`
  } else if (target) {
    return `${user} ${action} ${target}`
  } else {
    return `${user} ${action}`
  }
}

export default function AuditLogs() {
  const [logs, setLogs] = useState(fallbackLogs)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [userFilter, setUserFilter] = useState('All')

  const loadLogs = async () => {
    setLoading(true)
    setError('')

    try {
      const result = await auditLogsApi.list()
      // eslint-disable-next-line no-console
      console.log('Audit logs result:', result)
      const list = normalizeLogs(result)

      if (list.length) {
        setLogs(list.map(normalizeLog))
        setError('')
      } else {
        setLogs(fallbackLogs)
        setError('No audit logs found')
      }
    } catch (err) {
      console.error('Failed to load audit logs', err)
      setLogs(fallbackLogs)
      setError('Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }

  // Get unique users for filter dropdown
  const users = useMemo(() => {
    const userSet = new Set(logs.map(log => log.username).filter(Boolean))
    return ['All', ...Array.from(userSet).sort()]
  }, [logs])

  // Group logs by user
  const groupedLogs = useMemo(() => {
    const filtered = logs.filter(log => {
      const matchesSearch = !search ||
        `${log.username} ${log.target_name} ${log.description} ${log.ip_address}`
          .toLowerCase()
          .includes(search.toLowerCase())
      const matchesUser = userFilter === 'All' || log.username === userFilter
      return matchesSearch && matchesUser
    })

    const grouped = {}
    filtered.forEach(log => {
      const username = log.username || 'Unknown'
      if (!grouped[username]) {
        grouped[username] = []
      }
      grouped[username].push(log)
    })

    // Sort logs within each group by timestamp descending (newest first)
    Object.keys(grouped).forEach(username => {
      grouped[username].sort((a, b) => {
        const dateA = new Date(a.timestamp)
        const dateB = new Date(b.timestamp)
        return dateB - dateA // Newest logs first
      })
    })

    // Sort groups by most recent activity
    return Object.keys(grouped).sort((a, b) => {
      const aTime = grouped[a][0]?.timestamp || ''
      const bTime = grouped[b][0]?.timestamp || ''
      return new Date(bTime) - new Date(aTime)
    }).map(username => ({
      username,
      logs: grouped[username],
    }))
  }, [logs, search, userFilter])

  const formatTimestamp = (ts) => {
    if (!ts) return ''
    const date = new Date(ts)
    if (isNaN(date.getTime())) return ts
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Export to Excel (CSV format)
  const exportToExcel = () => {
    // Get all logs (not just filtered) for export
    const allLogs = logs.map(log => ({
      'Timestamp': formatTimestamp(log.timestamp),
      'User': log.username || 'Unknown',
      'Action': log.action || '',
      'Target Type': log.target_type || '',
      'Target Name': log.target_name || '',
      'Description': log.description || '',
      'IP Address': log.ip_address || '',
    }))

    if (allLogs.length === 0) {
      alert('No data to export')
      return
    }

    // Create CSV content
    const headers = ['Timestamp', 'User', 'Action', 'Target Type', 'Target Name', 'Description', 'IP Address']
    const csvRows = [headers.join(',')]

    allLogs.forEach(row => {
      const values = headers.map(header => {
        const value = row[header] || ''
        // Escape quotes and wrap in quotes if contains comma
        const escaped = String(value).replace(/"/g, '""')
        return escaped.includes(',') ? `"${escaped}"` : escaped
      })
      csvRows.push(values.join(','))
    })

    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  useEffect(() => {
    loadLogs()
  }, [])

  return (
    <div>
      <div className="page-head">
        <div>
          <h3>Audit Logs</h3>
          <p className="subtitle">Track user activities and system events.</p>
        </div>
        <div>
          <button className="btn ghost" onClick={exportToExcel} disabled={loading || logs.length === 0}>
            <Download size={16} />
            Export
          </button>
          <button className="btn ghost" onClick={loadLogs} disabled={loading}>
            {loading ? 'Reloading...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="filters">
        <input
          className="search-input"
          placeholder="Search by user, target or description..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="filter-select"
          value={userFilter}
          onChange={e => setUserFilter(e.target.value)}
        >
          {users.map(user => (
            <option key={user} value={user}>
              {user === 'All' ? 'All Users' : user}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="alert">{error}</div>}

      <div className="audit-groups">
        {groupedLogs.length > 0 ? (
          groupedLogs.map(group => (
            <div className="audit-group" key={group.username}>
              <div className="audit-group-header">
                <span className="audit-user">{group.username}</span>
                <span className="audit-count">{group.logs.length} action{group.logs.length !== 1 ? 's' : ''}</span>
              </div>
              <div className="audit-actions">
                {group.logs.map(log => (
                  <div className="audit-action" key={log.id}>
                    <span className="audit-time">{formatTimestamp(log.timestamp)}</span>
                    <span className="audit-statement">
                      {formatActionStatement(log)}
                    </span>
                    {log.ip_address && (
                      <span className="audit-ip">from {log.ip_address}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <p>No audit logs match your filters.</p>
          </div>
        )}
      </div>
    </div>
  )
}