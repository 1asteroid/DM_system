import { useEffect, useState } from 'react'
import { riskApi, topicsApi } from '../../api/api'
import toast from 'react-hot-toast'
import { ShieldAlert, AlertTriangle, Shield, Zap, RefreshCw } from 'lucide-react'

const normalizeRiskLevel = (level) => (level === 'very_high' ? 'critical' : level)

const RISK_CONFIG = {
  low:      { label: 'Past',        color: '#22c55e', bg: '#f0fdf4', icon: Shield },
  medium:   { label: "O'rta",      color: '#f59e0b', bg: '#fffbeb', icon: AlertTriangle },
  high:     { label: 'Yuqori',      color: '#ea580c', bg: '#fff7ed', icon: AlertTriangle },
  critical: { label: 'Juda Yuqori', color: '#dc2626', bg: '#fef2f2', icon: Zap },
}

function RiskBadge({ level }) {
  const cfg = RISK_CONFIG[normalizeRiskLevel(level)] || RISK_CONFIG.low
  const Icon = cfg.icon
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '3px 10px', borderRadius: '99px', background: cfg.bg, color: cfg.color, fontSize: '12px', fontWeight: '600' }}>
      <Icon size={12} />
      {cfg.label}
    </span>
  )
}

function RiskBar({ score }) {
  const color = score >= 90 ? '#dc2626' : score >= 80 ? '#ea580c' : score >= 60 ? '#f59e0b' : '#22c55e'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <div style={{ flex: 1, height: '8px', background: '#f1f5f9', borderRadius: '99px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${score}%`, background: color, borderRadius: '99px', transition: 'width 0.6s ease' }} />
      </div>
      <span style={{ fontSize: '13px', fontWeight: '700', color, minWidth: '36px' }}>{score}</span>
    </div>
  )
}

export default function RiskDashboard() {
  const [risks, setRisks] = useState([])
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(true)
  const [assessing, setAssessing] = useState(null)
  const [filter, setFilter] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const [rRes, tRes] = await Promise.all([
        riskApi.list(),
        topicsApi.list({ page_size: 100 }),
      ])
      console.log('Risks loaded:', rRes.data)
      console.log('Topics loaded:', tRes.data)
      setRisks(rRes.data)
      setTopics(tRes.data.items || tRes.data || [])
    } catch (error) {
      console.error('Load error:', error)
      toast.error(`Yuklanmadi: ${error.message}`)
    }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleAssess = async (topicId) => {
    setAssessing(topicId)
    try {
      await riskApi.assess(topicId)
      toast.success('Risk baholandi')
      load()
    } catch (error) {
      console.error('Risk assessment error:', error)
      toast.error(`Xatolik: ${error.response?.data?.detail || error.message || 'Noma\'lum xatolik'}`)
    }
    finally { setAssessing(null) }
  }

  const handleAssessAll = async () => {
    setAssessing('all')
    const results = await Promise.allSettled(topics.map(t => riskApi.assess(t.id)))
    const ok = results.filter(r => r.status === 'fulfilled').length
    const failed = results.filter(r => r.status === 'rejected').length
    if (ok > 0) toast.success(`${ok} ta mavzu baholandi`)
    if (failed > 0) {
      toast.error(`${failed} ta mavzu baholanmadi`)
      results.forEach((r, i) => {
        if (r.status === 'rejected') {
          console.error(`Topic ${topics[i]?.id} assessment failed:`, r.reason)
        }
      })
    }
    await load()
    setAssessing(null)
  }

  const filtered = filter ? risks.filter(r => normalizeRiskLevel(r.risk_level) === filter) : risks

  const counts = risks.reduce((acc, r) => {
    const level = normalizeRiskLevel(r.risk_level)
    acc[level] = (acc[level] || 0) + 1
    return acc
  }, {})

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
      <div style={{ width: '36px', height: '36px', border: '3px solid #e2e8f0', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: "'DM Sans',sans-serif" }}>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Risk Monitori</h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '3px' }}>Kechikish xavfi bo'lgan talabalar</p>
        </div>
        <button onClick={handleAssessAll} disabled={assessing === 'all'}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '10px', cursor: assessing === 'all' ? 'not-allowed' : 'pointer', opacity: assessing === 'all' ? 0.6 : 1, fontSize: '14px', fontWeight: '500' }}>
          <RefreshCw size={16} style={{ animation: assessing === 'all' ? 'spin 0.8s linear infinite' : 'none' }} />
          Hammasini baholash
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '14px' }}>
        {Object.entries(RISK_CONFIG).map(([level, cfg]) => {
          const Icon = cfg.icon
          return (
            <button key={level} onClick={() => setFilter(filter === level ? '' : level)}
              style={{ background: filter === level ? cfg.bg : '#fff', border: `2px solid ${filter === level ? cfg.color : '#e8ecf4'}`, borderRadius: '14px', padding: '18px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s' }}>
              <Icon size={20} color={cfg.color} />
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#1e293b', margin: '10px 0 4px', fontFamily: "'Sora',sans-serif" }}>{counts[level] || 0}</div>
              <div style={{ fontSize: '13px', color: '#64748b' }}>{cfg.label} risk</div>
            </button>
          )
        })}
      </div>

      {/* Risk table */}
      <div style={{ background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', overflow: 'hidden' }}>
        {filtered.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '60px', color: '#94a3b8' }}>
            <ShieldAlert size={40} style={{ marginBottom: '12px', opacity: 0.3 }} />
            <p>{filter ? "Bu darajada risk topilmadi" : "Hali hech qaysi mavzu baholanmagan"}</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e8ecf4' }}>
              <tr>
                {['Mavzu', 'Holat', 'Progress', 'Risk darajasi', 'Risk bali', 'Amal'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '12px 16px', fontSize: '12px', fontWeight: '600', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(r => (
                <tr key={r.id} style={{ borderBottom: '1px solid #f8fafc' }}>
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.topic_title}</div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                      Baholangan: {new Date(r.assessed_at).toLocaleDateString('uz-UZ')}
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: '600',
                      background: { draft: '#f1f5f9', pending: '#fffbeb', approved: '#f0fdf4', rejected: '#fef2f2' }[r.topic_status] || '#f1f5f9',
                      color: { draft: '#64748b', pending: '#b45309', approved: '#15803d', rejected: '#dc2626' }[r.topic_status] || '#64748b',
                    }}>
                      {{ draft: 'Qoralama', pending: 'Kutmoqda', approved: 'Tasdiqlangan', rejected: 'Rad etilgan' }[r.topic_status] || r.topic_status}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', minWidth: '140px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ flex: 1, height: '6px', background: '#f1f5f9', borderRadius: '99px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${r.topic_progress}%`, background: '#6366f1', borderRadius: '99px' }} />
                      </div>
                      <span style={{ fontSize: '12px', color: '#64748b', minWidth: '34px' }}>{r.topic_progress}%</span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px' }}><RiskBadge level={r.risk_level} /></td>
                  <td style={{ padding: '14px 16px', minWidth: '160px' }}><RiskBar score={Math.round(r.risk_score)} /></td>
                  <td style={{ padding: '14px 16px' }}>
                    <button onClick={() => handleAssess(r.topic_id)} disabled={assessing === r.topic_id}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: assessing === r.topic_id ? 'not-allowed' : 'pointer', fontSize: '12px', color: '#64748b', fontWeight: '500' }}>
                      <RefreshCw size={12} style={{ animation: assessing === r.topic_id ? 'spin 0.8s linear infinite' : 'none' }} />
                      Yangilash
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Topics without assessment */}
      {topics.filter(t => !risks.find(r => r.topic_id === t.id)).length > 0 && (
        <div style={{ background: '#fff', borderRadius: '16px', padding: '20px', border: '1px solid #e8ecf4' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b', marginBottom: '12px' }}>Baholanmagan mavzular</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {topics.filter(t => !risks.find(r => r.topic_id === t.id)).map(t => (
              <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '13px', color: '#475569', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</span>
                <button onClick={() => handleAssess(t.id)} disabled={!!assessing}
                  style={{ padding: '4px 10px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '6px', cursor: !!assessing ? 'not-allowed' : 'pointer', fontSize: '12px', fontWeight: '500' }}>
                  Baholash
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
