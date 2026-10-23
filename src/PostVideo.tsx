import { useEffect, useState } from 'react'
import { createPostVideoPlaybackUrl } from './videoUpload'

/** A private video is loaded only after Storage RLS approves a short-lived signed URL. */
export default function PostVideo({ path }: { path: string }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    setUrl('')
    setError('')
    void createPostVideoPlaybackUrl(path).then(value => {
      if (active) setUrl(value)
    }).catch(() => {
      if (active) setError('動画を読み込めません。権限または有効期限を確認してください。')
    })
    return () => { active = false }
  }, [path])
  if (error) return <p role="status">{error}</p>
  if (!url) return <p role="status">動画を読み込み中...</p>
  return <video controls playsInline preload="metadata" src={url}
    style={{ width: '100%', maxHeight: 480, borderRadius: 12, margin: '10px 0 14px' }} />
}
