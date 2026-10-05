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

  useEffect(() => {
    const loadFollowers = async () => {
      if (!id) {
        setUsers([])
        return
      }

      const { data, error } = await supabase
        .from('follows')
        .select('follower_id')
        .eq('following_id', id)

      if (error) {
        console.error(error)
        return
      }

      const followerIds = (data || []).map(
        (item) => item.follower_id
      )

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

      setUsers(profiles || [])
    }

    loadFollowers()
  }, [id])

  return (
    <main className="app">
      <div className="card">
        <h1>フォロワー一覧</h1>

        {users.length === 0 && (
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