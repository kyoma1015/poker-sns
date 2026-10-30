// Local-only conversion. The original MOV is never reserved, uploaded or persisted.
// The normal server ffprobe/SHA256/HMAC path still validates the resulting MP4.
const MAX_BYTES = 20 * 1024 * 1024
const MAX_SECONDS = 30
export const MOV_CONVERSION_HELP = 'MOVを変換できませんでした。iPhoneのショートカット「メディアをエンコード」でMP4（H.264）に変換し、30秒・20MiB以内で選び直してください。元の動画は送信していません。'

export function isMovVideo(file: Pick<File, 'name' | 'type'>): boolean {
  return file.type === 'video/quicktime' || /\.mov$/i.test(file.name)
}

/** Must start from the file-picker gesture so Safari can resume its audio context. */
export async function convertMovToMp4(file: File, signal?: AbortSignal): Promise<File> {
  signal?.throwIfAborted()
  if (!isMovVideo(file)) return file
  if (file.size <= 0 || file.size > MAX_BYTES) throw new Error('変換前のMOVも20MiB以内にしてください。' + MOV_CONVERSION_HELP)
  if (typeof MediaRecorder === 'undefined' || typeof AudioContext === 'undefined') throw new Error(MOV_CONVERSION_HELP)
  const mime = ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4;codecs=avc1,mp4a.40.2', 'video/mp4;codecs=avc1,opus'].find(type => MediaRecorder.isTypeSupported(type))
  const canvas = document.createElement('canvas')
  if (!mime || typeof canvas.captureStream !== 'function') throw new Error(MOV_CONVERSION_HELP)
  const audio = new AudioContext()
  // Do this before any await; no microphone permission or speaker output is needed.
  const resumed = audio.resume().then(() => true, () => false)
  const video = document.createElement('video')
  video.playsInline = true
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
    if (!audioReady) throw new Error(MOV_CONVERSION_HELP)
    signal?.throwIfAborted()
    const duration = video.duration
    if (!Number.isFinite(duration) || duration <= 0 || duration > MAX_SECONDS) throw new Error('動画は30秒以内にしてください。元の動画は送信していません。')
    if (!video.videoWidth || !video.videoHeight || audio.state !== 'running') throw new Error(MOV_CONVERSION_HELP)
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
      const timer = window.setTimeout(() => finish(new Error('変換が時間内に完了しませんでした。' + MOV_CONVERSION_HELP)), 45000)
      const finish = (error?: Error) => {
        if (done) return
        done = true
        clearTimeout(timer)
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
        video.onended = () => { if (recorder?.state === 'recording') recorder.stop() }
        recorder.start(250)
        void video.play().catch(() => finish(new Error(MOV_CONVERSION_HELP)))
        if (signal?.aborted) abort()
      } catch { finish(new Error(MOV_CONVERSION_HELP)) }
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
