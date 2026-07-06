

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
const AUTH_TOKEN_KEY = 'uedcl_access_token'
const REFRESH_TOKEN_KEY = 'uedcl_refresh_token'

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function getAuthToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

function getRefreshToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

// Track if a refresh is in progress to prevent multiple simultaneous refreshes
let isRefreshing = false
let refreshPromise = null

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  try {
    const res = await request('/login/refresh/', {
      method: 'POST',
      body: { refresh_token: refreshToken },
    })
    if (res?.success && res?.access_token) {
      localStorage.setItem(AUTH_TOKEN_KEY, res.access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, res.refresh_token)
      return res.access_token
    }
  } catch (err) {
    console.error('[API] token refresh failed', err)
  }
  return null
}

async function getValidToken() {
  const token = getAuthToken()
  if (token) return token

  // Try to refresh the token if access token is missing/expired
  if (!isRefreshing) {
    isRefreshing = true
    refreshPromise = refreshAccessToken().finally(() => {
      isRefreshing = false
      refreshPromise = null
    })
  }

  return refreshPromise
}

async function request(path, options = {}) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = path.startsWith('http') ? path : `${API_BASE}${normalizedPath}`

  // Skip token refresh for the refresh endpoint itself to prevent infinite loops
  const isRefreshEndpoint = normalizedPath.includes('/login/refresh/')

  const headers = {
    Accept: 'application/json',
    ...(options.headers || {}),
  }

  const accessToken = getAuthToken()
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }

  const init = {
    method: options.method || 'GET',
    mode: 'cors',
    credentials: 'include',
    ...options,
    headers,
  }

  if (options.body && !(options.body instanceof FormData)) {
    init.body = JSON.stringify(options.body)
    headers['Content-Type'] = 'application/json'
  }

  // Keep this quiet in production builds — handy in dev.
  if (import.meta.env.DEV) {
    // eslint-disable-next-line no-console
    console.debug('[API]', init.method, url)
  }

  let response
  try {
    response = await fetch(url, init)
  } catch (err) {
    console.error('[API] network error', url, err)
    throw new ApiError(err.message || 'Network error', 0, null)
  }

  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json') ? await response.json() : null

  // If 401 Unauthorized, try to refresh the token and retry the request
  if (response.status === 401 && !options._retry && !isRefreshEndpoint) {
    const newToken = await getValidToken()
    if (newToken) {
      // Retry the request with the new token
      headers.Authorization = `Bearer ${newToken}`
      init.headers = headers
      options._retry = true
      const retryResponse = await fetch(url, init)
      const retryContentType = retryResponse.headers.get('content-type') || ''
      const retryBody = retryContentType.includes('application/json')
        ? await retryResponse.json()
        : null
      if (!retryResponse.ok) {
        const message = retryBody?.detail || retryBody?.message || retryBody?.error || retryResponse.statusText
        throw new ApiError(message, retryResponse.status, retryBody)
      }
      return retryBody
    }
  }

  if (!response.ok) {
    const message = body?.detail || body?.message || body?.error || response.statusText
    console.error('[API] response error', response.status, message, body)
    throw new ApiError(message, response.status, body)
  }
  return body
}


// Projects — RESTful: list/create at collection, retrieve/update/delete at pk
export const projectsApi = {
  list: () => request('/projects/'),
  retrieve: (id) => request(`/projects/${id}/`),
  create: (data) => request('/projects/', { method: 'POST', body: data }),
  update: (id, data) => request(`/projects/${id}/`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/projects/${id}/`, { method: 'DELETE' }),
  checkDeadlines: () => request('/projects/check-deadlines/', { method: 'POST' }),
}


// Tasks — same RESTful pattern, plus a status helper endpoint
export const tasksApi = {
  list: (params) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request(`/tasks/${qs}`)
  },
  retrieve: (id) => request(`/tasks/${id}/`),
  create: (data) => request('/tasks/', { method: 'POST', body: data }),
  update: (id, data) => request(`/tasks/${id}/`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/tasks/${id}/`, { method: 'DELETE' }),
  setStatus: (id, status) => request(`/tasks/${id}/status/`, { method: 'PATCH', body: { status } }),
  checkDeadlines: () => request('/tasks/check-deadlines/', { method: 'POST' }),
}

// Users
export const usersApi = {
  list: () => request('/users/'),
  create: (data) => request('/users/', { method: 'POST', body: data }),
  retrieve: (id) => request(`/users/${id}/`),
  update: (id, data) => request(`/users/${id}/`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/users/${id}/`, { method: 'DELETE' }),
  current: () => request('/users/me/'),
}


// Comments
export const commentsApi = {
  list: (taskId) => request(`/comments/${taskId ? `?task_id=${taskId}` : ''}`),
  create: (data) => request('/comments/', { method: 'POST', body: data }),
  update: (id, data) => request(`/comments/${id}/`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/comments/${id}/`, { method: 'DELETE' }),
}

// Dashboard
export const dashboardApi = {
  stats: () => request('/dashboard/'),
  projectsBreakdown: () => request('/dashboard/projects-breakdown/'),
  taskStatistics: () => request('/dashboard/task-statistics/'),
  userTasks: (userId) => request(`/dashboard/user-tasks/?user_id=${userId}`),
}


// Auth — kept under /api/login/ to match the existing AuthContext.
// Maps to /api/users/login/, /api/users/register/
export const authApi = {
  login: (data) =>
    request('/login/login/', { method: 'POST', body: data }).then((res) => {
      // Backend returns { access_token, refresh_token, user }
      if (res && res.access_token) {
        localStorage.setItem(AUTH_TOKEN_KEY, res.access_token)
        localStorage.setItem(REFRESH_TOKEN_KEY, res.refresh_token)
      }
      return res
    }),

  register: (data) =>
    request('/login/register/', { method: 'POST', body: data }).then((res) => {
      // Backend returns { success, message, user }
      // Ensure user data is always available in response for AuthContext
      if (res?.success && res?.user) {
        return res
      }
      return res
    }),

  current: () => request('/users/me/'),

  refresh: () => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!refreshToken) {
      return Promise.reject(new Error('No refresh token available'))
    }

    // Backend refresh endpoint lives under /api/login/refresh/
    return request('/login/refresh/', {
      method: 'POST',
      body: { refresh_token: refreshToken },
    }).then((res) => {
      if (res?.success && res?.access_token) {
        localStorage.setItem(AUTH_TOKEN_KEY, res.access_token)
        localStorage.setItem(REFRESH_TOKEN_KEY, res.refresh_token)
      }
      return res
    })
  },

  logout: async () => {
    // Call backend logout first so Authorization header is still present.
    // Backend logout endpoint is under /api/login/logout/.
    try {
      const res = await request('/login/logout/', { method: 'POST' })
      return res
    } catch (err) {
      // If token is already invalid/expired, still clear local tokens.
      console.warn('[API] logout request failed, clearing local tokens anyway', err)
      return null
    } finally {
      localStorage.removeItem(AUTH_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
  },

  // Password reset
  passwordReset: (email) =>
    request('/login/password-reset-request/', { method: 'POST', body: { email } }),

  passwordVerify: (email, code) =>
    request('/login/password-reset-verify/', { method: 'POST', body: { email, code } }),

  passwordChange: (email, resetToken, newPassword) =>
    request('/login/password-reset-confirm/', {
      method: 'POST',
      body: { email, reset_token: resetToken, new_password: newPassword }
    }),
}


// Notifications
export const notificationsApi = {
  list: (params) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request(`/notifications/${qs}`)
  },
  unreadCount: () => request('/notifications/unread-count/'),
  markRead: (id) => request(`/notifications/${id}/read/`, { method: 'POST' }),
  markAllRead: () => request('/notifications/mark-all-read/', { method: 'POST' }),
}


// Audit Logs
export const auditLogsApi = {
  list: (params) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request(`/audit-logs/${qs}`)
  },
}
