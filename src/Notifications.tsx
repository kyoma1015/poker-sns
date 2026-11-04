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

type NotificationItem = {
  id: string
  created_at: string
  user_id: string
  actor_id: string
  type: string
  post_id: string | null
  read_at: string | null
  actorName: string
  actorPokerId: string
  actorAvatarUrl: string | null
}

function Notifications() {
  const navigate = useNavigate()
  const [accountId, setAccountId] = useState<string | null | undefined>(undefined)
  const authIdentity = useRef<string | null>(null)
  useEffect(() => {
    let active = true
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!active) return
      const id = session?.user?.id ?? null
      // Never call/await the SDK in its auth callback; invalidate before render.
      authIdentity.current = id
      setAccountId(id)
    })
    return () => { active = false; authIdentity.current = null; subscription.unsubscribe() }
  }, [])
  useEffect(() => { if (accountId === null) navigate('/login') }, [accountId, navigate])
  if (accountId === undefined) return <main className="app"><p>読み込み中...</p></main>
  if (accountId === null) return <main className="app"><p>ログインが必要です。</p></main>
  return <AccountNotifications key={accountId} accountId={accountId} authIdentity={authIdentity} />
}

function AccountNotifications({ accountId, authIdentity }: {
  accountId: string
  authIdentity: { current: string | null }
}) {
  const navigate = useNavigate()
  const refreshRootRef = useRef<HTMLElement | null>(null)
  const reloadNotificationsRef = useRef<() => Promise<void>>(async () => {})
  const { pullDistance, isRefreshing, refreshError } = usePullToRefresh(
    refreshRootRef, { onRefresh: () => reloadNotificationsRef.current() },
  )
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [message, setMessage] = useState('読み込み中...')
  const [openedUnreadIds, setOpenedUnreadIds] = useState<string[]>([])
  const [readFailed, setReadFailed] = useState(false)

  useEffect(() => {
    let active = true
    let generation = 0
    const valid = () => active && authIdentity.current === accountId
    const loadNotifications = async () => {
      if (!valid()) return
      const request = ++generation
      const current = () => valid() && generation === request
      let displayed = false
      try {
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (!current()) return
        if (authError || user?.id !== accountId) throw new Error('Authentication unavailable')
        const { data, error } = await supabase.from('notifications').select('*')
          .eq('user_id', accountId).order('created_at', { ascending: false })
        if (!current()) return
        if (error) throw error
        const owned = (data || []).filter(n => n.user_id === accountId)
        const blocked = owned.length ? await getBlockedUserIds(accountId) : new Set<string>()
        if (!current()) return
        const visible = owned.filter(n => !blocked.has(n.actor_id))
        const actors = [...new Set(visible.map(n => n.actor_id))]
        let profiles: { id: string; display_name: string | null; poker_id: string | null; avatar_url: string | null }[] = []
        if (actors.length) {
          const result = await supabase.from('profiles')
            .select('id, display_name, poker_id, avatar_url').in('id', actors)
          if (!current()) return
          if (result.error) throw result.error
          profiles = result.data || []
        }
        const items: NotificationItem[] = visible.map(n => {
          const actor = profiles.find(p => p.id === n.actor_id)
          return { ...n, actorName: actor?.display_name || 'Unknown Player',
            actorPokerId: actor?.poker_id || 'unknown', actorAvatarUrl: actor?.avatar_url || null }
        })
        const unreadIds = visible.filter(n => n.read_at === null).map(n => n.id)
        setNotifications(items); setOpenedUnreadIds(unreadIds); setMessage(''); setReadFailed(false)
        displayed = true
        if (!unreadIds.length) return
        // A missed auth event must not let the prior account acknowledge rows.
        const verified = await supabase.auth.getUser()
        if (!current()) return
        if (verified.error || verified.data.user?.id !== accountId) {
          displayed = false
          throw new Error('Authentication changed')
        }
        const readAt = new Date().toISOString()
        const updated = await supabase.from('notifications').update({ read_at: readAt })
          .eq('user_id', accountId).in('id', unreadIds).is('read_at', null).select('id, read_at')
        if (!current()) return
        if (updated.error) throw updated.error
        // UPDATE may silently affect zero rows when policy denies access. Only
        // confirmed returned rows can become read in this client.
        const confirmed = new Set((updated.data || []).filter(n =>
          unreadIds.includes(n.id) && typeof n.read_at === 'string').map(n => n.id))
        if (confirmed.size) {
          setNotifications(previous => previous.map(n => confirmed.has(n.id) ? { ...n, read_at: readAt } : n))
          window.dispatchEvent(new Event('poker-id-notifications-updated'))
        }
        if (confirmed.size !== unreadIds.length) throw new Error('Read acknowledgement unavailable')
      } catch {
        if (!current()) return
        if (!displayed) { setNotifications([]); setOpenedUnreadIds([]) }
        setMessage(displayed
          ? '通知は表示できましたが、既読に更新できませんでした。もう一度お試しください。'
          : '通知を読み込めませんでした。もう一度お試しください。')
        setReadFailed(true)
      }
    }
    reloadNotificationsRef.current = loadNotifications
    const channel = supabase.channel(`notifications-${accountId}`)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'notifications', filter: `user_id=eq.${accountId}` },
        () => { if (valid()) void loadNotifications() })
      .subscribe()
    void loadNotifications()
    return () => {
      active = false; generation++
      reloadNotificationsRef.current = async () => {}
      void supabase.removeChannel(channel)
    }
  }, [accountId, authIdentity])

  const getNotificationText = (
    notification: NotificationItem
  ) => {
    if (notification.type === 'poll_closed') return 'アンケートが終了しました。結果を確認して、引用リポストでみんなにシェアしよう！'
    if (
      notification.type ===
      'follow'
    ) {
      return 'あなたをフォローしました'
    }

    if (
      notification.type === 'like'
    ) {
      return 'あなたの投稿にいいねしました'
    }

    if (
      notification.type ===
      'comment'
    ) {
      return 'あなたの投稿にコメントしました'
    }

    return '新しい通知があります'
  }

  const getNotificationIcon = (
    notification: NotificationItem
  ) => {
    if (notification.type === 'poll_closed') return '📊'
    if (
      notification.type ===
      'follow'
    ) {
      return '♠'
    }

    if (
      notification.type === 'like'
    ) {
      return '♥'
    }

    if (
      notification.type ===
      'comment'
    ) {
      return '♧'
    }

    return '•'
  }

  const getNotificationIconColor = (
    notification: NotificationItem
  ) => {
    if (
      notification.type === 'like'
    ) {
      return '#ff4d6d'
    }

    return '#fff'
  }

  const formatNotificationTime = (
    createdAt: string
  ) => {
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
      return 'たった今'
    }

    if (minutes < 60) {
      return `${minutes}分前`
    }

    const hours = Math.floor(
      minutes / 60
    )

    if (hours < 24) {
      return `${hours}時間前`
    }

    const days = Math.floor(
      hours / 24
    )

    if (days < 7) {
      return `${days}日前`
    }

    return created.toLocaleDateString(
      'ja-JP',
      {
        month: 'numeric',
        day: 'numeric',
      }
    )
  }

  const handleNotificationClick = (
    notification: NotificationItem
  ) => {
    if (
      (notification.type ===
        'like' ||
        notification.type ===
          'comment' || notification.type === 'poll_closed') &&
      notification.post_id
    ) {
      navigate(
        `/post/${notification.post_id}`
      )
      return
    }

    navigate(
      `/player/${notification.actor_id}`
    )
  }

  const handleActorClick = (
    event: React.MouseEvent,
    actorId: string
  ) => {
    event.stopPropagation()

    navigate(
      `/player/${actorId}`
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
              fontSize: '20px',
              fontWeight: 800,
              letterSpacing:
                '-0.4px',
            }}
          >
            通知
          </div>
        </header>

        {(pullDistance > 0 || isRefreshing || refreshError) && (
          <div role="status" aria-live="polite" style={{ textAlign: 'center', padding: '9px 12px', color: '#aaa', fontSize: 12 }}>
            {refreshError || (isRefreshing ? '通知を更新中...' : pullDistance >= 76 ? '指を離すと更新' : '下に引っ張って更新')}
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
            {readFailed && <div><button type="button" onClick={() => { void reloadNotificationsRef.current() }}>通知を再読み込み</button></div>}
          </div>
        )}

        {/* 通知なし */}
        {!message &&
          notifications.length ===
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
                  width: '62px',
                  height: '62px',
                  margin:
                    '0 auto 17px',
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
                ♡
              </div>

              <div
                style={{
                  fontSize: '17px',
                  fontWeight: 800,
                }}
              >
                通知はまだありません
              </div>

              <div
                style={{
                  marginTop: '8px',
                  color: '#666',
                  fontSize: '13px',
                  lineHeight: 1.6,
                }}
              >
                フォロー・いいね・コメントなどの
                <br />
                アクティビティがここに表示されます
              </div>
            </div>
          )}

        {/* 通知一覧 */}
        {!message &&
          notifications.length >
            0 && (
            <section
              style={{
                margin: '0 -20px',
              }}
            >
              {notifications.map(
                (notification) => (
                  <div
                    key={
                      notification.id
                    }
                    onClick={() =>
                      handleNotificationClick(
                        notification
                      )
                    }
                    style={{
                      position:
                        'relative',
                      display: 'flex',
                      alignItems:
                        'flex-start',
                      gap: '12px',
                      padding:
                        '15px 20px',
                      borderBottom:
                        '1px solid #202020',
                      cursor: 'pointer',
                    }}
                  >
                    {/* 通知種類アイコン */}
                    <div
                      style={{
                        width: '25px',
                        flexShrink: 0,
                        paddingTop: '11px',
                        color:
                          getNotificationIconColor(
                            notification
                          ),
                        fontSize: '20px',
                        fontWeight: 700,
                        textAlign:
                          'center',
                        lineHeight: 1,
                      }}
                    >
                      {getNotificationIcon(
                        notification
                      )}
                    </div>

                    {/* アバター */}
                    {notification.type !== 'poll_closed' && <div
                      onClick={(
                        event
                      ) =>
                        handleActorClick(
                          event,
                          notification.actor_id
                        )
                      }
                      style={{
                        flexShrink: 0,
                        cursor:
                          'pointer',
                      }}
                    >
                      {notification.actorAvatarUrl ? (
                        <img
                          src={
                            notification.actorAvatarUrl
                          }
                          alt={`${notification.actorName}のプロフィール画像`}
                          style={{
                            width:
                              '48px',
                            height:
                              '48px',
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
                              '48px',
                            height:
                              '48px',
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
                              '20px',
                          }}
                        >
                          ♠
                        </div>
                      )}
                    </div>}

                    {/* 通知本文 */}
                    <div
                      style={{
                        flex: 1,
                        minWidth: 0,
                        paddingTop: '1px',
                      }}
                    >
                      <div
                        style={{
                          fontSize:
                            '14px',
                          lineHeight:
                            1.55,
                          color:
                            '#dedede',
                        }}
                      >
                        {notification.type !== 'poll_closed' && <button
                          onClick={(
                            event
                          ) =>
                            handleActorClick(
                              event,
                              notification.actor_id
                            )
                          }
                          style={{
                            width:
                              'auto',
                            padding: 0,
                            marginRight:
                              '5px',
                            display:
                              'inline',
                            background:
                              'transparent',
                            color:
                              '#fff',
                            borderRadius: 0,
                            fontSize:
                              '14px',
                            fontWeight:
                              800,
                          }}
                        >
                          {
                            notification.actorName
                          }
                        </button>}

                        {getNotificationText(
                          notification
                        )}
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
                          color: '#666',
                          fontSize:
                            '12px',
                        }}
                      >
                        {notification.type !== 'poll_closed' && <><span onClick={(event)=>handleActorClick(event,notification.actor_id)} style={{cursor:'pointer'}}>@{notification.actorPokerId}</span><span>·</span></>}
                        <span>
                          {formatNotificationTime(
                            notification.created_at
                          )}
                        </span>
                      </div>
                    </div>

                    {openedUnreadIds.includes(notification.id) && (
                      <span style={{ alignSelf: 'center', flexShrink: 0, fontSize: 10, fontWeight: 800, color: '#d4d4ff' }}>
                        新着
                      </span>
                    )}
                    {/* 詳細への矢印 */}
                    <div
                      style={{
                        alignSelf:
                          'center',
                        flexShrink: 0,
                        color: '#444',
                        fontSize: '22px',
                      }}
                    >
                      ›
                    </div>
                  </div>
                )
              )}
            </section>
          )}
      </div>
    </main>
  )
}

export default Notifications
