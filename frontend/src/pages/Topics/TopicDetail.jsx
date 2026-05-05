import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { topicsApi, stagesApi, filesApi, tasksApi, usersApi } from '../../api/api'
import toast from 'react-hot-toast'
import { CheckCircle, Clock, XCircle, Upload, Plus, Trash2, X, UserCheck, ArrowLeft, FileText, ListTodo, Layers, Lock, MessageSquare, Download } from 'lucide-react'
import useAuthStore from '../../store/authStore'

const STAGE_STATUS_STYLES = {
  not_started: 'bg-slate-100 text-slate-500',
  in_progress:  'bg-blue-50 text-blue-600',
  submitted:    'bg-amber-50 text-amber-600',
  approved:     'bg-emerald-50 text-emerald-700',
  rejected:     'bg-red-50 text-red-600',
}
const STAGE_STATUS_DOT = {
  not_started: 'bg-slate-300',
  in_progress: 'bg-blue-400',
  submitted: 'bg-amber-400',
  approved: 'bg-emerald-500',
  rejected: 'bg-red-400',
}
const STAGE_STATUS_LABEL = {
  not_started: 'Boshlanmagan', in_progress: 'Jarayonda',
  submitted: '', approved: 'Tasdiqlandi', rejected: 'Rad etildi',
}

const STATUS_STYLES = {
  draft:    'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
  pending:  'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  rejected: 'bg-red-50 text-red-600 ring-1 ring-red-200',
}
const STATUS_LABEL = { draft: 'Qoralama', pending: 'Kutmoqda', approved: 'Tasdiqlangan', rejected: 'Rad etilgan' }

const inputCls = 'w-full px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all'

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="text-base font-bold text-gray-900">{title}</h3>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors">
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export default function TopicDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isRole, user } = useAuthStore()
  const [topic, setTopic] = useState(null)
  const [stages, setStages] = useState([])
  const [files, setFiles] = useState([])
  const [tasks, setTasks] = useState([])
  const [tab, setTab] = useState('stages')
  const [loading, setLoading] = useState(true)
  const [supervisors, setSupervisors] = useState([])
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showApproveModal, setShowApproveModal] = useState(false)
  const [approveSupervisorId, setApproveSupervisorId] = useState('')
  const [showStageModal, setShowStageModal] = useState(false)
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [reviewModal, setReviewModal] = useState({ open: false, stageId: null })
  const [reviewComment, setReviewComment] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const load = async () => {
    try {
      const [t, s, f, tk] = await Promise.all([
        topicsApi.get(id),
        stagesApi.list(id),
        filesApi.list(id),
        tasksApi.list(id),
      ])
      setTopic(t.data)
      setStages(s.data)
      setFiles(f.data)
      setTasks(tk.data)
    } catch {
      toast.error('Ma\'lumot yuklashda xatolik')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    if (isRole('kafedra_head', 'admin')) {
      usersApi.list('supervisor').then(r => setSupervisors(r.data)).catch(() => {})
    }
  }, [id])

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      await filesApi.upload(id, formData)
      toast.success('Fayl yuklandi')
      load()
    } catch { toast.error('Yuklash xatoligi') }
  }

  const handleReviewSubmit = async (approved) => {
    try {
      await stagesApi.review(id, reviewModal.stageId, { approved, comment: reviewComment || undefined })
      toast.success(approved ? 'Bosqich tasdiqlandi' : 'Bosqich qaytarildi')
      setReviewModal({ open: false, stageId: null })
      setReviewComment('')
      load()
    } catch { toast.error('Xatolik') }
  }

  const handleStageFileUpload = async (e, stageId) => {
    const file = e.target.files[0]
    if (!file) return
    const MAX_BYTES = 20 * 1024 * 1024
    if (file.size > MAX_BYTES) {
      toast.error('Fayl hajmi 20 MB dan oshmasligi kerak')
      e.target.value = ''
      return
    }
    const formData = new FormData()
    formData.append('file', file)
    try {
      await filesApi.upload(id, formData, stageId)
      toast.success('Fayl yuklandi va ko\'rib chiqishga yuborildi')
      load()
    } catch (err) { toast.error(err?.response?.data?.detail || 'Yuklash xatoligi') }
    e.target.value = ''
  }

  const handleToggleTask = async (task) => {
    try {
      await tasksApi.update(id, task.id, { is_done: !task.is_done })
      load()
    } catch { toast.error('Xatolik') }
  }

  const emitTopicUpdated = () => window.dispatchEvent(new Event('topic-updated'))

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-24 gap-3">
      <div className="w-8 h-8 border-2 border-blue-200 border-t-blue-500 rounded-full animate-spin" />
      <p className="text-sm text-gray-400">Yuklanmoqda...</p>
    </div>
  )
  if (!topic) return (
    <div className="flex flex-col items-center justify-center py-24 gap-2">
      <p className="text-sm font-medium text-gray-500">Mavzu topilmadi</p>
    </div>
  )

  const progressColor = topic.progress >= 75 ? 'from-emerald-400 to-emerald-500'
    : topic.progress >= 40 ? 'from-blue-400 to-indigo-500'
    : 'from-slate-300 to-slate-400'

  // Joriy user shu mavzuning supervisorimikan
  // Backend supervisor_user_id qaytarishi kerak aniqlash uchun
  const isTopicSupervisor = isRole('supervisor') && (
    user?.supervisor_profile_id === topic.supervisor_id ||
    user?.id === topic.supervisor_user_id
  )
  const canManageStages = isRole('supervisor')

  const TABS = [
    { key: 'stages', label: 'Bosqichlar', icon: Layers, count: stages.length },
    { key: 'files',  label: 'Fayllar',    icon: FileText, count: files.filter(f => !f.stage_id).length },
    { key: 'tasks',  label: 'Vazifalar',  icon: ListTodo, count: tasks.length },
  ]

  return (
    <div className="space-y-6 max-w-4xl">

      {/* Back */}
      <button
        onClick={() => navigate('/topics')}
        className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        <ArrowLeft size={15} /> Mavzular ro'yxati
      </button>

      {/* Header card */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-6">
          <div className="flex items-start gap-3 mb-4">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${STATUS_STYLES[topic.status]}`}>
              {STATUS_LABEL[topic.status]}
            </span>
            <span className="text-xs font-medium text-gray-400 bg-gray-100 px-2.5 py-1 rounded-full">
              {topic.academic_year}
            </span>
          </div>

          <h2 className="text-xl font-bold text-gray-900 leading-snug">{topic.title}</h2>
          {topic.title_en && <p className="text-sm text-gray-400 mt-1">{topic.title_en}</p>}
          {topic.description && (
            <p className="text-sm text-gray-600 mt-3 leading-relaxed border-l-2 border-gray-200 pl-3">
              {topic.description}
            </p>
          )}

          {/* Progress */}
          <div className="mt-5">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Umumiy progress</span>
              <span className={`text-sm font-bold ${topic.progress >= 75 ? 'text-emerald-600' : topic.progress >= 40 ? 'text-blue-600' : 'text-gray-500'}`}>
                {topic.progress}%
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${progressColor} rounded-full transition-all duration-700`}
                style={{ width: `${topic.progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Action bar */}
        <div className="flex items-center gap-2 flex-wrap px-6 py-3.5 bg-gray-50/60 border-t border-gray-100">
          {topic.status === 'draft' && isRole('student') && (
            <button
              onClick={async () => { await topicsApi.submit(id); toast.success('Yuborildi'); load() }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-sm transition-all"
            >
              Tasdiqlashga yuborish
            </button>
          )}
          {topic.status === 'pending' && isRole('kafedra_head', 'admin') && (
            <>
              <button
                onClick={() => { setShowApproveModal(true); setApproveSupervisorId(topic.supervisor_id ? String(topic.supervisor_id) : '') }}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 transition-all"
              >
                <CheckCircle size={14} /> Tasdiqlash
              </button>
              <button
                onClick={() => { setShowRejectModal(true); setRejectReason('') }}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold text-white bg-red-500 hover:bg-red-600 transition-all"
              >
                <XCircle size={14} /> Rad etish
              </button>
            </>
          )}
          {isRole('kafedra_head', 'admin') && (
            <button
              onClick={() => setShowAssignModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold text-white bg-purple-600 hover:bg-purple-700 transition-all"
            >
              <UserCheck size={14} /> Rahbar tayinlash
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white border border-gray-100 shadow-sm p-1 rounded-2xl w-fit">
        {TABS.map(({ key, label, icon: Icon, count }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              tab === key
                ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Icon size={14} />
            {label}
            <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${tab === key ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-400'}`}>
              {count}
            </span>
          </button>
        ))}
      </div>

      {/* Tab: Stages */}
      {tab === 'stages' && (
        <div className="space-y-3">
          {canManageStages && (
            <button
              onClick={() => setShowStageModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-sm transition-all"
            >
              <Plus size={15} /> Bosqich qo'shish
            </button>
          )}
          {stages.length === 0 ? (
            <div className="flex flex-col items-center py-12 gap-3 bg-white rounded-2xl border border-gray-100">
              <Layers size={28} className="text-gray-200" />
              <p className="text-sm text-gray-400">Bosqichlar yo'q</p>
            </div>
          ) : (() => {
            const firstPendingIdx = stages.findIndex(s => s.status !== 'approved')
            return stages.map((stage, idx) => {
              const isLocked = firstPendingIdx !== -1 && idx > firstPendingIdx
              const stageFiles = files.filter(f => f.stage_id === stage.id)
              const canUpload = isRole('student') && !isLocked &&
                (stage.status === 'not_started' || stage.status === 'in_progress' || stage.status === 'rejected')
              const canReview = stage.status === 'submitted' && (isTopicSupervisor || isRole('admin', 'kafedra_head'))
              return (
            <div key={stage.id} className={`bg-white rounded-2xl border shadow-sm p-4 transition-all ${isLocked ? 'border-gray-100 opacity-50' : 'border-gray-100 hover:shadow-md'}`}>
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-8 h-8 flex-shrink-0 rounded-xl flex items-center justify-center text-xs font-bold ${
                    isLocked ? 'bg-gray-100 text-gray-400' :
                    stage.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                    stage.status === 'submitted' ? 'bg-amber-100 text-amber-700' :
                    stage.status === 'rejected' ? 'bg-red-100 text-red-600' :
                    'bg-gradient-to-br from-blue-50 to-indigo-100 text-indigo-700'
                  }`}>
                    {isLocked ? <Lock size={12} /> : stage.status === 'approved' ? <CheckCircle size={12} /> : stage.order}
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-900 text-sm truncate">{stage.name}</p>
                    {stage.deadline && (
                      <p className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                        <Clock size={10} /> {new Date(stage.deadline).toLocaleDateString('uz-UZ')}
                        {new Date(stage.deadline) < new Date() && stage.status !== 'approved' && (
                          <span className="text-red-400 font-semibold ml-1">· Muddati o'tdi</span>
                        )}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {stage.status !== 'submitted' && (
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${STAGE_STATUS_STYLES[stage.status]}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${STAGE_STATUS_DOT[stage.status]}`} />
                      {STAGE_STATUS_LABEL[stage.status]}
                    </span>
                  )}
                  {canReview && stage.status === 'submitted' && (
                    <button
                      onClick={() => { setReviewModal({ open: true, stageId: stage.id }); setReviewComment('') }}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                    >
                      Tasdiqlash / Qaytarish
                    </button>
                  )}
                  {/* Student: upload button when not submitted/approved */}
                  {canUpload && (
                    <label className="text-xs px-2.5 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold transition-colors cursor-pointer flex items-center gap-1">
                      <Upload size={11} /> {stage.status === 'rejected' ? 'Qayta yuklash' : 'Fayl yuklash'}
                      <input type="file" className="hidden" onChange={(e) => handleStageFileUpload(e, stage.id)} />
                    </label>
                  )}
                </div>
              </div>
              {stage.comment && (
                <p className="mt-3 text-xs text-gray-600 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2 flex items-start gap-2">
                  <MessageSquare size={12} className="mt-0.5 flex-shrink-0 text-amber-500" />
                  {stage.comment}
                </p>
              )}
              {stageFiles.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {stageFiles.map(f => (
                    <div key={f.id} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-xl">
                      <FileText size={13} className="text-indigo-400 flex-shrink-0" />
                      <span className="text-xs text-gray-700 font-medium flex-1 truncate">{f.file_name}</span>
                      {f.file_size && <span className="text-xs text-gray-400">{(f.file_size / 1024 / 1024).toFixed(2)} MB</span>}
                      <button
                        onClick={() => filesApi.download(id, f.id, f.file_name).catch(() => toast.error('Yuklab olishda xatolik'))}
                        className="w-6 h-6 rounded-lg hover:bg-blue-50 flex items-center justify-center text-gray-300 hover:text-blue-500 transition-all"
                        title="Yuklab olish"
                      >
                        <Download size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {/* Approved: show lock message */}
              {stage.status === 'approved' && stageFiles.length === 0 && (
                <p className="mt-3 text-xs text-emerald-600 bg-emerald-50 border border-emerald-100 rounded-xl px-3 py-2 flex items-center gap-2">
                  <CheckCircle size={12} /> Bosqich tasdiqlangan
                </p>
              )}
            </div>
              )
            })
          })()}
        </div>
      )}

      {/* Tab: Files */}
      {tab === 'files' && (
        <div className="space-y-3">
          {!isRole('student') && (
            <label className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-sm cursor-pointer transition-all">
              <Upload size={15} /> Fayl yuklash
              <input type="file" className="hidden" onChange={handleFileUpload} />
            </label>
          )}
          {files.filter(f => !f.stage_id).length === 0 ? (
            <div className="flex flex-col items-center py-12 gap-3 bg-white rounded-2xl border border-gray-100">
              <FileText size={28} className="text-gray-200" />
              <p className="text-sm text-gray-400">Fayllar yo'q</p>
            </div>
          ) : files.filter(f => !f.stage_id).map(f => (
            <div key={f.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-indigo-50 rounded-xl flex items-center justify-center">
                  <FileText size={16} className="text-indigo-500" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-800">{f.file_name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    v{f.version}
                    {f.file_type && <> · <span className="uppercase">{f.file_type}</span></>}
                    {f.file_size ? ` · ${(f.file_size / 1024).toFixed(1)} KB` : ''}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => filesApi.download(id, f.id, f.file_name).catch(() => toast.error('Yuklab olishda xatolik'))}
                  className="w-8 h-8 rounded-lg hover:bg-blue-50 flex items-center justify-center text-gray-300 hover:text-blue-500 transition-all"
                  title="Yuklab olish"
                >
                  <Download size={15} />
                </button>
                <button
                  onClick={async () => { await filesApi.delete(id, f.id); load() }}
                  className="w-8 h-8 rounded-lg hover:bg-red-50 flex items-center justify-center text-gray-300 hover:text-red-400 transition-all"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Tasks */}
      {tab === 'tasks' && (
        <div className="space-y-3">
          {isRole('supervisor', 'admin') && (
            <button
              onClick={() => setShowTaskModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-sm transition-all"
            >
              <Plus size={15} /> Vazifa qo'shish
            </button>
          )}
          {tasks.length === 0 ? (
            <div className="flex flex-col items-center py-12 gap-3 bg-white rounded-2xl border border-gray-100">
              <ListTodo size={28} className="text-gray-200" />
              <p className="text-sm text-gray-400">Vazifalar yo'q</p>
            </div>
          ) : tasks.map(task => (
            <div
              key={task.id}
              className={`bg-white rounded-2xl border shadow-sm p-4 flex items-start gap-3 transition-all hover:shadow-md ${
                task.is_done ? 'border-emerald-100 bg-emerald-50/30' : 'border-gray-100'
              }`}
            >
              <button
                onClick={() => handleToggleTask(task)}
                className={`w-5 h-5 rounded-lg flex-shrink-0 border-2 mt-0.5 flex items-center justify-center transition-all ${
                  task.is_done ? 'bg-emerald-500 border-emerald-500' : 'border-gray-300 hover:border-blue-400'
                }`}
              >
                {task.is_done && <CheckCircle size={11} className="text-white" />}
              </button>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-semibold ${task.is_done ? 'line-through text-gray-400' : 'text-gray-900'}`}>
                  {task.title}
                </p>
                {task.description && (
                  <p className="text-xs text-gray-500 mt-1">{task.description}</p>
                )}
                {task.deadline && (
                  <p className="text-xs text-gray-400 mt-1.5 flex items-center gap-1">
                    <Clock size={10} /> {new Date(task.deadline).toLocaleDateString('uz-UZ')}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Approve Topic */}
      {showApproveModal && (
        <Modal title="Mavzuni tasdiqlash" onClose={() => setShowApproveModal(false)}>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Ilmiy rahbar (ixtiyoriy)</label>
              <select
                value={approveSupervisorId}
                onChange={(e) => setApproveSupervisorId(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all"
              >
                <option value="">Rahbarsiz tasdiqlash</option>
                {supervisors.map(s => <option key={s.id} value={s.id}>{s.full_name}</option>)}
              </select>
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => setShowApproveModal(false)}
                className="flex-1 py-2.5 border border-gray-200 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 transition-all"
              >
                Bekor qilish
              </button>
              <button
                onClick={async () => {
                  try {
                    await topicsApi.approve(id, approveSupervisorId ? { supervisor_id: parseInt(approveSupervisorId) } : null)
                    toast.success('Tasdiqlandi')
                    setShowApproveModal(false)
                    setApproveSupervisorId('')
                    load()
                    emitTopicUpdated()
                  } catch (err) { toast.error(err?.response?.data?.detail || 'Xatolik') }
                }}
                className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold transition-all"
              >
                Tasdiqlash
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Assign Supervisor */}
      {showAssignModal && (
        <Modal title="Rahbar tayinlash" onClose={() => setShowAssignModal(false)}>
          <div className="p-6 space-y-4">
            <select
              className="w-full px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all"
              onChange={async (e) => {
                if (!e.target.value) return
                try {
                  await topicsApi.assignSupervisor(id, { supervisor_id: parseInt(e.target.value) })
                  toast.success('Rahbar tayinlandi')
                  setShowAssignModal(false)
                  load()
                  emitTopicUpdated()
                } catch (err) { toast.error(err?.response?.data?.detail || 'Xatolik') }
              }}
            >
              <option value="">Rahbar tanlang</option>
              {supervisors.map(s => <option key={s.id} value={s.id}>{s.full_name}</option>)}
            </select>
            <button
              onClick={() => setShowAssignModal(false)}
              className="w-full py-2.5 border border-gray-200 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 transition-all"
            >
              Bekor qilish
            </button>
          </div>
        </Modal>
      )}

      {/* Modal: Create Stage */}
      {showStageModal && (
        <Modal title="Yangi bosqich" onClose={() => setShowStageModal(false)}>
          <form
            className="p-6 space-y-4"
            onSubmit={async (e) => {
              e.preventDefault()
              const fd = Object.fromEntries(new FormData(e.target))
              try {
                await stagesApi.create(id, {
                  name: fd.name,
                  description: fd.description || undefined,
                  order: parseInt(fd.order) || (stages.length + 1),
                  deadline: fd.deadline || undefined,
                })
                toast.success('Bosqich yaratildi')
                setShowStageModal(false)
                load()
              } catch (err) { toast.error(err?.response?.data?.detail || 'Xatolik') }
            }}
          >
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Nomi *</label>
              <input name="name" required className={inputCls} placeholder="Bosqich nomi" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Tavsif</label>
              <textarea name="description" rows={2} className={`${inputCls} resize-none`} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Tartib â„–</label>
                <input name="order" type="number" defaultValue={stages.length + 1} className={inputCls} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Muddat</label>
                <input name="deadline" type="date" className={inputCls} />
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowStageModal(false)}
                className="flex-1 py-2.5 border border-gray-200 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 transition-all">
                Bekor qilish
              </button>
              <button type="submit"
                className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl text-sm font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all">
                Yaratish
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Create Task */}
      {showTaskModal && (
        <Modal title="Yangi vazifa" onClose={() => setShowTaskModal(false)}>
          <form
            className="p-6 space-y-4"
            onSubmit={async (e) => {
              e.preventDefault()
              const fd = Object.fromEntries(new FormData(e.target))
              try {
                await tasksApi.create(id, {
                  title: fd.title,
                  description: fd.description || undefined,
                  deadline: fd.deadline ? new Date(fd.deadline).toISOString() : undefined,
                })
                toast.success('Vazifa yaratildi')
                setShowTaskModal(false)
                load()
              } catch (err) { toast.error(err?.response?.data?.detail || 'Xatolik') }
            }}
          >
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Sarlavha *</label>
              <input name="title" required className={inputCls} placeholder="Vazifa sarlavhasi" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Tavsif</label>
              <textarea name="description" rows={2} className={`${inputCls} resize-none`} />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Muddat</label>
              <input name="deadline" type="datetime-local" className={inputCls} />
            </div>
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowTaskModal(false)}
                className="flex-1 py-2.5 border border-gray-200 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 transition-all">
                Bekor qilish
              </button>
              <button type="submit"
                className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl text-sm font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all">
                Yaratish
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Reject Topic */}
      {showRejectModal && (
        <Modal title="Mavzuni rad etish" onClose={() => setShowRejectModal(false)}>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Rad etish sababi *</label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={3}
                className={inputCls + ' resize-none'}
                placeholder="Rad etish sababini kiriting..."
                autoFocus
              />
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 py-2.5 border border-gray-200 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 transition-all"
              >
                Bekor qilish
              </button>
              <button
                onClick={async () => {
                  if (!rejectReason.trim()) return toast.error('Sabab kiritilmagan')
                  try {
                    await topicsApi.reject(id, { reason: rejectReason.trim() })
                    toast.success('Rad etildi')
                    setShowRejectModal(false)
                    load()
                  } catch (err) { toast.error(err?.response?.data?.detail || 'Xatolik') }
                }}
                disabled={!rejectReason.trim()}
                className="flex-1 py-2.5 bg-red-500 hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-sm font-semibold transition-all"
              >
                Rad etish
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Review Stage */}
      {reviewModal.open && (
        <Modal title="Tasdiqlash / Qaytarish" onClose={() => setReviewModal({ open: false, stageId: null })}>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Izoh (ixtiyoriy)</label>
              <textarea
                value={reviewComment}
                onChange={(e) => setReviewComment(e.target.value)}
                rows={3}
                className={`${inputCls} resize-none`}
                placeholder="Rad etish sababi yoki tavsiya..."
              />
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => handleReviewSubmit(false)}
                className="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-semibold transition-all"
              >
                Qaytarish
              </button>
              <button
                onClick={() => handleReviewSubmit(true)}
                className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold transition-all"
              >
                Tasdiqlash
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
