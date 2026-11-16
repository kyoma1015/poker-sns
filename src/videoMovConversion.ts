// Local-only conversion. The original MOV is never reserved, uploaded or persisted.
// The normal server ffprobe/SHA256/HMAC path still validates the resulting MP4.
const MAX_BYTES = 20 * 1024 * 1024
const MAX_SECONDS = 30
export const MOV_CONVERSION_HELP = 'MOVを変換できませんでした。iPhoneのショートカット「メディアをエンコード」でMP4（H.264）に変換し、30秒・20MiB以内で選び直してください。元の動画は送信していません。'

export function isMovVideo(file: Pick<File, 'name' | 'type'>): boolean {
  return file.type === 'video/quicktime' || /\.mov$/i.test(file.name)
}

export type MovPlaybackGesture = (step: 'source' | 'output', start: () => void) => () => void

/** A track marker alone does not prove that the recorded audio is audible. */
async function verifyRecordedMp4Audio(blob: Blob, audio: AudioContext, gesture: MovPlaybackGesture, signal: AbortSignal): Promise<void> {
  const bytes = new Uint8Array(await blob.arrayBuffer())
  // MP4 sample entry and handler names; these are only a structural precheck.
  const containsFourCC = (name: string) => {
    const chars = [...name].map(char => char.charCodeAt(0))
    return bytes.some((value, index) => value === chars[0] && index + 3 < bytes.length &&
      bytes[index + 1] === chars[1] && bytes[index + 2] === chars[2] && bytes[index + 3] === chars[3])
  }
  if (!containsFourCC('soun') || !(containsFourCC('mp4a') || containsFourCC('Opus'))) {
    throw new Error('変換後MP4の音声トラックを確認できませんでした。' + MOV_CONVERSION_HELP)
  }
  signal?.throwIfAborted()
  const probe = document.createElement('video')
  const url = URL.createObjectURL(blob)
  const analyser = audio.createAnalyser()
  analyser.fftSize = 2048
  const samples = new Float32Array(analyser.fftSize)
  let timer = 0
  let timeout = 0
  let source: MediaElementAudioSourceNode | undefined
  try {
    probe.playsInline = true
    probe.preload = 'auto'
    // Muting the media element may also mute its Web Audio source (including
    // Safari). The source connects only to an analyser, never the speakers.
    // If audible playback is disallowed, fail closed instead of accepting silence.
    probe.muted = false
    probe.defaultMuted = false
    probe.src = url
    source = audio.createMediaElementSource(probe)
    source.connect(analyser)
    await new Promise<void>((resolve, reject) => {
      let settled = false
      let clearControl: (() => void) | undefined
      let clicked = false
      const finish = (error?: Error) => {
        if (settled) return
        settled = true
        clearInterval(timer)
        clearTimeout(timeout)
        clearControl?.()
        probe.pause()
        signal?.removeEventListener('abort', onAbort)
        if (error) reject(error); else resolve()
      }
      const onAbort = () => finish(new Error('音声検証を中止しました。元の動画は送信していません。'))
      signal?.addEventListener('abort', onAbort, { once: true })
      if (signal.aborted) { onAbort(); return }
      timeout = window.setTimeout(() => finish(new Error('変換後MP4の音声を検証できませんでした。' + MOV_CONVERSION_HELP)), 45000)
      probe.onerror = () => finish(new Error('変換後MP4を再デコードできませんでした。' + MOV_CONVERSION_HELP))
      clearControl = gesture('output', () => {
        clearControl?.()
        if (settled || clicked || signal.aborted) return
        clicked = true
        const resumed = audio.resume()
        const playing = probe.play()
        void Promise.all([resumed, playing]).catch(() => finish(new Error('変換後MP4の音声を再生できませんでした。' + MOV_CONVERSION_HELP)))
        clearTimeout(timeout)
        timeout = window.setTimeout(() => finish(new Error('変換後MP4の音声を検証できませんでした。' + MOV_CONVERSION_HELP)), 8000)
        timer = window.setInterval(() => {
          analyser.getFloatTimeDomainData(samples)
          if (samples.some(sample => Math.abs(sample) > 0.002)) finish()
          else if (probe.ended) finish(new Error('変換後MP4に再生可能な音声を検出できませんでした。' + MOV_CONVERSION_HELP))
        }, 60)
      })
    })
  } finally {
    clearInterval(timer)
    clearTimeout(timeout)
    probe.pause()
    source?.disconnect()
    analyser.disconnect()
    probe.removeAttribute('src')
    try { probe.load() } catch { /* release local decoder */ }
    URL.revokeObjectURL(url)
  }
}

export async function convertMovToMp4(file: File, gesture: MovPlaybackGesture, selectionSignal?: AbortSignal): Promise<File> {
  const lifetime = new AbortController()
  const signal = selectionSignal ? AbortSignal.any([selectionSignal, lifetime.signal]) : lifetime.signal
  signal.throwIfAborted()
  if (!isMovVideo(file)) return file
  if (file.size <= 0 || file.size > MAX_BYTES) throw new Error('変換前のMOVも20MiB以内にしてください。' + MOV_CONVERSION_HELP)
  if (typeof MediaRecorder === 'undefined' || typeof AudioContext === 'undefined') throw new Error(MOV_CONVERSION_HELP)
  const mime = ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4;codecs=avc1,mp4a.40.2', 'video/mp4;codecs=avc1,opus', 'video/mp4'].find(type => MediaRecorder.isTypeSupported(type))
  const canvas = document.createElement('canvas')
  if (!mime) throw new Error('SafariがMP4動画の録画形式に対応していません。' + MOV_CONVERSION_HELP)
  if (typeof canvas.captureStream !== 'function') throw new Error('Safariが画面映像の変換に対応していません。' + MOV_CONVERSION_HELP)
  const audio = new AudioContext()
  const video = document.createElement('video')
  video.playsInline = true
  // Start muted while loading. Before recording, route audio exclusively to
  // MediaStreamDestination, then unmute so Web Audio receives decoded PCM.
  video.muted = true
  video.defaultMuted = true
  video.preload = 'auto'
  const url = URL.createObjectURL(file)
  let stream: MediaStream | undefined
  let recorder: MediaRecorder | undefined
  let frame = 0
  let cancel: ((error: Error) => void) | undefined
  const abort = () => cancel?.(new Error('動画の変換を中止しました。元の動画は送信していません。'))
  const hidden = () => { if (document.visibilityState === 'hidden') lifetime.abort() }
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
    signal?.throwIfAborted()
    const duration = video.duration
    if (!Number.isFinite(duration) || duration <= 0 || duration > MAX_SECONDS) throw new Error('動画は30秒以内にしてください。元の動画は送信していません。')
    if (!video.videoWidth || !video.videoHeight) throw new Error('MOVの映像・音声を読み込めませんでした（映像=' + video.videoWidth + 'x' + video.videoHeight + '、音声状態=' + audio.state + '）。' + MOV_CONVERSION_HELP)
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
    // Verify actual decoded PCM reaches Web Audio. A MediaStream audio track
    // can exist while containing only silence (observed on iPhone Safari).
    const analyser = audio.createAnalyser()
    analyser.fftSize = 2048
    source.connect(analyser)
    const audioSamples = new Float32Array(analyser.fftSize)
    let decodedAudioDetected = false
    const sampleDecodedAudio = () => {
      analyser.getFloatTimeDomainData(audioSamples)
      if (audioSamples.some(sample => Math.abs(sample) > 0.002)) decodedAudioDetected = true
    }
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
      let clearControl: (() => void) | undefined
      let clicked = false
      let audioSampleTimer = 0
      const stopAtSourceEnd = () => {
        if (done || stopRequested || !recorder || recorder.state !== 'recording') return
        stopRequested = true
        sampleDecodedAudio()
        if (!decodedAudioDetected) {
          finish(new Error('変換中に音声データを検出できませんでした。無音のMP4は投稿せず、音声付きのMP4へ変換して選び直してください。元の動画は送信していません。'))
          return
        }
        try { recorder.stop() } catch { finish(new Error(MOV_CONVERSION_HELP)) }
      }
      const timer = window.setTimeout(() => finish(new Error('変換が時間内に完了しませんでした。' + MOV_CONVERSION_HELP)), 95000)
      const finish = (error?: Error) => {
        if (done) return
        done = true
        clearTimeout(timer)
        window.clearInterval(playbackWatchdog)
        window.clearInterval(audioSampleTimer)
        clearControl?.()
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
        // Muted media elements can produce silent Web Audio PCM on Safari.
        // Unmute only after routing the source to MediaStreamDestination (not
        // audio.destination / speakers). If autoplay refuses, fail closed and
        // ask for a manually encoded MP4; never upload a silent conversion.
        video.muted = false
        video.defaultMuted = false
        clearControl = gesture('source', () => {
          clearControl?.()
          if (done || clicked || signal.aborted) return
          clicked = true
          try {
            // Keep resume and unmuted play on the native click stack.
            const resumed = audio.resume()
            const playing = video.play()
            const playback = Promise.all([resumed, playing])
            void playback.then(() => {
                if (done) return
                playbackStartedAt = performance.now()
                audioSampleTimer = window.setInterval(sampleDecodedAudio, 80)
                // Safari can omit ended on very short MOVs. Never record indefinitely.
                playbackWatchdog = window.setInterval(() => {
                  if (done) return
                  if (video.ended || video.currentTime >= duration - 0.05) {
                    stopAtSourceEnd()
                  } else if (performance.now() - playbackStartedAt > (duration + 4) * 1000) {
                    const position = Number.isFinite(video.currentTime) ? video.currentTime.toFixed(2) : 'unknown'
                    finish(new Error('動画の終了を確認できず、安全停止しました（再生位置 ' + position + '秒 / ' + duration.toFixed(2) + '秒、停止=' + video.paused + '、読込状態=' + video.readyState + '）。' + MOV_CONVERSION_HELP))
                  }
                }, 100)
            }).catch(() => finish(new Error('SafariでMOVの再生を開始できませんでした。' + MOV_CONVERSION_HELP)))
            recorder!.start(250)
          } catch { finish(new Error(MOV_CONVERSION_HELP)) }
        })
        if (signal.aborted) abort()
      } catch { finish(new Error('SafariのMP4録画処理を開始できませんでした。' + MOV_CONVERSION_HELP)) }
    })
    signal?.throwIfAborted()
    if (!result.size || result.size > MAX_BYTES) throw new Error(MOV_CONVERSION_HELP)
    // Validate the *recorded* MP4, not just the source PCM. Fail closed when
    // Safari cannot replay/decode it; never upload an unverified conversion.
    await verifyRecordedMp4Audio(result, audio, gesture, signal)
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
