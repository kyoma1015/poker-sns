/** Bound authenticated playback before buffering untrusted response bytes. */
export const MAX_PLAYBACK_BYTES = 20 * 1024 * 1024

export async function readVideoResponse(response: Response): Promise<Blob> {
  if (!response.ok || !response.body) {
    await response.body?.cancel().catch(() => undefined)
    throw new Error('動画を読み込めませんでした。')
  }
  const mime = response.headers.get('content-type')?.split(';', 1)[0]?.trim().toLowerCase()
  const length = response.headers.get('content-length')
  if (!mime || !['video/mp4', 'video/webm', 'video/quicktime'].includes(mime) ||
      (length !== null && (!/^[1-9][0-9]*$/.test(length) ||
        !Number.isSafeInteger(Number(length)) || Number(length) > MAX_PLAYBACK_BYTES))) {
    await response.body.cancel().catch(() => undefined)
    throw new Error('動画データが不正です。')
  }
  const reader = response.body.getReader()
  const chunks: BlobPart[] = []
  let total = 0
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      total += value.byteLength
      if (total > MAX_PLAYBACK_BYTES) throw new Error('動画は20MB以内にしてください。')
      chunks.push(value as Uint8Array<ArrayBuffer>)
    }
  } finally {
    await reader.cancel().catch(() => undefined)
    reader.releaseLock()
  }
  if (!total || (length !== null && Number(length) !== total)) throw new Error('動画データが不完全です。')
  return new Blob(chunks, { type: mime })
}
