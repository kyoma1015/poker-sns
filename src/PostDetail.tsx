import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
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
  parent_comment_id: string | null
  image_urls?: string[] | null
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
  image_urls?: string[] | null
}

function PostDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const refreshRootRef = useRef<HTMLElement | null>(null)

  const [post, setPost] = useState<Post | null>(null)
  const [currentUserId, setCurrentUserId] = useState('')
  const [commentInput, setCommentInput] = useState('')
  const [replyTo, setReplyTo] = useState<{ id: string; name: string } | null>(null)
  const [submittingComment, setSubmittingComment] = useState(false)
  const [message, setMessage] = useState('読み込み中...')
  const [expandedImage, setExpandedImage] = useState<string | null>(null)
  const deletingCommentRef = useRef(false)
  const [deletingCommentId, setDeletingCommentId] = useState<string | null>(null)
  const commentImageInputRef = useRef<HTMLInputElement | null>(null)
  const [commentImageFiles, setCommentImageFiles] = useState<File[]>([])
  const [commentImagePreviews, setCommentImagePreviews] = useState<string[]>([])
  const MAX_COMMENT_IMAGES = 4

  useEffect(() => {
    const urls = commentImageFiles.map(file => URL.createObjectURL(file))
    setCommentImagePreviews(urls)
    return () => urls.forEach(url => URL.revokeObjectURL(url))
  }, [commentImageFiles])

  const chooseCommentImages = (files: FileList | null) => {
    if (!files) return
    const selected = Array.from(files)
    if (selected.some(file => !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024)) {
      setMessage('画像はJPEG・PNG・WebP形式、各5MB以内にしてください。')
      return
    }
    if (selected.length + commentImageFiles.length > MAX_COMMENT_IMAGES) {
      setMessage('コメントに添付できる画像は最大4枚です。')
      return
    }
    setCommentImageFiles(previous => [...previous, ...selected])
    setMessage('')
  }


  const loadPost = async (quiet = false) => {
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
    // 手動更新では投稿を一度消さず、既存の表示・入力状態を維持する。
    if (!quiet) {
      setPost(null)
      setMessage('読み込み中...')
    }
    let blockedUserIds: Set<string>
    try {
      blockedUserIds = await getBlockedUserIds(user.id)
    } catch (blockError) {
      console.error('ブロック情報取得エラー:', blockError)
      setMessage('ブロック情報を取得できませんでした。再読み込みしてください。')
      return
    }

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

    if (blockedUserIds.has(postData.user_id)) {
      setPost(null)
      setMessage('この投稿は表示できません。')
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
      (comments || []).filter(comment => !blockedUserIds.has(comment.user_id))
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

  // 下書きや返信先、操作中の状態がある間はPull to Refreshを許可しない。
  // Hook自体の判定に加え、更新処理を開始する直前にも条件を確認する。
  const refreshAllowed = Boolean(post) && !commentInput.trim() && !replyTo &&
    !submittingComment && commentImageFiles.length === 0 && !deletingCommentId && !expandedImage
  const refreshAllowedRef = useRef(refreshAllowed)
  refreshAllowedRef.current = refreshAllowed
  const { pullDistance, isRefreshing, refreshError } = usePullToRefresh(
    refreshRootRef,
    {
      enabled: refreshAllowed,
      onRefresh: async () => {
        if (!refreshAllowedRef.current) return
        await loadPost(true)
      },
    },
  )

  useEffect(() => {
    void loadPost()
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
    if (!post || !currentUserId || submittingComment) return
    const trimmedComment = commentInput.trim()
    // 既存DBのcontent制約を壊さないよう、画像添付時も本文を必須にする。
    if (!trimmedComment) {
      setMessage('コメント本文を入力してください（画像だけでは送信できません）。')
      return
    }

    const replyTarget = replyTo ? post.comments.find(c => c.id === replyTo.id) : null
    if (replyTo && !replyTarget) {
      setMessage('返信先が見つかりません。再読み込みしてください。')
      return
    }

    setSubmittingComment(true)
    const uploadedPaths: string[] = []
    const uploadedUrls: string[] = []
    let commentSaved = false
    const bucket = supabase.storage.from('comment-images')
    try {
      const { data: { user }, error: authError } = await supabase.auth.getUser()
      if (authError || !user || user.id !== currentUserId) {
        setMessage('ログイン情報を確認できません。再ログインしてください。')
        return
      }

      // ユーザーID直下に保存。ストレージRLSも同じIDを検証する。
      for (const file of commentImageFiles) {
        const extension = file.type === 'image/png' ? 'png' : file.type === 'image/webp' ? 'webp' : 'jpg'
        const path = `${user.id}/${crypto.randomUUID()}.${extension}`
        const { error: uploadError } = await bucket.upload(path, file, { contentType: file.type, upsert: false })
        if (uploadError) throw new Error(`画像アップロード失敗：${uploadError.message}`)
        uploadedPaths.push(path)
        uploadedUrls.push(bucket.getPublicUrl(path).data.publicUrl)
      }

      const { error } = await supabase
        .from('post_comments')
        .insert({
          post_id: post.id,
          user_id: currentUserId,
          content: trimmedComment,
          parent_comment_id: replyTarget ? (replyTarget.parent_comment_id || replyTarget.id) : null,
          image_urls: uploadedUrls,
        })
      if (error) throw new Error(`コメントできませんでした：${error.message}`)
      commentSaved = true

      // 保存が確定したら初めて入力・画像・返信先をクリアする。
      setCommentInput('')
      setCommentImageFiles([])
      if (commentImageInputRef.current) commentImageInputRef.current.value = ''
      setReplyTo(null)
      setMessage('')

      if (post.user_id !== currentUserId) {
        const { error: notificationError } = await supabase
          .from('notifications')
          .insert({ user_id: post.user_id, actor_id: currentUserId, type: 'comment', post_id: post.id })
        if (notificationError) console.error('コメント通知作成エラー:', notificationError)
      }
      await loadPost(true)
    } catch (error) {
      console.error('コメント送信エラー:', error)
      // 失敗時は本文・画像選択・返信先を保持し、今回アップロードした画像だけ掃除する。
      if (!commentSaved && uploadedPaths.length) {
        const { error: cleanupError } = await bucket.remove(uploadedPaths)
        if (cleanupError) console.error('失敗した画像の片付けに失敗:', cleanupError)
      }
      setMessage(error instanceof Error ? error.message : 'コメントの送信に失敗しました。')
    } finally {
      setSubmittingComment(false)
    }
  }

  const handleDeleteComment = async (commentId: string) => {
    if (deletingCommentRef.current || !post) return
    const target = post.comments.find(comment => comment.id === commentId)
    if (!target || !currentUserId || target.user_id !== currentUserId) {
      setMessage('自分のコメントのみ削除できます。')
      return
    }
    // キャンセルではDBへの通信を一切実行しない。
    if (!window.confirm('このコメントを削除しますか？この操作は取り消せません。')) return

    deletingCommentRef.current = true
    setDeletingCommentId(commentId)
    try {
      const { data: { user }, error: authError } = await supabase.auth.getUser()
      if (authError || !user || user.id !== currentUserId || user.id !== target.user_id) {
        setMessage('ログイン情報を確認できません。再度ログインしてください。')
        return
      }
      const { data: deleted, error } = await supabase
        .from('post_comments')
        .delete()
        .eq('id', commentId)
        .eq('user_id', user.id)
        .select('id')
      if (error) {
        console.error(error)
        setMessage(`コメントを削除できませんでした：${error.message}`)
        return
      }
      if (!deleted || deleted.length !== 1) {
        setMessage('コメントが見つからないか、削除権限がありません。')
        return
      }
      // コメント削除が確定してから、そのコメント専用の画像だけを削除する。
      const publicPrefix = supabase.storage.from('comment-images').getPublicUrl('').data.publicUrl
      const ownFolder = `${user.id}/`
      const paths = (target.image_urls || []).flatMap(url => {
        if (!url.startsWith(publicPrefix)) return []
        const path = url.slice(publicPrefix.length).replace(/^\/+/, '').split('?')[0]
        return path.startsWith(ownFolder) && !path.includes('..') ? [path] : []
      })
      if (paths.length) {
        const { error: imageDeleteError } = await supabase.storage.from('comment-images').remove(paths)
        if (imageDeleteError) console.error('コメント画像の削除エラー:', imageDeleteError)
      }
      setMessage('')
      await loadPost()
    } finally {
      deletingCommentRef.current = false
      setDeletingCommentId(null)
    }
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
    <main className="app" ref={refreshRootRef}>
      <div className="card">
        <h1 className="logo">Poker ID</h1>
        <p className="subtitle">投稿</p>
        {(pullDistance > 0 || isRefreshing || refreshError) && (
          <div role="status" aria-live="polite" style={{ textAlign: 'center', padding: '9px 12px', color: refreshError ? '#ff9999' : '#aaa', fontSize: 12 }}>
            {refreshError || (isRefreshing ? '投稿を更新中...' : pullDistance >= 76 ? '指を離すと更新' : '下に引っ張って更新')}
          </div>
        )}

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

              {Array.isArray(post.image_urls) && post.image_urls.length > 0 && (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: post.image_urls.length === 1 ? '1fr' : 'repeat(2, minmax(0, 1fr))',
                    gap: '6px',
                    marginTop: '12px',
                    marginBottom: '12px',
                  }}
                >
                  {post.image_urls.map((url, index) => (
                    <button
                      key={`${url}-${index}`}
                      type="button"
                      onClick={() => setExpandedImage(url)}
                      aria-label={`画像${index + 1}を拡大`}
                      style={{
                        display: 'block',
                        padding: 0,
                        width: '100%',
                        border: 'none',
                        borderRadius: '10px',
                        background: '#181818',
                        overflow: 'hidden',
                        cursor: 'zoom-in',
                      }}
                    >
                      <img
                        src={url}
                        alt={`投稿画像 ${index + 1}`}
                        loading="lazy"
                        style={{
                          display: 'block',
                          width: '100%',
                          maxHeight: post.image_urls?.length === 1 ? '520px' : '260px',
                          objectFit: 'cover',
                        }}
                      />
                    </button>
                  ))}
                </div>
              )}

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
                  type="button"
                  onClick={handleLike}
                  aria-label={post.likedByMe ? 'いいねを解除' : 'いいねする'}
                  aria-pressed={post.likedByMe}
                  style={{
                    width: 'auto',
                    minHeight: '38px',
                    padding: '8px 14px',
                    fontSize: '14px',
                    fontWeight: 700,
                    color: post.likedByMe ? '#ff8f9b' : '#d4d4d4',
                    background: post.likedByMe ? '#2b1b20' : '#1c1c1c',
                    border: `1px solid ${post.likedByMe ? '#75424c' : '#3a3a3a'}`,
                    borderRadius: '12px',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '5px',
                    transition: 'background 150ms ease, border-color 150ms ease',
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
                ref={commentImageInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                multiple
                aria-label="コメントに添付する画像を選択"
                style={{ display: 'none' }}
                onChange={event => {
                  chooseCommentImages(event.target.files)
                  event.target.value = ''
                }}
              />
              <input
                type="text"
                placeholder={replyTo ? `${replyTo.name}に返信する...` : 'コメントを書く...'}
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
                type="button"
                aria-label="コメントに画像を添付"
                title="画像を添付（最大4枚）"
                disabled={submittingComment || commentImageFiles.length >= MAX_COMMENT_IMAGES}
                onClick={() => commentImageInputRef.current?.click()}
                style={{ width: 'auto', flexShrink: 0, minHeight: 40, padding: '8px 10px', background: '#242424', color: '#ddd', border: '1px solid #454545', borderRadius: 10, cursor: 'pointer' }}
              >
                ＋画像
              </button>
              <button
                type="button"
                onClick={handleComment}
                disabled={submittingComment}
                style={{
                  width: 'auto',
                  minWidth: '64px',
                  minHeight: '40px',
                  flexShrink: 0,
                  padding: '9px 14px',
                  fontSize: '13px',
                  fontWeight: 750,
                  color: submittingComment ? '#888' : '#f4f4f4',
                  background: submittingComment ? '#1a1a1a' : '#292929',
                  border: '1px solid #454545',
                  borderRadius: '10px',
                  cursor: submittingComment ? 'wait' : 'pointer',
                  transition: 'background 150ms ease, border-color 150ms ease',
                }}
              >
                {submittingComment ? '送信中...' : '送信'}
              </button>
            </div>
            {commentImagePreviews.length > 0 && (
              <div style={{ paddingBottom: 12, textAlign: 'left' }}>
                <div style={{ color: '#aaa', fontSize: 12, marginBottom: 8 }}>添付画像 {commentImagePreviews.length}/4（JPEG・PNG・WebP／各5MB以内）</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 8 }}>
                  {commentImagePreviews.map((url, index) => (
                    <div key={url} style={{ position: 'relative' }}>
                      <img src={url} alt={`添付予定画像${index + 1}`} style={{ display: 'block', width: '100%', maxHeight: 160, objectFit: 'cover', borderRadius: 8 }} />
                      <button
                        type="button"
                        aria-label={`添付予定画像${index + 1}を解除`}
                        disabled={submittingComment}
                        onClick={() => setCommentImageFiles(files => files.filter((_, i) => i !== index))}
                        style={{ position: 'absolute', top: 4, right: 4, width: 30, height: 30, padding: 0, borderRadius: 20, border: '1px solid #555', background: '#1b1b1b', color: '#fff' }}
                      >×</button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {replyTo && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 12, color: '#aaa', fontSize: 12 }}>
                <span>{replyTo.name}への返信を作成中</span>
                <button type="button" onClick={() => setReplyTo(null)} style={{ width: 'auto', padding: '4px 8px', fontSize: 12 }}>解除</button>
              </div>
            )}

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
                [...post.comments]
                  .sort((a, b) => {
                    const rootA = a.parent_comment_id || a.id
                    const rootB = b.parent_comment_id || b.id
                    const rootCommentA = post.comments.find(c => c.id === rootA) || a
                    const rootCommentB = post.comments.find(c => c.id === rootB) || b
                    const rootOrder = new Date(rootCommentA.created_at).getTime() - new Date(rootCommentB.created_at).getTime()
                    if (rootOrder !== 0) return rootOrder
                    if (a.parent_comment_id === null && b.parent_comment_id !== null) return -1
                    if (a.parent_comment_id !== null && b.parent_comment_id === null) return 1
                    return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                  })
                  .map((comment) => (
                  <div
                    key={comment.id}
                    style={{
                      padding: '16px 0',
                      paddingLeft: comment.parent_comment_id ? '28px' : 0,
                      borderLeft: comment.parent_comment_id ? '2px solid #333' : undefined,
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

                    {comment.parent_comment_id && (
                      <div style={{ marginLeft: 48, marginTop: 8, color: '#999', fontSize: 12 }}>
                        ↳ {post.comments.find(c => c.id === comment.parent_comment_id)?.profile?.display_name || 'コメント'}への返信
                      </div>
                    )}
                    <p
                      style={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        marginLeft: '48px',
                      }}
                    >
                      {comment.content}
                    </p>
                    {Array.isArray(comment.image_urls) && comment.image_urls.length > 0 && (
                      <div style={{ marginLeft: 48, marginBottom: 12, display: 'grid', gridTemplateColumns: comment.image_urls.length === 1 ? '1fr' : 'repeat(2, minmax(0, 1fr))', gap: 6 }}>
                        {comment.image_urls.map((url, index) => (
                          <button
                            key={`${url}-${index}`}
                            type="button"
                            aria-label={`コメント画像${index + 1}を拡大`}
                            onClick={() => setExpandedImage(url)}
                            style={{ width: '100%', padding: 0, border: 0, borderRadius: 8, overflow: 'hidden', background: '#191919', cursor: 'zoom-in' }}
                          >
                            <img src={url} alt={`コメント添付画像${index + 1}`} loading="lazy" style={{ display: 'block', width: '100%', maxHeight: 240, objectFit: 'cover' }} />
                          </button>
                        ))}
                      </div>
                    )}

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

                      <button
                        type="button"
                        onClick={() => {
                          setReplyTo({ id: comment.parent_comment_id || comment.id, name: comment.profile?.display_name || 'プレイヤー' })
                          setMessage('')
                        }}
                        style={{ width: 'auto', padding: '4px 8px', fontSize: '11px' }}
                      >返信</button>
                      {currentUserId ===
                        comment.user_id && (
                        <button
                          type="button"
                          disabled={deletingCommentId !== null}
                          onClick={() => { void handleDeleteComment(comment.id) }}
                          style={{
                            width: 'auto',
                            padding: '4px 8px',
                            fontSize: '11px',
                          }}
                        >
                          {deletingCommentId === comment.id ? '削除中...' : '削除'}
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {expandedImage && (
          <div
            role="presentation"
            onClick={() => setExpandedImage(null)}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 1000,
              background: 'rgba(0,0,0,0.92)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '20px',
              boxSizing: 'border-box',
              cursor: 'zoom-out',
            }}
          >
            <button
              type="button"
              onClick={() => setExpandedImage(null)}
              aria-label="拡大画像を閉じる"
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                width: '42px',
                height: '42px',
                fontSize: '26px',
                color: '#fff',
                background: '#333',
                border: 'none',
                borderRadius: '50%',
                cursor: 'pointer',
              }}
            >
              ×
            </button>
            <img
              src={expandedImage}
              alt="拡大した投稿画像"
              onClick={(event) => event.stopPropagation()}
              style={{ maxWidth: '100%', maxHeight: '90vh', objectFit: 'contain' }}
            />
          </div>
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