import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie,
} from 'recharts'
import {
  Users, BookOpen, TrendingUp,
  Clock, CheckCircle2, UserCheck,
} from 'lucide-react'
import { reportsApi } from '../../api/api'
import toast from 'react-hot-toast'

const normalizeRiskLevel = (level) => (level === 'very_high' ? 'critical' : level)
const RISK_COLOR  = { low: '#22c55e', medium: '#f59e0b', high: '#ea580c', critical: '#dc2626' }
const RISK_LABEL  = { low: 'Past', medium: "O'rta", high: 'Yuqori', critical: 'Juda Yuqori' }
const STATUS_COLORS = { approved: '#22c55e', pending: '#f59e0b', rejected: '#ef4444', draft: '#94a3b8' }
const STATUS_LABEL  = { approved: 'Tasdiqlangan', pending: 'Kutmoqda', rejected: 'Rad etilgan', draft: 'Qoralama' }

function KPICard({ icon: Icon, label, value, color, sub }) {
  return (
    <div style={{ background: '#fff', borderRadius: '16px', padding: '20px', border: '1px solid #e8ecf4', borderTop: `3px solid ${color}` }}>
      <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '14px' }}>
        <Icon size={20} color={color} />
      </div>
      <div style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>{value}</div>
      <div style={{ fontSize: '13px', color: '#64748b', fontWeight: '500', marginTop: '4px' }}>{label}</div>
      {sub && <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>{sub}</div>}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#1e293b', color: '#fff', padding: '10px 14px', borderRadius: '10px', fontSize: '13px' }}>
      <div>{label}</div>
      <div style={{ color: '#a5b4fc', marginTop: '2px' }}>{payload[0].value} ta</div>
    </div>
  )
}

export default function Analytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    reportsApi.analytics()
      .then(r => setData(r.data))
      .catch(() => toast.error('Analitika yuklanmadi'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
      <div style={{ width: '36px', height: '36px', border: '3px solid #e2e8f0', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  )
  if (!data) return <div style={{ textAlign: 'center', color: '#94a3b8', padding: '60px' }}>Ma'lumot topilmadi</div>

  const statusChartData = (data.topics_by_status || []).map(i => ({
    name: STATUS_LABEL[i.status] || i.status,
    count: i.count,
    status: i.status,
  }))

  const riskChartData = Object.entries(data.risk_distribution || {}).reduce((acc, [rawLevel, count]) => {
    const level = normalizeRiskLevel(rawLevel)
    const found = acc.find((item) => item.level === level)
    if (found) {
      found.value += count
    } else {
      acc.push({
        level,
        name: RISK_LABEL[level] || level,
        value: count,
        fill: RISK_COLOR[level] || '#94a3b8',
      })
    }
    return acc
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: "'DM Sans',sans-serif" }}>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>

      <div>
        <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Kengaytirilgan Analitika</h2>
        <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '3px' }}>Tizim bo'yicha to'liq statistika</p>
      </div>

      {/* KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px' }}>
        <KPICard icon={BookOpen}   label="Jami mavzular"    value={data.total_topics}     color="#6366f1" />
        <KPICard icon={Users}      label="Talabalar"        value={data.total_students}    color="#0ea5e9" />
        <KPICard icon={UserCheck}  label="Rahbarlar"        value={data.total_supervisors} color="#8b5cf6" />
        <KPICard icon={TrendingUp} label="O'rtacha progress" value={`${data.avg_progress}%`} color="#22c55e" />
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '16px' }}>
        {/* Status bar chart */}
        <div style={{ background: '#fff', borderRadius: '16px', padding: '22px', border: '1px solid #e8ecf4' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', fontFamily: "'Sora',sans-serif" }}>Holat bo'yicha taqsimot</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={statusChartData} barCategoryGap="35%">
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                {statusChartData.map((e, i) => <Cell key={i} fill={STATUS_COLORS[e.status] || '#94a3b8'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk pie chart */}
        <div style={{ background: '#fff', borderRadius: '16px', padding: '22px', border: '1px solid #e8ecf4' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', fontFamily: "'Sora',sans-serif" }}>Risk taqsimoti</h3>
          {riskChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={riskChartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={75} label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                  {riskChartData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: '#94a3b8', fontSize: '13px' }}>
              Risk baholari hali yo'q
            </div>
          )}
        </div>
      </div>

      {/* Overdue / Submitted row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={{ background: '#fff', borderRadius: '16px', padding: '20px', border: '1px solid #e8ecf4', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '50px', height: '50px', borderRadius: '14px', background: '#fef3c7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Clock size={24} color="#f59e0b" />
          </div>
          <div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>{data.overdue_stages_count}</div>
            <div style={{ fontSize: '13px', color: '#64748b' }}>Muddati o'tgan bosqichlar</div>
          </div>
        </div>
        <div style={{ background: '#fff', borderRadius: '16px', padding: '20px', border: '1px solid #e8ecf4', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '50px', height: '50px', borderRadius: '14px', background: '#dcfce7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CheckCircle2 size={24} color="#22c55e" />
          </div>
          <div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>{data.submitted_stages_count}</div>
            <div style={{ fontSize: '13px', color: '#64748b' }}>Ko'rib chiqilishi kutilmoqda</div>
          </div>
        </div>
      </div>

      {/* Supervisor table */}
      {data.supervisor_stats?.length > 0 && (
        <div style={{ background: '#fff', borderRadius: '16px', padding: '22px', border: '1px solid #e8ecf4' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', fontFamily: "'Sora',sans-serif" }}>Rahbar statistikasi</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                {['Rahbar', 'Talabalar', "O'rtacha progress", 'Yuqori risk'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '8px 12px', fontSize: '12px', fontWeight: '600', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.supervisor_stats.map(s => (
                <tr key={s.supervisor_id} style={{ borderBottom: '1px solid #f8fafc' }}>
                  <td style={{ padding: '12px', fontSize: '14px', fontWeight: '500', color: '#1e293b' }}>{s.supervisor_name}</td>
                  <td style={{ padding: '12px', fontSize: '14px', color: '#475569' }}>{s.total_students}</td>
                  <td style={{ padding: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ flex: 1, height: '6px', background: '#f1f5f9', borderRadius: '99px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${s.avg_progress}%`, background: '#6366f1', borderRadius: '99px' }} />
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '600', color: '#6366f1', minWidth: '40px' }}>{s.avg_progress}%</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{ display: 'inline-flex', padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: '600', background: s.high_risk_count > 0 ? '#fef2f2' : '#f0fdf4', color: s.high_risk_count > 0 ? '#ef4444' : '#22c55e' }}>
                      {s.high_risk_count}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
