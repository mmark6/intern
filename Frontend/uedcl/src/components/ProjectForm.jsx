import { useState } from 'react'
import { useApp } from '../context/AppContext.jsx'
import { useToast } from '../context/ToastContext.jsx'
import { useNotifications } from '../context/NotificationContext.jsx'

const STATUS_OPTIONS = [
  { label: 'Planning', value: 'PLANNING' },
  { label: 'In Progress', value: 'IN_PROGRESS' },
  { label: 'On Hold', value: 'ON_HOLD' },
  { label: 'Completed', value: 'COMPLETED' },
]
const PRIORITY_OPTIONS = [
  { label: 'Low', value: 'LOW' },
  { label: 'Medium', value: 'MEDIUM' },
  { label: 'High', value: 'HIGH' },
  { label: 'Critical', value: 'CRITICAL' },
]

export default function ProjectForm({ onClose }) {
  const { addProject } = useApp()
  const toast = useToast()
  const { refresh: refreshNotifications } = useNotifications()
  const [form, setForm] = useState({
    name: '',
    owner: '',
    status: 'PLANNING',
    priority: 'MEDIUM',
    start_date: '',
    end_date: '',
  })
  const [error, setError] = useState('')

  const handleChange = e => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async e => {
    e.preventDefault()

    if (!form.name.trim()) {
      setError('Project name is required.')
      return
    }

    const payload = {
      name: form.name.trim(),
      status: form.status,
      priority: form.priority,
    }
    if (form.owner.trim()) {
      payload.owner = form.owner.trim()
    }
    if (form.start_date) {
      payload.start_date = form.start_date
    }
    if (form.end_date) {
      payload.end_date = form.end_date
    }

    const res = await addProject(payload)

    if (!res.ok) {
      setError(res.error || res.message || 'Unable to save project to backend.')
      return
    }

    toast.success(`Project "${form.name}" created successfully!`)
    // Refresh notifications to show new project notification
    setTimeout(refreshNotifications, 500)
    onClose?.()
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h3>New Project</h3>

      {error && <div className="form-error">{error}</div>}

      <label className="field">
        <span>Project Name</span>
        <input
          type="text"
          name="name"
          value={form.name}
          onChange={handleChange}
          placeholder="e.g. Substation Upgrade"
          autoFocus
        />
      </label>

      <label className="field">
        <span>Owner</span>
        <input
          type="text"
          name="owner"
          value={form.owner}
          onChange={handleChange}
          placeholder="Optional owner"
        />
      </label>

      <div className="field-row">
        <label className="field">
          <span>Status</span>
          <select name="status" value={form.status} onChange={handleChange}>
            {STATUS_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Priority</span>
          <select name="priority" value={form.priority} onChange={handleChange}>
            {PRIORITY_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="field-row">
        <label className="field">
          <span>Start Date</span>
          <input
            type="date"
            name="start_date"
            value={form.start_date}
            onChange={handleChange}
          />
        </label>

        <label className="field">
          <span>End Date (Deadline)</span>
          <input
            type="date"
            name="end_date"
            value={form.end_date}
            onChange={handleChange}
          />
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn primary">Create Project</button>
      </div>
    </form>
  )
}
