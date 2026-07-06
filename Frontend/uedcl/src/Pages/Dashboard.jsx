import { useApp } from '../context/AppContext.jsx'
import StatCard from '../components/StatCard'
import { FolderKanban, ListChecks, LoaderCircle, CheckCircle2, Clock3 } from 'lucide-react'

export default function Dashboard() {
  const { stats, tasks, projects } = useApp()

  const recentTasks = [...(tasks || [])]
    .sort((a, b) => {
      const ad = a?.dueDate || a?.due_date || ''
      const bd = b?.dueDate || b?.due_date || ''
      if (!ad && !bd) return 0
      if (!ad) return 1
      if (!bd) return -1
      return new Date(ad) - new Date(bd)
    })
    .slice(0, 6)

  const topProjects = [...(projects || [])].slice(0, 6)

  // Use stats from AppContext (updates instantly)
  const totalProjects = stats?.projects ?? projects?.length ?? 0

  // Get status color class
  const getStatusClass = (status) => {
    if (!status) return 'status-todo'
    switch (status.toUpperCase()) {
      case 'DONE':
      case 'COMPLETED':
        return 'status-done'
      case 'IN_PROGRESS':
        return 'status-progress'
      case 'TODO':
        return 'status-todo'
      default:
        return 'status-todo'
    }
  }

  // Get status label
  const getStatusLabel = (status) => {
    if (!status) return 'To Do'
    switch (status.toUpperCase()) {
      case 'DONE':
      case 'COMPLETED':
        return 'Done'
      case 'IN_PROGRESS':
        return 'In Progress'
      case 'TODO':
        return 'To Do'
      default:
        return 'To Do'
    }
  }

  return (
    <div>
      <div className="stats-grid">
        <StatCard label="Projects" value={totalProjects} accent="#0f3d62" icon={FolderKanban} />
        <StatCard label="Projects Done" value={stats.projectsCompleted || 0} accent="#1f7a1f" icon={CheckCircle2} />
        <StatCard label="Tasks" value={stats.tasks} accent="#1b7f5a" icon={ListChecks} />
        <StatCard label="To Do" value={stats.todo} accent="#c27a00" icon={Clock3} />
        <StatCard label="In Progress" value={stats.progress} accent="#2b6cb0" icon={LoaderCircle} />
        <StatCard label="Done" value={stats.done} accent="#1f7a1f" icon={CheckCircle2} />
      </div>

      <div className="grid-2">
        {/* Recent Tasks */}
        <div className="panel">
          <div className="panel-head">
            <div className="panel-title-row">
              <h3>Recent Tasks</h3>
            </div>
            <p className="subtitle">Upcoming tasks sorted by due date</p>
          </div>
          <div className="dashboard-cards">
            {recentTasks.length > 0 ? (
              recentTasks.map((task, idx) => (
                <div className="dashboard-card" key={idx}>
                  <div className="dashboard-card-main">
                    <span className="dashboard-card-title">{task.title || task.name}</span>
                    <span className={`dashboard-card-badge ${getStatusClass(task.status)}`}>
                      {getStatusLabel(task.status)}
                    </span>
                  </div>
                                  </div>
              ))
            ) : (
              <div className="empty-state">
                <p>No tasks available</p>
              </div>
            )}
          </div>
        </div>

        {/* Top Projects */}
        <div className="panel">
          <div className="panel-head">
            <div className="panel-title-row">
              <h3>Projects</h3>
            </div>
            <p className="subtitle">Active projects overview</p>
          </div>
          <div className="dashboard-cards">
            {topProjects.length > 0 ? (
              topProjects.map((project, idx) => (
                <div className="dashboard-card" key={idx}>
                  <div className="dashboard-card-main">
                    <span className="dashboard-card-title">{project.name}</span>
                    <span className={`dashboard-card-badge ${getStatusClass(project.status)}`}>
                      {project.status ? project.status.replace(/_/g, ' ') : 'Pending'}
                    </span>
                  </div>
                                  </div>
              ))
            ) : (
              <div className="empty-state">
                <p>No projects available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}