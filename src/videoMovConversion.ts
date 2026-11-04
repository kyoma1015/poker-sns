// Local-only conversion. The original MOV is never reserved, uploaded or persisted.
// The normal server ffprobe/SHA256/HMAC path still validates the resulting MP4.
const MAX_BYTES = 20 * 1024 * 1024
const MAX_SECONDS = 30
export const MOV_CONVERSION_HELP = 'MOVを変換できませんでした。iPhoneのショートカット「メディアをエンコード」でMP4（H.264）に変換し、30秒・20MiB以内で選び直してください。元の動画は送信していません。'

export function isMovVideo(file: Pick<File, 'name' | 'type'>): boolean {
  return file.type === 'video/quicktime' || /\.mov$/i.test(file.name)
}

/** Prefer an audio context resumed by the attachment-button gesture before Safari opens the picker. */
export function prepareMovAudioContext(): AudioContext | null {
  if (typeof AudioContext === 'undefined') return null
  try {
    const audio = new AudioContext()
    void audio.resume().catch(() => {})
    return audio
  } catch { return null }
}

export async function convertMovToMp4(file: File, signal?: AbortSignal, preparedAudio?: AudioContext | null): Promise<File> {
  signal?.throwIfAborted()
  if (!isMovVideo(file)) return file
  if (file.size <= 0 || file.size > MAX_BYTES) throw new Error('変換前のMOVも20MiB以内にしてください。' + MOV_CONVERSION_HELP)
  if (typeof MediaRecorder === 'undefined' || typeof AudioContext === 'undefined') throw new Error(MOV_CONVERSION_HELP)
  const mime = ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4;codecs=avc1,mp4a.40.2', 'video/mp4;codecs=avc1,opus', 'video/mp4'].find(type => MediaRecorder.isTypeSupported(type))
  const canvas = document.createElement('canvas')
  if (!mime) throw new Error('SafariがMP4動画の録画形式に対応していません。' + MOV_CONVERSION_HELP)
  if (typeof canvas.captureStream !== 'function') throw new Error('Safariが画面映像の変換に対応していません。' + MOV_CONVERSION_HELP)
  const audio = preparedAudio && preparedAudio.state !== 'closed' ? preparedAudio : new AudioContext()
  // A prepared context may already be running from the initial attachment tap.
  const resumed = audio.state === 'running' ? Promise.resolve(true) : audio.resume().then(() => true, () => false)
  const video = document.createElement('video')
  video.playsInline = true
  // Safari blocks script-initiated audible playback after the asynchronous file picker.
  // Keep the element muted; decoded audio is routed to MediaStreamDestination below.
  video.muted = true
  video.defaultMuted = true
  video.preload = 'auto'
  const url = URL.createObjectURL(file)
  let stream: MediaStream | undefined
  let recorder: MediaRecorder | undefined
  let frame = 0
  let cancel: ((error: Error) => void) | undefined
  const abort = () => cancel?.(new Error('動画の変換を中止しました。元の動画は送信していません。'))
  const hidden = () => { if (document.visibilityState === 'hidden') abort() }
  signal?.addEventListener('abort', abort, { once: true })
  document.addEventListener('visibilitychange', hidden)
  try {
    await new Promise<void>((resolve, reject) => {
      const timer = window.setTimeout(() => finish(new Error(MOV_CONVERSION_HELP)), 15000)
      const finish = (error?: Error) => {
        clearTimeout(timer)
        cancel = undefined
        video.onloadeddata = null
        video.onerror = null
        if (error) reject(error); else resolve()
      }
      cancel = finish
      video.onloadeddata = () => finish()
      video.onerror = () => finish(new Error(MOV_CONVERSION_HELP))
      video.src = url
      video.load()
      if (signal?.aborted) abort()
    })
    const audioReady = await new Promise<boolean>((resolve, reject) => {
      const timer = window.setTimeout(() => finish(false), 5000)
      const finish = (ready: boolean) => { clearTimeout(timer); cancel = undefined; resolve(ready) }
      cancel = error => { clearTimeout(timer); cancel = undefined; reject(error) }
      void resumed.then(finish)
      if (signal?.aborted) abort()
    })
    if (!audioReady) throw new Error('Safariで音声変換を開始できませんでした。' + MOV_CONVERSION_HELP)
    signal?.throwIfAborted()
    const duration = video.duration
    if (!Number.isFinite(duration) || duration <= 0 || duration > MAX_SECONDS) throw new Error('動画は30秒以内にしてください。元の動画は送信していません。')
    if (!video.videoWidth || !video.videoHeight || audio.state !== 'running') throw new Error('MOVの映像・音声を読み込めませんでした。' + MOV_CONVERSION_HELP)
    // Bound decoder/encoder work for 4K/portrait phone captures; preserve aspect ratio.
    const scale = Math.min(1, 1280 / Math.max(video.videoWidth, video.videoHeight))
    canvas.width = Math.max(2, Math.floor(video.videoWidth * scale / 2) * 2)
    canvas.height = Math.max(2, Math.floor(video.videoHeight * scale / 2) * 2)
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error(MOV_CONVERSION_HELP)
    stream = canvas.captureStream(30)
    // Route decoded source audio into the recorder, never to the speakers.
    const source = audio.createMediaElementSource(video)
    const destination = audio.createMediaStreamDestination()
    source.connect(destination)
    destination.stream.getAudioTracks().forEach(track => stream!.addTrack(track))
    const draw = () => { ctx.drawImage(video, 0, 0, canvas.width, canvas.height); frame = requestAnimationFrame(draw) }
    draw()
    const result = await new Promise<Blob>((resolve, reject) => {
      const chunks: Blob[] = []
      let bytes = 0
      let done = false
      let stopRequested = false
      let playbackStartedAt = 0
      let playbackWatchdog = 0
      let resumeAttempted = false
      const stopAtSourceEnd = () => {
        if (done || stopRequested || !recorder || recorder.state !== 'recording') return
        stopRequested = true
        try { recorder.stop() } catch { finish(new Error(MOV_CONVERSION_HELP)) }
      }
      const timer = window.setTimeout(() => finish(new Error('変換が時間内に完了しませんでした。' + MOV_CONVERSION_HELP)), 45000)
      const finish = (error?: Error) => {
        if (done) return
        done = true
        clearTimeout(timer)
        window.clearInterval(playbackWatchdog)
        cancel = undefined
        video.pause()
        if (error) reject(error); else resolve(new Blob(chunks, { type: 'video/mp4' }))
      }
      cancel = finish
      try {
        recorder = new MediaRecorder(stream!, { mimeType: mime, videoBitsPerSecond: 3_000_000, audioBitsPerSecond: 128_000 })
        recorder.ondataavailable = event => {
          bytes += event.data.size
          if (bytes > MAX_BYTES) { finish(new Error('変換後の動画が20MiBを超えました。短くして選び直してください。')); return }
          if (!done && event.data.size) chunks.push(event.data)
        }
        recorder.onerror = () => finish(new Error(MOV_CONVERSION_HELP))
        recorder.onstop = () => finish()
        video.onerror = () => finish(new Error(MOV_CONVERSION_HELP))
        video.onended = stopAtSourceEnd
        recorder.start(250)
        void video.play().then(() => {
          // Keep the media element muted for the entire Safari playback. Unmuting
          // after play() resolves can trigger autoplay suspension (paused at ~0.08s).
          // WebAudio's MediaElementAudioSourceNode captures decoded audio upstream
          // of the element's muted output; the browser QA verifies audible samples.
          playbackStartedAt = performance.now()
          // Safari can omit ended on very short MOVs. Never record indefinitely.
          playbackWatchdog = window.setInterval(() => {
            if (done) return
            if (video.ended || video.currentTime >= duration - 0.05) {
              stopAtSourceEnd()
            } else if (video.paused && !resumeAttempted) {
              // Some Safari MOV decoders pause after the initial play() resolves.
              // Attempt one local resume, never restart recording or upload.
              resumeAttempted = true
              void video.play().catch(() => {})
            } else if (performance.now() - playbackStartedAt > (duration + 4) * 1000) {
              const position = Number.isFinite(video.currentTime) ? video.currentTime.toFixed(2) : 'unknown'
              finish(new Error('動画の終了を確認できず、安全停止しました（再生位置 ' + position + '秒 / ' + duration.toFixed(2) + '秒、停止=' + video.paused + '、読込状態=' + video.readyState + '）。' + MOV_CONVERSION_HELP))
            }
          }, 100)
        }).catch(() => finish(new Error('SafariでMOVの再生を開始できませんでした。' + MOV_CONVERSION_HELP)))
        if (signal?.aborted) abort()
      } catch { finish(new Error('SafariのMP4録画処理を開始できませんでした。' + MOV_CONVERSION_HELP)) }
    })
    signal?.throwIfAborted()
    if (!result.size || result.size > MAX_BYTES) throw new Error(MOV_CONVERSION_HELP)
    return new File([result], file.name.replace(/\.[^.]+$/, '') + '-converted.mp4', { type: 'video/mp4' })
  } finally {
    cancelAnimationFrame(frame)
    signal?.removeEventListener('abort', abort)
    document.removeEventListener('visibilitychange', hidden)
    video.onended = video.onerror = video.onloadeddata = null
    video.pause()
    if (recorder && recorder.state !== 'inactive') { recorder.onstop = null; recorder.ondataavailable = null; recorder.onerror = null; try { recorder.stop() } catch { /* already stopped */ } }
    stream?.getTracks().forEach(track => track.stop())
    video.removeAttribute('src')
    try { video.load() } catch { /* cleanup still releases local resources */ }
    URL.revokeObjectURL(url)
    await audio.close().catch(() => {})
  }
}
