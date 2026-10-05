import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'

function Home() {
  const navigate = useNavigate()

  const [unreadDmCount, setUnreadDmCount] = useState(0)
  const [unreadNotificationCount, setUnreadNotificationCount] = useState(0)

  useEffect(() => {
    let channel: ReturnType<typeof supabase.channel> | null = null
    let isActive = true

    const setupUnreadCounts = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser()

      if (!user) {
        navigate('/login')
        return
      }

      const loadUnreadDmCount = async () => {
        const { count, error } = await supabase
          .from('direct_messages')
          .select('*', {
            count: 'exact',
            head: true,
          })
          .eq('receiver_id', user.id)
          .is('read_at', null)

        if (error) {
          console.error('未読DM取得エラー:', error)
          return
        }

        if (isActive) {
          setUnreadDmCount(count || 0)
        }
      }

      const loadUnreadNotificationCount = async () => {
        const { count, error } = await supabase
          .from('notifications')
          .select('*', {
            count: 'exact',
            head: true,
          })
          .eq('user_id', user.id)
          .is('read_at', null)

        if (error) {
          console.error('未読通知取得エラー:', error)
          return
        }

        if (isActive) {
          setUnreadNotificationCount(count || 0)
        }
      }

      await Promise.all([
        loadUnreadDmCount(),
        loadUnreadNotificationCount(),
      ])

      if (!isActive) return

      channel = supabase
        .channel(`home-unread-${user.id}`)
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'direct_messages',
          },
          () => {
            loadUnreadDmCount()
          }
        )
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'notifications',
          },
          () => {
            loadUnreadNotificationCount()
          }
        )
        .subscribe()
    }

    setupUnreadCounts()

    return () => {
      isActive = false

      if (channel) {
        supabase.removeChannel(channel)
      }
    }
  }, [navigate])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <main className="app">
      <div className="card">
        <h1 className="logo">Poker ID</h1>
        <p className="subtitle">ホーム</p>

        <div className="buttons">
          <button
            className="signup-button"
            onClick={() => navigate('/timeline')}
          >
            タイムライン
          </button>

          <button
            className="signup-button"
            onClick={() => navigate('/search')}
          >
            プレイヤー検索
          </button>

          <button
            className="signup-button"
            onClick={() => navigate('/notifications')}
            style={{
              position: 'relative',
            }}
          >
            通知

            {unreadNotificationCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  right: '14px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  minWidth: '22px',
                  height: '22px',
                  padding: '0 6px',
                  boxSizing: 'border-box',
                  borderRadius: '11px',
                  background: '#ffffff',
                  color: '#111111',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {unreadNotificationCount > 99
                  ? '99+'
                  : unreadNotificationCount}
              </span>
            )}
          </button>

          <button
            className="signup-button"
            onClick={() => navigate('/dm')}
            style={{
              position: 'relative',
            }}
          >
            DM

            {unreadDmCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  right: '14px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  minWidth: '22px',
                  height: '22px',
                  padding: '0 6px',
                  boxSizing: 'border-box',
                  borderRadius: '11px',
                  background: '#ffffff',
                  color: '#111111',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {unreadDmCount > 99 ? '99+' : unreadDmCount}
              </span>
            )}
          </button>

          <button
            className="signup-button"
            onClick={() => navigate('/profile')}
          >
            マイプロフィール
          </button>

          <button
            className="signup-button"
            onClick={handleLogout}
          >
            ログアウト
          </button>
        </div>
      </div>
    </main>
  )
}

export default Home