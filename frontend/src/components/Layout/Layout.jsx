import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, BookOpen, BarChart3, ShieldAlert,
  MessageSquare, Bell, LogOut, GraduationCap, Menu, X, User,
  Users, Calendar, PlusCircle, Settings,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import useAuthStore from '../../store/authStore'
import { notificationsApi } from '../../api/api'

const NAV_BY_ROLE = {
  admin: [
    { to: '/dashboard',      icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/topics',         icon: BookOpen,         label: 'Mavzular' },
    { to: '/users',          icon: Users,            label: 'Foydalanuvchilar' },
    { to: '/analytics',      icon: BarChart3,        label: 'Analitika' },
    { to: '/risk',           icon: ShieldAlert,      label: 'Risk Monitor' },
    { to: '/meetings',       icon: Calendar,         label: 'Uchrashuvlar' },
    { to: '/messages',       icon: MessageSquare,    label: 'Xabarlar' },
    { to: '/notifications',  icon: Bell,             label: 'Bildirishnomalar' },
  ],
  kafedra_head: [
    { to: '/dashboard',      icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/topics',         icon: BookOpen,         label: 'Mavzular' },
    { to: '/analytics',      icon: BarChart3,        label: 'Analitika' },
    { to: '/messages',       icon: MessageSquare,    label: 'Xabarlar' },
    { to: '/notifications',  icon: Bell,             label: 'Bildirishnomalar' },
  ],
  supervisor: [
    { to: '/dashboard',           icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/supervisor/students', icon: Users,            label: 'Mening talabalarim' },
    { to: '/topics',              icon: BookOpen,         label: 'Mavzular' },
    { to: '/meetings',            icon: Calendar,         label: 'Uchrashuvlar' },
    { to: '/messages',            icon: MessageSquare,    label: 'Xabarlar' },
    { to: '/notifications',       icon: Bell,             label: 'Bildirishnomalar' },
  ],
  student: [
    { to: '/dashboard',      icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/topics',         icon: BookOpen,         label: 'Mavzularim' },
    { to: '/meetings',       icon: Calendar,         label: 'Uchrashuvlar' },
    { to: '/messages',       icon: MessageSquare,    label: 'Xabarlar' },
    { to: '/notifications',  icon: Bell,             label: 'Bildirishnomalar' },
  ],
}

const ROLE_LABELS = {
  admin: 'Admin',
  kafedra_head: "Kafedra boshlig'i",
  supervisor: 'Ilmiy rahbar',
  student: 'Talaba',
}

const ROLE_COLORS = {
  admin: '#ef4444',
  kafedra_head: '#22c55e',
  supervisor: '#8b5cf6',
  student: '#3b82f6',
}

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const loadUnreadCount = async () => {
    try {
      const { data } = await notificationsApi.list()
      setUnreadCount((data || []).filter((n) => !n.is_read).length)
    } catch {
      setUnreadCount(0)
    }
  }

  useEffect(() => {
    loadUnreadCount()

    const timer = setInterval(loadUnreadCount, 30000)
    const onNotificationsUpdated = () => loadUnreadCount()
    window.addEventListener('notifications-updated', onNotificationsUpdated)

    return () => {
      clearInterval(timer)
      window.removeEventListener('notifications-updated', onNotificationsUpdated)
    }
  }, [location.pathname])

  const handleLogout = () => { logout(); navigate('/login') }
  const NAV = NAV_BY_ROLE[user?.role] || NAV_BY_ROLE.student
  const roleColor = ROLE_COLORS[user?.role] || '#6366f1'

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8fafc', fontFamily: "'DM Sans', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap');
        .nav-link { display:flex; align-items:center; gap:10px; padding:10px 14px; border-radius:10px; color:#64748b; font-size:14px; font-weight:500; text-decoration:none; transition:all 0.15s; white-space:nowrap; overflow:hidden; }
        .nav-link:hover { background:#f1f5f9; color:#1e293b; }
        .nav-link.active { background:#eef2ff; color:#4f46e5; font-weight:600; }
        .nav-link.active svg { color:#4f46e5; }
        @media (max-width: 767px) {
          .sidebar-mobile { position:fixed; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:99; transition:opacity 0.2s; }
          .sidebar-mobile.hidden { display:none; }
        }
      `}</style>

      {/* Mobile overlay */}
      {isMobile && collapsed === false && (
        <div 
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 40 }}
          onClick={() => setCollapsed(true)}
        />
      )}

      {/* Sidebar */}
      <aside style={{
        width: isMobile ? (collapsed ? '0' : '280px') : (collapsed ? '64px' : '220px'),
        background: '#fff',
        borderRight: '1px solid #e8ecf4',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease',
        overflow: 'hidden',
        flexShrink: 0,
        position: isMobile ? 'fixed' : 'sticky',
        top: 0,
        height: '100vh',
        zIndex: 50,
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '20px 16px 16px', borderBottom: '1px solid #f1f5f9' }}>
          <div style={{ width: '34px', height: '34px', borderRadius: '10px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <GraduationCap size={18} color="#fff" />
          </div>
          {!collapsed && (
            <div>
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif", lineHeight: 1.2 }}>Diplom</div>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '500' }}>Monitoring</div>
            </div>
          )}
        </div>

        {/* Role badge */}
        {!collapsed && (
          <div style={{ padding: '10px 16px', borderBottom: '1px solid #f1f5f9' }}>
            <span style={{ display: 'inline-flex', padding: '3px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: '600', background: roleColor + '15', color: roleColor }}>
              {ROLE_LABELS[user?.role] || user?.role}
            </span>
          </div>
        )}

        {/* Nav */}
        <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '2px', overflowY: 'auto' }}>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} className="nav-link" title={collapsed ? label : undefined}>
              <Icon size={18} style={{ flexShrink: 0 }} />
              {!collapsed && label}
            </NavLink>
          ))}
        </nav>

        {/* Profile / Logout */}
        <div style={{ padding: '12px 8px', borderTop: '1px solid #f1f5f9' }}>
          {!collapsed && (
            <NavLink to="/profile" className="nav-link" style={{ marginBottom: '4px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <User size={13} color="#6366f1" />
              </div>
              <div style={{ overflow: 'hidden', flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.full_name}</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Profil sozlamalari</div>
              </div>
            </NavLink>
          )}
          <button onClick={handleLogout}
            style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 14px', borderRadius: '10px', border: 'none', background: 'none', cursor: 'pointer', color: '#ef4444', fontSize: '14px', fontWeight: '500' }}
            title={collapsed ? 'Chiqish' : undefined}>
            <LogOut size={18} style={{ flexShrink: 0 }} />
            {!collapsed && 'Chiqish'}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, marginLeft: isMobile ? 0 : undefined }}>
        {/* Top bar */}
        <header style={{ background: '#fff', borderBottom: '1px solid #e8ecf4', padding: isMobile ? '0 12px' : '0 24px', height: '56px', display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0, position: 'sticky', top: 0, zIndex: 10 }}>
          <button onClick={() => setCollapsed(c => !c)}
            style={{ padding: '6px', borderRadius: '8px', border: 'none', background: 'none', cursor: 'pointer', color: '#64748b' }}>
            {isMobile ? (collapsed ? <Menu size={20} /> : <X size={20} />) : (collapsed ? <Menu size={20} /> : <X size={20} />)}
          </button>
          <span style={{ fontSize: isMobile ? '12px' : '13px', color: '#94a3b8', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {new Date().toLocaleDateString('uz-UZ', { day: 'numeric', month: 'long', year: 'numeric' })}
          </span>
          <NavLink to="/notifications" style={{ position: 'relative', padding: '6px', borderRadius: '8px', color: '#64748b', textDecoration: 'none', display: 'flex' }}>
            <Bell size={18} />
            {unreadCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: -4,
                  right: -4,
                  minWidth: '16px',
                  height: '16px',
                  borderRadius: '999px',
                  background: '#ef4444',
                  color: '#fff',
                  fontSize: '10px',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0 4px',
                  lineHeight: 1,
                }}
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </NavLink>
          <NavLink to="/profile" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '10px', background: '#f8fafc', textDecoration: 'none' }}>
            <div style={{ width: '26px', height: '26px', borderRadius: '50%', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <User size={13} color="#6366f1" />
            </div>
            <span style={{ fontSize: isMobile ? '12px' : '13px', fontWeight: '500', color: '#1e293b', maxWidth: isMobile ? '80px' : undefined, overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.full_name?.split(' ')[0]}</span>
          </NavLink>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, padding: isMobile ? '16px' : '24px', overflowY: 'auto', overflowX: 'hidden' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

