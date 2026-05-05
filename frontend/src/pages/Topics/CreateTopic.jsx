import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { topicsApi, usersApi } from '../../api/api'
import toast from 'react-hot-toast'
import { BookOpen, ArrowLeft, GraduationCap, User } from 'lucide-react'

const inputCls = 'w-full px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all'
const labelCls = 'block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5'

export default function CreateTopic() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '', title_en: '', description: '',
    academic_year: `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`,
    supervisor_user_id: '',
  })
  const [supervisors, setSupervisors] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    usersApi.supervisors()
      .then(r => setSupervisors(r.data))
      .catch(() => {})
  }, [])

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return toast.error("Mavzu nomini kiriting")
    if (!/^\d{4}-\d{4}$/.test(form.academic_year)) return toast.error("O'quv yilini to'g'ri kiriting (masalan: 2024-2025)")
    setSaving(true)
    try {
      const payload = {
        title: form.title,
        title_en: form.title_en || undefined,
        description: form.description || undefined,
        academic_year: form.academic_year,
        supervisor_user_id: form.supervisor_user_id ? parseInt(form.supervisor_user_id) : undefined,
      }
      const { data } = await topicsApi.create(payload)
      toast.success("Mavzu qo'shildi!")
      navigate(`/topics/${data.id}`)
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Xatolik yuz berdi")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl">

      {/* Header */}
      <div className="flex items-center gap-3 mb-7">
        <button
          onClick={() => navigate('/topics')}
          className="w-9 h-9 rounded-xl bg-white border border-gray-200 flex items-center justify-center text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-all shadow-sm"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-sm">
            <GraduationCap size={18} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Yangi mavzu qo'shish</h2>
            <p className="text-xs text-gray-400 mt-0.5">Talabalar uchun rasmiy diplom mavzusi yarating</p>
          </div>
        </div>
      </div>

      {/* Form card */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-6 space-y-5">

          <div>
            <label className={labelCls}>
              Mavzu nomi (O'zbekcha) <span className="text-red-400 normal-case">*</span>
            </label>
            <input
              className={inputCls}
              name="title"
              value={form.title}
              onChange={handleChange}
              placeholder="Masalan: Veb-ilovalar xavfsizligini ta'minlash usullari"
              required
            />
          </div>

          <div>
            <label className={labelCls}>Mavzu nomi (Inglizcha)</label>
            <input
              className={inputCls}
              name="title_en"
              value={form.title_en}
              onChange={handleChange}
              placeholder="Methods of ensuring web application security"
            />
          </div>

          <div>
            <label className={labelCls}>Tavsif</label>
            <textarea
              className={`${inputCls} resize-none`}
              rows={4}
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Mavzu haqida qisqacha tavsif..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>
                O'quv yili <span className="text-red-400 normal-case">*</span>
              </label>
              <input
                className={inputCls}
                name="academic_year"
                value={form.academic_year}
                onChange={handleChange}
                placeholder="2024-2025"
                required
              />
            </div>
            <div>
              <label className={labelCls}>
                <span className="flex items-center gap-1"><User size={11} /> Ilmiy rahbar (ixtiyoriy)</span>
              </label>
              <select
                className={`${inputCls} cursor-pointer`}
                name="supervisor_user_id"
                value={form.supervisor_user_id}
                onChange={handleChange}
              >
                <option value="">Keyinroq belgilash</option>
                {supervisors.map(s => (
                  <option key={s.id} value={s.id}>{s.full_name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50/60 border-t border-gray-100">
          <button
            type="button"
            onClick={() => navigate('/topics')}
            className="px-4 py-2.5 rounded-xl text-sm font-semibold text-gray-600 bg-white border border-gray-200 hover:bg-gray-50 transition-all"
          >
            Bekor qilish
          </button>
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm hover:shadow-md transition-all"
          >
            <BookOpen size={15} />
            {saving ? 'Saqlanmoqda...' : 'Mavzu qo\'shish'}
          </button>
        </div>
      </form>
    </div>
  )
}

