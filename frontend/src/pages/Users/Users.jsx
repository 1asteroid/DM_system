import { useEffect, useState } from 'react'
import { usersApi } from '../../api/api'
import toast from 'react-hot-toast'
import { Users, UserPlus, Search, X, Check, ShieldCheck, GraduationCap, User, BookOpen } from 'lucide-react'

const ROLE_LABELS = {
  admin: 'Admin', kafedra_head: 'Kafedra boshlig\'i',
  supervisor: 'Ilmiy rahbar', student: 'Talaba',
}
const ROLE_COLORS = {
  admin: { bg: '#fef2f2', color: '#ef4444', icon: ShieldCheck },
  kafedra_head: { bg: '#f0fdf4', color: '#22c55e', icon: Check },
  supervisor: { bg: '#f5f3ff', color: '#8b5cf6', icon: BookOpen },
  student: { bg: '#eff6ff', color: '#3b82f6', icon: GraduationCap },
}

const S = {
  label: { fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px', display: 'block' },
  input: { width: '100%', padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: '10px', fontSize: '14px', outline: 'none', boxSizing: 'border-box' },
}

function RoleBadge({ role }) {
  const cfg = ROLE_COLORS[role] || { bg: '#f1f5f9', color: '#64748b', icon: User }
  const Icon = cfg.icon
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '3px 10px', borderRadius: '99px', background: cfg.bg, color: cfg.color, fontSize: '12px', fontWeight: '600' }}>
      <Icon size={11} />
      {ROLE_LABELS[role] || role}
    </span>
  )
}

function AddUserModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'student', kafedra_id: '', group_id: '', student_id: '', academic_rank: '' })
  const [saving, setSaving] = useState(false)
  const [kafedras, setKafedras] = useState([])
  const [groups, setGroups] = useState([])
  const [loadingData, setLoadingData] = useState(true)
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    const loadData = async () => {
      try {
        const [kafRes, grRes] = await Promise.all([usersApi.kafedras(), usersApi.groups()])
        setKafedras(kafRes.data)
        setGroups(grRes.data)
      } catch { toast.error("Ma'lumot yuklanmadi") }
      finally { setLoadingData(false) }
    }
    loadData()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (form.role === 'student' && !form.kafedra_id) {
      toast.error("Talabalar uchun kafedra tanlang")
      return
    }
    if (form.role === 'supervisor' && !form.academic_rank) {
      toast.error("Supervisor uchun unvonini tanlang")
      return
    }

    setSaving(true)
    try {
      const data = {
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        role: form.role,
        kafedra_id: form.kafedra_id ? parseInt(form.kafedra_id) : null,
        group_id: form.group_id ? parseInt(form.group_id) : null,
        student_id: form.student_id || null,
        academic_rank: form.academic_rank || null,
      }
      await usersApi.create(data)
      toast.success("Foydalanuvchi yaratildi")
      onSuccess()
      onClose()
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Xatolik")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: isMobile ? '16px' : '0' }}>
      <div style={{ background: '#fff', borderRadius: isMobile ? '16px' : '20px', padding: isMobile ? '24px' : '32px', width: isMobile ? '100%' : '500px', maxHeight: isMobile ? '95vh' : '90vh', overflow: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h3 style={{ fontSize: isMobile ? '16px' : '18px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Yangi foydalanuvchi</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '4px' }}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={S.label}>To'liq ism <span style={{ color: '#ef4444' }}>*</span></label>
            <input style={S.input} value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
              placeholder="Ism Familiya" required />
          </div>
          <div>
            <label style={S.label}>Email <span style={{ color: '#ef4444' }}>*</span></label>
            <input style={S.input} type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              placeholder="email@example.com" required />
          </div>
          <div>
            <label style={S.label}>Parol <span style={{ color: '#ef4444' }}>*</span></label>
            <input style={S.input} type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder="Kamida 8 belgi" required minLength={8} />
          </div>
          <div>
            <label style={S.label}>Rol <span style={{ color: '#ef4444' }}>*</span></label>
            <select style={{ ...S.input, cursor: 'pointer' }} value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value, kafedra_id: '', group_id: '', student_id: '', academic_rank: '' }))}>
              <option value="student">Talaba</option>
              <option value="supervisor">Ilmiy rahbar</option>
              <option value="kafedra_head">Kafedra boshlig'i</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          {form.role === 'student' && (
            <>
              <div>
                <label style={S.label}>Kafedra <span style={{ color: '#ef4444' }}>*</span></label>
                <select style={{ ...S.input, cursor: 'pointer' }} value={form.kafedra_id} onChange={e => setForm(f => ({ ...f, kafedra_id: e.target.value }))} required>
                  <option value="">Kafedra tanlang</option>
                  {kafedras.map(k => <option key={k.id} value={k.id}>{k.name}</option>)}
                </select>
              </div>
              <div>
                <label style={S.label}>Guruh</label>
                <select style={{ ...S.input, cursor: 'pointer' }} value={form.group_id} onChange={e => setForm(f => ({ ...f, group_id: e.target.value }))}>
                  <option value="">Guruh tanlang (ixtiyoriy)</option>
                  {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                </select>
              </div>
              <div>
                <label style={S.label}>Talaba ID</label>
                <input style={S.input} value={form.student_id} onChange={e => setForm(f => ({ ...f, student_id: e.target.value }))}
                  placeholder="12345 (ixtiyoriy)" />
              </div>
            </>
          )}

          {form.role === 'supervisor' && (
            <>
              <div>
                <label style={S.label}>Unvon <span style={{ color: '#ef4444' }}>*</span></label>
                <select style={{ ...S.input, cursor: 'pointer' }} value={form.academic_rank} onChange={e => setForm(f => ({ ...f, academic_rank: e.target.value }))} required>
                  <option value="">Unvonni tanlang</option>
                  <option value="Professor">Professor</option>
                  <option value="Dotsent">Dotsent</option>
                  <option value="Assistent">Assistent</option>
                  <option value="Assistent-professor">Assistent-professor</option>
                </select>
              </div>
            </>
          )}

          <div style={{ display: 'flex', gap: '10px', paddingTop: '8px' }}>
            <button type="button" onClick={onClose}
              style={{ flex: 1, padding: '10px', borderRadius: '10px', border: '1px solid #e2e8f0', background: '#fff', cursor: 'pointer', fontSize: '14px', fontWeight: '500', color: '#475569' }}>
              Bekor qilish
            </button>
            <button type="submit" disabled={saving || loadingData}
              style={{ flex: 1, padding: '10px', borderRadius: '10px', border: 'none', background: saving || loadingData ? '#a5b4fc' : '#6366f1', color: '#fff', cursor: saving || loadingData ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: '600' }}>
              {saving ? 'Saqlanmoqda...' : 'Yaratish'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function UsersPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await usersApi.list(roleFilter || undefined)
      setUsers(data)
    } catch { toast.error("Yuklanmadi") }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [roleFilter])

  const handleToggleActive = async (u) => {
    try {
      const { data } = await usersApi.deactivate(u.id)
      toast.success(data.message)
      setUsers(us => us.map(x => x.id === u.id ? { ...x, is_active: data.is_active } : x))
    } catch { toast.error("Xatolik") }
  }

  const filtered = users.filter(u =>
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: "'DM Sans',sans-serif" }}>
      {showModal && <AddUserModal onClose={() => setShowModal(false)} onSuccess={load} />}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? '12px' : '0' }}>
        <div>
          <h2 style={{ fontSize: isMobile ? '20px' : '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Foydalanuvchilar</h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '3px' }}>Jami: {users.length} ta</p>
        </div>
        <button onClick={() => setShowModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '14px', fontWeight: '600', width: isMobile ? '100%' : 'auto', justifyContent: isMobile ? 'center' : 'flex-start' }}>
          <UserPlus size={16} /> Yangi foydalanuvchi
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', flexDirection: isMobile ? 'column' : 'row' }}>
        <div style={{ position: 'relative', flex: isMobile ? '1' : '1', minWidth: isMobile ? '100%' : '200px', maxWidth: isMobile ? '100%' : '320px' }}>
          <Search size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Ism yoki email bo'yicha qidirish..."
            style={{ ...S.input, paddingLeft: '36px', width: '100%' }} />
        </div>
        <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)}
          style={{ ...S.input, width: isMobile ? '100%' : 'auto', cursor: 'pointer' }}>
          <option value="">Barcha rollar</option>
          <option value="student">Talabalar</option>
          <option value="supervisor">Ilmiy rahbarlar</option>
          <option value="kafedra_head">Kafedra boshliqlari</option>
          <option value="admin">Adminlar</option>
        </select>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)', gap: '12px' }}>
        {[
          { role: 'student', count: users.filter(u => u.role === 'student').length },
          { role: 'supervisor', count: users.filter(u => u.role === 'supervisor').length },
          { role: 'kafedra_head', count: users.filter(u => u.role === 'kafedra_head').length },
          { role: 'admin', count: users.filter(u => u.role === 'admin').length },
        ].map(({ role, count }) => {
          const cfg = ROLE_COLORS[role]
          const Icon = cfg.icon
          return (
            <div key={role} style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e8ecf4', padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} color={cfg.color} />
              </div>
              <div>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>{count}</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>{ROLE_LABELS[role]}</div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Table / Card Grid */}
      <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#94a3b8' }}>Yuklanmoqda...</div>
        ) : filtered.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '60px', color: '#94a3b8' }}>
            <Users size={40} style={{ marginBottom: '12px', opacity: 0.3 }} />
            <p>Foydalanuvchilar topilmadi</p>
          </div>
        ) : isMobile ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '16px' }}>
            {filtered.map(u => (
              <div key={u.id} style={{ background: '#f8fafc', borderRadius: '12px', padding: '14px', border: '1px solid #e8ecf4' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <User size={14} color="#6366f1" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{u.full_name}</div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{u.email}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <RoleBadge role={u.role} />
                    <span style={{ display: 'inline-flex', padding: '3px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: '600', background: u.is_active ? '#f0fdf4' : '#fef2f2', color: u.is_active ? '#22c55e' : '#ef4444' }}>
                      {u.is_active ? 'Faol' : 'Nofaol'}
                    </span>
                  </div>
                  <button onClick={() => handleToggleActive(u)}
                    style={{ padding: '5px 12px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', cursor: 'pointer', fontSize: '11px', fontWeight: '500', color: u.is_active ? '#ef4444' : '#22c55e', whiteSpace: 'nowrap' }}>
                    {u.is_active ? 'Bloklash' : 'Faollashtirish'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #f1f5f9', background: '#f8fafc' }}>
                {['Foydalanuvchi', 'Email', 'Rol', 'Holat', 'Amallar'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '12px 16px', fontSize: '12px', fontWeight: '600', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(u => (
                <tr key={u.id} style={{ borderBottom: '1px solid #f8fafc' }}>
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <User size={14} color="#6366f1" />
                      </div>
                      <span style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b' }}>{u.full_name}</span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: '13px', color: '#64748b' }}>{u.email}</td>
                  <td style={{ padding: '14px 16px' }}><RoleBadge role={u.role} /></td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{ display: 'inline-flex', padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: '600', background: u.is_active ? '#f0fdf4' : '#fef2f2', color: u.is_active ? '#22c55e' : '#ef4444' }}>
                      {u.is_active ? 'Faol' : 'Nofaol'}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <button onClick={() => handleToggleActive(u)}
                      style={{ padding: '6px 14px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', cursor: 'pointer', fontSize: '12px', fontWeight: '500', color: u.is_active ? '#ef4444' : '#22c55e' }}>
                      {u.is_active ? 'Bloklash' : 'Faollashtirish'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
