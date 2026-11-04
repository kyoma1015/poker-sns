import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'
import { usePullToRefresh } from './usePullToRefresh'


// ブロックは双方の関係を確認する（自分→相手、相手→自分）。
async function getBlockedUserIds(userId: string): Promise<Set<string>> {
  const { data, error } = await supabase
    .from('user_blocks')
    .select('blocker_id, blocked_id')
    .or(`blocker_id.eq.${userId},blocked_id.eq.${userId}`)
  if (error) throw error
  return new Set((data || []).map(row => row.blocker_id === userId ? row.blocked_id : row.blocker_id))
}

type Conversation = {
  userId: string
  displayName: string
  pokerId: string
  avatarUrl: string | null
  lastMessage: string
  lastMessageAt: string
  unreadCount: number
}

function DirectMessages() {
  const navigate = useNavigate()
  const [accountId, setAccountId] = useState<string | null | undefined>(undefined)
  const authIdentity = useRef<string | null>(null)
  useEffect(() => {
    let active = true
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!active) return
      // Synchronous invalidation only: SDK calls inside this callback may deadlock.
      const id = session?.user?.id ?? null
      authIdentity.current = id
      setAccountId(id)
    })
    return () => { active = false; authIdentity.current = null; subscription.unsubscribe() }
  }, [])
  useEffect(() => { if (accountId === null) navigate('/login') }, [accountId, navigate])
  if (accountId === undefined) return <main className="app"><p>読み込み中...</p></main>
  if (accountId === null) return <main className="app"><p>ログインが必要です。</p></main>
  return <AccountInbox key={accountId} accountId={accountId} authIdentity={authIdentity} />
}

function AccountInbox({ accountId, authIdentity }: {
  accountId: string
  authIdentity: { current: string | null }
}) {
  const navigate = useNavigate()
  const refreshRootRef = useRef<HTMLElement | null>(null)
  const reloadRef = useRef<() => Promise<void>>(async () => {})
  const { pullDistance, isRefreshing, refreshError } = usePullToRefresh(refreshRootRef, {
    onRefresh: () => reloadRef.current(),
  })
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [message, setMessage] = useState('読み込み中...')
  const [readFailed, setReadFailed] = useState(false)

  useEffect(() => {
    let active = true
    let generation = 0
    const valid = () => active && authIdentity.current === accountId
    const loadConversations = async () => {
      if (!valid()) return
      const request = ++generation
      const current = () => valid() && generation === request
      try {
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (!current()) return
        if (authError || !user || user.id !== accountId) throw new Error('Authentication unavailable')
        const { data: messages, error } = await supabase
          .from('direct_messages')
          .select('*')
          .or(`sender_id.eq.${accountId},receiver_id.eq.${accountId}`)
          .order('created_at', { ascending: false })
        if (!current()) return
        if (error) throw error
        // This is defense in depth, never a replacement for server-side RLS.
        const ownedMessages = (messages || []).filter(dm =>
          dm.sender_id === accountId || dm.receiver_id === accountId)
        if (ownedMessages.length === 0) {
          setConversations([]); setMessage(''); setReadFailed(false)
          return
        }
        const blockedUserIds = await getBlockedUserIds(accountId)
        if (!current()) return
        const visibleMessages = ownedMessages.filter(dm =>
          !blockedUserIds.has(dm.sender_id === accountId ? dm.receiver_id : dm.sender_id))
        const otherUserIds = [...new Set(visibleMessages.map(dm =>
          dm.sender_id === accountId ? dm.receiver_id : dm.sender_id))]
        if (otherUserIds.length === 0) {
          setConversations([]); setMessage(''); setReadFailed(false)
          return
        }
        const { data: profiles, error: profileError } = await supabase
          .from('profiles').select('id, display_name, poker_id, avatar_url').in('id', otherUserIds)
        if (!current()) return
        if (profileError) throw profileError
        const conversationList: Conversation[] = otherUserIds.map(otherUserId => {
          const conversationMessages = visibleMessages.filter(dm =>
            (dm.sender_id === accountId && dm.receiver_id === otherUserId) ||
            (dm.sender_id === otherUserId && dm.receiver_id === accountId))
          const latestMessage = conversationMessages[0]
          const profile = profiles?.find(item => item.id === otherUserId)
          return {
            userId: otherUserId,
            displayName: profile?.display_name || 'Unknown Player',
            pokerId: profile?.poker_id || 'unknown',
            avatarUrl: profile?.avatar_url || null,
            lastMessage: latestMessage?.content || '',
            lastMessageAt: latestMessage?.created_at || '',
            unreadCount: conversationMessages.filter(dm =>
              dm.sender_id === otherUserId && dm.receiver_id === accountId && dm.read_at === null).length,
          }
        })
        conversationList.sort((a, b) => new Date(b.lastMessageAt).getTime() - new Date(a.lastMessageAt).getTime())
        setConversations(conversationList); setMessage(''); setReadFailed(false)
      } catch {
        if (!current()) return
        setConversations([])
        setMessage('DM一覧を読み込めませんでした。もう一度お試しください。')
        setReadFailed(true)
      }
    }
    reloadRef.current = loadConversations
    // Subscribe before the initial snapshot so an event during its read triggers
    // a newer generation instead of being silently missed.
    const channel = supabase.channel(`dm-list-${accountId}`)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'direct_messages' },
        () => { if (valid()) void loadConversations() })
      .subscribe()
    void loadConversations()
    return () => {
      active = false; generation++
      reloadRef.current = async () => {}
      void supabase.removeChannel(channel)
    }
  }, [accountId, authIdentity])

  const formatTime = (
    createdAt: string
  ) => {
    if (!createdAt) {
      return ''
    }

    const created =
      new Date(createdAt)

    const now = new Date()

    const difference =
      now.getTime() -
      created.getTime()

    const minutes = Math.floor(
      difference / 60000
    )

    if (minutes < 1) {
      return '今'
    }

    if (minutes < 60) {
      return `${minutes}分`
    }

    const hours = Math.floor(
      minutes / 60
    )

    if (hours < 24) {
      return `${hours}時間`
    }

    const days = Math.floor(
      hours / 24
    )

    if (days < 7) {
      return `${days}日`
    }

    return created.toLocaleDateString(
      'ja-JP',
      {
        month: 'numeric',
        day: 'numeric',
      }
    )
  }

  return (
    <main className="app" ref={refreshRootRef}>
      <div
        className="card"
        style={{
          paddingTop: 0,
        }}
      >
        {/* ヘッダー */}
        <header
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 20,
            margin: '0 -20px',
            padding: '16px 20px',
            background:
              'rgba(0, 0, 0, 0.94)',
            borderBottom:
              '1px solid #242424',
            backdropFilter:
              'blur(14px)',
            WebkitBackdropFilter:
              'blur(14px)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <button
              onClick={() =>
                navigate('/timeline')
              }
              aria-label="戻る"
              style={{
                width: '34px',
                height: '34px',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent:
                  'center',
                background:
                  'transparent',
                color: '#fff',
                borderRadius: '50%',
                fontSize: '25px',
                fontWeight: 300,
              }}
            >
              ‹
            </button>

            <div
              style={{
                fontSize: '20px',
                fontWeight: 800,
                letterSpacing:
                  '-0.4px',
              }}
            >
              メッセージ
            </div>
          </div>
        </header>

        {(pullDistance > 0 || isRefreshing || refreshError) && (
          <div role="status" aria-live="polite" style={{ padding: '9px 12px', textAlign: 'center', color: '#aaa', fontSize: 12 }}>
            {refreshError || (isRefreshing ? 'DM一覧を更新中...' : pullDistance >= 76 ? '離して更新' : '下に引っ張って更新')}
          </div>
        )}
        {/* 読み込み / エラー */}
        {message && (
          <div
            style={{
              padding: '60px 20px',
              color: '#777',
              fontSize: '13px',
              textAlign: 'center',
            }}
          >
            {message}
            {readFailed && <div><button type="button" onClick={() => { void reloadRef.current() }}>DM一覧を再読み込み</button></div>}
          </div>
        )}

        {/* DMなし */}
        {!message &&
          conversations.length ===
            0 && (
            <div
              style={{
                padding:
                  '80px 25px',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  margin:
                    '0 auto 18px',
                  display: 'flex',
                  alignItems:
                    'center',
                  justifyContent:
                    'center',
                  background: '#111',
                  border:
                    '1px solid #292929',
                  borderRadius: '50%',
                  fontSize: '27px',
                }}
              >
                ✉
              </div>

              <div
                style={{
                  fontSize: '17px',
                  fontWeight: 800,
                }}
              >
                メッセージはまだありません
              </div>

              <div
                style={{
                  marginTop: '8px',
                  color: '#666',
                  fontSize: '13px',
                  lineHeight: 1.6,
                }}
              >
                プレイヤーのプロフィールから
                <br />
                メッセージを送ることができます
              </div>

              <button
                onClick={() =>
                  navigate('/search')
                }
                style={{
                  width: 'auto',
                  marginTop: '22px',
                  padding:
                    '10px 18px',
                  background: '#fff',
                  color: '#000',
                  borderRadius:
                    '999px',
                  fontSize: '13px',
                  fontWeight: 800,
                }}
              >
                プレイヤーを探す
              </button>
            </div>
          )}

        {/* DM一覧 */}
        {!message &&
          conversations.length >
            0 && (
            <section
              style={{
                margin: '0 -20px',
              }}
            >
              {conversations.map(
                (conversation) => (
                  <div
                    key={
                      conversation.userId
                    }
                    onClick={() =>
                      navigate(
                        `/dm/${conversation.userId}`
                      )
                    }
                    style={{
                      display: 'flex',
                      alignItems:
                        'center',
                      gap: '13px',
                      padding:
                        '14px 20px',
                      borderBottom:
                        '1px solid #202020',
                      cursor: 'pointer',
                    }}
                  >
                    {/* アバター */}
                    <div
                      style={{
                        position:
                          'relative',
                        flexShrink: 0,
                      }}
                    >
                      {conversation.avatarUrl ? (
                        <img
                          src={
                            conversation.avatarUrl
                          }
                          alt={`${conversation.displayName}のプロフィール画像`}
                          style={{
                            width:
                              '56px',
                            height:
                              '56px',
                            borderRadius:
                              '50%',
                            objectFit:
                              'cover',
                            border:
                              '1px solid #333',
                            display:
                              'block',
                          }}
                        />
                      ) : (
                        <div
                          style={{
                            width:
                              '56px',
                            height:
                              '56px',
                            borderRadius:
                              '50%',
                            background:
                              '#171717',
                            border:
                              '1px solid #333',
                            display:
                              'flex',
                            alignItems:
                              'center',
                            justifyContent:
                              'center',
                            fontSize:
                              '22px',
                          }}
                        >
                          ♠
                        </div>
                      )}

                      {conversation.unreadCount >
                        0 && (
                        <div
                          style={{
                            position:
                              'absolute',
                            right: '-2px',
                            bottom: '-1px',
                            width:
                              '13px',
                            height:
                              '13px',
                            background:
                              '#fff',
                            border:
                              '3px solid #000',
                            borderRadius:
                              '50%',
                          }}
                        />
                      )}
                    </div>

                    {/* 会話情報 */}
                    <div
                      style={{
                        flex: 1,
                        minWidth: 0,
                      }}
                    >
                      <div
                        style={{
                          display:
                            'flex',
                          alignItems:
                            'center',
                          gap: '6px',
                          minWidth: 0,
                        }}
                      >
                        <span
                          style={{
                            overflow:
                              'hidden',
                            textOverflow:
                              'ellipsis',
                            whiteSpace:
                              'nowrap',
                            color: '#fff',
                            fontSize:
                              '15px',
                            fontWeight:
                              conversation.unreadCount >
                              0
                                ? 800
                                : 700,
                          }}
                        >
                          {
                            conversation.displayName
                          }
                        </span>

                        <span
                          style={{
                            overflow:
                              'hidden',
                            textOverflow:
                              'ellipsis',
                            whiteSpace:
                              'nowrap',
                            color: '#666',
                            fontSize:
                              '12px',
                          }}
                        >
                          @
                          {
                            conversation.pokerId
                          }
                        </span>
                      </div>

                      <div
                        style={{
                          display:
                            'flex',
                          alignItems:
                            'center',
                          gap: '6px',
                          marginTop:
                            '5px',
                          minWidth: 0,
                        }}
                      >
                        <span
                          style={{
                            flex: 1,
                            minWidth: 0,
                            overflow:
                              'hidden',
                            whiteSpace:
                              'nowrap',
                            textOverflow:
                              'ellipsis',
                            color:
                              conversation.unreadCount >
                              0
                                ? '#f2f2f2'
                                : '#777',
                            fontSize:
                              '13px',
                            fontWeight:
                              conversation.unreadCount >
                              0
                                ? 600
                                : 400,
                          }}
                        >
                          {
                            conversation.lastMessage
                          }
                        </span>

                        {conversation.lastMessageAt && (
                          <>
                            <span
                              style={{
                                color:
                                  '#555',
                                fontSize:
                                  '11px',
                              }}
                            >
                              ·
                            </span>

                            <span
                              style={{
                                flexShrink: 0,
                                color:
                                  conversation.unreadCount >
                                  0
                                    ? '#aaa'
                                    : '#555',
                                fontSize:
                                  '11px',
                              }}
                            >
                              {formatTime(
                                conversation.lastMessageAt
                              )}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* 未読数 */}
                    {conversation.unreadCount >
                      0 && (
                      <div
                        style={{
                          minWidth:
                            '23px',
                          height: '23px',
                          padding:
                            '0 7px',
                          flexShrink: 0,
                          display:
                            'flex',
                          alignItems:
                            'center',
                          justifyContent:
                            'center',
                          background:
                            '#fff',
                          color: '#000',
                          borderRadius:
                            '999px',
                          fontSize:
                            '11px',
                          fontWeight: 800,
                        }}
                      >
                        {conversation.unreadCount >
                        99
                          ? '99+'
                          : conversation.unreadCount}
                      </div>
                    )}

                    <span
                      style={{
                        flexShrink: 0,
                        color: '#444',
                        fontSize: '22px',
                      }}
                    >
                      ›
                    </span>
                  </div>
                )
              )}
            </section>
          )}
      </div>
    </main>
  )
}

export default DirectMessages