const LOCAL_PROJECTS_KEY = 'uedcl_local_projects'
const LOCAL_TASKS_KEY = 'uedcl_local_tasks'

const DUMMY_PROJECTS = [
  {
    id: 1,
    name: 'Substation Upgrade',
    owner: 'Local Admin',
    status: 'IN_PROGRESS',
    priority: 'HIGH',
    statusLabel: 'In Progress',
    priorityLabel: 'High',
  },
  {
    id: 2,
    name: 'Transformer Maintenance',
    owner: 'MANAGER',
    status: 'PLANNING',
    priority: 'MEDIUM',
    statusLabel: 'Planning',
    priorityLabel: 'Medium',
  },
  {
    id: 3,
    name: 'Site Safety Audit',
    owner: 'Local Admin',
    status: 'ON_HOLD',
    priority: 'LOW',
    statusLabel: 'On Hold',
    priorityLabel: 'Low',
  },
]

const DUMMY_TASKS = [
  {
    id: 1,
    title: 'Inspect transformer panels',
    project: 1,
    projectId: 1,
    project_name: 'Substation Upgrade',
    assignee: 'Local Admin',
    status: 'TODO',
    due_date: '2026-07-01',
    dueDate: '2026-07-01',
    statusLabel: 'To Do',
  },
  {
    id: 2,
    title: 'Prepare maintenance report',
    project: 2,
    projectId: 2,
    project_name: 'Transformer Maintenance',
    assignee: 'Local Admin',
    status: 'IN_PROGRESS',
    due_date: '2026-07-05',
    dueDate: '2026-07-05',
    statusLabel: 'In Progress',
  },
  {
    id: 3,
    title: 'Gather audit documents',
    project: 3,
    projectId: 3,
    project_name: 'Site Safety Audit',
    assignee: 'Local Admin',
    status: 'DONE',
    due_date: '2026-06-20',
    dueDate: '2026-06-20',
    statusLabel: 'Done',
  },
]

function readStoredData(key, fallback) {
  try {
    const stored = window.localStorage.getItem(key)
    if (stored) return JSON.parse(stored)
  } catch (err) {
    console.warn('Failed to parse local data', key, err)
  }
  return fallback
}

function writeStoredData(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch (err) {
    console.warn('Failed to save local data', key, err)
  }
}

function normalizeProject(project) {
  // Prioritize owner_username over owner (which might be a numeric ID)
  const ownerUsername = project.owner_username ?? project.owner ?? ''
  const ownerRole = project.owner_role || ''
  const ownerDisplay = ownerRole || ownerUsername

  return {
    id: project.id,
    name: project.name,
    owner: ownerDisplay,
    owner_username: ownerUsername,
    owner_role: ownerRole,
    status: project.status || 'PLANNING',
    priority: project.priority || 'MEDIUM',
    statusLabel:
      project.statusLabel ||
      {
        PLANNING: 'Planning',
        IN_PROGRESS: 'In Progress',
        ON_HOLD: 'On Hold',
        COMPLETED: 'Completed',
        CANCELLED: 'Cancelled',
      }[project.status] ||
      'Planning',
    priorityLabel:
      project.priorityLabel ||
      {
        LOW: 'Low',
        MEDIUM: 'Medium',
        HIGH: 'High',
        CRITICAL: 'Critical',
      }[project.priority] ||
      'Medium',
  }
}

function normalizeTask(task) {
  const status = task.status || 'TODO'
  const dueDate = task.due_date || task.dueDate || ''
  const projectId = task.project ?? task.projectId

  // Prefer assignee_username for display, fallback to assignee (ID)
  const assigneeUsername = task.assignee_username || task.assignee || ''
  // Use role name if available
  const assigneeRole = task.assignee_role || ''
  // Display as "username (role)" or just "username" if no role
  const assigneeDisplay = assigneeRole || assigneeUsername

  return {
    id: task.id,
    title: task.title,
    status,
    statusLabel:
      task.statusLabel ||
      {
        TODO: 'To Do',
        IN_PROGRESS: 'In Progress',
        REVIEW: 'Review',
        BLOCKED: 'Blocked',
        DONE: 'Done',
      }[status] ||
      status,
    priority: task.priority || 'MEDIUM',
    due_date: dueDate,
    dueDate,
    assignee: assigneeDisplay,
    assignee_username: assigneeUsername,
    assignee_role: assigneeRole,
    projectId,
    project: projectId,
    project_name: task.project_name || '',
  }
}

function computeStats(projects, tasks) {
  return {
    projects: projects.length,
    projectsCompleted: projects.filter(p => p.status === 'COMPLETED').length,
    projectsInProgress: projects.filter(p => p.status === 'IN_PROGRESS').length,
    tasks: tasks.length,
    todo: tasks.filter(task => task.status === 'TODO').length,
    progress: tasks.filter(task => task.status === 'IN_PROGRESS').length,
    done: tasks.filter(task => task.status === 'DONE').length,
  }
}

export {
  LOCAL_PROJECTS_KEY,
  LOCAL_TASKS_KEY,
  DUMMY_PROJECTS,
  DUMMY_TASKS,
  readStoredData,
  writeStoredData,
  normalizeProject,
  normalizeTask,
  computeStats,
}
