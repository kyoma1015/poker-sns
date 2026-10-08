import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { supabase } from './supabase'

type UserProfile = {
  id: string
  display_name: string
  poker_id: string
  avatar_url: string | null
}

function FollowerList() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [users, setUsers] = useState<UserProfile[]>([])
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    const loadFollowers = async () => {
      setLoadError('')
      if (!id) {
        setUsers([])
        return
      }

      const { data: { user }, error: authError } = await supabase.auth.getUser()
      if (authError || !user) {
        setUsers([])
        navigate('/login')
        return
      }

      // ブロックは双方向に適用。取得失敗時は一覧を表示しない。
      const { data: blockRows, error: blockError } = await supabase
        .from('user_blocks')
        .select('blocker_id, blocked_id')
        .or(`blocker_id.eq.${user.id},blocked_id.eq.${user.id}`)

      if (blockError) {
        console.error('ブロック情報取得エラー:', blockError)
        setUsers([])
        setLoadError('ブロック情報を取得できませんでした。')
        return
      }

      const blockedIds = new Set<string>()
      for (const block of blockRows || []) {
        blockedIds.add(block.blocker_id === user.id ? block.blocked_id : block.blocker_id)
      }

      const { data, error } = await supabase
        .from('follows')
        .select('follower_id')
        .eq('following_id', id)

      if (error) {
        console.error(error)
        return
      }

      const followerIds = (data || [])
        .map((item) => item.follower_id)
        .filter((userId) => !blockedIds.has(userId))

      if (followerIds.length === 0) {
        setUsers([])
        return
      }

      const { data: profiles, error: profilesError } =
        await supabase
          .from('profiles')
          .select(
            'id, display_name, poker_id, avatar_url'
          )
          .in('id', followerIds)

      if (profilesError) {
        console.error(profilesError)
        return
      }

      setUsers((profiles || []).filter((profile) => !blockedIds.has(profile.id)))
    }

    loadFollowers()
  }, [id, navigate])

  return (
    <main className="app">
      <div className="card">
        <h1>フォロワー一覧</h1>

        {loadError && <p style={{ color: '#ff8888' }}>{loadError}</p>}

        {!loadError && users.length === 0 && (
          <p
            style={{
              color: '#999',
              marginTop: '30px',
            }}
          >
            フォロワーはいません
          </p>
        )}

        <div style={{ marginTop: '25px' }}>
          {users.map((user) => (
            <div
              key={user.id}
              onClick={() =>
                navigate(`/player/${user.id}`)
              }
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                textAlign: 'left',
                padding: '14px 0',
                borderTop: '1px solid #333',
                cursor: 'pointer',
              }}
            >
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={`${user.display_name}のプロフィール画像`}
                  style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: '1px solid #444',
                    flexShrink: 0,
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    background: '#292929',
                    border: '1px solid #444',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px',
                    flexShrink: 0,
                  }}
                >
                  ♠
                </div>
              )}

              <div
                style={{
                  flex: 1,
                  minWidth: 0,
                }}
              >
                <div
                  style={{
                    fontWeight: 'bold',
                  }}
                >
                  {user.display_name}
                </div>

                <div
                  style={{
                    color: '#888',
                    fontSize: '13px',
                    marginTop: '3px',
                  }}
                >
                  @{user.poker_id}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}

export default FollowerList