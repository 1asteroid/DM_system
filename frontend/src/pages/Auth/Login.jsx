import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, BookOpen, GraduationCap, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'
import useAuthStore from '../../store/authStore'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(form)
      toast.success('Xush kelibsiz!')
      navigate('/dashboard')
    } catch (err) {
      if (!err.response) {
        toast.error("Server bilan bog'lanib bo'lmadi. Backend ishga tushirilganligini tekshiring.")
      } else {
        toast.error(err.response?.data?.detail || "Email yoki parol noto'g'ri")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.root}>
      <div style={styles.blob1} />
      <div style={styles.blob2} />
      <div style={styles.grid} />

      <div style={styles.wrapper}>
        {/* Left */}
        <div style={styles.left}>
          <div style={styles.logoRow}>
            <div style={styles.logoBox}><GraduationCap size={26} color="#fff" /></div>
            <span style={styles.logoText}>DiploMap</span>
          </div>
          <h1 style={styles.title}>
            Diplom<br />
            <span style={styles.titleAccent}>Monitoring</span><br />
            Tizimi
          </h1>
          <p style={styles.sub}>
            Talabalar diplom loyihalarini real vaqtda kuzatish,
            bosqichma-bosqich monitoring va ilmiy rahbar bilan
            samarali hamkorlik platformasi.
          </p>
          <div style={styles.stats}>
            {[['500+','Talaba'],['48','Rahbar'],['96%','Muvaffaqiyat']].map(([n,l])=>(
              <div key={l}>
                <div style={styles.statNum}>{n}</div>
                <div style={styles.statLabel}>{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right */}
        <div style={styles.right}>
          <div style={styles.card}>
            <div style={styles.cardIconBox}><BookOpen size={20} color="#6366f1" /></div>
            <h2 style={styles.cardTitle}>Tizimga kirish</h2>
            <p style={styles.cardSub}>Davom etish uchun hisobingizga kiring</p>

            <form onSubmit={handleSubmit} style={styles.form}>
              <div style={styles.field}>
                <label style={styles.label}>Email manzil</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={e => setForm({...form, email: e.target.value})}
                  placeholder="email@university.uz"
                  required
                  style={styles.input}
                  onFocus={e => e.target.style.borderColor='#6366f1'}
                  onBlur={e => e.target.style.borderColor='#e2e8f0'}
                />
              </div>

              <div style={styles.field}>
                <label style={styles.label}>Parol</label>
                <div style={{position:'relative'}}>
                  <input
                    type={showPass ? 'text' : 'password'}
                    value={form.password}
                    onChange={e => setForm({...form, password: e.target.value})}
                    placeholder="••••••••"
                    required
                    style={{...styles.input, paddingRight:'48px'}}
                    onFocus={e => e.target.style.borderColor='#6366f1'}
                    onBlur={e => e.target.style.borderColor='#e2e8f0'}
                  />
                  <button type="button" onClick={()=>setShowPass(!showPass)} style={styles.eyeBtn}>
                    {showPass ? <EyeOff size={16} color="#94a3b8"/> : <Eye size={16} color="#94a3b8"/>}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{...styles.btn, opacity: loading ? 0.75 : 1}}
              >
                {loading
                  ? <span style={styles.spinner}/>
                  : <><span>Kirish</span><ArrowRight size={17}/></>
                }
              </button>
            </form>

            <div style={styles.badges}>
              {['Admin','Kafedra mudiri','Ilmiy rahbar','Talaba'].map(r=>(
                <span key={r} style={styles.badge}>{r}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');
        @keyframes blob { 0%,100%{border-radius:60% 40% 30% 70%/60% 30% 70% 40%} 50%{border-radius:30% 60% 70% 40%/50% 60% 30% 60%} }
        @keyframes spin { to{transform:rotate(360deg)} }
        @keyframes up { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
      `}</style>
    </div>
  )
}

const styles = {
  root:{ minHeight:'100vh', background:'linear-gradient(135deg,#0f0c29,#302b63,#24243e)', display:'flex', alignItems:'center', justifyContent:'center', position:'relative', overflow:'hidden', padding:'24px', fontFamily:"'DM Sans',sans-serif" },
  blob1:{ position:'absolute', width:'500px', height:'500px', background:'radial-gradient(circle,rgba(99,102,241,0.35) 0%,transparent 70%)', top:'-100px', left:'-100px', animation:'blob 8s ease-in-out infinite', borderRadius:'60% 40% 30% 70%/60% 30% 70% 40%' },
  blob2:{ position:'absolute', width:'400px', height:'400px', background:'radial-gradient(circle,rgba(139,92,246,0.3) 0%,transparent 70%)', bottom:'-80px', right:'-80px', animation:'blob 10s ease-in-out infinite reverse', borderRadius:'30% 60% 70% 40%/50% 60% 30% 60%' },
  grid:{ position:'absolute', inset:0, backgroundImage:'linear-gradient(rgba(255,255,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.03) 1px,transparent 1px)', backgroundSize:'60px 60px' },
  wrapper:{ position:'relative', zIndex:10, display:'flex', gap:'48px', width:'100%', maxWidth:'1020px', alignItems:'center' },
  left:{ flex:1, color:'#fff', animation:'up 0.6s ease forwards' },
  logoRow:{ display:'flex', alignItems:'center', gap:'12px', marginBottom:'44px' },
  logoBox:{ width:'48px', height:'48px', background:'linear-gradient(135deg,#6366f1,#8b5cf6)', borderRadius:'14px', display:'flex', alignItems:'center', justifyContent:'center', boxShadow:'0 8px 32px rgba(99,102,241,0.45)' },
  logoText:{ fontSize:'22px', fontWeight:'700', fontFamily:"'Sora',sans-serif", background:'linear-gradient(135deg,#fff,#c4b5fd)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' },
  title:{ fontSize:'52px', fontWeight:'800', lineHeight:1.1, fontFamily:"'Sora',sans-serif", color:'#fff', marginBottom:'20px' },
  titleAccent:{ background:'linear-gradient(135deg,#818cf8,#c084fc)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' },
  sub:{ fontSize:'15px', lineHeight:1.75, color:'rgba(255,255,255,0.5)', maxWidth:'360px', marginBottom:'44px' },
  stats:{ display:'flex', gap:'36px' },
  statNum:{ fontSize:'28px', fontWeight:'700', fontFamily:"'Sora',sans-serif", background:'linear-gradient(135deg,#fff,#a5b4fc)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' },
  statLabel:{ fontSize:'12px', color:'rgba(255,255,255,0.4)', fontWeight:'500', marginTop:'3px' },
  right:{ width:'420px', flexShrink:0, animation:'up 0.6s ease 0.15s both' },
  card:{ background:'rgba(255,255,255,0.98)', borderRadius:'28px', padding:'40px', boxShadow:'0 32px 80px rgba(0,0,0,0.5),0 0 0 1px rgba(255,255,255,0.08)' },
  cardIconBox:{ width:'44px', height:'44px', background:'linear-gradient(135deg,#eef2ff,#e0e7ff)', borderRadius:'12px', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'16px' },
  cardTitle:{ fontSize:'26px', fontWeight:'700', fontFamily:"'Sora',sans-serif", color:'#0f172a', marginBottom:'6px' },
  cardSub:{ fontSize:'14px', color:'#64748b', marginBottom:'28px' },
  form:{ display:'flex', flexDirection:'column', gap:'18px' },
  field:{ display:'flex', flexDirection:'column', gap:'7px' },
  label:{ fontSize:'13px', fontWeight:'600', color:'#374151', letterSpacing:'0.02em' },
  input:{ width:'100%', padding:'13px 16px', border:'2px solid #e2e8f0', borderRadius:'12px', fontSize:'15px', color:'#0f172a', outline:'none', transition:'border-color 0.2s', background:'#f8fafc', fontFamily:"'DM Sans',sans-serif" },
  eyeBtn:{ position:'absolute', right:'14px', top:'50%', transform:'translateY(-50%)', background:'none', border:'none', cursor:'pointer', display:'flex', alignItems:'center' },
  btn:{ marginTop:'6px', padding:'14px', background:'linear-gradient(135deg,#6366f1,#8b5cf6)', color:'#fff', border:'none', borderRadius:'12px', fontSize:'15px', fontWeight:'600', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', gap:'8px', boxShadow:'0 8px 24px rgba(99,102,241,0.45)', transition:'all 0.2s', fontFamily:"'DM Sans',sans-serif" },
  spinner:{ width:'18px', height:'18px', border:'2px solid rgba(255,255,255,0.3)', borderTopColor:'#fff', borderRadius:'50%', display:'inline-block', animation:'spin 0.7s linear infinite' },
  badges:{ display:'flex', flexWrap:'wrap', gap:'8px', marginTop:'24px', paddingTop:'20px', borderTop:'1px solid #f1f5f9' },
  badge:{ padding:'4px 12px', background:'#f1f5f9', borderRadius:'20px', fontSize:'12px', fontWeight:'500', color:'#64748b' },
}