import { useEffect, useState, useRef, useCallback } from 'react'
import { messagesContactsApi, usersApi } from '../../api/api'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'
import { Send, MessageSquare, Search, UserPlus, Users } from 'lucide-react'

function Avatar({ name, size = 38 }) {
  const initials = name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?'
  const colors = ['#6366f1', '#8b5cf6', '#0ea5e9', '#22c55e', '#f59e0b', '#ef4444']
  const color = colors[name?.charCodeAt(0) % colors.length] || '#6366f1'
  return (
    <div style={{ width: size, height: size, borderRadius: '50%', background: `${color}20`, border: `2px solid ${color}40`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: size * 0.32, fontWeight: '700', color, flexShrink: 0 }}>
      {initials}
    </div>
  )
}

function OnlineDot({ online }) {
  if (!online) return null
  return (
    <span style={{ position: 'absolute', bottom: 0, right: 0, width: 10, height: 10, borderRadius: '50%', background: '#22c55e', border: '2px solid #fff' }} />
  )
}

export default function Messages() {
  const { user } = useAuthStore()
  const [contacts, setContacts] = useState([])
  const [selected, setSelected] = useState(null)        // { type: 'direct', user_id, full_name } or { type: 'supervisor_group', supervisor_user_id, name }
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [search, setSearch] = useState('')
  const [onlineIds, setOnlineIds] = useState(new Set())
  const [showSearch, setShowSearch] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('direct') // 'direct' | 'group'
  const [supervisorGroup, setSupervisorGroup] = useState(null) // { supervisor_user_id, name }
  const bottomRef = useRef(null)
  const wsRef = useRef(null)
  const selectedRef = useRef(null)
  useEffect(() => { selectedRef.current = selected }, [selected])

  const loadContacts = useCallback(async () => {
    try {
      const { data } = await messagesContactsApi.contacts()
      setContacts(data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }, [])

  const refreshCurrentConversation = useCallback(async () => {
    const current = selectedRef.current
    if (!current) return
    try {
      if (current.type === 'supervisor_group') {
        const { data } = await messagesContactsApi.supervisorGroup(current.supervisor_user_id)
        setMessages(data)
      } else {
        const { data } = await messagesContactsApi.conversation(current.user_id)
        setMessages(data)
      }
    } catch { /* silent */ }
  }, [])

  // Load supervisor group info
  const loadSupervisorGroup = useCallback(async () => {
    try {
      if (user?.role === 'supervisor') {
        // Supervisor's own group (their user_id is the group ID)
        setSupervisorGroup({ supervisor_user_id: user.id, name: `${user.full_name} guruhi` })
      } else if (user?.role === 'student') {
        // Student: find their supervisor
        const { data } = await usersApi.mySupervisor()
        if (data?.user_id) {
          setSupervisorGroup({ supervisor_user_id: data.user_id, name: `${data.full_name} guruhi` })
        }
      }
    } catch { /* silent */ }
  }, [user])

  const loadConversation = useCallback(async (contact) => {
    setSelected({ type: 'direct', user_id: contact.user_id, full_name: contact.full_name })
    try {
      const { data } = await messagesContactsApi.conversation(contact.user_id)
      setMessages(data)
      setContacts(prev => prev.map(c =>
        c.user_id === contact.user_id ? { ...c, unread_count: 0 } : c
      ))
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch { toast.error('Xabarlar yuklanmadi') }
  }, [])

  const loadSupervisorGroupConversation = useCallback(async (group) => {
    setSelected({ type: 'supervisor_group', supervisor_user_id: group.supervisor_user_id, name: group.name })
    try {
      const { data } = await messagesContactsApi.supervisorGroup(group.supervisor_user_id)
      setMessages(data)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch { toast.error('Guruh xabarlari yuklanmadi') }
  }, [])

  const handleSend = useCallback(async () => {
    if (!text.trim() || !selected) return
    setSending(true)
    const content = text.trim()
    setText('')
    try {
      if (selected.type === 'supervisor_group') {
        const { data: msg } = await messagesContactsApi.sendSupervisorGroup({ supervisor_user_id: selected.supervisor_user_id, content })
        setMessages(prev => prev.some(m => m.id === msg.id) ? prev : [...prev, msg])
      } else {
        const { data: msg } = await messagesContactsApi.send({ receiver_id: selected.user_id, content })
        setMessages(prev => prev.some(m => m.id === msg.id) ? prev : [...prev, msg])
        setContacts(prev => prev.map(c =>
          c.user_id === selected.user_id ? { ...c, last_message: content } : c
        ))
      }
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    } catch {
      toast.error('Yuborilmadi')
      setText(content)
    }
    finally { setSending(false) }
  }, [text, selected])

  // User search for new conversations
  const handleUserSearch = useCallback(async (q) => {
    setSearchQuery(q)
    if (q.trim().length < 2) { setSearchResults([]); return }
    setSearchLoading(true)
    try {
      const { data } = await usersApi.search(q.trim())
      setSearchResults(data)
    } catch { /* silent */ }
    finally { setSearchLoading(false) }
  }, [])

  const startConversation = useCallback((foundUser) => {
    setShowSearch(false)
    setSearchQuery('')
    setSearchResults([])
    // Add to contacts list if not already there
    setContacts(prev => {
      if (prev.some(c => c.user_id === foundUser.id)) return prev
      return [{ user_id: foundUser.id, full_name: foundUser.full_name, last_message: '', last_message_at: new Date().toISOString(), unread_count: 0 }, ...prev]
    })
    setSelected({ type: 'direct', user_id: foundUser.id, full_name: foundUser.full_name })
    setMessages([])
    // Load existing conversation
    messagesContactsApi.conversation(foundUser.id)
      .then(({ data }) => setMessages(data))
      .catch(() => {})
  }, [])

  // WebSocket connection
  const connectWs = useCallback(() => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    const prevWs = wsRef.current
    if (prevWs && (prevWs.readyState === WebSocket.OPEN || prevWs.readyState === WebSocket.CONNECTING)) {
      prevWs.onclose = null
      prevWs.close()
    }

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${protocol}://${location.host}/ws?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (e) => {
      let event
      try { event = JSON.parse(e.data) } catch { return }
      const cur = selectedRef.current

      switch (event.type) {
        case 'online_users':
          setOnlineIds(new Set(event.user_ids))
          break
        case 'user_online':
          setOnlineIds(prev => new Set([...prev, event.user_id]))
          break
        case 'user_offline':
          setOnlineIds(prev => { const s = new Set(prev); s.delete(event.user_id); return s })
          break
        case 'message': {
          const msg = event.message
          if (msg.sender_id !== user?.id) {
            if (cur?.type === 'direct' && (msg.sender_id === cur.user_id || msg.receiver_id === cur.user_id)) {
              setMessages(prev => prev.some(m => m.id === msg.id) ? prev : [...prev, msg])
              setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
              setContacts(prev => prev.map(c =>
                c.user_id === msg.sender_id ? { ...c, last_message: msg.content, unread_count: 0 } : c
              ))
            } else {
              setContacts(prev => {
                const exists = prev.some(c => c.user_id === msg.sender_id)
                if (exists) {
                  return prev.map(c =>
                    c.user_id === msg.sender_id
                      ? { ...c, last_message: msg.content, unread_count: (c.unread_count || 0) + 1 }
                      : c
                  )
                }
                loadContacts()
                return prev
              })
            }
          }
          break
        }
        case 'supervisor_group_message': {
          const msg = event.message
          if (cur?.type === 'supervisor_group' && cur.supervisor_user_id === event.supervisor_user_id && msg.sender_id !== user?.id) {
            setMessages(prev => prev.some(m => m.id === msg.id) ? prev : [...prev, msg])
            setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
          }
          break
        }
        default: break
      }
    }

    ws.onclose = () => {
      // cPanel/Passenger often blocks WebSocket; the polling fallback below keeps chat usable.
    }
    ws.onerror = () => { try { ws.close() } catch { /* silent */ } }
  }, [user?.id, loadContacts])

  useEffect(() => { loadContacts(); loadSupervisorGroup() }, [loadContacts, loadSupervisorGroup])
  useEffect(() => {
    connectWs()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connectWs])

  useEffect(() => {
    const sync = async () => {
      await loadContacts()
      await refreshCurrentConversation()
    }
    sync()
    const interval = setInterval(sync, 12000)
    return () => clearInterval(interval)
  }, [loadContacts, refreshCurrentConversation])

  const filteredContacts = contacts.filter(c => c.full_name.toLowerCase().includes(search.toLowerCase()))

  const isGroup = selected?.type === 'supervisor_group'
  const selectedName = isGroup ? `👥 ${selected?.name}` : selected?.full_name

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0', fontFamily: "'DM Sans',sans-serif", height: 'calc(100vh - 104px)' }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#1e293b', fontFamily: "'Sora',sans-serif" }}>Xabarlar</h2>
        <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '3px' }}>Yozishmalar va guruh suhbatlar</p>
      </div>

      <div style={{ display: 'flex', flex: 1, background: '#fff', borderRadius: '16px', border: '1px solid #e8ecf4', overflow: 'hidden', minHeight: 0 }}>
        {/* Contacts sidebar */}
        <div style={{ width: '280px', borderRight: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #f1f5f9' }}>
            <button onClick={() => setActiveTab('direct')}
              style={{ flex: 1, padding: '12px 8px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: activeTab === 'direct' ? '700' : '500', color: activeTab === 'direct' ? '#6366f1' : '#94a3b8', borderBottom: activeTab === 'direct' ? '2px solid #6366f1' : '2px solid transparent' }}>
              💬 Shaxsiy
            </button>
            <button onClick={() => setActiveTab('group')}
              style={{ flex: 1, padding: '12px 8px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: activeTab === 'group' ? '700' : '500', color: activeTab === 'group' ? '#6366f1' : '#94a3b8', borderBottom: activeTab === 'group' ? '2px solid #6366f1' : '2px solid transparent' }}>
              👥 Guruh
            </button>
          </div>

          {activeTab === 'direct' && (
            <>
              <div style={{ padding: '12px', borderBottom: '1px solid #f1f5f9', display: 'flex', gap: '8px' }}>
                <div style={{ position: 'relative', flex: 1 }}>
                  <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                  <input value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="Qidirish..."
                    style={{ width: '100%', paddingLeft: '32px', paddingRight: '12px', paddingTop: '8px', paddingBottom: '8px', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }} />
                </div>
                <button onClick={() => setShowSearch(s => !s)} title="Yangi suhbat boshlash"
                  style={{ width: '36px', height: '36px', borderRadius: '8px', background: showSearch ? '#6366f1' : '#eef2ff', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <UserPlus size={16} color={showSearch ? '#fff' : '#6366f1'} />
                </button>
              </div>

              {/* User search panel */}
              {showSearch && (
                <div style={{ padding: '12px', borderBottom: '1px solid #f1f5f9', background: '#fafbff' }}>
                  <div style={{ fontSize: '12px', fontWeight: '600', color: '#6366f1', marginBottom: '8px' }}>Foydalanuvchi qidirish</div>
                  <input value={searchQuery} onChange={e => handleUserSearch(e.target.value)}
                    placeholder="Ism yoki email..."
                    autoFocus
                    style={{ width: '100%', padding: '8px 12px', border: '1px solid #c7d2fe', borderRadius: '8px', fontSize: '13px', outline: 'none', boxSizing: 'border-box', marginBottom: '8px' }} />
                  {searchLoading && <div style={{ fontSize: '12px', color: '#94a3b8' }}>Qidirilmoqda...</div>}
                  {searchResults.map(u => (
                    <button key={u.id} onClick={() => startConversation(u)}
                      style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px', border: 'none', background: '#fff', cursor: 'pointer', borderRadius: '8px', marginBottom: '4px', textAlign: 'left' }}>
                      <Avatar name={u.full_name} size={32} />
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: '600', color: '#1e293b' }}>{u.full_name}</div>
                        <div style={{ fontSize: '11px', color: '#94a3b8' }}>{u.email}</div>
                      </div>
                    </button>
                  ))}
                  {searchQuery.length >= 2 && !searchLoading && searchResults.length === 0 && (
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>Topilmadi</div>
                  )}
                </div>
              )}

              <div style={{ flex: 1, overflowY: 'auto' }}>
                {loading ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '40px', color: '#94a3b8' }}>Yuklanmoqda...</div>
                ) : filteredContacts.length === 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px 20px', color: '#94a3b8', textAlign: 'center' }}>
                    <MessageSquare size={32} style={{ marginBottom: '10px', opacity: 0.3 }} />
                    <p style={{ fontSize: '13px' }}>Yozishmalar yo'q</p>
                    <p style={{ fontSize: '12px', marginTop: '4px' }}>Yangi suhbat boshlash uchun <strong>+</strong> tugmasini bosing</p>
                  </div>
                ) : (
                  filteredContacts.map(c => (
                    <button key={c.user_id} onClick={() => loadConversation(c)}
                      style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', padding: '14px 16px', border: 'none', background: selected?.user_id === c.user_id && selected?.type === 'direct' ? '#f5f3ff' : 'none', cursor: 'pointer', borderBottom: '1px solid #f8fafc', textAlign: 'left' }}>
                      <div style={{ position: 'relative' }}>
                        <Avatar name={c.full_name} size={40} />
                        <OnlineDot online={onlineIds.has(c.user_id)} />
                        {c.unread_count > 0 && (
                          <span style={{ position: 'absolute', top: -2, right: -2, width: '18px', height: '18px', background: '#6366f1', color: '#fff', borderRadius: '50%', fontSize: '10px', fontWeight: '700', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{c.unread_count}</span>
                        )}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '14px', fontWeight: c.unread_count > 0 ? '700' : '500', color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.full_name}</span>
                          {onlineIds.has(c.user_id) && (
                            <span style={{ fontSize: '10px', color: '#22c55e', fontWeight: '600', flexShrink: 0 }}>• online</span>
                          )}
                        </div>
                        <div style={{ fontSize: '12px', color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: '2px' }}>{c.last_message}</div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </>
          )}

          {activeTab === 'group' && (
            <div style={{ flex: 1, overflowY: 'auto' }}>
              {!supervisorGroup ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px 20px', color: '#94a3b8', textAlign: 'center' }}>
                  <Users size={32} style={{ marginBottom: '10px', opacity: 0.3 }} />
                  <p style={{ fontSize: '13px' }}>Guruh suhbat mavjud emas</p>
                  <p style={{ fontSize: '12px', marginTop: '4px' }}>Rahbar biriktirilgandan so'ng guruh yaratiladi</p>
                </div>
              ) : (
                <button onClick={() => loadSupervisorGroupConversation(supervisorGroup)}
                  style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', padding: '14px 16px', border: 'none', background: selected?.type === 'supervisor_group' ? '#f5f3ff' : 'none', cursor: 'pointer', borderBottom: '1px solid #f8fafc', textAlign: 'left' }}>
                  <div style={{ width: 40, height: 40, borderRadius: '50%', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px', flexShrink: 0 }}>👥</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{supervisorGroup.name}</div>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                      {user?.role === 'supervisor' ? 'Barcha o\'quvchilarim' : 'Rahbar guruhi'}
                    </div>
                  </div>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Conversation panel */}
        {selected ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 20px', borderBottom: '1px solid #f1f5f9' }}>
              <div style={{ position: 'relative' }}>
                {isGroup
                  ? <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px' }}>👥</div>
                  : <><Avatar name={selected.full_name} size={36} /><OnlineDot online={onlineIds.has(selected.user_id)} /></>
                }
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>{selectedName}</div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                  {isGroup ? (user?.role === 'supervisor' ? 'Barcha o\'quvchilarim' : 'Rahbar guruhi') : onlineIds.has(selected.user_id) ? 'Online' : 'Offline'}
                </div>
              </div>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {messages.map(m => {
                const isMe = m.sender_id === user?.id
                return (
                  <div key={m.id} style={{ display: 'flex', justifyContent: isMe ? 'flex-end' : 'flex-start' }}>
                    <div style={{
                      maxWidth: '65%', padding: '10px 14px', borderRadius: isMe ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                      background: isMe ? '#6366f1' : '#f1f5f9',
                      color: isMe ? '#fff' : '#1e293b', fontSize: '14px', lineHeight: 1.5,
                    }}>
                      {isGroup && !isMe && m.sender_name && (
                        <div style={{ fontSize: '11px', fontWeight: '600', color: '#6366f1', marginBottom: '4px' }}>{m.sender_name}</div>
                      )}
                      <div>{m.content}</div>
                      <div style={{ fontSize: '11px', color: isMe ? 'rgba(255,255,255,0.65)' : '#94a3b8', marginTop: '4px', textAlign: 'right' }}>
                        {new Date(m.created_at).toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })}
                        {isMe && !isGroup && <span style={{ marginLeft: '4px' }}>{m.is_read ? '✓✓' : '✓'}</span>}
                      </div>
                    </div>
                  </div>
                )
              })}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div style={{ padding: '14px 20px', borderTop: '1px solid #f1f5f9', display: 'flex', gap: '10px' }}>
              <input value={text} onChange={e => setText(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                placeholder="Xabar yozing..."
                style={{ flex: 1, padding: '10px 16px', border: '1px solid #e2e8f0', borderRadius: '24px', fontSize: '14px', outline: 'none' }} />
              <button onClick={handleSend} disabled={!text.trim() || sending}
                style={{ width: '42px', height: '42px', borderRadius: '50%', background: text.trim() ? '#6366f1' : '#f1f5f9', border: 'none', cursor: text.trim() ? 'pointer' : 'not-allowed', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'background 0.15s', flexShrink: 0 }}>
                <Send size={17} color={text.trim() ? '#fff' : '#94a3b8'} />
              </button>
            </div>
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', gap: '12px' }}>
            <MessageSquare size={48} style={{ opacity: 0.2 }} />
            <p style={{ fontSize: '14px' }}>Suhbat boshlash uchun kontakt tanlang</p>
            <p style={{ fontSize: '13px', color: '#c7d2fe' }}>Yangi suhbat uchun <strong>+</strong> tugmasini bosing</p>
          </div>
        )}
      </div>
    </div>
  )
}
