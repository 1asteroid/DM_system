import { useState, useEffect } from 'react'
import { authApi, usersApi } from '../../api/api'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'
import { User, Lock, Save, Eye, EyeOff, Edit2, Phone, Mail, BookOpen } from 'lucide-react'

const ROLE_LABELS = {
  admin: 'Admin', kafedra_head: "Kafedra boshlig'i",
  supervisor: 'Ilmiy rahbar', student: 'Talaba',
}

const S = {
  label: { fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px', display: 'block' },
  input: { width: '100%', padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: '10px', fontSize: '14px', outline: 'none', boxSizing: 'border-box', color: '#1e293b' },
  inputReadonly: { width: '100%', padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: '10px', fontSize: '14px', outline: 'none', boxSizing: 'border-box', color: '#1e293b', background: '#f8fafc', cursor: 'not-allowed' },
  card: { background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', padding: '28px', marginBottom: '20px' },
}

function PasswordField({ label, value, onChange, placeholder }) {
  const [show, setShow] = useState(false)
  return (
    <div>
      <label style={S.label}>{label}</label>
      <div style={{ position: 'relative' }}>
        <input type={show ? 'text' : 'password'} value={value} onChange={onChange}
          placeholder={placeholder} style={{ ...S.input, paddingRight: '40px' }} />
        <button type="button" onClick={() => setShow(s => !s)}
          style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '2px', display: 'flex' }}>
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    </div>
  )
}

export default function Profile() {
  const { user } = useAuthStore()
  const [profileForm, setProfileForm] = useState({ full_name: user?.full_name || '', phone: user?.phone || '' })
  const [profileSaving, setProfileSaving] = useState(false)
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [saving, setSaving] = useState(false)
  const [supervisor, setSupervisor] = useState(null)

  useEffect(() => {
    const loadSupervisor = () => {
      if (user?.role === 'student') {
        usersApi.mySupervisor().then(({ data }) => setSupervisor(data)).catch(() => {})
      }
    }

    loadSupervisor()
    window.addEventListener('topic-updated', loadSupervisor)
    return () => window.removeEventListener('topic-updated', loadSupervisor)
  }, [user?.role])

  const handleProfileSave = async (e) => {
    e.preventDefault()
    if (!profileForm.full_name.trim()) return toast.error("Ism bo'sh bo'lishi mumkin emas")
    setProfileSaving(true)
    try {
      await authApi.updateProfile({
        full_name: profileForm.full_name.trim(),
        phone: profileForm.phone.trim() || null,
      })
      toast.success("Profil muvaffaqiyatli yangilandi")
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Xatolik yuz berdi")
    } finally {
      setProfileSaving(false)
    }
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    if (pwForm.new_password.length < 8) return toast.error("Yangi parol kamida 8 belgi bo'lishi kerak")
    if (pwForm.new_password !== pwForm.confirm) return toast.error("Parollar mos kelmadi")
    setSaving(true)
    try {
      await authApi.changePassword({ old_password: pwForm.old_password, new_password: pwForm.new_password })
      toast.success("Parol muvaffaqiyatli o'zgartirildi")
      setPwForm({ old_password: '', new_password: '', confirm: '' })
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Xatolik yuz berdi")
    } finally {
      setSaving(false)
    }
  }

  const initials = user?.full_name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?'

  return (
    <div style={{ maxWidth: '600px', fontFamily: "'DM Sans',sans-serif" }}>
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Profil</h2>
        <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '3px' }}>Hisob ma'lumotlari va sozlamalar</p>
      </div>

      {/* Avatar */}
      <div style={S.card}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px', paddingBottom: '24px', borderBottom: '1px solid #f1f5f9' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px', fontWeight: '700', color: '#fff', flexShrink: 0 }}>
            {initials}
          </div>
          <div>
            <div style={{ fontSize: '18px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>{user?.full_name}</div>
            <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>{user?.email}</div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '3px 10px', borderRadius: '99px', background: '#eef2ff', color: '#6366f1', fontSize: '12px', fontWeight: '600', marginTop: '6px' }}>
              <User size={11} /> {ROLE_LABELS[user?.role] || user?.role}
            </span>
          </div>
        </div>

        {/* Editable profile form */}
        <form onSubmit={handleProfileSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Edit2 size={15} color="#6366f1" />
            <span style={{ fontSize: '14px', fontWeight: '600', color: '#374151' }}>Ma'lumotlarni tahrirlash</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={S.label}>To'liq ism *</label>
              <input style={S.input} value={profileForm.full_name}
                onChange={e => setProfileForm(f => ({ ...f, full_name: e.target.value }))}
                placeholder="To'liq ismingiz" />
            </div>
            <div>
              <label style={S.label}>Telefon</label>
              <input style={S.input} value={profileForm.phone}
                onChange={e => setProfileForm(f => ({ ...f, phone: e.target.value }))}
                placeholder="+998 90 000 00 00" />
            </div>
            <div>
              <label style={S.label}>Email (o'zgartirilmaydi)</label>
              <input style={S.inputReadonly} value={user?.email || ''} readOnly />
            </div>
            <div>
              <label style={S.label}>Telegram ID</label>
              <input style={S.inputReadonly} value={user?.telegram_id || 'Ulanmagan'} readOnly />
            </div>
          </div>
          <button type="submit" disabled={profileSaving}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '11px', borderRadius: '10px', border: 'none', background: profileSaving ? '#a5b4fc' : '#6366f1', color: '#fff', cursor: profileSaving ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: '600' }}>
            <Save size={15} /> {profileSaving ? 'Saqlanmoqda...' : 'Saqlash'}
          </button>
        </form>
      </div>

      {/* Supervisor contact card — students only */}
      {user?.role === 'student' && supervisor && (
        <div style={S.card}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <User size={16} color="#22c55e" />
            </div>
            <div>
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#1e293b' }}>Ilmiy rahbarim</div>
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>Kontakt ma'lumotlari</div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: '#f8fafc', borderRadius: '10px' }}>
              <User size={15} color="#64748b" />
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>{supervisor.full_name}</span>
            </div>
            {supervisor.email && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: '#f8fafc', borderRadius: '10px' }}>
                <Mail size={15} color="#64748b" />
                <a href={`mailto:${supervisor.email}`} style={{ fontSize: '14px', color: '#6366f1', textDecoration: 'none' }}>{supervisor.email}</a>
              </div>
            )}
            {supervisor.phone && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: '#f8fafc', borderRadius: '10px' }}>
                <Phone size={15} color="#64748b" />
                <a href={`tel:${supervisor.phone}`} style={{ fontSize: '14px', color: '#6366f1', textDecoration: 'none' }}>{supervisor.phone}</a>
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '10px 14px', background: '#f8fafc', borderRadius: '10px' }}>
              <BookOpen size={15} color="#64748b" style={{ marginTop: '2px' }} />
              <span style={{ fontSize: '13px', color: '#64748b' }}>{supervisor.topic_title}</span>
            </div>
          </div>
        </div>
      )}

      {/* Password change card */}
      <div style={S.card}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Lock size={16} color="#6366f1" />
          </div>
          <div>
            <div style={{ fontSize: '16px', fontWeight: '700', color: '#1e293b' }}>Parolni o'zgartirish</div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>Xavfsizlik uchun muntazam yangilab turing</div>
          </div>
        </div>
        <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <PasswordField label="Joriy parol" value={pwForm.old_password}
            onChange={e => setPwForm(f => ({ ...f, old_password: e.target.value }))}
            placeholder="Joriy parolni kiriting" />
          <PasswordField label="Yangi parol" value={pwForm.new_password}
            onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))}
            placeholder="Kamida 8 belgi" />
          <PasswordField label="Yangi parolni tasdiqlang" value={pwForm.confirm}
            onChange={e => setPwForm(f => ({ ...f, confirm: e.target.value }))}
            placeholder="Yangi parolni qayta kiriting" />
          {pwForm.new_password && pwForm.confirm && pwForm.new_password !== pwForm.confirm && (
            <p style={{ fontSize: '12px', color: '#ef4444', marginTop: '-8px' }}>Parollar mos kelmadi</p>
          )}
          <button type="submit" disabled={saving || !pwForm.old_password || !pwForm.new_password}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '11px', borderRadius: '10px', border: 'none', background: (saving || !pwForm.old_password || !pwForm.new_password) ? '#a5b4fc' : '#6366f1', color: '#fff', cursor: (saving || !pwForm.old_password || !pwForm.new_password) ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: '600', opacity: (saving || !pwForm.old_password || !pwForm.new_password) ? 0.7 : 1 }}>
            <Save size={15} /> {saving ? 'Saqlanmoqda...' : "Parolni o'zgartirish"}
          </button>
        </form>
      </div>
    </div>
  )
}
