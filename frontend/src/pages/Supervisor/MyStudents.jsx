import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Users, ChevronRight, GraduationCap, CheckCircle, Clock, AlertCircle, Inbox, TrendingUp } from 'lucide-react'
import { usersApi, riskApi } from '../../api/api'
import toast from 'react-hot-toast'

const STATUS_STYLES = {
  draft:    'bg-slate-100 text-slate-600',
  pending:  'bg-amber-50 text-amber-700',
  approved: 'bg-emerald-50 text-emerald-700',
  rejected: 'bg-red-50 text-red-600',
}
const STATUS_LABEL = {
  draft: 'Qoralama', pending: 'Kutmoqda', approved: 'Tasdiqlangan', rejected: 'Rad etilgan',
}

const RISK_COLORS = {
  critical: 'bg-red-50 text-red-700',
  very_high: 'bg-red-50 text-red-700',
  high: 'bg-orange-50 text-orange-700',
  medium: 'bg-amber-50 text-amber-700',
  low: 'bg-emerald-50 text-emerald-700',
}
const RISK_LABELS = {
  critical: 'Juda Yuqori',
  very_high: 'Juda Yuqori',
  high:     'Yuqori',
  medium:   "O'rta",
  low:      'Past',
}

function ProgressBar({ value }) {
  const color = value >= 75 ? 'from-emerald-400 to-emerald-500'
    : value >= 40 ? 'from-blue-400 to-indigo-500'
    : 'from-slate-300 to-slate-400'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-xs font-bold text-gray-500 w-8 text-right">{value}%</span>
    </div>
  )
}

export default function MyStudents() {
  const [students, setStudents] = useState([])
  const [risks, setRisks] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [studentsRes, risksRes] = await Promise.all([
          usersApi.supervisorStudents(),
          riskApi.list(),
        ])
        setStudents(studentsRes.data)

        const riskMap = {}
        risksRes.data.forEach(risk => {
          riskMap[risk.topic_id] = risk
        })

        const missingRisks = studentsRes.data.filter(s => !riskMap[s.topic_id])
        if (missingRisks.length > 0) {
          await Promise.all(
            missingRisks.map(s => riskApi.assess(s.topic_id).catch(() => null))
          )

          await new Promise(r => setTimeout(r, 500))
          const updatedRisks = await riskApi.list()
          updatedRisks.data.forEach(risk => {
            riskMap[risk.topic_id] = risk
          })
        }

        setRisks(riskMap)
      } catch (err) {
        console.error('Error loading data:', err)
        toast.error('Ma\'lumot yuklanmadi')
      } finally {
        setLoading(false)
      }
    }

    loadData()
    window.addEventListener('topic-updated', loadData)
    return () => window.removeEventListener('topic-updated', loadData)
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="w-8 h-8 border-2 border-blue-200 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-sm text-gray-400">Yuklanmoqda...</p>
      </div>
    )
  }

  const pendingReview = students.filter(s => s.stages_submitted > 0).length

  return (
    <div className="space-y-6 max-w-4xl">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-sm">
            <Users size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Mening talabalarim</h2>
            <p className="text-sm text-gray-400 mt-0.5">
              Jami <span className="font-semibold text-gray-600">{students.length}</span> talaba
              {pendingReview > 0 && (
                <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs font-semibold">
                  <AlertCircle size={11} /> {pendingReview} ta ko'rib chiqish kerak
                </span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Empty state */}
      {students.length === 0 && (
        <div className="flex flex-col items-center py-20 gap-3 bg-white rounded-2xl border border-gray-100">
          <Inbox size={36} className="text-gray-200" />
          <p className="text-sm font-medium text-gray-400">Sizga biriktirilgan talabalar yo'q</p>
          <p className="text-xs text-gray-300">Mavzular biriktirilgandan so'ng bu yerda ko'rinadi</p>
        </div>
      )}

      {/* Students list */}
      <div className="space-y-3">
        {students.map(s => (
          <div
            key={s.topic_id}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow p-5"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 min-w-0">
                {/* Avatar */}
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-100 to-purple-200 flex items-center justify-center flex-shrink-0">
                  <GraduationCap size={18} className="text-purple-600" />
                </div>
                <div className="min-w-0">
                  <p className="font-bold text-gray-900 text-sm">{s.student_name}</p>
                  {s.student_email && (
                    <p className="text-xs text-gray-400 mt-0.5 truncate">{s.student_email}</p>
                  )}
                  <p className="text-sm text-gray-600 mt-2 line-clamp-2">{s.topic_title}</p>
                </div>
              </div>

              {/* Status + action */}
              <div className="flex flex-col items-end gap-2 flex-shrink-0">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${STATUS_STYLES[s.status] || 'bg-gray-100 text-gray-500'}`}>
                  {STATUS_LABEL[s.status] || s.status}
                </span>
                <Link
                  to={`/topics/${s.topic_id}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 transition-all"
                >
                  Ko'rish <ChevronRight size={12} />
                </Link>
              </div>
            </div>

            {/* Progress */}
            <div className="mt-4">
              <ProgressBar value={s.progress || 0} />
            </div>

            {/* Stage summary */}
            {(s.stages_total > 0 || risks[s.topic_id]) && (
              <div className="mt-3 flex items-center gap-3 pt-3 border-t border-gray-50 flex-wrap">
                {s.stages_total > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-semibold">
                    <CheckCircle size={13} /> {s.stages_approved}/{s.stages_total} tasdiqlandi
                  </div>
                )}
                {s.stages_submitted > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-amber-600 font-semibold">
                    <Clock size={13} /> {s.stages_submitted} ta ko'rib chiqish kutmoqda
                  </div>
                )}
                {s.stages_rejected > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-red-500 font-semibold">
                    <AlertCircle size={13} /> {s.stages_rejected} ta qaytarilgan
                  </div>
                )}
                {risks[s.topic_id] && (
                  <div className={`flex items-center gap-1.5 text-xs font-semibold px-2 py-1 rounded-full ${RISK_COLORS[risks[s.topic_id].risk_level] || 'bg-gray-100 text-gray-600'}`}>
                    <TrendingUp size={13} />
                    Risk: {RISK_LABELS[risks[s.topic_id].risk_level] || risks[s.topic_id].risk_level}
                    ({Math.round(risks[s.topic_id].risk_score)}%)
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
