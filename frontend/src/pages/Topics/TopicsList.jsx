import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, BookOpen, ChevronRight, GraduationCap, Library, AlertCircle } from 'lucide-react'
import { topicsApi } from '../../api/api'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'

const STATUS_STYLES = {
  draft:    'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
  pending:  'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  rejected: 'bg-red-50 text-red-600 ring-1 ring-red-200',
}

const STATUS_DOT = {
  draft: 'bg-slate-400', pending: 'bg-amber-400',
  approved: 'bg-emerald-500', rejected: 'bg-red-400',
}

const STATUS_LABEL = {
  draft: 'Qoralama', pending: 'Kutmoqda',
  approved: 'Tasdiqlangan', rejected: 'Rad etilgan',
}

function ProgressBar({ value }) {
  const color = value >= 75 ? 'from-emerald-400 to-emerald-500'
    : value >= 40 ? 'from-blue-400 to-blue-500'
    : 'from-slate-300 to-slate-400'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-gray-500 w-8 text-right">{value}%</span>
    </div>
  )
}

export default function TopicsList() {
  const [topics, setTopics] = useState([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const { isRole, user } = useAuthStore()

  const fetchTopics = async () => {
    setLoading(true)
    try {
      const { data } = await topicsApi.list({ search, status: status || undefined, page, page_size: 10 })
      setTopics(data.items)
      setTotal(data.total)
    } catch {
      toast.error('Mavzularni yuklashda xatolik')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchTopics() }, [search, status, page])

  const totalPages = Math.ceil(total / 10)

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm">
            <GraduationCap size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Diplom mavzulari</h2>
            <p className="text-sm text-gray-400 mt-0.5">Jami <span className="font-semibold text-gray-600">{total}</span> ta mavzu</p>
          </div>
        </div>
        {isRole('kafedra_head', 'admin') && (
          <Link
            to="/topics/catalog"
            className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow-sm hover:shadow-md transition-all"
          >
            <Library size={16} />
            Mavzular katalogi
          </Link>
        )}
        {isRole('student') && !topics.some(t => t.status === 'approved') && (
          <Link
            to="/topics/propose"
            className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow-sm hover:shadow-md transition-all"
          >
            <Plus size={16} />
            Mavzu tavsiya qilish
          </Link>
        )}
        {isRole('student') && !topics.some(t => t.status === 'approved') && (
          <Link
            to="/topics/catalog"
            className="inline-flex items-center gap-2 bg-white border border-indigo-200 hover:bg-indigo-50 text-indigo-600 px-4 py-2.5 rounded-xl text-sm font-semibold shadow-sm transition-all"
          >
            <Library size={16} />
            Katalogdan tanlash
          </Link>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all"
            placeholder="Mavzu qidirish..."
          />
        </div>
        <select
          value={status}
          onChange={e => { setStatus(e.target.value); setPage(1) }}
          className="px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all appearance-none cursor-pointer pr-8"
          style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 10px center' }}
        >
          <option value="">Barcha holat</option>
          <option value="draft">Qoralama</option>
          <option value="pending">Kutmoqda</option>
          <option value="approved">Tasdiqlangan</option>
          <option value="rejected">Rad etilgan</option>
        </select>
      </div>

      {/* Content */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-8 h-8 border-2 border-blue-200 border-t-blue-500 rounded-full animate-spin" />
            <p className="text-sm text-gray-400">Yuklanmoqda...</p>
          </div>
        ) : topics.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center">
              <BookOpen size={28} className="text-gray-300" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-500">Mavzular topilmadi</p>
              <p className="text-xs text-gray-400 mt-1">Qidiruv yoki filtrni o'zgartiring</p>
            </div>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/60">
                <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-400 uppercase tracking-wider">Mavzu</th>
                <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-400 uppercase tracking-wider">Holat</th>
                <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-400 uppercase tracking-wider w-44">Taraqqiyot</th>
                <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-400 uppercase tracking-wider">Yil</th>
                <th className="px-4 py-3.5 w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {topics.map(topic => (
                <tr key={topic.id} className="hover:bg-blue-50/30 transition-colors group">
                  <td className="px-5 py-4 max-w-xs">
                    <p className="text-sm font-semibold text-gray-800 line-clamp-1 group-hover:text-blue-700 transition-colors">
                      {topic.title}
                    </p>
                    {topic.title_en && (
                      <p className="text-xs text-gray-400 line-clamp-1 mt-0.5">{topic.title_en}</p>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[topic.status]}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[topic.status]}`} />
                      {STATUS_LABEL[topic.status]}
                    </span>
                  </td>
                  <td className="px-4 py-4 w-44">
                    <ProgressBar value={topic.progress ?? 0} />
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">
                      {topic.academic_year}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <Link
                      to={`/topics/${topic.id}`}
                      className="w-8 h-8 rounded-lg bg-gray-100 hover:bg-blue-600 flex items-center justify-center text-gray-400 hover:text-white transition-all group-hover:bg-blue-100 group-hover:text-blue-600"
                    >
                      <ChevronRight size={15} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-1.5">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-500 bg-white border border-gray-200 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            ‹
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
            <button
              key={p}
              onClick={() => setPage(p)}
              className={`w-8 h-8 rounded-lg text-sm font-semibold transition-all ${
                p === page
                  ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-sm'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {p}
            </button>
          ))}
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-500 bg-white border border-gray-200 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            ›
          </button>
        </div>
      )}
    </div>
  )
}
