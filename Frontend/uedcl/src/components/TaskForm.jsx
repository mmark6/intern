import { useState, useEffect } from 'react'
import { useApp } from '../context/AppContext.jsx'
import { useToast } from '../context/ToastContext.jsx'
import { useNotifications } from '../context/NotificationContext.jsx'
import { usersApi } from '../api/api.js'

const STATUS_OPTIONS = [
  { label: 'To Do', value: 'TODO' },
  { label: 'In Progress', value: 'IN_PROGRESS' },
  { label: 'Review', value: 'REVIEW' },
  { label: 'Done', value: 'DONE' },
  { label: 'Blocked', value: 'BLOCKED' },
]

export default function TaskForm({ onClose }) {
  const { projects, addTask } = useApp()
  const toast = useToast()
  const { refresh: refreshNotifications } = useNotifications()
  const [users, setUsers] = useState([])
  const [form, setForm] = useState({ title: '', projectId: projects[0]?.id || '', assignee: '', status: 'TODO', dueDate: '' })
  const [error, setError] = useState('')

  // Fetch all users for assignee dropdown
  useEffect(() => {
    usersApi.list().then(data => {
      const list = Array.isArray(data) ? data : data.users || data.results || []
      setUsers(list)
    }).catch(() => {
      // If API fails, fall back to empty list
      setUsers([])
    })
  }, [])

  const submit = async e => {
    e.preventDefault()
    if (!form.title.trim()) {
      setError('Task title is required.')
      return
    }
    if (!form.projectId) {
      setError('Please select a project for the task.')
      return
    }
    if (!form.dueDate) {
      setError('Due date is required.')
      return
    }

    const payload = {
      title: form.title.trim(),
      project_id: form.projectId,
      status: form.status,
      due_date: form.dueDate,
    }
    if (form.assignee) {
      payload.assignee_id = Number(form.assignee)
    }

    let res
    try {
      res = await addTask(payload)
    } catch (e) {
      // If addTask throws, show something useful
      console.error('[TaskForm] addTask threw', e)
      setError(e?.message || 'Unable to save task to backend.')
      return
    }

    if (!res.ok) {
      console.error('[TaskForm] addTask failed response:', res)
      const status = res?.status
      const payload = res?.payload || res?.error || res
      setError(
        typeof res?.message === 'string'
          ? res.message
          : `Unable to save task to backend (status ${status || 'unknown'}).`
      )
      console.error('[TaskForm] addTask error payload:', payload)
      return
    }

    toast.success(`Task "${form.title}" created successfully!`)
    // Refresh notifications to show new task notification
    setTimeout(refreshNotifications, 500)
    onClose?.()
  }

  return (
    <form className="form" onSubmit={submit}>
      <h3>Create Task</h3>

      {error && <div className="form-error">{error}</div>}

      <label className="field">
        <span>Task Title</span>
        <input
          placeholder="Task title"
          value={form.title}
          onChange={e => setForm({ ...form, title: e.target.value })}
          required
        />
      </label>

      <label className="field">
        <span>Project</span>
        <select value={form.projectId} onChange={e => setForm({ ...form, projectId: Number(e.target.value) })}>
          <option value="">Select project</option>
          {projects.map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Assignee</span>
        <select value={form.assignee} onChange={e => setForm({ ...form, assignee: e.target.value })}>
          <option value="">Select assignee (optional)</option>
          {users.map(u => (
            <option key={u.id} value={u.id}>{u.username} - {(u.role_name || 'No role').toUpperCase()}</option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Status</span>
        <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
          {STATUS_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Due Date</span>
        <input type="date" value={form.dueDate} onChange={e => setForm({ ...form, dueDate: e.target.value })} required />
      </label>

      <div className="form-actions">
        <button className="btn primary">Save Task</button>
      </div>
    </form>
  )
}