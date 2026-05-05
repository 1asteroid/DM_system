import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import {
  BookOpen, CheckCircle, Clock, XCircle, TrendingUp, Users,
  Calendar, AlertTriangle, FileText, ChevronRight, UserCheck,
  ShieldAlert, PlusCircle, Eye,
} from 'lucide-react'
import { reportsApi, topicsApi, stagesApi, meetingsApi, riskApi } from '../../api/api'
import useAuthStore from '../../store/authStore'

const STATUS_COLORS = {
  approved: '#22c55e', pending: '#f59e0b', rejected: '#ef4444', draft: '#94a3b8',
}
const STATUS_LABELS = {
  approved: 'Tasdiqlangan', pending: 'Kutmoqda', rejected: 'Rad etilgan', draft: 'Qoralama',
}
const STAGE_STATUS_LABEL = {
  not_started: 'Boshlanmagan', in_progress: 'Jarayonda',
  submitted: 'Yuborildi', approved: 'Tasdiqlandi', rejected: 'Rad etildi',
}
const STAGE_STATUS_COLORS = {
  not_started: { bg: '#f1f5f9', color: '#64748b' },
  in_progress: { bg: '#eff6ff', color: '#3b82f6' },
  submitted: { bg: '#fffbeb', color: '#f59e0b' },
  approved: { bg: '#f0fdf4', color: '#22c55e' },
  rejected: { bg: '#fef2f2', color: '#ef4444' },
}
const RISK_BADGE = {
  low: { label: 'Past', bg: '#dbeafe', color: '#1e40af' },
  medium: { label: "O'rta", bg: '#fef3c7', color: '#92400e' },
  high: { label: 'Yuqori', bg: '#fed7aa', color: '#9a3412' },
  critical: { label: 'Juda Yuqori', bg: '#fee2e2', color: '#991b1b' },
  very_high: { label: 'Juda Yuqori', bg: '#fee2e2', color: '#991b1b' },
}

function StatCard({ icon: Icon, label, value, color, bg, sub, linkTo }) {
  const card = (
    <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', padding: '20px', borderTop: `3px solid ${color}` }}>
      <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: bg || `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '14px' }}>
        <Icon size={18} color={color} />
      </div>
      <div style={{ fontSize: '26px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>{value}</div>
      <div style={{ fontSize: '13px', color: '#64748b', fontWeight: '500', marginTop: '4px' }}>{label}</div>
      {sub && <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>{sub}</div>}
    </div>
  )
  return linkTo ? <Link to={linkTo} style={{ textDecoration: 'none' }}>{card}</Link> : card
}

function SectionCard({ title, children, action }) {
  return (
    <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 22px', borderBottom: '1px solid #f1f5f9' }}>
        <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>{title}</h3>
        {action}
      </div>
      <div>{children}</div>
    </div>
  )
}

// ─── STUDENT DASHBOARD ──────────────────────────
function StudentDashboard({ user }) {
  const [topic, setTopic] = useState(null)
  const [stages, setStages] = useState([])
  const [risk, setRisk] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadTopic = async () => {
      try {
        const r = await topicsApi.list({ page_size: 1 })
        const t = r.data.items[0]
        setTopic(t || null)
        if (t) {
          const [sr] = await Promise.all([
            stagesApi.list(t.id),
          ])
          setStages(sr.data)

          // Risk assessment'ni yaratish va keyin olish
          try {
            const assessRes = await riskApi.assess(t.id)
            setRisk(assessRes.data || null)
          } catch (assessErr) {
            console.log('Risk assess error, trying to get existing...')
            try {
              const getRiskRes = await riskApi.get(t.id)
              setRisk(getRiskRes.data || null)
            } catch (getRiskErr) {
              console.log('Risk get error:', getRiskErr)
              setRisk(null)
            }
          }
        }
      } catch (err) {
        console.error('Error loading topic:', err)
        setTopic(null)
      } finally {
        setLoading(false)
      }
    }

    loadTopic()
  }, [])

  if (loading) return <Spinner />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: "'DM Sans',sans-serif" }}>
      <Greeting name={user?.full_name} subtitle="Diplom loyihangiz holati" />

      {!topic ? (
        <div style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', borderRadius: '20px', padding: '40px', textAlign: 'center', color: '#fff' }}>
          <BookOpen size={48} style={{ marginBottom: '16px', opacity: 0.8 }} />
          <h3 style={{ fontSize: '20px', fontWeight: '700', fontFamily: "'Sora',sans-serif", marginBottom: '8px' }}>Diplom mavzuingiz yo'q</h3>
          <p style={{ fontSize: '14px', opacity: 0.8, marginBottom: '24px' }}>Mavzu yarating va ilmiy rahbar tayinlashni boshlang</p>
          <Link to="/topics/new" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', background: '#fff', color: '#6366f1', borderRadius: '12px', fontWeight: '700', fontSize: '14px', textDecoration: 'none' }}>
            <PlusCircle size={16} /> Mavzu yaratish
          </Link>
        </div>
      ) : (
        <>
          {/* Topic summary */}
          <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: '16px' }}>
              <div style={{ flex: 1 }}>
                <span style={{ display: 'inline-flex', padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: '600', background: STATUS_COLORS[topic.status] + '20', color: STATUS_COLORS[topic.status], marginBottom: '8px' }}>
                  {STATUS_LABELS[topic.status]}
                </span>
                <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#1e293b', lineHeight: 1.3, fontFamily: "'Sora',sans-serif" }}>{topic.title}</h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>{topic.academic_year} o'quv yili</p>
              </div>
              <Link to={`/topics/${topic.id}`} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', background: '#eef2ff', color: '#6366f1', borderRadius: '10px', fontWeight: '600', fontSize: '13px', textDecoration: 'none', flexShrink: 0 }}>
                <Eye size={14} /> Ko'rish
              </Link>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', color: '#64748b' }}>Umumiy progress</span>
                <span style={{ fontSize: '14px', fontWeight: '700', color: '#6366f1' }}>{topic.progress}%</span>
              </div>
              <div style={{ height: '8px', background: '#f1f5f9', borderRadius: '99px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${topic.progress}%`, background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', borderRadius: '99px', transition: 'width 0.4s ease' }} />
              </div>

              {/* Risk indicator */}
              {risk && (
                <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '13px', color: '#64748b' }}>Risk darajasi</span>
                  {(() => {
                    const cfg = RISK_BADGE[risk.risk_level] || RISK_BADGE.low
                    return (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600',
                        background: cfg.bg,
                        color: cfg.color,
                      }}>
                        <TrendingUp size={12} />
                        {cfg.label} ({Math.round(risk.risk_score)}%)
                      </span>
                    )
                  })()}
                </div>
              )}
            </div>
          </div>

          {/* Stages */}
          {stages.length > 0 && (
            <SectionCard title="Bosqichlar" action={
              <Link to={`/topics/${topic.id}`} style={{ fontSize: '13px', color: '#6366f1', textDecoration: 'none', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Hammasi <ChevronRight size={14} />
              </Link>
            }>
              {stages.slice(0, 5).map(s => {
                const sc = STAGE_STATUS_COLORS[s.status] || STAGE_STATUS_COLORS.not_started
                return (
                  <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 22px', borderBottom: '1px solid #f8fafc' }}>
                    <span style={{ width: '26px', height: '26px', borderRadius: '8px', background: '#eef2ff', color: '#6366f1', fontSize: '12px', fontWeight: '700', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{s.order}</span>
                    <span style={{ flex: 1, fontSize: '14px', color: '#1e293b' }}>{s.name}</span>
                    {s.deadline && <span style={{ fontSize: '12px', color: '#94a3b8' }}>{new Date(s.deadline).toLocaleDateString('uz-UZ')}</span>}
                    <span style={{ padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: '600', background: sc.bg, color: sc.color }}>
                      {STAGE_STATUS_LABEL[s.status]}
                    </span>
                  </div>
                )
              })}
            </SectionCard>
          )}
        </>
      )}
    </div>
  )
}

// ─── SUPERVISOR DASHBOARD ────────────────────────
function SupervisorDashboard({ user }) {
  const [stats, setStats] = useState(null)
  const [topics, setTopics] = useState([])
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      reportsApi.dashboard(),
      topicsApi.list({ page_size: 5 }),
      meetingsApi.listAll(),
    ]).then(([sr, tr, mr]) => {
      setStats(sr.data)
      setTopics(tr.data.items)
      setMeetings(mr.data.filter(m => m.status === 'planned').slice(0, 3))
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const pendingStages = topics.reduce((acc, t) => acc, 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: "'DM Sans',sans-serif" }}>
      <Greeting name={user?.full_name} subtitle="Talabalaringiz holati" />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '16px' }}>
        <StatCard icon={Users} label="Talabalar" value={stats?.total_topics || 0} color="#6366f1" linkTo="/topics" />
        <StatCard icon={CheckCircle} label="Tasdiqlangan" value={stats?.approved || 0} color="#22c55e" />
        <StatCard icon={Clock} label="O'rtacha progress" value={`${stats?.avg_progress || 0}%`} color="#f59e0b" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '20px' }}>
        <SectionCard title="So'nggi talabalar" action={
          <Link to="/topics" style={{ fontSize: '13px', color: '#6366f1', textDecoration: 'none', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>
            Hammasi <ChevronRight size={14} />
          </Link>
        }>
          {topics.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>Talabalar yo'q</div>
          ) : topics.map(t => (
            <Link key={t.id} to={`/topics/${t.id}`} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 22px', borderBottom: '1px solid #f8fafc', textDecoration: 'none' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                  <div style={{ height: '4px', width: '80px', background: '#f1f5f9', borderRadius: '99px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${t.progress}%`, background: '#6366f1', borderRadius: '99px' }} />
                  </div>
                  <span style={{ fontSize: '12px', color: '#94a3b8' }}>{t.progress}%</span>
                </div>
              </div>
              <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: '600', background: STATUS_COLORS[t.status] + '20', color: STATUS_COLORS[t.status] }}>
                {STATUS_LABELS[t.status]}
              </span>
            </Link>
          ))}
        </SectionCard>

        <SectionCard title="Yaqinlashgan uchrashuvlar" action={
          <Link to="/meetings" style={{ fontSize: '13px', color: '#6366f1', textDecoration: 'none', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>
            Hammasi <ChevronRight size={14} />
          </Link>
        }>
          {meetings.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>Uchrashuvlar yo'q</div>
          ) : meetings.map(m => {
            const dt = new Date(m.scheduled_at)
            return (
              <div key={m.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '14px 22px', borderBottom: '1px solid #f8fafc' }}>
                <div style={{ width: '42px', textAlign: 'center', background: '#eef2ff', borderRadius: '10px', padding: '8px 6px', flexShrink: 0 }}>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: '#6366f1' }}>{dt.getDate()}</div>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>{dt.toLocaleDateString('uz-UZ', { month: 'short' })}</div>
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '500', color: '#1e293b' }}>
                    {dt.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  {m.location && <div style={{ fontSize: '12px', color: '#94a3b8' }}>{m.location}</div>}
                </div>
              </div>
            )
          })}
        </SectionCard>
      </div>
    </div>
  )
}

// ─── KAFEDRA HEAD DASHBOARD ──────────────────────
function KafedraHeadDashboard({ user }) {
  const [stats, setStats] = useState(null)
  const [pendingTopics, setPendingTopics] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      reportsApi.dashboard(),
      topicsApi.list({ status: 'pending', page_size: 5 }),
    ]).then(([sr, tr]) => {
      setStats(sr.data)
      setPendingTopics(tr.data.items)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: "'DM Sans',sans-serif" }}>
      <Greeting name={user?.full_name} subtitle="Kafedra monitoringi" />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px' }}>
        <StatCard icon={BookOpen} label="Jami mavzular" value={stats?.total_topics || 0} color="#6366f1" />
        <StatCard icon={Clock} label="Tasdiqlash kutmoqda" value={stats?.pending || 0} color="#f59e0b" linkTo="/topics?status=pending" />
        <StatCard icon={CheckCircle} label="Tasdiqlangan" value={stats?.approved || 0} color="#22c55e" />
        <StatCard icon={TrendingUp} label="O'rtacha progress" value={`${stats?.avg_progress || 0}%`} color="#8b5cf6" />
      </div>

      <SectionCard title="Tasdiqlash kutayotgan mavzular" action={
        <Link to="/topics" style={{ fontSize: '13px', color: '#6366f1', textDecoration: 'none', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>
          Barchasi <ChevronRight size={14} />
        </Link>
      }>
        {pendingTopics.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
            <CheckCircle size={32} style={{ marginBottom: '10px', opacity: 0.3 }} />
            <p>Barcha mavzular ko'rib chiqilgan</p>
          </div>
        ) : pendingTopics.map(t => (
          <Link key={t.id} to={`/topics/${t.id}`} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '16px 22px', borderBottom: '1px solid #f8fafc', textDecoration: 'none' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: '#fffbeb', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Clock size={16} color="#f59e0b" />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</div>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>{t.academic_year}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#6366f1', fontSize: '13px', fontWeight: '500', flexShrink: 0 }}>
              Ko'rish <ChevronRight size={14} />
            </div>
          </Link>
        ))}
      </SectionCard>

      {/* Status chart */}
      {stats?.topics_by_status?.length > 0 && (
        <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', padding: '22px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', fontFamily: "'Sora',sans-serif" }}>Holat bo'yicha taqsimot</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.topics_by_status.map(i => ({ name: STATUS_LABELS[i.status] || i.status, count: i.count, status: i.status }))}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                {stats.topics_by_status.map((e, i) => <Cell key={i} fill={STATUS_COLORS[e.status] || '#94a3b8'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

// ─── ADMIN DASHBOARD ─────────────────────────────
function AdminDashboard({ user }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    reportsApi.dashboard()
      .then(r => setStats(r.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: "'DM Sans',sans-serif" }}>
      <Greeting name={user?.full_name} subtitle="Tizim boshqaruvi" />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px' }}>
        <StatCard icon={BookOpen} label="Jami mavzular" value={stats?.total_topics || 0} color="#6366f1" linkTo="/topics" />
        <StatCard icon={CheckCircle} label="Tasdiqlangan" value={stats?.approved || 0} color="#22c55e" />
        <StatCard icon={Clock} label="Kutmoqda" value={stats?.pending || 0} color="#f59e0b" />
        <StatCard icon={TrendingUp} label="O'rtacha progress" value={`${stats?.avg_progress || 0}%`} color="#8b5cf6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '20px' }}>
        <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', padding: '22px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', fontFamily: "'Sora',sans-serif" }}>Holat bo'yicha taqsimot</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={(stats?.topics_by_status || []).map(i => ({ name: STATUS_LABELS[i.status] || i.status, count: i.count, status: i.status }))}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                {(stats?.topics_by_status || []).map((e, i) => <Cell key={i} fill={STATUS_COLORS[e.status] || '#94a3b8'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', padding: '22px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', fontFamily: "'Sora',sans-serif" }}>Holat tafsiloti</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {(stats?.topics_by_status || []).map(item => (
              <div key={item.status} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: STATUS_COLORS[item.status], flexShrink: 0 }} />
                <span style={{ flex: 1, fontSize: '13px', color: '#64748b' }}>{STATUS_LABELS[item.status] || item.status}</span>
                <span style={{ fontWeight: '600', color: '#1e293b', fontSize: '14px' }}>{item.count}</span>
                <div style={{ width: '60px', height: '6px', background: '#f1f5f9', borderRadius: '99px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', borderRadius: '99px', background: STATUS_COLORS[item.status], width: `${stats.total_topics ? (item.count / stats.total_topics * 100) : 0}%` }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #f1f5f9', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <Link to="/users" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px 12px', background: '#eef2ff', color: '#6366f1', borderRadius: '10px', fontSize: '13px', fontWeight: '600', textDecoration: 'none' }}>
              <Users size={14} /> Foydalanuvchilar
            </Link>
            <Link to="/analytics" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px 12px', background: '#f0fdf4', color: '#22c55e', borderRadius: '10px', fontSize: '13px', fontWeight: '600', textDecoration: 'none' }}>
              <TrendingUp size={14} /> Analitika
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── HELPERS ────────────────────────────────────
function Greeting({ name, subtitle }) {
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Xayrli tong' : hour < 17 ? 'Xayrli kun' : 'Xayrli kech'
  return (
    <div>
      <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>
        {greeting}, {name} 👋
      </h2>
      <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '3px' }}>{subtitle}</p>
    </div>
  )
}

function Spinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
      <div style={{ width: '36px', height: '36px', border: '3px solid #e2e8f0', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuthStore()

  if (!user) return <Spinner />

  if (user.role === 'student') return <StudentDashboard user={user} />
  if (user.role === 'supervisor') return <SupervisorDashboard user={user} />
  if (user.role === 'kafedra_head') return <KafedraHeadDashboard user={user} />
  return <AdminDashboard user={user} />
}

