import { createContext, useContext, useEffect, useState } from 'react'
import { projectsApi, authApi, tasksApi, dashboardApi } from '../api/api.js'
import {
  LOCAL_PROJECTS_KEY,
  LOCAL_TASKS_KEY,
  DUMMY_PROJECTS,
  DUMMY_TASKS,
  readStoredData,
  writeStoredData,
  normalizeProject,
  normalizeTask,
  computeStats,
} from './appContextUtils.js'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState(computeStats(DUMMY_PROJECTS, DUMMY_TASKS));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadProjects = async () => {
    try {
      const data = await projectsApi.list();
      const list = Array.isArray(data) ? data : data.projects || data.results || [];
      const normalized = list.map(normalizeProject);
      setProjects(normalized);
      writeStoredData(LOCAL_PROJECTS_KEY, normalized);
      // Update project-related stats
      setStats(prev => ({
        ...prev,
        projects: normalized.length,
        projectsCompleted: normalized.filter(p => p.status === 'COMPLETED').length,
        projectsInProgress: normalized.filter(p => p.status === 'IN_PROGRESS').length,
      }));
    } catch (err) {
      console.error('Failed to load projects', err);
      // If backend fails (offline/auth), fall back to last known cache.
      const cached = readStoredData(LOCAL_PROJECTS_KEY, []).map(normalizeProject);
      setProjects(cached);
      setStats(prev => ({ ...prev, projects: cached.length }));
    }
  };

  const loadTasks = async () => {
    try {
      const data = await tasksApi.list();
      const list = Array.isArray(data) ? data : data.tasks || data.results || [];
      const normalized = list.map(normalizeTask);
      setTasks(normalized);
      writeStoredData(LOCAL_TASKS_KEY, normalized);
      // Update task-specific stats only
      setStats(prev => ({
        ...prev,
        tasks: normalized.length,
        todo: normalized.filter(t => t.status === 'TODO').length,
        progress: normalized.filter(t => t.status === 'IN_PROGRESS').length,
        done: normalized.filter(t => t.status === 'DONE').length,
      }));
    } catch (err) {
      console.error('Failed to load tasks', err);
      const storedTasks = readStoredData(LOCAL_TASKS_KEY, DUMMY_TASKS).map(normalizeTask);
      setTasks(storedTasks);
      setStats(prev => computeStats(projects, storedTasks) || prev);
    }
  };

  const loadStats = async () => {
    try {
      const data = await dashboardApi.stats();
      setStats({
        projects: data.projects || 0,
        tasks: data.tasks || 0,
        todo: data.todo || 0,
        progress: data.progress || 0,
        done: data.done || 0,
      });
    } catch (err) {
      console.error('Failed to load dashboard stats', err);
      setStats(computeStats(projects, tasks));
    }
  };

  const loadUser = async () => {
    try {
      const data = await authApi.current();
      setUser(data);
    } catch (err) {
      console.error('Failed to load user', err);
    }
  };

  useEffect(() => {
    async function init() {
      const token = localStorage.getItem('uedcl_access_token');

      if (!token) {
        // Avoid direct cascading state updates inside the effect body.
        await Promise.resolve();

        const storedProjects = readStoredData(LOCAL_PROJECTS_KEY, DUMMY_PROJECTS).map(normalizeProject);
        const storedTasks = readStoredData(LOCAL_TASKS_KEY, DUMMY_TASKS).map(normalizeTask);

        setProjects(storedProjects);
        setTasks(storedTasks);
        setStats(computeStats(storedProjects, storedTasks));
        setLoading(false);
        return;
      }

      // Load data sequentially to ensure stats have both projects and tasks
      await loadProjects();
      await loadTasks();
      await loadUser();
      // Recalculate stats with both loaded
      setStats(prev => ({
        ...prev,
        projects: prev.projects,
        tasks: prev.tasks,
        todo: prev.todo,
        progress: prev.progress,
        done: prev.done,
      }));
      // Check for deadline notifications (catch errors silently)
      try {
        await tasksApi.checkDeadlines();
        await projectsApi.checkDeadlines();
      } catch (err) {
        // Silently ignore - deadline check is non-critical
      }
      setLoading(false);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }

    init();
  }, []);

  // Check for deadline notifications every 5 minutes while app is open
  useEffect(() => {
    const token = localStorage.getItem('uedcl_access_token');
    if (!token) return;

    const checkDeadlines = async () => {
      try {
        await tasksApi.checkDeadlines();
        await projectsApi.checkDeadlines();
      } catch (err) {
        // Silently ignore
      }
    };

    const interval = setInterval(checkDeadlines, 5 * 60 * 1000); // Every 5 minutes

    // Initial check after 30 seconds
    const timer = setTimeout(checkDeadlines, 30 * 1000);

    return () => {
      clearInterval(interval);
      clearTimeout(timer);
    };
  }, []);

  const createProject = async data => {
    const created = await projectsApi.create(data);
    setProjects(prev => [...prev, created]);
    return created;
  };

  const updateProject = async (id, data) => {
    const updated = await projectsApi.update(id, data);
    const normalized = normalizeProject(updated);
    setProjects(prev => {
      const next = prev.map(p => (p.id === id ? normalized : p))
      // Update projects count in stats
      setStats(currentStats => ({
        ...currentStats,
        projects: next.length,
      }))
      return next
    })
    return normalized;
  };

  const deleteProject = async id => {
    await projectsApi.delete(id);
    setProjects(prev => {
      const next = prev.filter(p => p.id !== id)
      setStats(computeStats(next, tasks))
      return next
    })
  };

  const deleteTask = async id => {
    await tasksApi.delete(id);
    setTasks(prev => {
      const next = prev.filter(t => t.id !== id)
      writeStoredData(LOCAL_TASKS_KEY, next)
      setStats(computeStats(projects, next))
      return next
    })
  };

  const updateTask = async (id, data) => {
    try {
      const payload = { ...data }
      // Map projectId to project_id for backend
      if (payload.projectId !== undefined) {
        payload.project_id = payload.projectId
        delete payload.projectId
      }
      if (payload.dueDate !== undefined) {
        payload.due_date = payload.dueDate
        delete payload.dueDate
      }

      const updated = await tasksApi.update(id, payload)

      if (updated?.success === false) {
        return { ok: false, error: updated.error || 'Failed to update task' }
      }

      const task = normalizeTask(updated.task || updated)
      setTasks(prev => {
        const next = prev.map(t => (t.id === id ? task : t))
        // Use getter to access current projects value
        setStats(currentStats => ({
          ...currentStats,
          tasks: next.length,
          todo: next.filter(t => t.status === 'TODO').length,
          progress: next.filter(t => t.status === 'IN_PROGRESS').length,
          done: next.filter(t => t.status === 'DONE').length,
        }))
        return next
      })

      return { ok: true, task }
    } catch (err) {
      console.error('[AppContext] updateTask failed:', err)
      return { ok: false, error: err?.message || 'Failed to update task' }
    }
  };

  const addProject = async data => {
    try {
      const created = await projectsApi.create(data);

      if (created?.success === false) {
        const backendError =
          created.error ||
          (created.errors && typeof created.errors === 'object' ? JSON.stringify(created.errors) : created.errors) ||
          'Failed to create project';

        return { ok: false, error: backendError };
      }

      const project = normalizeProject(created.project || created);
      const nextProjects = [...projects, project];

      setProjects(nextProjects);
      writeStoredData(LOCAL_PROJECTS_KEY, nextProjects);
      setStats(computeStats(nextProjects, tasks));

      return { ok: true, project };
    } catch (err) {
      console.error('[AppContext] addProject failed:', err);
      return { ok: false, error: err?.message || 'Failed to create project' };
    }
  };

  const addTask = async data => {
    try {
      const created = await tasksApi.create(data);

      if (created?.success === false) {
        return { ok: false, error: created.error || 'Failed to create task' };
      }

      const task = normalizeTask(created.task || created);
      setTasks(prev => {
        const nextTasks = [...prev, task];
        writeStoredData(LOCAL_TASKS_KEY, nextTasks);
        return nextTasks;
      });
      setStats(prev => ({ ...prev, tasks: tasks.length + 1 }));

      return { ok: true, task };
    } catch (err) {
      console.error('[AppContext] addTask failed:', err);
      return { ok: false, error: err?.message || 'Failed to create task' };
    }
  };

  return (
    <AppContext.Provider
      value={{
        projects,
        tasks,
        stats,
        user,
        loading,
        createProject,
        addProject,
        updateProject,
        deleteProject,
        deleteTask,
        updateTask,
        addTask,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useApp must be used within AppProvider');
  }
  return ctx;
}
