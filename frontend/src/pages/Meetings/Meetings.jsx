import { useEffect, useState } from 'react'
import { meetingsApi, usersApi } from '../../api/api'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'
import { Calendar, Plus, Trash2, X, MapPin, Clock, CheckCircle, XCircle } from 'lucide-react'

const STATUS_COLORS = {
  planned: { bg: '#eff6ff', color: '#3b82f6', label: 'Rejalashtirilgan' },
  completed: { bg: '#f0fdf4', color: '#22c55e', label: 'Bajarildi' },
  cancelled: { bg: '#fef2f2', color: '#ef4444', label: 'Bekor qilindi' },
}

const S = {
  input: { width: '100%', padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: '10px', fontSize: '14px', outline: 'none', boxSizing: 'border-box' },
  label: { fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '6px', display: 'block' },
}

function CreateMeetingModal({ isSupervisor, onClose, onSuccess }) {
  const [form, setForm] = useState({ title: '', reason: '', scheduled_at: '', duration_min: 30, location: '' })
  const [students, setStudents] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [saving, setSaving] = useState(false)
  const [studentsLoading, setStudentsLoading] = useState(false)

  useEffect(() => {
    if (!isSupervisor) return

    const normalizeStudents = (rows = []) => rows
      .map((s) => ({
        id: s.student_id ?? s.id,
        full_name: s.student_name ?? s.full_name,
      }))
      .filter((s) => s.id && s.full_name)

    const loadStudents = async () => {
      setStudentsLoading(true)
      try {
        const assignedRes = await meetingsApi.myStudents()
        let normalized = normalizeStudents(assignedRes.data || [])

        if (normalized.length === 0) {
          const allStudentsRes = await usersApi.list('student')
          normalized = normalizeStudents(allStudentsRes.data || [])
        }

        setStudents(normalized)
      } catch {
        setStudents([])
      } finally {
        setStudentsLoading(false)
      }
    }

    loadStudents()
  }, [isSupervisor])

  const toggleStudent = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const selectAll = () => setSelectedIds(students.map(s => s.id))
  const clearAll = () => setSelectedIds([])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return toast.error("Uchrashuv nomini kiriting")
    if (!form.scheduled_at) return toast.error("Vaqtni kiriting")
    if (isSupervisor && students.length > 0 && selectedIds.length === 0) {
      return toast.error("Kamida bir talabani tanlang")
    }
    setSaving(true)
    try {
      await meetingsApi.create({
        title: form.title.trim(),
        reason: form.reason || undefined,
        scheduled_at: new Date(form.scheduled_at).toISOString(),
        duration_min: parseInt(form.duration_min),
        location: form.location || undefined,
        attendee_ids: selectedIds,
      })
      toast.success("Uchrashuv yaratildi")
      onSuccess()
      onClose()
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Xatolik")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, overflowY: 'auto', padding: '20px' }}>
      <div style={{ background: '#fff', borderRadius: '20px', padding: '32px', width: '500px', boxShadow: '0 20px 60px rgba(0,0,0,0.15)', position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Yangi uchrashuv</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={S.label}>Uchrashuv nomi <span style={{ color: '#ef4444' }}>*</span></label>
            <input style={S.input} value={form.title} placeholder="Masalan: Haftalik tahlil" required
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
          </div>
          <div>
            <label style={S.label}>Sabab / maqsad</label>
            <textarea style={{ ...S.input, resize: 'vertical', minHeight: '70px' }} value={form.reason}
              placeholder="Uchrashuv sababi yoki maqsadi..."
              onChange={e => setForm(f => ({ ...f, reason: e.target.value }))} />
          </div>
          <div>
            <label style={S.label}>Sana va vaqt <span style={{ color: '#ef4444' }}>*</span></label>
            <input style={S.input} type="datetime-local" value={form.scheduled_at} required
              onChange={e => setForm(f => ({ ...f, scheduled_at: e.target.value }))} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={S.label}>Davomiyligi (daqiqa)</label>
              <input style={S.input} type="number" min="5" max="300" value={form.duration_min}
                onChange={e => setForm(f => ({ ...f, duration_min: e.target.value }))} />
            </div>
            <div>
              <label style={S.label}>Joy</label>
              <input style={S.input} value={form.location} placeholder="110-xona"
                onChange={e => setForm(f => ({ ...f, location: e.target.value }))} />
            </div>
          </div>

          {isSupervisor && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label style={S.label}>Qatnashchilar</label>
                {students.length > 0 && (
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button type="button" onClick={selectAll}
                      style={{ fontSize: '12px', color: '#6366f1', background: 'none', border: 'none', cursor: 'pointer', fontWeight: '500' }}>
                      Barchasini tanlash
                    </button>
                    <button type="button" onClick={clearAll}
                      style={{ fontSize: '12px', color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}>
                      Tozalash
                    </button>
                  </div>
                )}
              </div>

              {studentsLoading ? (
                <div style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '12px 14px', fontSize: '13px', color: '#94a3b8' }}>
                  Talabalar yuklanmoqda...
                </div>
              ) : students.length > 0 ? (
                <>
                  <div style={{ border: '1px solid #e2e8f0', borderRadius: '10px', maxHeight: '160px', overflowY: 'auto' }}>
                    {students.map(s => (
                      <label key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', cursor: 'pointer', borderBottom: '1px solid #f1f5f9', background: selectedIds.includes(s.id) ? '#eef2ff' : '#fff' }}>
                        <input type="checkbox" checked={selectedIds.includes(s.id)} onChange={() => toggleStudent(s.id)}
                          style={{ accentColor: '#6366f1', width: '16px', height: '16px' }} />
                        <span style={{ fontSize: '14px', color: '#1e293b' }}>{s.full_name}</span>
                      </label>
                    ))}
                  </div>
                  {selectedIds.length > 0 && (
                    <p style={{ fontSize: '12px', color: '#6366f1', marginTop: '6px' }}>{selectedIds.length} ta talaba tanlandi</p>
                  )}
                </>
              ) : (
                <div style={{ border: '1px dashed #cbd5e1', borderRadius: '10px', padding: '12px 14px', fontSize: '13px', color: '#94a3b8' }}>
                  Sizga biriktirilgan talabalar topilmadi.
                </div>
              )}
            </div>
          )}

          <div style={{ display: 'flex', gap: '10px', paddingTop: '8px' }}>
            <button type="button" onClick={onClose}
              style={{ flex: 1, padding: '10px', borderRadius: '10px', border: '1px solid #e2e8f0', background: '#fff', cursor: 'pointer', fontSize: '14px', fontWeight: '500', color: '#475569' }}>
              Bekor qilish
            </button>
            <button type="submit" disabled={saving}
              style={{ flex: 1, padding: '10px', borderRadius: '10px', border: 'none', background: saving ? '#a5b4fc' : '#6366f1', color: '#fff', cursor: saving ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: '600' }}>
              {saving ? 'Saqlanmoqda...' : 'Yaratish'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Meetings() {
  const { isRole } = useAuthStore()
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')

  const isSupervisor = isRole('supervisor')

  const load = async () => {
    setLoading(true)
    try {
      const mr = await meetingsApi.listAll()
      setMeetings(mr.data)
    } catch { toast.error("Yuklanmadi") }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id) => {
    if (!confirm("O'chirishni tasdiqlaysizmi?")) return
    try {
      await meetingsApi.delete(id)
      toast.success("O'chirildi")
      setMeetings(ms => ms.filter(m => m.id !== id))
    } catch { toast.error("Xatolik") }
  }

  const handleStatusUpdate = async (meeting, status) => {
    try {
      await meetingsApi.update(meeting.id, { status })
      toast.success("Yangilandi")
      setMeetings(ms => ms.map(m => m.id === meeting.id ? { ...m, status } : m))
    } catch { toast.error("Xatolik") }
  }

  const filtered = statusFilter ? meetings.filter(m => m.status === statusFilter) : meetings

  const upcomingCount = meetings.filter(m => m.status === 'planned' && new Date(m.scheduled_at) > new Date()).length
  const completedCount = meetings.filter(m => m.status === 'completed').length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: "'DM Sans',sans-serif" }}>
      {showModal && (
        <CreateMeetingModal isSupervisor={isSupervisor} onClose={() => setShowModal(false)} onSuccess={load} />
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Uchrashuvlar</h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '3px' }}>Belgilangan va o'tgan uchrashuvlar</p>
        </div>
        {isRole('supervisor', 'admin', 'kafedra_head') && (
          <button onClick={() => setShowModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '14px', fontWeight: '600' }}>
            <Plus size={16} /> Yangi uchrashuv
          </button>
        )}
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '12px' }}>
        {[
          { label: 'Jami uchrashuvlar', value: meetings.length, color: '#6366f1', bg: '#eef2ff' },
          { label: 'Rejalashtirilgan', value: upcomingCount, color: '#3b82f6', bg: '#eff6ff' },
          { label: 'Bajarilgan', value: completedCount, color: '#22c55e', bg: '#f0fdf4' },
        ].map(({ label, value, color, bg }) => (
          <div key={label} style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e8ecf4', padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Calendar size={18} color={color} />
            </div>
            <div>
              <div style={{ fontSize: '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>{value}</div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {[['', 'Barchasi'], ['planned', 'Rejalashtirilgan'], ['completed', 'Bajarilgan'], ['cancelled', 'Bekor qilingan']].map(([val, lbl]) => (
          <button key={val} onClick={() => setStatusFilter(val)}
            style={{ padding: '7px 16px', borderRadius: '8px', border: `1px solid ${statusFilter === val ? '#6366f1' : '#e2e8f0'}`, background: statusFilter === val ? '#eef2ff' : '#fff', color: statusFilter === val ? '#6366f1' : '#64748b', cursor: 'pointer', fontSize: '13px', fontWeight: '500' }}>
            {lbl}
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#94a3b8' }}>Yuklanmoqda...</div>
      ) : filtered.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '60px', background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', color: '#94a3b8' }}>
          <Calendar size={40} style={{ marginBottom: '12px', opacity: 0.3 }} />
          <p>Uchrashuvlar topilmadi</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {filtered.map(m => {
            const dt = new Date(m.scheduled_at)
            const isPast = dt < new Date()
            const sc = STATUS_COLORS[m.status] || STATUS_COLORS.planned
            return (
              <div key={m.id} style={{ background: '#fff', borderRadius: '14px', border: '1px solid #e8ecf4', padding: '18px 22px', display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                {/* Date column */}
                <div style={{ width: '54px', flexShrink: 0, textAlign: 'center', background: '#f8fafc', borderRadius: '12px', padding: '10px 8px' }}>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#1e293b', lineHeight: 1 }}>{dt.getDate()}</div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '3px' }}>
                    {dt.toLocaleDateString('uz-UZ', { month: 'short' })}
                  </div>
                </div>
                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '6px' }}>
                    <span style={{ display: 'inline-flex', padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: '600', background: sc.bg, color: sc.color }}>
                      {sc.label}
                    </span>
                    {isPast && m.status === 'planned' && (
                      <span style={{ fontSize: '12px', color: '#f59e0b', fontWeight: '500' }}>⚠ Vaqt o'tdi</span>
                    )}
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: '700', color: '#1e293b', marginBottom: '4px' }}>
                    {m.title}
                  </div>
                  {m.reason && (
                    <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px', fontStyle: 'italic' }}>
                      📝 {m.reason}
                    </div>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px', color: '#64748b', flexWrap: 'wrap' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <Clock size={13} /> {dt.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })} ({m.duration_min} daqiqa)
                    </span>
                    {m.location && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <MapPin size={13} /> {m.location}
                      </span>
                    )}
                  </div>
                  {m.attendees && m.attendees.length > 0 && (
                    <div style={{ fontSize: '12px', color: '#6366f1', marginTop: '6px' }}>
                      👥 {m.attendees.map(a => a.full_name).join(', ')}
                    </div>
                  )}
                  {m.notes && <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px', fontStyle: 'italic' }}>{m.notes}</p>}
                </div>
                {/* Actions */}
                {isRole('supervisor', 'admin') && (
                  <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
                    {m.status === 'planned' && (
                      <button onClick={() => handleStatusUpdate(m, 'completed')}
                        style={{ padding: '6px 10px', borderRadius: '8px', border: 'none', background: '#f0fdf4', color: '#22c55e', cursor: 'pointer', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle size={13} /> Bajarildi
                      </button>
                    )}
                    {m.status === 'planned' && (
                      <button onClick={() => handleStatusUpdate(m, 'cancelled')}
                        style={{ padding: '6px 10px', borderRadius: '8px', border: 'none', background: '#fef2f2', color: '#ef4444', cursor: 'pointer', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <XCircle size={13} /> Bekor
                      </button>
                    )}
                    <button onClick={() => handleDelete(m.id)}
                      style={{ padding: '6px', borderRadius: '8px', border: 'none', background: '#f8fafc', color: '#94a3b8', cursor: 'pointer' }}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
