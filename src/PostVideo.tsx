import { useEffect, useState } from 'react'
import { loadAuthorizedVideo, VIDEO_SERVER_ENABLED } from './videoApi'
import { supabase } from './supabase'

/** Playback is gated until the server verifies JWT and post visibility per request. */
export default function PostVideo({ postId }: { postId: string }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    if (!VIDEO_SERVER_ENABLED) { setUrl(''); setError('動画再生は安全なサーバー接続の準備中です。'); return }
    let active = true
    let objectUrl = ''
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      // A Blob URL bypasses the server after the initial authorized fetch.
      // Discard the locally cached media as soon as the session ends or
      // changes, so an old authenticated video cannot keep playing.
      if (event === 'SIGNED_OUT' || event === 'USER_UPDATED') {
        active = false
        if (objectUrl) URL.revokeObjectURL(objectUrl)
        objectUrl = ''
        setUrl('')
        setError('動画を再生するには再読み込みしてください。')
      }
    })
    setUrl('')
    setError('')
    void loadAuthorizedVideo(postId).then(value => {
      objectUrl = value
      if (active) setUrl(value)
      else URL.revokeObjectURL(value)
    }).catch(() => {
      if (active) setError('動画を読み込めません。権限を確認してください。')
    })
    return () => { active = false; subscription.unsubscribe(); if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [postId])
  if (error) return <p role="status">{error}</p>
  if (!url) return <p role="status">動画を読み込み中...</p>
  return <video key={postId} controls playsInline preload="metadata" src={url}
    style={{ width: '100%', maxHeight: 480, borderRadius: 12, margin: '10px 0 14px' }} />
}
