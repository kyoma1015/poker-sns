import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { supabase } from './supabase'

type Profile = {
  display_name: string
  poker_id: string
  avatar_url: string | null
}

type Comment = {
  id: string
  post_id: string
  user_id: string
  content: string
  created_at: string
  profile?: Profile
}

type Post = {
  id: string
  user_id: string
  content: string
  created_at: string
  profile?: Profile
  likeCount: number
  likedByMe: boolean
  comments: Comment[]
}

function PostDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [post, setPost] = useState<Post | null>(null)
  const [currentUserId, setCurrentUserId] = useState('')
  const [commentInput, setCommentInput] = useState('')
  const [message, setMessage] = useState('読み込み中...')

  const loadPost = async () => {
    if (!id) {
      setMessage('投稿が見つかりませんでした。')
      return
    }

    const {
      data: { user },
    } = await supabase.auth.getUser()

    if (!user) {
      navigate('/login')
      return
    }

    setCurrentUserId(user.id)

    const { data: postData, error } = await supabase
      .from('posts')
      .select('*')
      .eq('id', id)
      .maybeSingle()

    if (error) {
      console.error(error)
      setMessage(
        `投稿の取得に失敗しました：${error.message}`
      )
      return
    }

    if (!postData) {
      setPost(null)
      setMessage('投稿が見つかりませんでした。')
      return
    }

    const { data: likes, error: likesError } =
      await supabase
        .from('post_likes')
        .select('user_id')
        .eq('post_id', id)

    if (likesError) {
      console.error(likesError)
      setMessage(
        `いいね情報の取得に失敗しました：${likesError.message}`
      )
      return
    }

    const { data: comments, error: commentsError } =
      await supabase
        .from('post_comments')
        .select('*')
        .eq('post_id', id)
        .order('created_at', { ascending: true })

    if (commentsError) {
      console.error(commentsError)
      setMessage(
        `コメントの取得に失敗しました：${commentsError.message}`
      )
      return
    }

    const profileUserIds = [
      ...new Set([
        postData.user_id,
        ...(comments || []).map(
          (comment) => comment.user_id
        ),
      ]),
    ]

    const { data: profiles, error: profileError } =
      await supabase
        .from('profiles')
        .select(
          'id, display_name, poker_id, avatar_url'
        )
        .in('id', profileUserIds)

    if (profileError) {
      console.error(profileError)
      setMessage(
        `プロフィールの取得に失敗しました：${profileError.message}`
      )
      return
    }

    const postProfile = profiles?.find(
      (profile) => profile.id === postData.user_id
    )

    const commentsWithProfiles: Comment[] = (
      comments || []
    ).map((comment) => {
      const commentProfile = profiles?.find(
        (profile) => profile.id === comment.user_id
      )

      return {
        ...comment,
        profile: commentProfile
          ? {
              display_name:
                commentProfile.display_name,
              poker_id: commentProfile.poker_id,
              avatar_url: commentProfile.avatar_url,
            }
          : undefined,
      }
    })

    setPost({
      ...postData,
      profile: postProfile
        ? {
            display_name: postProfile.display_name,
            poker_id: postProfile.poker_id,
            avatar_url: postProfile.avatar_url,
          }
        : undefined,
      likeCount: likes?.length || 0,
      likedByMe:
        likes?.some(
          (like) => like.user_id === user.id
        ) || false,
      comments: commentsWithProfiles,
    })

    setMessage('')
  }

  useEffect(() => {
    loadPost()
  }, [id])

  const handleLike = async () => {
    if (!post || !currentUserId) return

    if (post.likedByMe) {
      const { error } = await supabase
        .from('post_likes')
        .delete()
        .eq('post_id', post.id)
        .eq('user_id', currentUserId)

      if (error) {
        console.error(error)
        setMessage(
          `いいねを解除できませんでした：${error.message}`
        )
        return
      }
    } else {
      const { error } = await supabase
        .from('post_likes')
        .insert({
          post_id: post.id,
          user_id: currentUserId,
        })

      if (error) {
        console.error(error)
        setMessage(
          `いいねできませんでした：${error.message}`
        )
        return
      }

      if (post.user_id !== currentUserId) {
        const { error: notificationError } =
          await supabase
            .from('notifications')
            .insert({
              user_id: post.user_id,
              actor_id: currentUserId,
              type: 'like',
              post_id: post.id,
            })

        /*
          23505 は、
          同じユーザーから同じ投稿への
          いいね通知がすでに存在している場合の
          DB側の重複エラー。

          いいね解除後の再いいねでは
          通知を増やさないため、
          このエラーだけ正常動作として無視する。
        */
        if (
          notificationError &&
          notificationError.code !== '23505'
        ) {
          console.error(
            'いいね通知作成エラー:',
            notificationError
          )
        }
      }
    }

    setMessage('')
    await loadPost()
  }

  const handleComment = async () => {
    if (!post || !currentUserId) return

    const trimmedComment = commentInput.trim()

    if (!trimmedComment) {
      setMessage('コメントを入力してください。')
      return
    }

    const { error } = await supabase
      .from('post_comments')
      .insert({
        post_id: post.id,
        user_id: currentUserId,
        content: trimmedComment,
      })

    if (error) {
      console.error(error)
      setMessage(
        `コメントできませんでした：${error.message}`
      )
      return
    }

    if (post.user_id !== currentUserId) {
      const { error: notificationError } =
        await supabase
          .from('notifications')
          .insert({
            user_id: post.user_id,
            actor_id: currentUserId,
            type: 'comment',
            post_id: post.id,
          })

      if (notificationError) {
        console.error(
          'コメント通知作成エラー:',
          notificationError
        )
      }
    }

    setCommentInput('')
    setMessage('')
    await loadPost()
  }

  const handleDeleteComment = async (
    commentId: string
  ) => {
    const { error } = await supabase
      .from('post_comments')
      .delete()
      .eq('id', commentId)

    if (error) {
      console.error(error)
      setMessage(
        `コメントを削除できませんでした：${error.message}`
      )
      return
    }

    setMessage('')
    await loadPost()
  }

  const handleProfileClick = (userId: string) => {
    if (userId === currentUserId) {
      navigate('/profile')
      return
    }

    navigate(`/player/${userId}`)
  }

  const renderAvatar = (
    profile: Profile | undefined,
    size: number
  ) => {
    if (profile?.avatar_url) {
      return (
        <img
          src={profile.avatar_url}
          alt={`${profile.display_name}のプロフィール画像`}
          style={{
            width: `${size}px`,
            height: `${size}px`,
            borderRadius: '50%',
            objectFit: 'cover',
            border: '1px solid #444',
            flexShrink: 0,
          }}
        />
      )
    }

    return (
      <div
        style={{
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: '50%',
          background: '#292929',
          border: '1px solid #444',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: `${Math.round(size * 0.43)}px`,
          flexShrink: 0,
        }}
      >
        ♠
      </div>
    )
  }

  return (
    <main className="app">
      <div className="card">
        <h1 className="logo">Poker ID</h1>
        <p className="subtitle">投稿</p>

        {message && <p>{message}</p>}

        {post && (
          <>
            <div
              style={{
                textAlign: 'left',
                borderTop: '1px solid #333',
                padding: '20px 0',
              }}
            >
              <div
                onClick={() =>
                  handleProfileClick(post.user_id)
                }
                style={{
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                }}
              >
                {renderAvatar(post.profile, 48)}

                <div style={{ minWidth: 0 }}>
                  <div>
                    <strong>
                      {post.profile?.display_name ||
                        'Unknown Player'}
                    </strong>
                  </div>

                  <div
                    style={{
                      color: '#888',
                      fontSize: '13px',
                      marginTop: '2px',
                    }}
                  >
                    @{post.profile?.poker_id || 'unknown'}
                  </div>
                </div>
              </div>

              <p
                style={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontSize: '17px',
                  lineHeight: '1.6',
                }}
              >
                {post.content}
              </p>

              <p
                style={{
                  color: '#777',
                  fontSize: '12px',
                }}
              >
                {new Date(
                  post.created_at
                ).toLocaleString('ja-JP')}
              </p>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginTop: '15px',
                }}
              >
                <button
                  onClick={handleLike}
                  style={{
                    width: 'auto',
                    padding: '6px 12px',
                    fontSize: '14px',
                  }}
                >
                  {post.likedByMe ? '♥' : '♡'}{' '}
                  {post.likeCount}
                </button>

                <span
                  style={{
                    color: '#aaa',
                    fontSize: '14px',
                  }}
                >
                  コメント {post.comments.length}
                </span>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                gap: '8px',
                padding: '18px 0',
                borderTop: '1px solid #333',
              }}
            >
              <input
                type="text"
                placeholder="コメントを書く..."
                value={commentInput}
                onChange={(e) =>
                  setCommentInput(e.target.value)
                }
                maxLength={300}
                style={{
                  flex: 1,
                  minWidth: 0,
                  padding: '10px',
                  boxSizing: 'border-box',
                  borderRadius: '8px',
                }}
              />

              <button
                onClick={handleComment}
                style={{
                  width: 'auto',
                  padding: '8px 12px',
                  fontSize: '13px',
                }}
              >
                送信
              </button>
            </div>

            <div
              style={{
                textAlign: 'left',
                borderTop: '1px solid #333',
              }}
            >
              {post.comments.length === 0 ? (
                <p
                  style={{
                    color: '#888',
                    textAlign: 'center',
                    padding: '20px 0',
                  }}
                >
                  まだコメントはありません
                </p>
              ) : (
                post.comments.map((comment) => (
                  <div
                    key={comment.id}
                    style={{
                      padding: '16px 0',
                      borderBottom:
                        '1px solid #333',
                    }}
                  >
                    <div
                      onClick={() =>
                        handleProfileClick(
                          comment.user_id
                        )
                      }
                      style={{
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                      }}
                    >
                      {renderAvatar(
                        comment.profile,
                        38
                      )}

                      <div style={{ minWidth: 0 }}>
                        <div>
                          <strong>
                            {comment.profile
                              ?.display_name ||
                              'Unknown Player'}
                          </strong>
                        </div>

                        <div
                          style={{
                            color: '#888',
                            fontSize: '12px',
                            marginTop: '2px',
                          }}
                        >
                          @
                          {comment.profile
                            ?.poker_id ||
                            'unknown'}
                        </div>
                      </div>
                    </div>

                    <p
                      style={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        marginLeft: '48px',
                      }}
                    >
                      {comment.content}
                    </p>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        marginLeft: '48px',
                      }}
                    >
                      <span
                        style={{
                          color: '#666',
                          fontSize: '11px',
                        }}
                      >
                        {new Date(
                          comment.created_at
                        ).toLocaleString('ja-JP')}
                      </span>

                      {currentUserId ===
                        comment.user_id && (
                        <button
                          onClick={() =>
                            handleDeleteComment(
                              comment.id
                            )
                          }
                          style={{
                            width: 'auto',
                            padding: '4px 8px',
                            fontSize: '11px',
                          }}
                        >
                          削除
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        <button
          className="signup-button"
          onClick={() => navigate('/timeline')}
          style={{ marginTop: '25px' }}
        >
          タイムラインへ戻る
        </button>
      </div>
    </main>
  )
}

export default PostDetail