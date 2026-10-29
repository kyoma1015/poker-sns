import { MAX_VIDEO_BYTES, MAX_VIDEO_SECONDS, readVideoDuration, validateVideo } from './videoUpload'

/** Best-effort, fail-closed browser transcoding. Never uploads the original oversized file. */
export async function compressOversizedVideo(file: File): Promise<File> {
  if (file.size <= MAX_VIDEO_BYTES) return file
  if (typeof document === 'undefined' || typeof MediaRecorder === 'undefined') {
    throw new Error('この端末は動画の自動圧縮に対応していません。20MB以内の動画を選択してください。')
  }
  const duration = await readVideoDuration(file)
  if (duration > MAX_VIDEO_SECONDS || duration <= 0) throw new Error('動画は30秒以内にしてください。')
  const mime = ['video/mp4', 'video/webm;codecs=vp8,opus', 'video/webm'].find(type => MediaRecorder.isTypeSupported(type))
  if (!mime) throw new Error('この端末は動画の自動圧縮に対応していません。20MB以内の動画を選択してください。')
  const video = document.createElement('video')
  const url = URL.createObjectURL(file)
  video.src = url
  video.muted = true
  video.playsInline = true
  video.preload = 'auto'
  const capture = video as HTMLVideoElement & { captureStream?: () => MediaStream }
  let stream: MediaStream | undefined
  let recorder: MediaRecorder | undefined
  try {
    await new Promise<void>((resolve, reject) => {
      video.onloadeddata = () => resolve()
      video.onerror = () => reject(new Error('動画を読み込めませんでした。'))
      video.load()
    })
    if (!capture.captureStream) throw new Error('この端末は動画の自動圧縮に対応していません。20MB以内の動画を選択してください。')
    stream = capture.captureStream()
    if (!stream.getVideoTracks().length) throw new Error('動画の映像トラックを取得できませんでした。')
    // Capturing muted video can discard audio. Never silently strip audio.
    if (file.type !== 'video/webm' && !stream.getAudioTracks().length) {
      throw new Error('音声を保持した自動圧縮を確認できません。20MB以内に変換してから選択してください。')
    }
    const chunks: BlobPart[] = []
    const result = await new Promise<Blob>((resolve, reject) => {
      let settled = false
      const finish = (error?: Error) => {
        if (settled) return
        settled = true
        clearTimeout(timeout)
        video.pause()
        if (error) reject(error)
        else resolve(new Blob(chunks, { type: recorder?.mimeType || mime }))
      }
      const timeout = window.setTimeout(() => {
        try { recorder?.stop() } catch { /* timeout is always an error */ }
        finish(new Error('圧縮が時間内に完了しませんでした。'))
      }, 45000)
      try {
        recorder = new MediaRecorder(stream!, { mimeType: mime, videoBitsPerSecond: Math.min(3_000_000, Math.floor((MAX_VIDEO_BYTES * 8 * 0.85) / Math.max(duration, 1))) })
        recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data) }
        recorder.onerror = () => finish(new Error('動画の圧縮に失敗しました。'))
        recorder.onstop = () => finish()
        video.onended = () => { if (recorder?.state === 'recording') recorder.stop() }
        recorder.start()
        void video.play().catch(() => finish(new Error('動画の自動圧縮を開始できませんでした。')))
      } catch { finish(new Error('この端末は動画の自動圧縮に対応していません。')) }
    })
    const outputType = result.type.split(';')[0]
    const ext = outputType === 'video/mp4' ? 'mp4' : 'webm'
    const output = new File([result], file.name.replace(/\.[^.]+$/, '') + '-compressed.' + ext, { type: outputType })
    const validation = await validateVideo(output)
    if (validation) throw new Error('圧縮後の動画を検証できませんでした。' + validation)
    return output
  } finally {
    video.pause()
    video.removeAttribute('src')
    stream?.getTracks().forEach(track => track.stop())
    URL.revokeObjectURL(url)
  }
}
