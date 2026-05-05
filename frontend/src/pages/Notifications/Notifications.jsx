import { useEffect, useState } from 'react'
import { notificationsApi } from '../../api/api'
import toast from 'react-hot-toast'
import { Bell, BellOff, CheckCheck, Info, AlertCircle, Calendar, FileText, MessageCircle, Check } from 'lucide-react'

const TYPE_CONFIG = {
  deadline_reminder: { icon: Calendar,      color: '#f59e0b', bg: '#fffbeb', label: 'Muddat eslatmasi' },
  new_task:          { icon: CheckCheck,    color: '#6366f1', bg: '#eef2ff', label: 'Yangi vazifa' },
  file_uploaded:     { icon: FileText,      color: '#0ea5e9', bg: '#f0f9ff', label: 'Fayl yuklandi' },
  comment_added:     { icon: MessageCircle, color: '#22c55e', bg: '#f0fdf4', label: 'Izoh qoldirildi' },
  meeting_scheduled: { icon: Calendar,      color: '#8b5cf6', bg: '#f5f3ff', label: 'Uchrashuv belgilandi' },
  status_changed:    { icon: Info,          color: '#64748b', bg: '#f8fafc', label: "Holat o'zgartirildi" },
}

function NotifCard({ notif, onMarkRead }) {
  const cfg = TYPE_CONFIG[notif.type] || { icon: Bell, color: '#6366f1', bg: '#eef2ff', label: notif.type }
  const Icon = cfg.icon
  const dt = new Date(notif.created_at)

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: '14px', padding: '16px 20px',
      background: notif.is_read ? '#fff' : '#fafbff',
      borderLeft: `3px solid ${notif.is_read ? 'transparent' : cfg.color}`,
      borderBottom: '1px solid #f1f5f9', transition: 'background 0.15s',
    }}>
      <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={18} color={cfg.color} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: notif.is_read ? '500' : '600', color: '#1e293b' }}>{notif.title}</div>
            {notif.body && <div style={{ fontSize: '13px', color: '#64748b', marginTop: '3px' }}>{notif.body}</div>}
            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ padding: '1px 7px', borderRadius: '99px', background: cfg.bg, color: cfg.color, fontSize: '11px', fontWeight: '600' }}>{cfg.label}</span>
              <span>{dt.toLocaleDateString('uz-UZ')} {dt.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          </div>
          {!notif.is_read && (
            <button onClick={() => onMarkRead(notif.id)}
              style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '5px 10px', background: '#f1f5f9', border: 'none', borderRadius: '7px', cursor: 'pointer', fontSize: '12px', color: '#64748b', flexShrink: 0 }}>
              <Check size={12} /> O'qildi
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Notifications() {
  const [notifs, setNotifs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  const emitBadgeRefresh = () => {
    window.dispatchEvent(new Event('notifications-updated'))
  }

  const load = async () => {
    try {
      const { data } = await notificationsApi.list()
      setNotifs(data)
      emitBadgeRefresh()
    } catch { toast.error('Yuklanmadi') }
    finally { setLoading(false) }
  }

  const handleMarkRead = async (id) => {
    try {
      await notificationsApi.markRead(id)
      setNotifs(ns => ns.map(n => n.id === id ? { ...n, is_read: true } : n))
      emitBadgeRefresh()
    } catch { toast.error('Xatolik') }
  }

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllRead()
      setNotifs(ns => ns.map(n => ({ ...n, is_read: true })))
      emitBadgeRefresh()
      toast.success("Hammasi o'qildi deb belgilandi")
    } catch { toast.error('Xatolik') }
  }

  useEffect(() => { load() }, [])

  const unreadCount = notifs.filter(n => !n.is_read).length
  const filtered = filter === 'unread' ? notifs.filter(n => !n.is_read)
    : filter === 'read' ? notifs.filter(n => n.is_read)
    : notifs

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', fontFamily: "'DM Sans',sans-serif" }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Bildirishnomalar</h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '3px' }}>
            {unreadCount > 0 ? `${unreadCount} ta o'qilmagan` : "Barcha o'qilgan"}
          </p>
        </div>
        {unreadCount > 0 && (
          <button onClick={handleMarkAllRead}
            style={{ display: 'flex', alignItems: 'center', gap: '7px', padding: '9px 16px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', cursor: 'pointer', fontSize: '13px', color: '#475569', fontWeight: '500' }}>
            <CheckCheck size={15} /> Hammasini o'qildi deb belgilash
          </button>
        )}
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: '2px', background: '#f1f5f9', padding: '4px', borderRadius: '10px', width: 'fit-content' }}>
        {[['all', 'Barchasi'], ['unread', "O'qilmagan"], ['read', "O'qilgan"]].map(([val, lbl]) => (
          <button key={val} onClick={() => setFilter(val)}
            style={{ padding: '7px 16px', borderRadius: '7px', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: '500', background: filter === val ? '#fff' : 'transparent', color: filter === val ? '#1e293b' : '#64748b', boxShadow: filter === val ? '0 1px 3px rgba(0,0,0,0.06)' : 'none', transition: 'all 0.15s' }}>
            {lbl}
          </button>
        ))}
      </div>

      {/* List */}
      <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#94a3b8' }}>Yuklanmoqda...</div>
        ) : filtered.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '60px', color: '#94a3b8' }}>
            <BellOff size={40} style={{ marginBottom: '12px', opacity: 0.3 }} />
            <p>Bildirishnomalar yo'q</p>
          </div>
        ) : (
          filtered.map(n => <NotifCard key={n.id} notif={n} onMarkRead={handleMarkRead} />)
        )}
      </div>
    </div>
  )
}
