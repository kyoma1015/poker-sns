// These deadlines bound waiting for browser callbacks, not OS/browser scheduling.
const IMAGE_DEADLINE_MS = 15000
export function loadShareImage(source: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    let settled = false
    const finish = (failure?: Error) => {
      if (settled) return
      settled = true
      window.clearTimeout(timer)
      image.onload = null
      image.onerror = null
      if (failure) reject(failure)
      else resolve(image)
    }
    const timer = window.setTimeout(() => finish(new Error('画像の読み込みがタイムアウトしました')), IMAGE_DEADLINE_MS)
    image.onload = () => finish()
    image.onerror = () => finish(new Error('動物画像を読み込めませんでした'))
    // Set handlers before src, including for a synchronously available image.
    try { image.src = source } catch { finish(new Error('動物画像を読み込めませんでした')) }
  })
}
export function encodeSharePng(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    let settled = false
    const finish = (blob: Blob | null) => {
      if (settled) return
      settled = true
      window.clearTimeout(timer)
      if (blob) resolve(blob)
      else reject(new Error('画像データを作成できませんでした'))
    }
    const timer = window.setTimeout(() => finish(null), IMAGE_DEADLINE_MS)
    try { canvas.toBlob(finish, 'image/png') } catch { finish(null) }
  })
}
