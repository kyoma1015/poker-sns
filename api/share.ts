import type { VercelRequest, VercelResponse } from '@vercel/node'

// Public RPCs enforce is_public=true server-side and never expose private answers.
async function getPublicPlayerTypeResult(supabaseUrl: string, anonKey: string, id: string) {
  const headers = { apikey: anonKey, Authorization: `Bearer ${anonKey}`, 'Content-Type': 'application/json' }
  for (const [functionName, argument] of [
    ['get_public_player_type_result_by_id', 'p_result_id'],
    ['get_public_player_type_result', 'p_user_id'],
  ] as const) {
    const response = await fetch(`${supabaseUrl}/rest/v1/rpc/${functionName}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ [argument]: id }),
    })
    if (!response.ok) throw new Error(`Public diagnosis lookup failed: ${response.status}`)
    const result = (await response.json())?.[0]
    if (result) return result
  }
  return null
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i


const esc = (value: unknown) =>
  String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')

const sendShareNotice = (res: VercelResponse, status: number, message: string) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8')
  res.setHeader('Cache-Control', 'no-store')
  return res.status(status).send(`<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Poker ID｜公開シェア</title></head>
<body style="margin:0;background:#080808;color:#f6f6f6;font-family:system-ui,sans-serif;padding:24px">
<main style="max-width:540px;margin:50px auto;padding:24px;border:1px solid #383838;border-radius:16px">
<p style="color:#bbb">♠ Poker ID · 公開シェア</p><h1 style="font-size:24px">共有ページ</h1>
<p role="status">${esc(message)}</p>
<a href="/timeline" style="display:inline-block;margin-top:16px;padding:12px 16px;background:#fff;color:#111;border-radius:9px;text-decoration:none;font-weight:700">Poker IDを見る →</a>
</main></body></html>`)
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const type = String(req.query.type ?? '')
  const id = String(req.query.id ?? '')
  const origin = `https://${req.headers.host}`

  if (!['tournament', 'amusement', 'cash', 'player-type', 'poker-id'].includes(type) || !id) {
    return sendShareNotice(res, 400, '共有URLが正しくありません。')
  }

  const supabaseUrl = process.env.VITE_SUPABASE_URL
  const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY
  if (!supabaseUrl || !supabaseKey) return sendShareNotice(res, 503, '現在、共有ページを表示できません。時間をおいて再度お試しください。')

  if (type === 'poker-id') {
    const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
    if (!serviceKey) return res.status(500).send('Missing share configuration')
    const headers = { apikey: serviceKey, Authorization: `Bearer ${serviceKey}` }
    try {
      const cardResponse = await fetch(`${supabaseUrl}/rest/v1/poker_id_cards?user_id=eq.${encodeURIComponent(id)}&is_public=eq.true&select=user_id`, { headers })
      if (!cardResponse.ok) throw new Error('Public card lookup failed')
      if (!(await cardResponse.json()).length) return res.status(404).send('Card not public')
      const profileResponse = await fetch(`${supabaseUrl}/rest/v1/profiles?id=eq.${encodeURIComponent(id)}&select=display_name,poker_id`, { headers })
      if (!profileResponse.ok) throw new Error('Profile lookup failed')
      const profile = (await profileResponse.json())[0]
      if (!profile) return res.status(404).send('Player not found')
      const canonical = `${origin}/share/poker-id/${encodeURIComponent(id)}${req.query.v ? '?v='+encodeURIComponent(String(req.query.v)) : ''}`
      const image = `${origin}/api/poker-id-image?id=${encodeURIComponent(id)}&v=${encodeURIComponent(String(req.query.v ?? '1'))}`
      const destination = `${origin}/player/${encodeURIComponent(id)}/card`
      const title = `${profile.display_name || profile.poker_id || 'プレイヤー'}のPoker IDカード`
      const description = 'プレイヤータイプ・ポーカー歴・メイン種目・大会実績を1枚に。Poker IDでプロフィールを見る'
      res.setHeader('Content-Type', 'text/html; charset=utf-8')
      res.setHeader('Cache-Control', 'public, s-maxage=60')
      return res.status(200).send(`<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(description)}">
<link rel="canonical" href="${esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Poker ID">
<meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${esc(canonical)}"><meta property="og:image" content="${esc(image)}">
<meta property="og:image:width" content="1080"><meta property="og:image:height" content="1350">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}"><meta name="twitter:image" content="${esc(image)}">
</head><body style="background:#080808;color:white;font-family:system-ui,sans-serif;padding:40px;text-align:center">
<h1>${esc(title)}</h1><a href="${esc(destination)}">Poker IDで見る</a>
<script>location.replace(${JSON.stringify(destination)})</script></body></html>`)
    } catch(error) { console.error(error); return res.status(500).send('Failed to load card') }
  }

  if (type === 'player-type') {
    if (!UUID_PATTERN.test(id)) return sendShareNotice(res, 404, 'この記録は非公開、削除済み、または存在しません。')
    let result
    try { result = await getPublicPlayerTypeResult(supabaseUrl, supabaseKey, id) }
    catch (error) {
      console.error('公開診断結果の取得に失敗:', error)
      return sendShareNotice(res, 503, '記録の取得に失敗しました。時間をおいて再度お試しください。')
    }
    if (!result) return sendShareNotice(res, 404, 'この記録は非公開、削除済み、または存在しません。')
    const canonical = `${origin}/share/player-type/${encodeURIComponent(id)}`
    const title = `ポーカータイプ診断：${result.animal_name_ja || '動物タイプ'} | Poker ID`
    const description = `${result.catchphrase || 'あなたはどのタイプ？'}｜全50問・36種類の動物タイプ。※プレイヤータイプは強さや技術の優劣を示すものではありません。`
    res.setHeader('Content-Type', 'text/html; charset=utf-8')
    // Visibility can change at any time. Avoid keeping publicly cached results after privacy changes.
    res.setHeader('Cache-Control', 'no-store')
    return res.status(200).send(`<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(description)}">
<link rel="canonical" href="${esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Poker ID">
<meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${esc(canonical)}">
<meta name="twitter:card" content="summary"><meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
</head><body style="margin:0;background:#080808;color:#fff;font-family:system-ui,sans-serif;padding:24px">
<main style="max-width:540px;margin:50px auto;padding:24px;border:1px solid #383838;border-radius:16px">
<p style="color:#bbb">♠ Poker ID · 公開シェア</p>
<h1 style="font-size:25px;overflow-wrap:anywhere">${esc(result.animal_name_ja || '動物タイプ診断')}</h1>
<p>${esc(result.catchphrase || '')}</p>
${result.description ? `<section><h2 style="font-size:16px">特徴</h2><p style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(result.description)}</p></section>` : ''}
${result.strength_text ? `<section><h2 style="font-size:16px">強み</h2><p style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(result.strength_text)}</p></section>` : ''}
${result.weakness_text ? `<section><h2 style="font-size:16px">注意点</h2><p style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(result.weakness_text)}</p></section>` : ''}
<a href="/timeline" style="display:inline-block;margin-top:16px;padding:12px 16px;background:#fff;color:#111;border-radius:9px;text-decoration:none;font-weight:700">Poker IDを見る →</a>
</main></body></html>`)
  }

  if (!UUID_PATTERN.test(id)) return sendShareNotice(res, 404, 'この記録は非公開、削除済み、または存在しません。')

  const tables: Record<string, string> = {
    tournament: 'poker_results',
    amusement: 'amusement_ring_results',
    cash: 'cash_game_results',
  }

  const response = await fetch(
    `${supabaseUrl}/rest/v1/${tables[type]}?id=eq.${encodeURIComponent(id)}&is_public=eq.true&select=*`,
    { headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}` } }
  )

  if (!response.ok) return sendShareNotice(res, 503, '記録の取得に失敗しました。時間をおいて再度お試しください。')
  const rows = await response.json()
  const result = rows?.[0]
  if (!result) return sendShareNotice(res, 404, 'この記録は非公開、削除済み、または存在しません。')

  let title = 'Poker ID Result'
  let description = 'Poker IDでポーカー戦績をチェック'
  if (type === 'tournament') {
    const rank = result.rank_unknown || !result.rank ? '順位不明' : `${result.rank}位`
    const entries = result.entry_count ? ` / ${result.entry_count}人` : ''
    title = `${result.tournament_name} | ${rank}${entries}`
    description = result.is_itm ? 'Tournament Result · ITM' : 'Tournament Result'
  } else if (type === 'amusement') {
    title = `${result.venue || 'Ring Game'} | Poker ID`
    description = 'Ring Game Result'
  } else {
    title = `${result.venue || result.site || 'Cash Game'} | Poker ID`
    description = 'Cash Game Result'
  }

  const canonical = `${origin}/share/${type}/${encodeURIComponent(id)}`
  const image = `${origin}/api/og?type=${encodeURIComponent(type)}&id=${encodeURIComponent(id)}`
  const destination = result.user_id ? `${origin}/player/${encodeURIComponent(result.user_id)}` : `${origin}/timeline`

  res.setHeader('Content-Type', 'text/html; charset=utf-8')
  // Public results can be made private at any time; do not cache their shared HTML.
  res.setHeader('Cache-Control', 'no-store')
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
