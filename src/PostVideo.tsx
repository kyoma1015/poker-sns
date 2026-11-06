import { useEffect, useRef, useState } from 'react'
import { loadAuthorizedVideo, VIDEO_SERVER_ENABLED } from './videoApi'
import { supabase } from './supabase'
import { readLocalVideoPoster } from './videoPosterCache'

/** Playback is gated until the server verifies JWT and post visibility per request. */
export default function PostVideo({ postId, videoPath }: { postId: string; videoPath?: string | null }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [poster, setPoster] = useState('')
  const [playing, setPlaying] = useState(false)
  const [playbackError, setPlaybackError] = useState('')
  const posterSeekAttempts = useRef(0)
  const posterFrameCallback = useRef<number | null>(null)
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
    posterSeekAttempts.current = 0
    posterFrameCallback.current = null
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
      if (active) {
        // Read only after JWT-backed authorization succeeds; never grant media access via cache.
        setPoster(readLocalVideoPoster(viewerId || '', videoPath || ''))
        setUrl(value)
      }
      else URL.revokeObjectURL(value)
    }).catch(() => {
      if (active) setError('動画を読み込めません。権限を確認してください。')
    })
    return () => { active = false; subscription.unsubscribe(); if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [postId, videoPath])
  const capturePoster = (video: HTMLVideoElement) => {
    if (poster || playing || !video.videoWidth || !video.videoHeight || video.readyState < 2) return
    try {
      const canvas = document.createElement('canvas')
      const scale = Math.min(1, 640 / Math.max(video.videoWidth, video.videoHeight))
      canvas.width = Math.max(1, Math.round(video.videoWidth * scale))
      canvas.height = Math.max(1, Math.round(video.videoHeight * scale))
      const context = canvas.getContext('2d')
      if (!context) return
      context.drawImage(video, 0, 0, canvas.width, canvas.height)
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data
      let nonBlack = 0
      for (let i = 0; i < pixels.length; i += Math.max(4, Math.floor(pixels.length / 256 / 4) * 4)) {
        if (pixels[i] > 16 || pixels[i + 1] > 16 || pixels[i + 2] > 16) nonBlack++
      }
      if (nonBlack > 2) { setPoster(canvas.toDataURL('image/jpeg', 0.76)); return }
    } catch { /* cross-origin or Safari decoding failure: preserve playback */ }
    const next = [0.8, 1.6, 2.8, 4.0][posterSeekAttempts.current++]
    if (next !== undefined && Number.isFinite(video.duration) && video.duration > 0.1) {
      const time = Math.min(next, video.duration * 0.85)
      if (time > video.currentTime + 0.05) {
        try { video.currentTime = time } catch { /* keep native playback */ }
      }
    }
  }
  const captureAfterDecodedFrame = (video: HTMLVideoElement) => {
    // Safari may fire seeked before the frame is actually available to Canvas.
    // requestVideoFrameCallback runs when a decoded frame is submitted for presentation.
    if ('requestVideoFrameCallback' in video) {
      if (posterFrameCallback.current !== null) video.cancelVideoFrameCallback(posterFrameCallback.current)
      posterFrameCallback.current = video.requestVideoFrameCallback(() => {
        posterFrameCallback.current = null
        capturePoster(video)
      })
    } else capturePoster(video)
  }
  if (error) return <p role="status">{error}</p>
  if (!url) return <p role="status">動画を読み込み中...</p>
  return <div style={{ position: 'relative', margin: '10px 0 14px', borderRadius: 12, overflow: 'hidden', background: '#101010' }}>
    <video key={postId} controls={playing || Boolean(playbackError)} playsInline preload="auto" src={url} poster={poster || undefined}
      onLoadedMetadata={event => {
        const video = event.currentTarget
        if (!poster && !playing && Number.isFinite(video.duration) && video.duration > 0.2) {
          try { video.currentTime = Math.min(0.35, video.duration / 2) } catch { /* native fallback */ }
        }
      }}
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
      onSeeked={event => captureAfterDecodedFrame(event.currentTarget)}
      onCanPlay={event => { if (!poster && !playing) captureAfterDecodedFrame(event.currentTarget) }}
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
