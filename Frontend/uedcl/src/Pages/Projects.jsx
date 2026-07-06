import { useMemo, useState } from 'react'
import { useApp } from '../context/AppContext.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import ProjectForm from '../components/ProjectForm.jsx'

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

export default function Projects() {
  const { projects, updateProject, deleteProject, user } = useApp()
  const { user: authUser } = useAuth()
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [savingProjectId, setSavingProjectId] = useState(null)

  // Get current user role - prefer authUser, fallback to user from AppContext
  const currentUser = authUser || user
  const userRole = currentUser?.role || currentUser?.role_name || 'staff'
  const canManageProjects = userRole === 'admin' || userRole === 'manager'

  const filteredProjects = useMemo(
    () => projects.filter(project => {
      const query = search.trim().toLowerCase()
      if (!query) return true
      return [
        project.name,
        project.owner,
        project.statusLabel || project.status,
        project.priorityLabel || project.priority,
      ]
        .join(' ')
        .toLowerCase()
        .includes(query)
    }),
    [projects, search]
  )

  const handleStatusChange = async (projectId, status) => {
    setSavingProjectId(projectId)
    await updateProject(projectId, { status })
    setSavingProjectId(null)
  }

  const handlePriorityChange = async (projectId, priority) => {
    setSavingProjectId(projectId)
    await updateProject(projectId, { priority })
    setSavingProjectId(null)
  }

  const handleDelete = async projectId => {
    const confirmed = window.confirm('Delete this project? This action cannot be undone.')
    if (!confirmed) return
    await deleteProject(projectId)
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h3>Projects</h3>
          <p className="subtitle">Browse projects and create new plans for your team.</p>
        </div>
        <div className="filters">
          <input
            className="search-input"
            placeholder="Search projects by name or owner..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          {canManageProjects && (
            <button className="btn primary" onClick={() => setOpen(true)}>+ New Project</button>
          )}
        </div>
      </div>

      {open && (
        <div className="modal">
          <div className="modal-card">
            <ProjectForm onClose={() => setOpen(false)} />
            <button className="btn ghost" onClick={() => setOpen(false)}>Close</button>
          </div>
        </div>
      )}

      <div className="table">
        <div className="row head">
          <span>Name</span>
          <span>Owner</span>
          <span>Status</span>
          <span>Priority</span>
          <span>Actions</span>
        </div>
        {filteredProjects.length ? (
          filteredProjects.map(project => (
            <div className="row" key={project.id}>
              <span>{project.name}</span>
              <span>{project.owner}</span>
              <span>
                <select
                  className={`status-select ${(project.status || '').toLowerCase().replace(/_/g, '-')}`}
                  value={project.status}
                  onChange={e => handleStatusChange(project.id, e.target.value)}
                  disabled={savingProjectId === project.id}
                >
                  {STATUS_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </span>
              <span>
                <select
                  className={`priority-select ${(project.priority || '').toLowerCase()}`}
                  value={project.priority}
                  onChange={e => handlePriorityChange(project.id, e.target.value)}
                  disabled={savingProjectId === project.id}
                >
                  {PRIORITY_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </span>
              <span>
                {canManageProjects && (
                  <button className="btn ghost" type="button" onClick={() => handleDelete(project.id)}>
                    Delete
                  </button>
                )}
              </span>
            </div>
          ))
        ) : (
          <div className="row empty">
            <span>No projects match your search.</span>
          </div>
        )}
      </div>
    </div>
  )
}