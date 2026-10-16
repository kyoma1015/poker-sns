import type { VercelRequest, VercelResponse } from '@vercel/node'

// Serve the exact 1080x1350 PNG saved by the card's client-side Canvas renderer.
// Private storage is never exposed directly. Each request validates visibility.
export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'GET' && req.method !== 'HEAD') return res.status(405).send('Method not allowed')
  const id = String(req.query.id ?? '')
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) return res.status(400).send('Invalid player')
  const base = process.env.VITE_SUPABASE_URL
  const secret = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!base || !secret) return res.status(500).send('Missing server configuration')
  const headers = { apikey: secret, Authorization: `Bearer ${secret}` }
  try {
    const card = await fetch(`${base}/rest/v1/poker_id_cards?user_id=eq.${encodeURIComponent(id)}&is_public=eq.true&select=user_id`, { headers, cache:'no-store' })
    if (!card.ok) throw new Error(`Card lookup failed (${card.status})`)
    if (!(await card.json()).length) return res.status(404).send('Card not public')
    const png = await fetch(`${base}/storage/v1/object/poker-id-card-og/${encodeURIComponent(id)}/card.png`, { headers, cache:'no-store' })
    if (png.status === 404 || png.status === 400) return res.status(404).send('Card preview image not yet generated')
    if (!png.ok) throw new Error(`Image lookup failed (${png.status})`)
    res.setHeader('Content-Type','image/png')
    res.setHeader('X-Content-Type-Options','nosniff')
    res.setHeader('Cache-Control','private, no-store, max-age=0')
    if (req.method === 'HEAD') return res.status(200).end()
    return res.status(200).send(Buffer.from(await png.arrayBuffer()))
  } catch (error) {
    console.error('Poker ID OG image error', error)
    return res.status(500).send('Failed to generate card preview')
  }
}
