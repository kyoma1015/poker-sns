import type { VercelRequest, VercelResponse } from '@vercel/node'
async function getPublicPlayerTypeResult(supabaseUrl: string, serviceKey: string, id: string) {
  const headers = { apikey: serviceKey, Authorization: `Bearer ${serviceKey}` }
  const response = await fetch(`${supabaseUrl}/rest/v1/player_type_diagnosis_results?id=eq.${encodeURIComponent(id)}&is_public=eq.true&select=id,result_type_key,version_id`, { headers })
  if (!response.ok) throw new Error(`Result lookup failed: ${response.status}`)
  const result = (await response.json())[0]
  if (!result) return null
  const versionResponse = await fetch(`${supabaseUrl}/rest/v1/player_type_diagnosis_versions?id=eq.${encodeURIComponent(result.version_id)}&version_key=eq.player-type-v2&select=id`, { headers })
  if (!versionResponse.ok || !(await versionResponse.json()).length) return null
  const defResponse = await fetch(`${supabaseUrl}/rest/v1/player_type_definitions?type_key=eq.${encodeURIComponent(result.result_type_key)}&select=animal_name_ja,catchphrase`, { headers })
  if (!defResponse.ok) throw new Error(`Definition lookup failed: ${defResponse.status}`)
  const definition = (await defResponse.json())[0]
  return definition ? { ...result, ...definition } : null
}


const esc = (value: unknown) =>
  String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const type = String(req.query.type ?? '')
  const id = String(req.query.id ?? '')
  const origin = `https://${req.headers.host}`

  if (!['tournament', 'amusement', 'cash', 'player-type'].includes(type) || !id) {
    return res.status(400).send('Invalid share URL')
  }

  const supabaseUrl = process.env.VITE_SUPABASE_URL
  const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY
  if (!supabaseUrl || !supabaseKey) return res.status(500).send('Missing Supabase environment variables')

  if (type === 'player-type') {
    const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
    if (!serviceKey) return res.status(500).send('SUPABASE_SERVICE_ROLE_KEY is missing')
    let result
    try { result = await getPublicPlayerTypeResult(supabaseUrl, serviceKey, id) }
    catch (error) { console.error(error); return res.status(500).send('Failed to load diagnosis') }
    if (!result) return res.status(404).send('Public diagnosis not found')
    const canonical = `${origin}/share/player-type/${encodeURIComponent(id)}`
    const image = `${origin}/api/og?type=player-type&id=${encodeURIComponent(id)}`
    const destination = `${origin}/player-type?result=${encodeURIComponent(id)}`
    const title = `ポーカータイプ診断：${result.animal_name_ja} | Poker ID`
    const description = `${result.catchphrase || 'あなたはどのタイプ？'}｜全50問・36種類の動物タイプ`
    res.setHeader('Content-Type', 'text/html; charset=utf-8')
    res.setHeader('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=300')
    return res.status(200).send(`<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(description)}">
<link rel="canonical" href="${esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Poker ID">
<meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${esc(canonical)}"><meta property="og:image" content="${esc(image)}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}"><meta name="twitter:image" content="${esc(image)}">
</head><body style="background:#080808;color:#fff;text-align:center;font-family:system-ui,sans-serif;padding:40px">
<h1>Poker ID</h1><p>${esc(title)}</p><a href="${esc(destination)}" style="color:#d4b879">診断結果を見る</a>
<script>location.replace(${JSON.stringify(destination)})</script></body></html>`)
  }

  const tables: Record<string, string> = {
    tournament: 'poker_results',
    amusement: 'amusement_ring_results',
    cash: 'cash_game_results',
  }

  const response = await fetch(
    `${supabaseUrl}/rest/v1/${tables[type]}?id=eq.${encodeURIComponent(id)}&is_public=eq.true&select=*`,
    { headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}` } }
  )

  if (!response.ok) return res.status(404).send('Result not found')
  const rows = await response.json()
  const result = rows?.[0]
  if (!result) return res.status(404).send('Result not found or private')

  let title = 'Poker ID Result'
  let description = 'Poker IDでポーカー戦績をチェック'
  if (type === 'tournament') {
    const rank = result.rank_unknown || !result.rank ? '順位不明' : `${result.rank}位`
    const entries = result.entry_count ? ` / ${result.entry_count}人` : ''
    title = `${result.tournament_name} | ${rank}${entries}`
    description = result.is_itm ? 'Tournament Result · ITM' : 'Tournament Result'
  } else if (type === 'amusement') {
    title = `${result.venue || 'Amusement Poker'} | Poker ID`
    description = 'Amusement Ring Result'
  } else {
    title = `${result.venue || result.site || 'Cash Game'} | Poker ID`
    description = 'Cash Game Result'
  }

  const canonical = `${origin}/share/${type}/${encodeURIComponent(id)}`
  const image = `${origin}/api/og?type=${encodeURIComponent(type)}&id=${encodeURIComponent(id)}`
  const destination = result.user_id ? `${origin}/player/${encodeURIComponent(result.user_id)}` : `${origin}/timeline`

  res.setHeader('Content-Type', 'text/html; charset=utf-8')
  res.setHeader('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=300')
  return res.status(200).send(`<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<link rel="canonical" href="${esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Poker ID">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${esc(canonical)}">
<meta property="og:image" content="${esc(image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${esc(image)}">
</head>
<body style="margin:0;background:#050505;color:#fff;font-family:system-ui,sans-serif">
<main style="max-width:680px;margin:80px auto;padding:24px;text-align:center">
<h1>Poker ID</h1>
<p>${esc(title)}</p>
<a href="${esc(destination)}" style="color:#fff">Poker IDで見る</a>
</main>
<script>location.replace(${JSON.stringify(destination)})</script>
</body>
</html>`)
}
