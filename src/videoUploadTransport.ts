// Scope cancellation to the exact private video upload. Other SDK traffic is
// unchanged; neither credentials nor request/response bodies are retained.
const uploads = new Map<string, AbortSignal>()
export const VIDEO_UPLOAD_TIMEOUT_MS = 90000

export async function withVideoUploadRequest<T>(path: string, signal: AbortSignal | undefined, upload: () => Promise<T>): Promise<T> {
  const deadline = new AbortController()
  const timer = setTimeout(() => deadline.abort(), VIDEO_UPLOAD_TIMEOUT_MS)
  const combined = signal ? AbortSignal.any([signal, deadline.signal]) : deadline.signal
  const key = '/storage/v1/object/post-videos/' + path.split('/').map(encodeURIComponent).join('/')
  uploads.set(key, combined)
  try {
    combined.throwIfAborted()
    return await upload()
  } finally {
    clearTimeout(timer)
    if (uploads.get(key) === combined) uploads.delete(key)
  }
}

export const videoStorageFetch: typeof fetch = (input, init) => {
  const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input.href : input.url)
  const signal = uploads.get(url.pathname)
  if (!signal || (init?.method ?? (input instanceof Request ? input.method : 'GET')).toUpperCase() !== 'POST') {
    return fetch(input, init)
  }
  const original = init?.signal ?? (input instanceof Request ? input.signal : undefined)
  return fetch(input, { ...init, redirect: 'error', signal: original ? AbortSignal.any([signal, original]) : signal })
}
