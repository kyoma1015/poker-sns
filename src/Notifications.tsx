import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'


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

  const [notifications, setNotifications] =
    useState<NotificationItem[]>([])

  const [message, setMessage] =
    useState('読み込み中...')

  useEffect(() => {
    const loadNotifications = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser()

      if (!user) {
        navigate('/login')
        return
      }

      const { data, error } = await supabase
        .from('notifications')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', {
          ascending: false,
        })

      if (error) {
        console.error(error)
        setMessage(
          `通知の取得に失敗しました：${error.message}`
        )
        return
      }

      if (!data || data.length === 0) {
        setNotifications([])
        setMessage('')
        return
      }

      let blockedUserIds: Set<string>
      try {
        blockedUserIds = await getBlockedUserIds(user.id)
      } catch (blockError) {
        console.error('ブロック情報取得エラー:', blockError)
        setNotifications([])
        setMessage('ブロック情報を取得できませんでした。再読み込みしてください。')
        return
      }
      const visibleData = data.filter(notification => !blockedUserIds.has(notification.actor_id))
      if (visibleData.length === 0) {
        setNotifications([])
        setMessage('')
        return
      }

      const actorIds = [
        ...new Set(
          visibleData.map(
            (notification) =>
              notification.actor_id
          )
        ),
      ]

      const {
        data: profiles,
        error: profileError,
      } = await supabase
        .from('profiles')
        .select(
          'id, display_name, poker_id, avatar_url'
        )
        .in('id', actorIds)

      if (profileError) {
        console.error(profileError)
        setMessage(
          `プロフィールの取得に失敗しました：${profileError.message}`
        )
        return
      }

      const notificationList: NotificationItem[] =
        visibleData.map((notification) => {
          const actor = profiles?.find(
            (profile) =>
              profile.id ===
              notification.actor_id
          )

          return {
            ...notification,
            actorName:
              actor?.display_name ||
              'Unknown Player',
            actorPokerId:
              actor?.poker_id ||
              'unknown',
            actorAvatarUrl:
              actor?.avatar_url ||
              null,
          }
        })

      setNotifications(
        notificationList
      )

      setMessage('')

      const unreadIds = visibleData
        .filter(
          (notification) =>
            notification.read_at ===
            null
        )
        .map(
          (notification) =>
            notification.id
        )

      if (unreadIds.length > 0) {
        const readAt =
          new Date().toISOString()

        const { error: readError } =
          await supabase
            .from('notifications')
            .update({
              read_at: readAt,
            })
            .in('id', unreadIds)

        if (readError) {
          console.error(
            '通知既読エラー:',
            readError
          )
        } else {
          setNotifications(
            (previous) =>
              previous.map(
                (notification) =>
                  unreadIds.includes(
                    notification.id
                  )
                    ? {
                        ...notification,
                        read_at:
                          readAt,
                      }
                    : notification
              )
          )
        }
      }
    }

    loadNotifications()
  }, [navigate])

  const getNotificationText = (
    notification: NotificationItem
  ) => {
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
          'comment') &&
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
    <main className="app">
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
                    <div
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
                    </div>

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
                        <button
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
                        </button>

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
                        <span
                          onClick={(
                            event
                          ) =>
                            handleActorClick(
                              event,
                              notification.actor_id
                            )
                          }
                          style={{
                            cursor:
                              'pointer',
                          }}
                        >
                          @
                          {
                            notification.actorPokerId
                          }
                        </span>

                        <span>·</span>

                        <span>
                          {formatNotificationTime(
                            notification.created_at
                          )}
                        </span>
                      </div>
                    </div>

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