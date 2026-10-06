import { ImageResponse } from '@vercel/og'

const money = (value) => {
  const n = Number(value)
  return Number.isFinite(n)
    ? `¥${Math.round(n).toLocaleString('ja-JP')}`
    : '—'
}

export async function GET(request) {
  try {
    const url = new URL(request.url)
    const type = url.searchParams.get('type') || ''
    const id = url.searchParams.get('id') || ''

    const supabaseUrl = process.env.VITE_SUPABASE_URL
    const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY

    if (!supabaseUrl) {
      return new Response('VITE_SUPABASE_URL is missing', { status: 500 })
    }

    if (!supabaseKey) {
      return new Response('VITE_SUPABASE_ANON_KEY is missing', { status: 500 })
    }

    if (!id) {
      return new Response('Result ID is missing', { status: 400 })
    }

    const tables = {
      tournament: 'poker_results',
      amusement: 'amusement_ring_results',
      cash: 'cash_game_results',
    }

    const table = tables[type]

    if (!table) {
      return new Response('Invalid result type', { status: 400 })
    }

    const dbResponse = await fetch(
      `${supabaseUrl}/rest/v1/${table}?id=eq.${encodeURIComponent(id)}&is_public=eq.true&select=*`,
      {
        headers: {
          apikey: supabaseKey,
          Authorization: `Bearer ${supabaseKey}`,
        },
      },
    )

    if (!dbResponse.ok) {
      const body = await dbResponse.text()

      return new Response(
        `Supabase error ${dbResponse.status}\n${body}`,
        { status: 500 },
      )
    }

    const rows = await dbResponse.json()
    const r = rows?.[0]

    if (!r) {
      return new Response('Result not found or private', { status: 404 })
    }

    let eyebrow = 'POKER RESULT'
    let title = 'Poker ID'
    let main = 'RESULT'
    let sub = ''
    let detail = ''
    let badge = ''

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

        if (rank === 1) badge = 'WINNER'
        else if (rank === 2) badge = '2ND PLACE'
        else if (rank === 3) badge = '3RD PLACE'
        else if (r.is_itm) badge = 'ITM'
      } else if (r.is_itm) {
        main = 'ITM'
        badge = 'IN THE MONEY'
      }

      if (r.entry_count) {
        sub = `${Number(r.entry_count).toLocaleString('ja-JP')} ENTRIES`
      }

      if (Number(r.prize_amount) > 0) {
        detail = `PRIZE VALUE  ${money(r.prize_amount)}`
      } else if (r.venue) {
        detail = r.venue
      }
    }

    if (type === 'amusement') {
      eyebrow = 'AMUSEMENT RING RESULT'
      title = r.venue || 'Amusement Poker'

      const bb = Number(r.result_bb ?? r.profit_bb ?? 0)

      main = `${bb >= 0 ? '+' : ''}${
        Number.isFinite(bb) ? bb.toFixed(1) : '0.0'
      } BB`

      sub = r.game_type || r.game || ''
      detail = r.played_at || ''
      badge = bb >= 0 ? 'WIN' : 'LOSS'
    }

    if (type === 'cash') {
      eyebrow = 'CASH GAME RESULT'
      title = r.venue || r.site || 'Cash Game'

      const profit = Number(r.profit_jpy ?? r.profit ?? 0)

      main = `${profit >= 0 ? '+' : ''}${money(profit)}`
      sub = r.game_type || r.game || ''
      detail = r.played_at || ''
      badge = profit >= 0 ? 'WIN' : 'LOSS'
    }

    const element = {
      type: 'div',
      props: {
        style: {
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          background: '#050505',
          color: '#ffffff',
          padding: '64px 72px',
          fontFamily: 'sans-serif',
        },
        children: [
          {
            type: 'div',
            props: {
              style: {
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              },
              children: [
                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      fontSize: 32,
                      fontWeight: 800,
                      letterSpacing: '-1px',
                    },
                    children: '♠ POKER ID',
                  },
                },
                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      fontSize: 18,
                      letterSpacing: '4px',
                      color: '#a3a3a3',
                    },
                    children: eyebrow,
                  },
                },
              ],
            },
          },

          {
            type: 'div',
            props: {
              style: {
                display: 'flex',
                flexDirection: 'column',
                gap: '18px',
              },
              children: [
                badge
                  ? {
                      type: 'div',
                      props: {
                        style: {
                          display: 'flex',
                          alignSelf: 'flex-start',
                          border: '2px solid #ffffff',
                          borderRadius: '999px',
                          padding: '8px 18px',
                          fontSize: 18,
                          fontWeight: 700,
                          letterSpacing: '2px',
                        },
                        children: badge,
                      },
                    }
                  : null,

                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      fontSize: 34,
                      color: '#d4d4d4',
                      maxWidth: '1000px',
                      overflow: 'hidden',
                    },
                    children: title,
                  },
                },

                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      alignItems: 'baseline',
                      gap: '24px',
                    },
                    children: [
                      {
                        type: 'div',
                        props: {
                          style: {
                            display: 'flex',
                            fontSize: 112,
                            fontWeight: 900,
                            lineHeight: 1,
                            letterSpacing: '-6px',
                          },
                          children: main,
                        },
                      },
                      {
                        type: 'div',
                        props: {
                          style: {
                            display: 'flex',
                            fontSize: 28,
                            color: '#bdbdbd',
                          },
                          children: sub,
                        },
                      },
                    ],
                  },
                },
              ],
            },
          },

          {
            type: 'div',
            props: {
              style: {
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-end',
                borderTop: '1px solid #333333',
                paddingTop: '28px',
              },
              children: [
                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      fontSize: 26,
                      fontWeight: 700,
                    },
                    children: detail,
                  },
                },
                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      fontSize: 18,
                      color: '#777777',
                    },
                    children: 'poker-sns-vert.vercel.app',
                  },
                },
              ],
            },
          },
        ],
      },
    }

    return new ImageResponse(element, {
      width: 1200,
      height: 630,
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    })
  } catch (error) {
    const message =
      error instanceof Error ? error.stack || error.message : String(error)

    return new Response(`OG ERROR\n\n${message}`, {
      status: 500,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    })
  }
}