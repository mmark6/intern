import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useNotifications } from '../context/NotificationContext.jsx'
import { LayoutDashboard, FolderKanban, ListChecks, Users, LogOut, User, Bell, FileText } from 'lucide-react'
import downloadImage from '../assets/download.jpg'

export default function Layout() {
  const { user, logout } = useAuth()
  const { notifications, unreadCount, markRead, markAllRead } = useNotifications()
  const navigate = useNavigate()
  const [showNotifications, setShowNotifications] = useState(false)
  const links = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/projects', label: 'Projects', icon: FolderKanban },
    { to: '/tasks', label: 'Tasks', icon: ListChecks },
    { to: '/profile', label: 'Profile', icon: User },
    ...(user?.role === 'admin' ? [{ to: '/users', label: 'Users', icon: Users }] : []),
    ...(user?.role === 'admin' || user?.role === 'manager' ? [{ to: '/audit-logs', label: 'Audit Logs', icon: FileText }] : []),
  ]

  const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      await markRead(notification.id)
    }
    setShowNotifications(false)
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img className="brand-mark" src={downloadImage} alt="UEDCL brand" />
          <div>
            <h1>UEDCL</h1>
            <p>Task Tracker</p>
          </div>
        </div>

        <nav>
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end={to === '/'}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <button className="btn ghost" onClick={() => { logout(); navigate('/login') }}>
          <LogOut size={18} />
          Logout
        </button>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <h2>Welcome, {user?.name}</h2>
            <p>{user?.role?.toUpperCase()}</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div className="notification-wrapper" style={{ position: 'relative' }}>
              <button
                className="btn ghost"
                onClick={() => setShowNotifications(!showNotifications)}
                style={{ padding: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <Bell size={20} />
                {unreadCount > 0 && (
                  <span className="notification-badge">{unreadCount}</span>
                )}
              </button>
              {showNotifications && (
                <div className="notification-dropdown">
                  <div className="notification-header">
                    <h3>Notifications</h3>
                    {unreadCount > 0 && (
                      <button className="btn-link" onClick={markAllRead}>
                        Mark all read
                      </button>
                    )}
                  </div>
                  <div className="notification-list">
                    {notifications.length === 0 ? (
                      <p className="notification-empty">No notifications</p>
                    ) : (
                      notifications.slice(0, 10).map((notification) => (
                        <div
                          key={notification.id}
                          className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                          onClick={() => handleNotificationClick(notification)}
                        >
                          <div className="notification-title">{notification.title}</div>
                          <div className="notification-message">{notification.message}</div>
                          <div className="notification-time">
                            {new Date(notification.created_at).toLocaleString()}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="pill">Secure enterprise workspace</div>
          </div>
        </header>

        <section className="content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}