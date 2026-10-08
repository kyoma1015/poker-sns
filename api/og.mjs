import { ImageResponse } from '@vercel/og'
async function getPlayerTypeResult(supabaseUrl, serviceKey, id) {
  const headers = { apikey: serviceKey, Authorization: `Bearer ${serviceKey}` }
  const resultsResponse = await fetch(
    `${supabaseUrl}/rest/v1/player_type_diagnosis_results?id=eq.${encodeURIComponent(id)}&is_public=eq.true&select=id,result_type_key`,
    { headers },
  )
  if (!resultsResponse.ok) {
    const errorBody = (await resultsResponse.text()).slice(0, 1200)
    console.error('Player type result lookup failed', { status: resultsResponse.status, body: errorBody })
    throw new Error(`Result lookup failed: ${resultsResponse.status}. Check Vercel logs.`)
  }
  const result = (await resultsResponse.json())[0]
  if (!result) return null

  // 公開済み結果は過去の診断バージョンでも表示できるようにする。
  // version_key の固定値による追加フィルタは行わない。
  const definitionsResponse = await fetch(
    `${supabaseUrl}/rest/v1/player_type_definitions?type_key=eq.${encodeURIComponent(result.result_type_key)}&select=animal_name_ja,catchphrase`,
    { headers },
  )
  if (!definitionsResponse.ok) {
    const errorBody = (await definitionsResponse.text()).slice(0, 1200)
    console.error('Player type definition lookup failed', { status: definitionsResponse.status, body: errorBody })
    throw new Error(`Definition lookup failed: ${definitionsResponse.status}. Check Vercel logs.`)
  }
  const definition = (await definitionsResponse.json())[0]
  if (!definition) {
    console.error('Player type definition missing', { type_key: result.result_type_key })
    throw new Error(`Definition not found for animal type: ${result.result_type_key}`)
  }
  return { ...result, ...definition }
}

const money = (value) => {
  const n = Number(value)
  return Number.isFinite(n) ? `¥${Math.round(n).toLocaleString('ja-JP')}` : '—'
}

const number = (value, digits = 0) => {
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  return n.toLocaleString('ja-JP', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

const dateLabel = (value) => {
  if (!value) return ''
  const parts = String(value).slice(0, 10).split('-')
  if (parts.length !== 3) return String(value)
  return `${parts[0]}.${parts[1]}.${parts[2]}`
}

const ordinal = (rank) => {
  const n = Number(rank)
  if (!Number.isFinite(n)) return ''
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 13) return `${n}TH`
  const mod10 = n % 10
  if (mod10 === 1) return `${n}ST`
  if (mod10 === 2) return `${n}ND`
  if (mod10 === 3) return `${n}RD`
  return `${n}TH`
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

    if (type === 'player-type') {
      const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
      if (!serviceKey) return new Response('SUPABASE_SERVICE_ROLE_KEY is missing', { status: 500 })
      const result = await getPlayerTypeResult(supabaseUrl, serviceKey, id)
      if (!result) return new Response('Public diagnosis not found', { status: 404 })
      const allowedAnimals = new Set('badger bear bison bull cat chameleon crocodile deer dog dolphin eagle elephant fox giraffe gorilla hedgehog horse hyena leopard lion magpie monkey mountain_goat otter owl penguin rabbit raccoon rhino shark sloth snake squirrel tiger turtle wolf'.split(' '))
      const key = allowedAnimals.has(result.result_type_key) ? result.result_type_key : 'lion'
      const animalUrl = new URL(`/animals/${key}.png`, url.origin).toString()
      const element = { type: 'div', props: { style: { width: '100%', height: '100%', display: 'flex', flexDirection: 'row', alignItems: 'center', padding: '65px', background: '#080808', color: '#fff', fontFamily: 'sans-serif', border: '14px solid #b89b5b' }, children: [
        { type: 'div', props: { style: { display: 'flex', flexDirection: 'column', width: '57%', justifyContent: 'center' }, children: [
          { type: 'div', props: { style: { display: 'flex', fontSize: 26, color: '#d4b879', letterSpacing: '3px', fontWeight: 800 }, children: 'POKER ID  /  PLAYER TYPE' } },
          { type: 'div', props: { style: { display: 'flex', fontSize: 31, marginTop: '42px', color: '#d4b879' }, children: 'あなたのポーカータイプは…' } },
          { type: 'div', props: { style: { display: 'flex', fontSize: 62, fontWeight: 900, marginTop: '15px', lineHeight: 1.25 }, children: result.animal_name_ja } },
          { type: 'div', props: { style: { display: 'flex', fontSize: 26, marginTop: '25px', lineHeight: 1.4, color: '#e8dcc2' }, children: String(result.catchphrase || '').slice(0, 75) } },
          { type: 'div', props: { style: { display: 'flex', fontSize: 21, marginTop: '45px', color: '#bca675' }, children: '全50問・36種類  あなたも無料診断！' } },
        ] } },
        { type: 'img', props: { src: animalUrl, width: 430, height: 430, style: { objectFit: 'contain' } } },
      ] } }
      return new ImageResponse(element, { width: 1200, height: 630, headers: { 'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400' } })
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
    let metaLeft = ''
    let metaRight = ''
    let badge = ''
    let accent = '#ffffff'

    if (type === 'tournament') {
      eyebrow = 'TOURNAMENT RESULT'
      title = r.tournament_name || 'Tournament'

      if (!r.rank_unknown && r.rank) {
        const rank = Number(r.rank)
        main = ordinal(rank)

        if (rank === 1) {
          badge = 'WINNER'
          accent = '#f5c451'
        } else if (rank === 2) {
          badge = '2ND PLACE'
          accent = '#d4d4d8'
        } else if (rank === 3) {
          badge = '3RD PLACE'
          accent = '#c98b5b'
        } else if (r.is_itm) {
          badge = 'ITM'
          accent = '#62d98b'
        }
      } else if (r.is_itm) {
        main = 'ITM'
        badge = 'IN THE MONEY'
        accent = '#62d98b'
      } else {
        main = 'PLAYED'
        badge = 'TOURNAMENT'
      }

      if (r.entry_count) {
        sub = `${Number(r.entry_count).toLocaleString('ja-JP')} ENTRIES`
      }

      if (Number(r.prize_amount) > 0) {
        metaLeft = `PRIZE  ${money(r.prize_amount)}`
      } else if (r.venue) {
        metaLeft = r.venue
      }

      metaRight = dateLabel(r.played_at)
    }

    if (type === 'amusement') {
      eyebrow = 'AMUSEMENT RING RESULT'
      title = r.venue || 'Amusement Poker'

      const bigBlind = Number(r.big_blind)
      const startingStack = Number(r.starting_stack)
      const additionalStack = Number(r.additional_stack ?? 0)
      const endingStack = Number(r.ending_stack)

      const bb =
        Number.isFinite(bigBlind) &&
        bigBlind > 0 &&
        Number.isFinite(startingStack) &&
        Number.isFinite(additionalStack) &&
        Number.isFinite(endingStack)
          ? (endingStack - (startingStack + additionalStack)) / bigBlind
          : 0

      main = `${bb >= 0 ? '+' : ''}${number(bb, 1)} BB`

      const blindText =
        Number(r.small_blind) > 0 && Number(r.big_blind) > 0
          ? `${number(r.small_blind)}/${number(r.big_blind)}`
          : ''

      sub = [r.game_type || r.game || '', blindText].filter(Boolean).join('  ·  ')

      if (bb >= 100) {
        badge = 'BIG WIN'
        accent = '#62d98b'
      } else if (bb >= 0) {
        badge = 'WIN'
        accent = '#62d98b'
      } else if (bb <= -100) {
        badge = 'BIG LOSS'
        accent = '#ff6b6b'
      } else {
        badge = 'LOSS'
        accent = '#ff6b6b'
      }

      if (Number(r.play_minutes) > 0) {
        const minutes = Number(r.play_minutes)
        const hours = Math.floor(minutes / 60)
        const mins = minutes % 60
        metaLeft = `PLAY TIME  ${hours > 0 ? `${hours}h ` : ''}${mins > 0 ? `${mins}m` : ''}`.trim()
      }

      metaRight = dateLabel(r.played_at)
    }

    if (type === 'cash') {
      const isOnline = r.play_type === 'online'
      eyebrow = isOnline ? 'ONLINE CASH RESULT' : 'LIVE CASH RESULT'
      title = r.venue || r.site || (isOnline ? 'Online Cash Game' : 'Cash Game')

      const profitJpy = Number(r.profit_jpy ?? 0)
      const profitAmount = Number(r.profit_amount ?? 0)
      const bigBlind = Number(r.big_blind)

      const bb =
        Number.isFinite(profitAmount) &&
        Number.isFinite(bigBlind) &&
        bigBlind > 0
          ? profitAmount / bigBlind
          : null

      main = `${profitJpy >= 0 ? '+' : ''}${money(profitJpy)}`

      const blindText =
        Number(r.small_blind) > 0 && Number(r.big_blind) > 0
          ? `${number(r.small_blind)}/${number(r.big_blind)} ${r.currency || ''}`.trim()
          : ''

      sub = [r.game_type || r.game || '', blindText].filter(Boolean).join('  ·  ')

      if (profitJpy >= 0) {
        badge = 'WIN'
        accent = '#62d98b'
      } else {
        badge = 'LOSS'
        accent = '#ff6b6b'
      }

      if (bb !== null) {
        metaLeft = `${bb >= 0 ? '+' : ''}${number(bb, 1)} BB`
      } else if (r.currency && r.currency !== 'JPY') {
        metaLeft = `${profitAmount >= 0 ? '+' : ''}${number(profitAmount, 2)} ${r.currency}`
      }

      metaRight = dateLabel(r.played_at)
    }

    const element = {
      type: 'div',
      props: {
        style: {
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          background: '#050505',
          color: '#ffffff',
          fontFamily: 'sans-serif',
          position: 'relative',
          overflow: 'hidden',
        },
        children: [
          {
            type: 'div',
            props: {
              style: {
                position: 'absolute',
                width: '520px',
                height: '520px',
                borderRadius: '999px',
                right: '-170px',
                top: '-240px',
                background: accent,
                opacity: 0.08,
                display: 'flex',
              },
            },
          },
          {
            type: 'div',
            props: {
              style: {
                position: 'absolute',
                width: '2px',
                height: '420px',
                right: '138px',
                top: '62px',
                background: accent,
                opacity: 0.35,
                transform: 'rotate(28deg)',
                display: 'flex',
              },
            },
          },
          {
            type: 'div',
            props: {
              style: {
                height: '505px',
                padding: '54px 70px 34px 70px',
                display: 'flex',
                flexDirection: 'column',
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
                            alignItems: 'center',
                            gap: '14px',
                          },
                          children: [
                            {
                              type: 'div',
                              props: {
                                style: {
                                  width: '42px',
                                  height: '42px',
                                  borderRadius: '12px',
                                  background: '#ffffff',
                                  color: '#050505',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: 27,
                                  fontWeight: 900,
                                },
                                children: '♠',
                              },
                            },
                            {
                              type: 'div',
                              props: {
                                style: {
                                  display: 'flex',
                                  fontSize: 30,
                                  fontWeight: 900,
                                  letterSpacing: '-1px',
                                },
                                children: 'POKER ID',
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
                            fontSize: 16,
                            fontWeight: 700,
                            letterSpacing: '4px',
                            color: '#8d8d93',
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
                      marginTop: '52px',
                      display: 'flex',
                      flexDirection: 'column',
                    },
                    children: [
                      {
                        type: 'div',
                        props: {
                          style: {
                            display: 'flex',
                            alignSelf: 'flex-start',
                            border: `1px solid ${accent}`,
                            color: accent,
                            borderRadius: '999px',
                            padding: '8px 17px',
                            fontSize: 16,
                            fontWeight: 900,
                            letterSpacing: '2px',
                          },
                          children: badge,
                        },
                      },
                      {
                        type: 'div',
                        props: {
                          style: {
                            display: 'flex',
                            marginTop: '18px',
                            fontSize: 31,
                            fontWeight: 700,
                            color: '#d2d2d6',
                            maxWidth: '930px',
                            whiteSpace: 'nowrap',
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
                            marginTop: '8px',
                            gap: '24px',
                          },
                          children: [
                            {
                              type: 'div',
                              props: {
                                style: {
                                  display: 'flex',
                                  fontSize: main.length > 13 ? 82 : 104,
                                  fontWeight: 900,
                                  lineHeight: 1,
                                  letterSpacing: '-5px',
                                  color: '#ffffff',
                                },
                                children: main,
                              },
                            },
                            sub
                              ? {
                                  type: 'div',
                                  props: {
                                    style: {
                                      display: 'flex',
                                      fontSize: 23,
                                      fontWeight: 700,
                                      color: '#8d8d93',
                                    },
                                    children: sub,
                                  },
                                }
                              : null,
                          ],
                        },
                      },
                      {
                        type: 'div',
                        props: {
                          style: {
                            display: 'flex',
                            marginTop: '25px',
                            gap: '30px',
                            fontSize: 19,
                            fontWeight: 700,
                            color: '#a7a7ad',
                          },
                          children: [
                            metaLeft
                              ? {
                                  type: 'div',
                                  props: {
                                    style: { display: 'flex' },
                                    children: metaLeft,
                                  },
                                }
                              : null,
                            metaRight
                              ? {
                                  type: 'div',
                                  props: {
                                    style: { display: 'flex' },
                                    children: metaRight,
                                  },
                                }
                              : null,
                          ],
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
                height: '125px',
                borderTop: '1px solid #202024',
                padding: '23px 70px 0 70px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                color: '#66666d',
              },
              children: [
                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      fontSize: 15,
                      fontWeight: 700,
                      letterSpacing: '2px',
                    },
                    children: 'YOUR POKER HISTORY, IN ONE ID.',
                  },
                },
                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      fontSize: 15,
                      fontWeight: 700,
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
      error instanceof Error
        ? error.stack || error.message
        : String(error)

    return new Response(`OG ERROR\n\n${message}`, {
      status: 500,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    })
  }
}
