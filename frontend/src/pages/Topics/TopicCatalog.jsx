import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { topicsApi, usersApi } from '../../api/api'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'
import {
  Library, Plus, Clock, User, ChevronRight, CheckCircle,
  ArrowLeft, AlertCircle, Loader2, Users, CalendarDays,
} from 'lucide-react'

const inputCls =
  'w-full px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 ' +
  'placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all'
const labelCls = 'block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5'

// ── Countdown chip ─────────────────────────────────────────────────────────
function Deadline({ iso }) {
  if (!iso) return null
  const diff = new Date(iso) - Date.now()
  const days = Math.ceil(diff / 86400000)
  if (diff < 0) return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full ring-1 ring-red-200">
      <AlertCircle size={11} /> Muddat o'tdi
    </span>
  )
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ring-1 ${
      days <= 3 ? 'text-orange-600 bg-orange-50 ring-orange-200' : 'text-blue-600 bg-blue-50 ring-blue-200'
    }`}>
      <Clock size={11} /> {days} kun qoldi
    </span>
  )
}

// ── Catalog card ───────────────────────────────────────────────────────────
function CatalogCard({ topic, onSelect, isStudent, selecting }) {
  const expired = topic.selection_deadline && new Date(topic.selection_deadline) < Date.now()
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-all p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 leading-snug">{topic.title}</h3>
          {topic.title_en && (
            <p className="text-xs text-gray-400 mt-0.5 line-clamp-1 italic">{topic.title_en}</p>
          )}
        </div>
        <span className="shrink-0 text-xs font-medium text-gray-400 bg-gray-50 px-2 py-0.5 rounded-lg border border-gray-100">
          {topic.academic_year}
        </span>
      </div>

      {topic.description && (
        <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">{topic.description}</p>
      )}

      <div className="flex items-center gap-2 flex-wrap">
        {topic.selection_deadline && <Deadline iso={topic.selection_deadline} />}
        {topic.supervisor_id && (
          <span className="inline-flex items-center gap-1 text-xs text-gray-500 bg-gray-50 px-2 py-0.5 rounded-full ring-1 ring-gray-200">
            <User size={11} /> Rahbar tayinlangan
          </span>
        )}
      </div>

      {isStudent && (
        <button
          disabled={expired || selecting}
          onClick={() => onSelect(topic.id)}
          className={`mt-auto w-full py-2 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
            expired
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm'
          }`}
        >
          {selecting ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
          {expired ? 'Muddat o\'tdi' : 'Bu mavzuni tanlash'}
        </button>
      )}
    </div>
  )
}

// ── Create catalog form (kafedra_head only) ────────────────────────────────
function CreateCatalogForm({ onCreated }) {
  const [form, setForm] = useState({
    title: '', title_en: '', description: '',
    academic_year: `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`,
    supervisor_user_id: '',
    selection_deadline: '',
  })
  const [supervisors, setSupervisors] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    usersApi.supervisors().then(r => setSupervisors(r.data)).catch(() => {})
  }, [])

  const set = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return toast.error('Mavzu nomini kiriting')
    if (!form.supervisor_user_id) return toast.error('Rahbarni tanlang')
    if (!form.selection_deadline) return toast.error('Tanlash muddatini kiriting')
    setSaving(true)
    try {
      const payload = {
        title: form.title,
        title_en: form.title_en || undefined,
        description: form.description || undefined,
        academic_year: form.academic_year,
        supervisor_user_id: parseInt(form.supervisor_user_id),
        selection_deadline: new Date(form.selection_deadline).toISOString(),
      }
      const { data } = await topicsApi.createCatalog(payload)
      toast.success('Katalog mavzu qo\'shildi!')
      setForm({
        title: '', title_en: '', description: '',
        academic_year: `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`,
        supervisor_user_id: '', selection_deadline: '',
      })
      onCreated(data)
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Xatolik yuz berdi')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
      <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
        <Plus size={16} className="text-indigo-500" /> Yangi katalog mavzu
      </h3>

      <div>
        <label className={labelCls}>Mavzu nomi (O'zbekcha) *</label>
        <input className={inputCls} name="title" value={form.title} onChange={set}
          placeholder="Mavzu sarlavhasi..." required />
      </div>

      <div>
        <label className={labelCls}>Mavzu nomi (Inglizcha)</label>
        <input className={inputCls} name="title_en" value={form.title_en} onChange={set}
          placeholder="Topic title in English..." />
      </div>

      <div>
        <label className={labelCls}>Tavsif</label>
        <textarea className={`${inputCls} resize-none`} rows={3} name="description"
          value={form.description} onChange={set} placeholder="Qisqacha tavsif..." />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelCls}>O'quv yili *</label>
          <input className={inputCls} name="academic_year" value={form.academic_year} onChange={set}
            placeholder="2024-2025" required />
        </div>
        <div>
          <label className={labelCls}>Tanlash muddati *</label>
          <input className={inputCls} type="datetime-local" name="selection_deadline"
            value={form.selection_deadline} onChange={set} required />
        </div>
      </div>

      <div>
        <label className={labelCls}>Ilmiy rahbar *</label>
        <select className={inputCls} name="supervisor_user_id" value={form.supervisor_user_id} onChange={set} required>
          <option value="">— Rahbarni tanlang —</option>
          {supervisors.map(s => (
            <option key={s.id} value={s.id}>{s.full_name}</option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={saving}
        className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl flex items-center justify-center gap-2 transition-all shadow-sm"
      >
        {saving ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
        Katalogga qo'shish
      </button>
    </form>
  )
}

// ── Auto-assign panel ──────────────────────────────────────────────────────
function AutoAssignPanel() {
  const [year, setYear] = useState(`${new Date().getFullYear()}-${new Date().getFullYear() + 1}`)
  const [loading, setLoading] = useState(false)

  const run = async () => {
    if (!confirm(`"${year}" o'quv yili uchun avtomatik tayinlashni ishga tushirasizmi?`)) return
    setLoading(true)
    try {
      const { data } = await topicsApi.autoAssign(year)
      toast.success(data.message || 'Tayinlash amalga oshirildi')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Xatolik yuz berdi')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-center justify-between gap-4">
      <div>
        <p className="text-sm font-semibold text-amber-800 flex items-center gap-1.5">
          <Users size={15} /> Avtomatik tayinlash
        </p>
        <p className="text-xs text-amber-600 mt-1">
          Mavzu tanlamagan talablarga mavzu va rahbar avtomatik tayinlanadi
        </p>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <input
          className="px-3 py-2 text-sm border border-amber-300 bg-white rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-400/40 w-28"
          value={year} onChange={e => setYear(e.target.value)} placeholder="2024-2025"
        />
        <button
          onClick={run} disabled={loading}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-semibold rounded-xl flex items-center gap-2 transition-all"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <ChevronRight size={14} />}
          Ishga tushirish
        </button>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function TopicCatalog() {
  const navigate = useNavigate()
  const { isRole, user } = useAuthStore()
  const isStudent = isRole('student')
  const isManager = isRole('kafedra_head', 'admin')

  const [topics, setTopics] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [includeTaken, setIncludeTaken] = useState(false)
  const [loading, setLoading] = useState(false)
  const [selecting, setSelecting] = useState(null) // topic id being selected

  const fetchCatalog = async () => {
    setLoading(true)
    try {
      const { data } = await topicsApi.getCatalog({ include_taken: includeTaken, page, page_size: 12 })
      setTopics(data.items)
      setTotal(data.total)
    } catch {
      toast.error('Katalogni yuklashda xatolik')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchCatalog() }, [includeTaken, page])

  // Real-time: remove topic from list when another student selects it
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${location.host}/ws?token=${token}`)
    ws.onmessage = (e) => {
      let event
      try { event = JSON.parse(e.data) } catch { return }
      if (event.type === 'topic_selected' && !includeTaken) {
        setTopics(prev => prev.filter(t => t.id !== event.topic_id))
        setTotal(prev => Math.max(0, prev - 1))
      }
    }
    ws.onerror = () => ws.close()
    return () => ws.close()
  }, [includeTaken])

  const handleSelect = async (topicId) => {
    setSelecting(topicId)
    try {
      await topicsApi.selectCatalog(topicId)
      toast.success('Mavzu tanlandi! Mavzular ro\'yxatiga o\'tmoqdasiz...')
      setTimeout(() => navigate('/topics'), 1500)
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Xatolik yuz berdi')
    } finally {
      setSelecting(null)
    }
  }

  const handleCreated = (newTopic) => {
    setTopics(prev => [newTopic, ...prev])
    setTotal(t => t + 1)
  }

  const totalPages = Math.ceil(total / 12)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/topics')}
            className="w-9 h-9 rounded-xl bg-white border border-gray-200 flex items-center justify-center text-gray-500 hover:bg-gray-50 transition-all shadow-sm"
          >
            <ArrowLeft size={16} />
          </button>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-sm">
            <Library size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Mavzular katalogi</h2>
            <p className="text-sm text-gray-400 mt-0.5">
              Jami <span className="font-semibold text-gray-600">{total}</span> ta mavzu
            </p>
          </div>
        </div>

        {isManager && (
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={includeTaken}
              onChange={e => { setIncludeTaken(e.target.checked); setPage(1) }}
              className="w-4 h-4 rounded text-indigo-600"
            />
            Tanlangan mavzularni ham ko'rsatish
          </label>
        )}
      </div>

      {/* Auto-assign panel for managers */}
      {isManager && <AutoAssignPanel />}

      <div className={`gap-6 ${isManager ? 'grid grid-cols-1 lg:grid-cols-3' : ''}`}>
        {/* Create form for kafedra_head */}
        {isManager && (
          <div className="lg:col-span-1">
            <CreateCatalogForm onCreated={handleCreated} />
          </div>
        )}

        {/* Topic grid */}
        <div className={isManager ? 'lg:col-span-2' : ''}>
          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400">
              <Loader2 size={28} className="animate-spin" />
            </div>
          ) : topics.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center text-gray-400">
              <Library size={40} className="mb-3 opacity-30" />
              <p className="font-semibold text-gray-500">Katalogda mavzular yo'q</p>
              {isManager && <p className="text-sm mt-1">Chap tarafdan yangi mavzu qo'shing</p>}
              {isStudent && <p className="text-sm mt-1">Kafedra mudiri katalog yaratadiganligi kuting</p>}
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {topics.map(t => (
                  <CatalogCard
                    key={t.id}
                    topic={t}
                    isStudent={isStudent}
                    selecting={selecting === t.id}
                    onSelect={handleSelect}
                  />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 text-sm font-medium rounded-xl border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition-all"
                  >
                    ← Oldingi
                  </button>
                  <span className="text-sm text-gray-500">{page} / {totalPages}</span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-4 py-2 text-sm font-medium rounded-xl border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition-all"
                  >
                    Keyingi →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
