import { useEffect, useState } from 'react'
import { loadAuthorizedVideo, VIDEO_SERVER_ENABLED } from './videoApi'

/** Playback is gated until the server verifies JWT and post visibility per request. */
export default function PostVideo({ postId }: { postId: string }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    if (!VIDEO_SERVER_ENABLED) { setError('動画再生は安全なサーバー接続の準備中です。'); return }
    let active = true
    let objectUrl = ''
    setUrl('')
    setError('')
    void loadAuthorizedVideo(postId).then(value => {
      objectUrl = value
      if (active) setUrl(value)
      else URL.revokeObjectURL(value)
    }).catch(() => {
      if (active) setError('動画を読み込めません。権限を確認してください。')
    })
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [postId])
  if (error) return <p role="status">{error}</p>
  if (!url) return <p role="status">動画を読み込み中...</p>
  return <video controls playsInline preload="metadata" src={url}
    style={{ width: '100%', maxHeight: 480, borderRadius: 12, margin: '10px 0 14px' }} />
}
