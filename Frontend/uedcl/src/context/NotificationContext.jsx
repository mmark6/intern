import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { notificationsApi } from '../api/api.js'

const NotificationContext = createContext(null)

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(true)

  const loadNotifications = useCallback(async () => {
    try {
      const data = await notificationsApi.list()
      const list = data.notifications || []
      setNotifications(list)
    } catch (err) {
      console.error('Failed to load notifications', err)
    }
  }, [])

  const loadUnreadCount = useCallback(async () => {
    try {
      const data = await notificationsApi.unreadCount()
      setUnreadCount(data.unread_count || 0)
    } catch (err) {
      console.error('Failed to load unread count', err)
    }
  }, [])

  const refresh = useCallback(async () => {
    await Promise.all([loadNotifications(), loadUnreadCount()])
  }, [loadNotifications, loadUnreadCount])

  useEffect(() => {
    async function init() {
      setLoading(true)
      await refresh()
      setLoading(false)
    }

    init()

    // Auto-refresh every 10 seconds to catch new notifications
    const interval = setInterval(refresh, 10000)
    return () => clearInterval(interval)
  }, [refresh])

  const markRead = async (id) => {
    try {
      await notificationsApi.markRead(id)
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (err) {
      console.error('Failed to mark notification as read', err)
    }
  }

  const markAllRead = async () => {
    try {
      await notificationsApi.markAllRead()
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch (err) {
      console.error('Failed to mark all notifications as read', err)
    }
  }

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        loading,
        refresh,
        markRead,
        markAllRead,
      }}
    >
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const ctx = useContext(NotificationContext)
  if (!ctx) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return ctx
}