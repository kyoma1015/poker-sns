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


type MovieBox = { start: number; end: number; type: string; path: string }

/** Remux the compatible subset without moving media samples or chunk offsets. */
class MovVerificationError extends Error {}

function remuxCompatibleMov(buffer: ArrayBuffer): { buffer: ArrayBuffer; audioOnly: ArrayBuffer } {
  const view = new DataView(buffer)
  const bytes = new Uint8Array(buffer)
  const fourcc = (at: number) => String.fromCharCode(...bytes.subarray(at, at + 4))
  const writeType = (at: number, type: string) => bytes.set(Array.from(type, char => char.charCodeAt(0)), at)
  const boxes = (start: number, end: number, path: string, videoExtensions = false): MovieBox[] => {
    const result: MovieBox[] = []
    for (let at = start; at < end;) {
      const remaining = end - at
      const detail = () => `${path} offset=${at} remaining=${remaining} boxes=${result.length}`
      if (result.length >= 4096) throw new MovVerificationError('MOV box limit: ' + detail())
      // QuickTime video sample descriptions allow one final four-byte zero
      // terminator after the extension atoms. It is outside the atom list.
      if (videoExtensions && remaining === 4 && view.getUint32(at) === 0) break
      if (remaining < 8) throw new MovVerificationError('truncated MOV box header: ' + detail())
      const type = fourcc(at + 4)
      let size = view.getUint32(at)
      // QuickTime can use an extended size or extend mdat to EOF.
      // Keep its header and payload in place so stco/co64 offsets stay valid.
      if (start === 0 && type === 'mdat' && size === 0) {
        size = end - at
      } else if (start === 0 && type === 'mdat' && size === 1 && end - at >= 16) {
        const extended = view.getBigUint64(at + 8)
        if (extended < 16n || extended > BigInt(end - at)) throw new MovVerificationError('invalid extended mdat size')
        size = Number(extended)
      }
      if (size < 8 || size > end - at) throw new MovVerificationError('invalid MOV box size: ' + detail())
      result.push({ start: at, end: at + size, type, path: path + '/' + (['moov', 'trak', 'mdia', 'minf', 'dinf', 'dref', 'stbl', 'stsd', 'avc1', 'hvc1', 'hev1', 'mp4a', 'wave'].includes(type) ? type : 'box') })
      at += size
    }
    return result
  }
  const children = (box: MovieBox) => boxes(box.start + 8, box.end, box.path)
  const one = (items: MovieBox[], type: string) => {
    const matches = items.filter(item => item.type === type)
    if (matches.length !== 1) throw new MovVerificationError('unsupported MOV structure')
    return matches[0]
  }
  const top = boxes(0, bytes.length, 'file')
  const brand = one(top, 'ftyp')
  if (brand.start !== 0 || brand.end < 20 || brand.end % 4 !== 0 ||
      !['qt  ', 'isom', 'mp41', 'mp42'].includes(fourcc(8)) ||
      top.some(box => !['ftyp', 'moov', 'mdat', 'free', 'skip', 'wide'].includes(box.type))) {
    throw new MovVerificationError('unsupported MOV container')
  }
  if (!top.some(box => box.type === 'mdat')) throw new MovVerificationError('missing mdat')
  const tracks = children(one(top, 'moov')).filter(box => box.type === 'trak')
  let videoCount = 0
  const audioTracks: MovieBox[] = []
  for (const track of tracks) {
    const media = children(one(children(track), 'mdia'))
    const handler = one(media, 'hdlr')
    if (handler.end < handler.start + 20) throw new MovVerificationError('invalid handler')
    const kind = fourcc(handler.start + 16)
    const info = children(one(media, 'minf'))
    const dataRef = one(children(one(info, 'dinf')), 'dref')
    if (dataRef.end < dataRef.start + 16 || view.getUint32(dataRef.start + 12) !== 1) throw new MovVerificationError('invalid data reference')
    const refs = boxes(dataRef.start + 16, dataRef.end, dataRef.path)
    const ref = refs[0]
    if (refs.length !== 1 || !['url ', 'alis'].includes(ref.type) || ref.end - ref.start !== 12 ||
        view.getUint32(ref.start + 8) !== 1) throw new MovVerificationError('external media reference')
    if (ref.type === 'alis') writeType(ref.start + 4, 'url ')
    const description = one(children(one(info, 'stbl')), 'stsd')
    if (description.end < description.start + 16 || view.getUint32(description.start + 12) !== 1) throw new MovVerificationError('multiple sample descriptions')
    const entries = boxes(description.start + 16, description.end, description.path)
    if (entries.length !== 1) throw new MovVerificationError('invalid sample description')
    const sample = entries[0]
    if (sample.end < sample.start + 16 || view.getUint16(sample.start + 14) !== 1) throw new MovVerificationError('invalid sample data reference')
    if (kind === 'vide' && ['avc1', 'hvc1', 'hev1'].includes(sample.type)) {
      const config = sample.type === 'avc1' ? 'avcC' : 'hvcC'
      if (sample.end < sample.start + 86) throw new MovVerificationError('truncated video sample description')
      one(boxes(sample.start + 86, sample.end, sample.path, true), config)
      videoCount++
    } else if (kind === 'soun' && sample.type === 'mp4a' && sample.end >= sample.start + 36) {
      const header = one(media, 'mdhd')
      const layout = bytes[header.start + 8]
      const versionOne = layout === 1
      if ((layout !== 0 && !versionOne) || header.end < header.start + (versionOne ? 40 : 28)) {
        throw new MovVerificationError('unsupported audio timing')
      }
      const timescale = view.getUint32(header.start + (versionOne ? 28 : 20))
      const ticks = versionOne ? Number(view.getBigUint64(header.start + 32)) : view.getUint32(header.start + 24)
      const duration = ticks / timescale
      if (!timescale || !Number.isFinite(duration) || duration <= 0 || duration > MAX_SECONDS + 0.25) throw new MovVerificationError('invalid audio duration')
      const version = view.getUint16(sample.start + 16)
      if (version > 1) throw new MovVerificationError('unsupported QuickTime audio entry')
      const properties = boxes(sample.start + (version === 1 ? 52 : 36), sample.end, sample.path)
      const wave = properties.find(box => box.type === 'wave')
      if (wave || version === 1) {
        const esds = one(wave ? children(wave) : properties, 'esds')
        const descriptor = bytes.slice(esds.start, esds.end)
        const end = sample.start + 36 + descriptor.length
        if (sample.end - end < 8) throw new MovVerificationError('missing compatible AAC descriptor space')
        bytes.fill(0, sample.start + 16, sample.start + 24)
        view.setUint16(sample.start + 28, 0)
        view.setUint16(sample.start + 30, 0)
        bytes.set(descriptor, sample.start + 36)
        view.setUint32(end, sample.end - end)
        writeType(end + 4, 'free')
        bytes.fill(0, end + 8, sample.end)
      } else one(properties, 'esds')
      audioTracks.push(track)
    } else if (!['mebx', 'mdta'].includes(sample.type)) {
      throw new MovVerificationError('unsupported MOV track')
    }
  }
  if (videoCount !== 1 || audioTracks.length !== 1) throw new MovVerificationError('missing or ambiguous audio/video')
  writeType(8, 'isom')
  view.setUint32(12, 0x200)
  for (let offset = 16; offset < brand.end; offset += 4) writeType(offset, offset === 16 ? 'isom' : 'mp42')
  for (const box of top) if (box.type === 'wide') writeType(box.start + 4, 'free')
  // Keep chunk offsets and AAC samples identical to the upload candidate.
  // WebAudio receives a single-track audio container instead of a movie.
  const audioOnly = buffer.slice(0)
  const audioView = new DataView(audioOnly)
  for (const track of tracks) {
    if (track !== audioTracks[0]) audioView.setUint32(track.start + 4, 0x66726565) // free
  }
  return { buffer, audioOnly }
}

async function verifyLocalMp4(file: File, audioOnly: ArrayBuffer, signal: AbortSignal, onAudioStage: () => void): Promise<void> {
  const video = document.createElement('video')
  const url = URL.createObjectURL(file)
  video.preload = 'auto'
  video.playsInline = true
  video.muted = true
  try {
    // Keep the probe in the document for WebKit. It is muted throughout.
    video.setAttribute('aria-hidden', 'true')
    video.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;opacity:0;pointer-events:none'
    document.body.append(video)
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = 1
    const frame = canvas.getContext('2d')
    if (!frame) throw new MovVerificationError('frame canvas unavailable')
    await new Promise<void>((resolve, reject) => {
      const events = ['loadedmetadata', 'loadeddata', 'canplay', 'playing', 'timeupdate', 'seeking', 'seeked'] as const
      const observed = new Set<string>()
      let done = false
      let playback = 'not-requested'
      let decodeTimer: number | undefined
      const diagnostic = () => `readyState=${video.readyState} networkState=${video.networkState} error=${video.error?.code ?? 0} size=${video.videoWidth}x${video.videoHeight} duration=${Number.isFinite(video.duration) ? video.duration.toFixed(2) : 'unknown'} mutedPlay=${playback} events=${[...observed].join(',') || 'none'}`
      const finish = (error?: unknown) => {
        if (done) return
        done = true
        clearTimeout(timeout)
        clearTimeout(decodeTimer)
        signal.removeEventListener('abort', abort)
        for (const event of events) video.removeEventListener(event, inspect)
        video.removeEventListener('error', onError)
        if (error) reject(error)
        else resolve()
      }
      const abort = () => finish(signal.reason)
      const verifyFrame = () => {
        if (done || video.readyState < 2 || video.seeking) return
        if (video.videoWidth <= 0 || video.videoHeight <= 0 ||
            !Number.isFinite(video.duration) || video.duration <= 0 || video.duration > MAX_SECONDS) {
          finish(new MovVerificationError('invalid decoded video: ' + diagnostic()))
          return
        }
        try {
          frame.drawImage(video, 0, 0, 1, 1)
        } catch {
          finish(new MovVerificationError('cannot draw decoded MP4 frame: ' + diagnostic()))
          return
        }
        finish()
      }
      const requestDecode = () => {
        if (done) return
        playback = 'pending'
        void video.play().then(() => {
          playback = 'started'
          verifyFrame()
        }, error => {
          if (done) return
          playback = error instanceof DOMException && ['NotAllowedError', 'NotSupportedError', 'AbortError'].includes(error.name)
            ? error.name : 'rejected'
          // Preloading can still complete if autoplay itself is blocked.
        })
      }
      const inspect = (event: Event) => {
        observed.add(event.type)
        if (event.type === 'loadedmetadata') {
          if (!Number.isFinite(video.duration) || video.duration <= 0 || video.duration > MAX_SECONDS) {
            finish(new MovVerificationError('invalid MP4 video duration: ' + diagnostic()))
            return
          }
          // A paused seek can leave WebKit at HAVE_METADATA. Start muted inline
          // decoding only if preload does not already yield a frame.
          decodeTimer = window.setTimeout(requestDecode, 250)
        }
        verifyFrame()
      }
      const onError = () => finish(new MovVerificationError('cannot decode MP4 video: ' + diagnostic()))
      const timeout = window.setTimeout(() => finish(new MovVerificationError('MP4 frame timeout: ' + diagnostic())), 8000)
      for (const event of events) video.addEventListener(event, inspect)
      video.addEventListener('error', onError)
      signal.addEventListener('abort', abort, { once: true })
      if (signal.aborted) abort()
      else video.src = url
    })
    video.pause()
    signal.throwIfAborted()
    onAudioStage()
    const audio = (async () => {
      if (typeof OfflineAudioContext === 'undefined') throw new MovVerificationError('OfflineAudioContext unavailable')
      const context = new OfflineAudioContext(1, 1, 48000)
      const decode = async (input: ArrayBuffer, container: string) => {
        try {
          return await context.decodeAudioData(input)
        } catch (error) {
          const name = error instanceof DOMException && ['EncodingError', 'NotSupportedError', 'InvalidStateError'].includes(error.name)
            ? error.name : 'failed'
          throw new MovVerificationError(container + ' ' + name)
        }
      }
      let decoded: AudioBuffer
      try {
        decoded = await decode(audioOnly, 'AAC-only MP4')
      } catch (firstError) {
        signal.throwIfAborted()
        // WebKit may reject the single-track view while accepting the same AAC
        // samples through the final MP4 demuxer.
        try {
          decoded = await decode(await file.arrayBuffer(), 'video MP4')
        } catch (secondError) {
          if (firstError instanceof MovVerificationError && secondError instanceof MovVerificationError) {
            throw new MovVerificationError(firstError.message + ' / ' + secondError.message)
          }
          throw secondError
        }
      }
      if (decoded.duration > MAX_SECONDS + 0.25) throw new MovVerificationError('decoded audio too long')
      for (let channel = 0; channel < decoded.numberOfChannels; channel++) {
        if (decoded.getChannelData(channel).some(sample => Number.isFinite(sample) && Math.abs(sample) > 0.002)) return
      }
      throw new MovVerificationError('no audible PCM in MP4')
    })()
    await Promise.race([audio, new Promise<never>((_, reject) => {
      const timeout = window.setTimeout(() => stop(new MovVerificationError('MP4 audio validation timed out')), 8000)
      const abort = () => stop(signal.reason)
      const stop = (error?: unknown) => {
        clearTimeout(timeout)
        signal.removeEventListener('abort', abort)
        if (error) reject(error)
      }
      signal.addEventListener('abort', abort, { once: true })
      if (signal.aborted) abort()
      void audio.then(() => stop(), stop)
    })])
    signal.throwIfAborted()
  } finally {
    video.pause()
    video.remove()
    video.removeAttribute('src')
    try { video.load() } finally { URL.revokeObjectURL(url) }
  }
}

/** Fast path can request muted decoding; it never needs audible playback or a retained gesture. */
export async function prepareMovForUpload(file: File, gesture: MovPlaybackGesture, selectionSignal: AbortSignal, onFallback?: (diagnostic: string) => void): Promise<File> {
  selectionSignal.throwIfAborted()
  if (!isMovVideo(file) || file.size < 1 || file.size > MAX_BYTES) return convertMovToMp4(file, gesture, selectionSignal)
  const work = new AbortController()
  const hide = () => { if (document.hidden) work.abort(new Error('動画の変換を中止しました。')) }
  const signal = AbortSignal.any([selectionSignal, work.signal])
  document.addEventListener('visibilitychange', hide)
  let stage = 'file'
  try {
    const input = await file.arrayBuffer()
    stage = 'container'
    const { buffer, audioOnly } = remuxCompatibleMov(input)
    signal.throwIfAborted()
    const mp4 = new File([buffer], file.name.replace(/\\.[^.]+$/, '') + '-converted.mp4', { type: 'video/mp4' })
    stage = 'video'
    await verifyLocalMp4(mp4, audioOnly, signal, () => { stage = 'audio' })
    return mp4
  } catch (error) {
    signal.throwIfAborted()
    // Only report static verifier messages. Native errors may contain local details.
    const reason = error instanceof MovVerificationError ? error.message : 'browser error'
    onFallback?.(stage + ': ' + reason)
  } finally {
    work.abort()
    document.removeEventListener('visibilitychange', hide)
  }
  return convertMovToMp4(file, gesture, selectionSignal)
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
