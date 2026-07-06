import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext.jsx'
import { AppProvider } from './context/AppContext.jsx'
import { NotificationProvider } from './context/NotificationContext.jsx'
import { ToastProvider } from './context/ToastContext.jsx'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './Pages/Login'
import Register from './Pages/Register'
import ForgotPassword from './Pages/ForgotPassword'
import Dashboard from './Pages/Dashboard'
import Projects from './Pages/Projects'
import Tasks from './Pages/Task'
import Users from './Pages/Users'
import AuditLogs from './Pages/AuditLogs'
import Profile from './Pages/Profile'

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <NotificationProvider>
          <AppProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />

                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <Layout />
                    </ProtectedRoute>
                  }
                >
                  <Route index element={<Dashboard />} />
                  <Route path="projects" element={<Projects />} />
                  <Route path="tasks" element={<Tasks />} />
                  <Route path="profile" element={<Profile />} />
                  <Route
                    path="users"
                    element={
                      <ProtectedRoute allowedRoles={['admin']}>
                        <Users />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="audit-logs"
                    element={
                      <ProtectedRoute allowedRoles={['admin', 'manager']}>
                        <AuditLogs />
                      </ProtectedRoute>
                    }
                  />
                </Route>

                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </BrowserRouter>
          </AppProvider>
        </NotificationProvider>
      </ToastProvider>
    </AuthProvider>
  )
}