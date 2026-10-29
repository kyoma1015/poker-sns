import { useEffect, useState } from 'react'
import { loadAuthorizedVideo, VIDEO_SERVER_ENABLED } from './videoApi'
import { supabase } from './supabase'

/** Playback is gated until the server verifies JWT and post visibility per request. */
export default function PostVideo({ postId }: { postId: string }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [poster, setPoster] = useState('')
  const [playing, setPlaying] = useState(false)
  const [playbackError, setPlaybackError] = useState('')
  useEffect(() => {
    if (!VIDEO_SERVER_ENABLED) { setUrl(''); setError('動画再生は安全なサーバー接続の準備中です。'); return }
    let active = true
    let objectUrl = ''
    let viewerId: string | undefined
    let notifiedViewerId: string | undefined
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      // A Blob URL bypasses the server after the initial authorized fetch.
      // Discard the locally cached media as soon as the session ends or
      // changes, so an old authenticated video cannot keep playing.
      if ((event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') && session?.user.id) {
        notifiedViewerId = session.user.id
      }
      const identityChanged = (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') &&
        (viewerId !== undefined && session?.user.id !== viewerId)
      if (event === 'SIGNED_OUT' || event === 'USER_UPDATED' || identityChanged) {
        active = false
        if (objectUrl) URL.revokeObjectURL(objectUrl)
        objectUrl = ''
        setUrl('')
        setError('動画を再生するには再読み込みしてください。')
      }
    })
    setUrl('')
    setPoster('')
    setPlaying(false)
    setPlaybackError('')
    setError('')
    void (async () => {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()
      if (!active) return undefined
      if (sessionError || !session?.user.id) throw new Error('missing playback session')
      // An account switch may arrive before getSession resolves. Never fetch
      // media using a stale session after observing a different identity.
      if (notifiedViewerId && notifiedViewerId !== session.user.id) {
        throw new Error('playback identity changed during session initialization')
      }
      viewerId = session.user.id
      return loadAuthorizedVideo(postId)
    })().then(value => {
      if (!value) return
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
  return <div style={{ position: 'relative', margin: '10px 0 14px', borderRadius: 12, overflow: 'hidden', background: '#101010' }}>
    <video key={postId} controls={playing || Boolean(playbackError)} playsInline preload="auto" src={url} poster={poster || undefined}
      onLoadedData={event => {
        if (poster) return
        const video = event.currentTarget
        if (!video.videoWidth || !video.videoHeight) return
        // Safari can expose a decoded first frame before it is actually paintable.
        // Seek slightly forward once; only capture after seeked, never freeze a black
        // initial canvas as the poster. Playback remains independent of this step.
        if (video.currentTime === 0 && Number.isFinite(video.duration) && video.duration > 0.2) {
          try { video.currentTime = Math.min(0.15, video.duration / 2) } catch { /* keep native preview */ }
        }
      }}
      onSeeked={event => {
        if (poster || playing) return
        const video = event.currentTarget
        if (!video.videoWidth || !video.videoHeight || video.readyState < 2) return
        try {
          const canvas = document.createElement('canvas')
          const scale = Math.min(1, 640 / Math.max(video.videoWidth, video.videoHeight))
          canvas.width = Math.max(1, Math.round(video.videoWidth * scale))
          canvas.height = Math.max(1, Math.round(video.videoHeight * scale))
          const context = canvas.getContext('2d')
          if (!context) return
          context.drawImage(video, 0, 0, canvas.width, canvas.height)
          const pixels = context.getImageData(0, 0, Math.min(canvas.width, 8), Math.min(canvas.height, 8)).data
          if (!pixels.some((value, index) => index % 4 !== 3 && value > 12)) return
          setPoster(canvas.toDataURL('image/jpeg', 0.72))
        } catch { /* Native video preview and playback remain available. */ }
      }}
      onPlay={() => { setPlaying(true); setPlaybackError('') }} onPause={() => setPlaying(false)}
      onError={() => setPlaybackError('動画を再生できません。形式または通信状態をご確認ください。')}
      style={{ display: 'block', width: '100%', maxHeight: 480, minHeight: 120, objectFit: 'contain' }} />
    {!playing && !playbackError && <button type="button" aria-label="動画を再生" onClick={event => {
      const video = event.currentTarget.parentElement?.querySelector('video')
      if (video) void video.play().catch(() => setPlaybackError('再生を開始できませんでした。動画の操作ボタンから再試行してください。'))
    }} style={{ position: 'absolute', inset: 0, border: 0, width: '100%', background: 'transparent', color: 'white', cursor: 'pointer', display: 'grid', placeItems: 'center' }}>
      <span aria-hidden="true" style={{ display: 'grid', placeItems: 'center', width: 60, height: 60, borderRadius: '50%', background: '#000a', fontSize: 28 }}>▶</span>
    </button>}
    {playbackError && <p role="status" style={{ padding: '8px 12px', margin: 0, color: '#f5c8c8', fontSize: 12 }}>{playbackError}</p>}
  </div>
}
