import { useMemo, useState } from 'react'
import { useApp } from '../context/AppContext.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import TaskForm from '../components/TaskForm.jsx'

const STATUS_FILTERS = ['All', 'To Do', 'In Progress', 'Review', 'Blocked', 'Done']

const STATUS_LABELS = {
  TODO: 'To Do',
  IN_PROGRESS: 'In Progress',
  REVIEW: 'Review',
  BLOCKED: 'Blocked',
  DONE: 'Done',
}

const STATUS_CLASS = {
  TODO: 'status-todo',
  IN_PROGRESS: 'status-in-progress',
  REVIEW: 'status-review',
  BLOCKED: 'status-blocked',
  DONE: 'status-done',
}

export default function Tasks() {
  const { tasks, projects, updateTask, user } = useApp()
  const { user: authUser } = useAuth()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('All')
  const [savingTaskId, setSavingTaskId] = useState(null)

  // Get current user role - prefer authUser, fallback to user from AppContext
  const currentUser = authUser || user
  // All authenticated users can create tasks
  const canManageTasks = !!currentUser

  const filtered = useMemo(
    () =>
      tasks.filter(
        t =>
          (status === 'All' || t.statusLabel === status) &&
          `${t.title} ${t.assignee} ${projects.find(p => p.id === t.projectId)?.name || ''}`
            .toLowerCase()
            .includes(query.toLowerCase())
      ),
    [tasks, query, status, projects]
  )

  const handleStatusChange = async (taskId, newStatus) => {
    setSavingTaskId(taskId)
    await updateTask(taskId, { status: newStatus })
    setSavingTaskId(null)
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h3>Tasks</h3>
          <p className="subtitle">Track task progress across projects and update status directly.</p>
        </div>
        <div>
          {canManageTasks && (
            <button className="btn primary" onClick={() => setOpen(true)}>+ New Task</button>
          )}
        </div>
      </div>

      <div className="filters">
        <input className="search-input" placeholder="Search tasks by title, assignee or project..." value={query} onChange={e => setQuery(e.target.value)} />
        <select className="filter-select" value={status} onChange={e => setStatus(e.target.value)}>
          {STATUS_FILTERS.map(option => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </div>

      {open && (
        <div className="modal">
          <div className="modal-card">
            <TaskForm onClose={() => setOpen(false)} />
            <button className="btn ghost" onClick={() => setOpen(false)}>Close</button>
          </div>
        </div>
      )}

      <div className="table">
        <div className="row head">
          <span>Task</span>
          <span>Project</span>
          <span>Assignee</span>
          <span>Due Date</span>
          <span>Status</span>
        </div>
        {filtered.length ? (
          filtered.map(t => (
            <div className="row" key={t.id}>
              <span>{t.title}</span>
              <span>{projects.find(p => p.id === t.projectId)?.name || 'N/A'}</span>
              <span>{t.assignee_role || t.assignee}</span>
              <span>{t.dueDate ? new Date(t.dueDate).toLocaleDateString() : '-'}</span>
              <span>
                <select
                  className={`status-select ${(t.status || '').toLowerCase().replace(/_/g, '-')}`}
                  value={t.status}
                  onChange={e => handleStatusChange(t.id, e.target.value)}
                  disabled={savingTaskId === t.id}
                >
                  <option value="TODO">To Do</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="REVIEW">Review</option>
                  <option value="BLOCKED">Blocked</option>
                  <option value="DONE">Done</option>
                </select>
              </span>
            </div>
          ))
        ) : (
          <div className="row empty">
            <span>No tasks match your filters.</span>
          </div>
        )}
      </div>
    </div>
  )
}