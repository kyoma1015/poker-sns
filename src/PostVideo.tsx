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
  const posterGeneration = useRef(0)
  const posterProbeCleanup = useRef<(() => void) | null>(null)
  useEffect(() => {
    posterGeneration.current++
    posterProbeCleanup.current?.()
    posterProbeCleanup.current = null
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
        posterGeneration.current++
        posterProbeCleanup.current?.()
        posterProbeCleanup.current = null
        setPoster('')
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
      if (active) {
        // Read only after JWT-backed authorization succeeds; never grant media access via cache.
        setPoster(readLocalVideoPoster(viewerId || '', videoPath || ''))
        setUrl(value)
      }
      else URL.revokeObjectURL(value)
    }).catch(() => {
      if (active) setError('動画を読み込めません。権限を確認してください。')
    })
    return () => {
      active = false
      posterGeneration.current++
      posterProbeCleanup.current?.()
      posterProbeCleanup.current = null
      subscription.unsubscribe()
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [postId, videoPath])
  useEffect(() => {
    if (!url || poster) return
    const generation = ++posterGeneration.current
    const probe = document.createElement('video')
    probe.muted = true
    probe.defaultMuted = true
    probe.playsInline = true
    probe.preload = 'auto'
    let disposed = false
    let completed = false
    let frameCallback: number | null = null
    let frameVersion = 0
    let settleTimer: ReturnType<typeof setTimeout> | undefined
    let seekIndex = 0
    let timeout: ReturnType<typeof setTimeout> | undefined
    const seekTimes = [0.35, 0.8, 1.6, 2.8, 4.0]
    const isCurrent = () => !disposed && !completed && generation === posterGeneration.current
    const cleanup = () => {
      if (disposed) return
      disposed = true
      if (timeout !== undefined) clearTimeout(timeout)
      if (settleTimer !== undefined) clearTimeout(settleTimer)
      frameVersion++
      if (frameCallback !== null && typeof probe.cancelVideoFrameCallback === 'function') {
        probe.cancelVideoFrameCallback(frameCallback)
      }
      probe.removeEventListener('loadedmetadata', onMetadata)
      probe.removeEventListener('loadeddata', onFrame)
      probe.removeEventListener('seeked', onFrame)
      probe.removeEventListener('canplay', onFrame)
      probe.pause()
      probe.removeAttribute('src')
      try { probe.load() } catch { /* release even if decoder is gone */ }
    }
    const nextSeek = () => {
      if (!isCurrent() || !Number.isFinite(probe.duration) || probe.duration <= 0) return
      while (seekIndex < seekTimes.length) {
        const next = Math.min(seekTimes[seekIndex++], probe.duration * 0.85)
        if (next <= probe.currentTime + 0.05) continue
        try {
          frameVersion++
          if (frameCallback !== null && typeof probe.cancelVideoFrameCallback === 'function') probe.cancelVideoFrameCallback(frameCallback)
          frameCallback = null
          probe.currentTime = next
          return
        } catch { /* try next position */ }
      }
    }
    const capture = () => {
      if (!isCurrent() || probe.readyState < 2 || !probe.videoWidth || !probe.videoHeight) return false
      try {
        const canvas = document.createElement('canvas')
        const scale = Math.min(1, 640 / Math.max(probe.videoWidth, probe.videoHeight))
        canvas.width = Math.max(1, Math.round(probe.videoWidth * scale))
        canvas.height = Math.max(1, Math.round(probe.videoHeight * scale))
        const ctx = canvas.getContext('2d')
        if (!ctx) return false
        ctx.drawImage(probe, 0, 0, canvas.width, canvas.height)
        const side = Math.min(24, canvas.width, canvas.height)
        const pixels = ctx.getImageData(Math.floor((canvas.width - side) / 2), Math.floor((canvas.height - side) / 2), side, side).data
        if (!pixels.some((v, i) => i % 4 !== 3 && v > 16)) return false
        const dataUrl = canvas.toDataURL('image/jpeg', 0.76)
        if (!isCurrent()) return false
        completed = true
        setPoster(dataUrl)
        cleanup()
        return true
      } catch { return false /* Safari decode/canvas failure must not block playback */ }
    }
    const onFrame = () => {
      if (!isCurrent()) return
      if (capture()) return
      const version = frameVersion
      if (frameCallback === null && typeof probe.requestVideoFrameCallback === 'function') {
        frameCallback = probe.requestVideoFrameCallback(() => {
          frameCallback = null
          if (version !== frameVersion || !isCurrent()) return
          if (capture()) return
          nextSeek()
        })
      }
      if (settleTimer !== undefined) clearTimeout(settleTimer)
      settleTimer = setTimeout(() => {
        settleTimer = undefined
        if (version !== frameVersion || !isCurrent()) return
        if (capture()) return
        nextSeek()
      }, 220)
    }
    const onMetadata = () => nextSeek()
    probe.addEventListener('loadedmetadata', onMetadata)
    probe.addEventListener('loadeddata', onFrame)
    probe.addEventListener('seeked', onFrame)
    probe.addEventListener('canplay', onFrame)
    timeout = setTimeout(cleanup, 7000)
    probe.src = url
    probe.load()
    posterProbeCleanup.current = cleanup
    return () => {
      cleanup()
      if (posterProbeCleanup.current === cleanup) posterProbeCleanup.current = null
    }
  }, [url, poster])
  if (error) return <p role="status">{error}</p>
  if (!url) return <p role="status">動画を読み込み中...</p>
  return <div style={{ position: 'relative', margin: '10px 0 14px', borderRadius: 12, overflow: 'hidden', background: '#101010' }}>
    <video key={postId} controls={playing || Boolean(playbackError)} playsInline preload="auto" src={url} poster={poster || undefined}
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
