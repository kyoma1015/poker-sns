import { ImageResponse } from '@vercel/og'

const money = (value: unknown) => {
  const n = Number(value)

  return Number.isFinite(n)
    ? `¥${Math.round(n).toLocaleString('ja-JP')}`
    : '—'
}

export async function GET(request: Request) {
  try {
    const url = new URL(request.url)

    const type = url.searchParams.get('type') || ''
    const id = url.searchParams.get('id') || ''

    const supabaseUrl = process.env.VITE_SUPABASE_URL
    const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY

    if (!supabaseUrl) {
      return new Response('ERROR: VITE_SUPABASE_URL is missing', {
        status: 500,
      })
    }

    if (!supabaseKey) {
      return new Response('ERROR: VITE_SUPABASE_ANON_KEY is missing', {
        status: 500,
      })
    }

    if (!id) {
      return new Response('ERROR: result id is missing', {
        status: 400,
      })
    }

    const tables: Record<string, string> = {
      tournament: 'poker_results',
      amusement: 'amusement_ring_results',
      cash: 'cash_game_results',
    }

    const table = tables[type]

    if (!table) {
      return new Response(`ERROR: invalid result type: ${type}`, {
        status: 400,
      })
    }

    const apiUrl =
      `${supabaseUrl}/rest/v1/${table}` +
      `?id=eq.${encodeURIComponent(id)}` +
      `&is_public=eq.true` +
      `&select=*`

    const response = await fetch(apiUrl, {
      headers: {
        apikey: supabaseKey,
        Authorization: `Bearer ${supabaseKey}`,
      },
    })

    if (!response.ok) {
      const errorText = await response.text()

      return new Response(
        `ERROR: Supabase request failed\nStatus: ${response.status}\n${errorText}`,
        {
          status: 500,
          headers: {
            'Content-Type': 'text/plain; charset=utf-8',
          },
        },
      )
    }

    const rows = await response.json()
    const r = rows?.[0]

    if (!r) {
      return new Response(
        'ERROR: result not found or result is not public',
        {
          status: 404,
        },
      )
    }

    let eyebrow = 'POKER RESULT'
    let title = 'Poker ID'
    let main = 'RESULT'
    let sub = ''
    let detail = ''

    if (type === 'tournament') {
      eyebrow = 'TOURNAMENT RESULT'
      title = r.tournament_name || 'Tournament'

      if (!r.rank_unknown && r.rank) {
        const rank = Number(r.rank)

        const suffix =
          rank === 1
            ? 'ST'
            : rank === 2
              ? 'ND'
              : rank === 3
                ? 'RD'
                : 'TH'

        main = `${rank}${suffix}`
      }

      sub = r.entry_count
        ? `/ ${Number(r.entry_count).toLocaleString('ja-JP')} ENTRIES`
        : r.is_itm
          ? 'ITM'
          : ''

      detail =
        Number(r.prize_amount) > 0
          ? `PRIZE VALUE  ${money(r.prize_amount)}`
          : r.venue || ''
    }

    if (type === 'amusement') {
      eyebrow = 'AMUSEMENT RING RESULT'
      title = r.venue || 'Amusement Poker'

      const bb = Number(r.result_bb ?? r.profit_bb ?? 0)

      main =
        `${bb >= 0 ? '+' : ''}` +
        `${Number.isFinite(bb) ? bb.toFixed(1) : '0'} BB`

      sub = r.game_type || r.game || ''
      detail = r.played_at || ''
    }

    if (type === 'cash') {
      eyebrow = 'CASH GAME RESULT'
      title = r.venue || r.site || 'Cash Game'

      const profit = Number(r.profit_jpy ?? r.profit ?? 0)

      main = `${profit >= 0 ? '+' : ''}${money(profit)}`
      sub = r.game_type || r.game || ''
      detail = r.played_at || ''
    }

    return new ImageResponse(
      (
        <div
          style={{
            width: '1200px',
            height: '630px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            background: '#050505',
            color: '#ffffff',
            padding: '64px 72px',
            fontFamily: 'sans-serif',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div
              style={{
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: '-1px',
              }}
            >
              POKER ID
            </div>

            <div
              style={{
                fontSize: 22,
                color: '#8a8a8a',
                letterSpacing: '4px',
              }}
            >
              {eyebrow}
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div
              style={{
                fontSize: 32,
                color: '#a0a0a0',
                marginBottom: 20,
                maxWidth: 980,
              }}
            >
              {title}
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'baseline',
                gap: 24,
              }}
            >
              <div
                style={{
                  fontSize: 112,
                  fontWeight: 900,
                  letterSpacing: '-6px',
                }}
              >
                {main}
              </div>

              {sub && (
                <div
                  style={{
                    fontSize: 34,
                    color: '#b5b5b5',
                  }}
                >
                  {sub}
                </div>
              )}
            </div>

            {detail && (
              <div
                style={{
                  fontSize: 30,
                  marginTop: 24,
                  color: '#dedede',
                }}
              >
                {detail}
              </div>
            )}
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              borderTop: '1px solid #292929',
              paddingTop: 24,
            }}
          >
            <div
              style={{
                fontSize: 22,
                color: '#777',
              }}
            >
              Your poker history becomes your identity.
            </div>

            <div
              style={{
                fontSize: 22,
                color: '#777',
              }}
            >
              poker-sns-vert.vercel.app
            </div>
          </div>
        </div>
      ),
      {
        width: 1200,
        height: 630,
      },
    )
  } catch (error) {
    const message =
      error instanceof Error
        ? `${error.name}: ${error.message}\n${error.stack || ''}`
        : String(error)

    return new Response(`OG ERROR:\n${message}`, {
      status: 500,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    })
  }
}