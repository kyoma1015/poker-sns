import type { VercelRequest, VercelResponse } from '@vercel/node'

// The Edge Function checks is_public before reading the private Storage object.
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function reject(res: VercelResponse, status: number, message: string) {
  res.setHeader('Cache-Control', 'no-store')
  res.setHeader('Content-Type', 'text/plain; charset=utf-8')
  res.setHeader('X-Content-Type-Options', 'nosniff')
  return res.status(status).send(message)
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'GET' && req.method !== 'HEAD') return reject(res, 405, 'この操作は利用できません。')
  const id = String(req.query.id ?? '')
  if (!UUID_PATTERN.test(id)) return reject(res, 400, 'カードIDが正しくありません。')

  const base = process.env.VITE_SUPABASE_URL
  const anonKey = process.env.VITE_SUPABASE_ANON_KEY
  if (!base || !anonKey) return reject(res, 503, '現在、カード画像を表示できません。')

  try {
    const response = await fetch(`${base}/functions/v1/public-poker-id-card-image?id=${encodeURIComponent(id)}`, {
      method: req.method,
      headers: { apikey: anonKey, Authorization: `Bearer ${anonKey}` },
      cache: 'no-store',
    })
    if (response.status === 404) return reject(res, 404, 'このカード画像は非公開、削除済み、または存在しません。')
    if (!response.ok) {
      console.error('Public card image unavailable', response.status)
      return reject(res, 503, 'カード画像の取得に失敗しました。')
    }

    res.setHeader('Content-Type', 'image/png')
    res.setHeader('X-Content-Type-Options', 'nosniff')
    res.setHeader('Cache-Control', 'no-store')
    if (req.method === 'HEAD') return res.status(200).end()
    return res.status(200).send(Buffer.from(await response.arrayBuffer()))
  } catch (error) {
    console.error('Public card image proxy failure', error)
    return reject(res, 503, 'カード画像の取得に失敗しました。')
  }
}
