// Same-device poster fallback. Never uploaded, never shared, and never used to authorize media.
// Scope to the authenticated owner AND immutable video object path.
const PREFIX = 'poker-id-video-poster-v1:'
const MAX_POSTER_CHARS = 160_000
const MAX_ENTRIES = 12
const key = (owner: string, path: string) => PREFIX + owner + ':' + encodeURIComponent(path)

export function rememberLocalVideoPoster(owner: string, path: string, dataUrl: string): void {
  if (!owner || !path || !/^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(dataUrl) || dataUrl.length > MAX_POSTER_CHARS) return
  try {
    const entries = Object.keys(localStorage).filter(k => k.startsWith(PREFIX) && k !== key(owner, path))
    while (entries.length >= MAX_ENTRIES) localStorage.removeItem(entries.shift()!)
    localStorage.setItem(key(owner, path), dataUrl)
  } catch { /* Quota and private browsing must never block a post. */ }
}

export function readLocalVideoPoster(owner: string, path: string): string {
  if (!owner || !path) return ''
  try {
    const value = localStorage.getItem(key(owner, path)) || ''
    return /^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(value) && value.length <= MAX_POSTER_CHARS ? value : ''
  } catch { return '' }
}
