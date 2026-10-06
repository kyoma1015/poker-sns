import { useState } from 'react'

import { useNavigate } from 'react-router-dom'

import { supabase } from './supabase'

function PokerResultCreate() {

  const navigate = useNavigate()

  const getToday = () => {

    const now = new Date()

    const local = new Date(

      now.getTime() - now.getTimezoneOffset() * 60 * 1000

    )

    return local.toISOString().split('T')[0]

  }

  const [tournamentName, setTournamentName] = useState('')

  const [playedAt, setPlayedAt] = useState(getToday())

  const [venue, setVenue] = useState('')

  const [rank, setRank] = useState('')

  const [rankUnknown, setRankUnknown] = useState(false)

  const [entryCount, setEntryCount] = useState('')

  const [isItm, setIsItm] = useState(false)

  const [entryFee, setEntryFee] = useState('')

  const [bullets, setBullets] = useState('1')

  const [totalEntryFee, setTotalEntryFee] = useState('')

  const [totalFeeEdited, setTotalFeeEdited] = useState(false)

  const [prizeAmount, setPrizeAmount] = useState('0')

  const [entryTiming, setEntryTiming] = useState<

    'early' | 'middle' | 'late'

  >('early')

  const [showDetails, setShowDetails] = useState(false)

  const [entryBb, setEntryBb] = useState('')

  const [gameType, setGameType] = useState('')

  const [prizeDescription, setPrizeDescription] = useState('')

  const [memo, setMemo] = useState('')

  const [isPublic, setIsPublic] = useState(false)

  const [isFeatured, setIsFeatured] = useState(false)

  const [shareToTimeline, setShareToTimeline] = useState(false)

  const [timelineComment, setTimelineComment] = useState('')

  const [message, setMessage] = useState('')

  const [isSaving, setIsSaving] = useState(false)

  const [savedSuccessfully, setSavedSuccessfully] = useState(false)

  const [savedResultId, setSavedResultId] = useState('')

  const calculatedTotalFee = () => {

    const fee = Number(entryFee)

    const bulletCount = Number(bullets)

    if (

      entryFee === '' ||

      bullets === '' ||

      !Number.isFinite(fee) ||

      !Number.isFinite(bulletCount)

    ) {

      return ''

    }

    return String(fee * bulletCount)

  }

  const displayedTotalFee = totalFeeEdited

    ? totalEntryFee

    : calculatedTotalFee()

  const formatYen = (value: string) => {

    if (value === '') return '—'

    const number = Number(value)

    if (!Number.isFinite(number)) return '—'

    return `${number.toLocaleString('ja-JP')}円`

  }

  const handleEntryFeeChange = (value: string) => {

    setEntryFee(value)

    if (!totalFeeEdited) {

      setTotalEntryFee('')

    }

  }

  const handleBulletsChange = (value: string) => {

    setBullets(value)

    if (!totalFeeEdited) {

      setTotalEntryFee('')

    }

  }

  const handlePublicChange = (value: boolean) => {

    setIsPublic(value)

    if (!value) {

      setIsFeatured(false)

    }

  }

  const handleSave = async () => {

    setMessage('')

    const trimmedTournamentName = tournamentName.trim()

    if (!trimmedTournamentName) {

      setMessage('トーナメント名を入力してください。')

      return

    }

    if (!playedAt) {

      setMessage('開催日を入力してください。')

      return

    }

    if (!rankUnknown && rank === '') {

      setMessage(

        '順位を入力するか「順位不明」を選択してください。'

      )

      return

    }

    const rankNumber =

      rankUnknown || rank === '' ? null : Number(rank)

    const entryCountNumber =

      entryCount === '' ? null : Number(entryCount)

    const entryFeeNumber =

      entryFee === '' ? null : Number(entryFee)

    const bulletsNumber = Number(bullets)

    const finalTotalEntryFee =

      displayedTotalFee === ''

        ? null

        : Number(displayedTotalFee)

    const prizeAmountNumber =

      prizeAmount === '' ? 0 : Number(prizeAmount)

    const entryBbNumber =

      entryBb === '' ? null : Number(entryBb)

    if (

      rankNumber !== null &&

      (!Number.isInteger(rankNumber) || rankNumber < 1)

    ) {

      setMessage('順位は1以上の整数で入力してください。')

      return

    }

    if (

      entryCountNumber !== null &&

      (!Number.isInteger(entryCountNumber) ||

        entryCountNumber < 1)

    ) {

      setMessage(

        '参加人数は1以上の整数で入力してください。'

      )

      return

    }

    if (

      rankNumber !== null &&

      entryCountNumber !== null &&

      rankNumber > entryCountNumber

    ) {

      setMessage('順位が参加人数を超えています。')

      return

    }

    if (

      entryFeeNumber !== null &&

      (!Number.isFinite(entryFeeNumber) ||

        entryFeeNumber < 0)

    ) {

      setMessage('参加費は0円以上で入力してください。')

      return

    }

    if (

      !Number.isInteger(bulletsNumber) ||

      bulletsNumber < 1

    ) {

      setMessage(

        '使用エントリー数は1以上の整数で入力してください。'

      )

      return

    }

    if (

      finalTotalEntryFee !== null &&

      (!Number.isFinite(finalTotalEntryFee) ||

        finalTotalEntryFee < 0)

    ) {

      setMessage(

        '総参加費は0円以上で入力してください。'

      )

      return

    }

    if (

      !Number.isFinite(prizeAmountNumber) ||

      prizeAmountNumber < 0

    ) {

      setMessage(

        '獲得額（相当額）は0円以上で入力してください。'

      )

      return

    }

    if (

      entryBbNumber !== null &&

      (!Number.isFinite(entryBbNumber) ||

        entryBbNumber <= 0)

    ) {

      setMessage('参加時BBは0より大きい数値で入力してください。')

      return

    }

    setIsSaving(true)

    setMessage('保存中...')

    const {

      data: { user },

    } = await supabase.auth.getUser()

    if (!user) {

      setIsSaving(false)

      navigate('/login')

      return

    }

    const { data: savedResult, error } = await supabase

      .from('poker_results')

      .insert({

        user_id: user.id,

        tournament_name: trimmedTournamentName,

        played_at: playedAt,

        venue: venue.trim() || null,

        rank: rankNumber,

        rank_unknown: rankUnknown,

        entry_count: entryCountNumber,

        is_itm: isItm,

        entry_fee: entryFeeNumber,

        bullets: bulletsNumber,

        total_entry_fee: finalTotalEntryFee,

        prize_amount: prizeAmountNumber,

        entry_timing: entryTiming,

        entry_bb: entryBbNumber,

        game_type: gameType || null,

        prize_description:

          prizeDescription.trim() || null,

        memo: memo.trim() || null,

        is_public: isPublic,

        is_featured: isPublic ? isFeatured : false,

      })

      .select('id')

      .single()

    if (error) {

      console.error(error)

      setMessage(`保存に失敗しました：${error.message}`)

      setIsSaving(false)

      return

    }

    if (shareToTimeline) {

      const { error: postError } = await supabase.from('posts').insert({

        user_id: user.id,

        content: timelineComment.trim(),

        post_type: 'result',

        result_type: 'tournament',

        result_id: savedResult.id,

      })

      if (postError) {

        console.error(postError)

        setMessage(`記録は保存されましたが、タイムライン投稿に失敗しました：${postError.message}`)

        setIsSaving(false)

        return

      }

    }

    setIsSaving(false)

    setMessage('')

    setSavedResultId(savedResult.id)

    setSavedSuccessfully(true)

  }



  const handleShareToX = () => {
  if (!savedResultId) return

  const rankNumber = rankUnknown || rank === '' ? null : Number(rank)
  const entryNumber = entryCount === '' ? null : Number(entryCount)
  const prizeNumber = prizeAmount === '' ? 0 : Number(prizeAmount)
  const eventName = tournamentName.trim()
  const venueName = venue.trim()

  let headline = venueName
    ? `♠️ ${venueName}で「${eventName}」に出場！`
    : `♠️ 「${eventName}」に出場！`

  if (rankNumber === 1) {
    headline = venueName
      ? `🏆 ${venueName}の「${eventName}」で優勝しました！`
      : `🏆 「${eventName}」で優勝しました！`
  }

  let resultLine = '結果：順位不明'
  if (rankNumber !== null && entryNumber !== null) {
    resultLine = `結果：${entryNumber}人中 ${rankNumber}位${isItm ? ' / ITM 🎉' : ''}`
  } else if (rankNumber !== null) {
    resultLine = `結果：${rankNumber}位${isItm ? ' / ITM 🎉' : ''}`
  } else if (entryNumber !== null) {
    resultLine = `結果：順位不明 / ${entryNumber}人${isItm ? ' / ITM 🎉' : ''}`
  } else if (isItm) {
    resultLine = '結果：ITM 🎉'
  }

  const resultLines = [headline, resultLine]
  if (Number.isFinite(prizeNumber) && prizeNumber > 0) {
    resultLines.push(`獲得賞金 ¥${prizeNumber.toLocaleString('ja-JP')}`)
  }

  const text = [
    ...resultLines,
    '',
    'Poker IDであなたのポーカー戦績を記録しよう。',
    '#PokerID #ポーカー',
  ].join('\n')

  const shareUrl = `${window.location.origin}/share/tournament/${savedResultId}`
  const intentUrl =
    `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}` +
    `&url=${encodeURIComponent(shareUrl)}`

  window.open(intentUrl, '_blank', 'noopener,noreferrer')
}



  const labelStyle = {

    marginBottom: '8px',

    fontSize: '13px',

    fontWeight: 700,

  } as const

  const optionalStyle = {

    marginLeft: '5px',

    color: '#777',

    fontWeight: 400,

  } as const

  const choiceButton = (

    selected: boolean

  ): React.CSSProperties => ({

    flex: 1,

    minHeight: '44px',

    padding: '10px 12px',

    background: selected ? '#f5f5f5' : '#111',

    color: selected ? '#000' : '#aaa',

    border: selected

      ? '1px solid #f5f5f5'

      : '1px solid #2d2d2d',

    borderRadius: '12px',

    fontSize: '13px',

    fontWeight: 700,

  })

  if (savedSuccessfully) {

    return (

      <main className="app">

        <div className="card" style={{ paddingTop: 0 }}>

          <header

            style={{

              position: 'sticky',

              top: 0,

              zIndex: 20,

              margin: '0 -20px',

              padding: '15px 20px',

              background: 'rgba(0, 0, 0, 0.95)',

              borderBottom: '1px solid #242424',

              backdropFilter: 'blur(14px)',

              WebkitBackdropFilter: 'blur(14px)',

            }}

          >

            <div style={{ fontSize: '18px', fontWeight: 800 }}>保存完了</div>

          </header>



          <div style={{ padding: '52px 0 28px', textAlign: 'center' }}>

            <div

              style={{

                width: '58px',

                height: '58px',

                margin: '0 auto',

                display: 'flex',

                alignItems: 'center',

                justifyContent: 'center',

                borderRadius: '50%',

                background: '#fff',

                color: '#000',

                fontSize: '28px',

                fontWeight: 900,

              }}

            >

              ✓

            </div>



            <div style={{ marginTop: '20px', fontSize: '22px', fontWeight: 900 }}>

              トーナメント記録を保存しました

            </div>



            <div

              style={{

                marginTop: '9px',

                color: '#777',

                fontSize: '13px',

                lineHeight: 1.6,

              }}

            >

              この結果をXにもシェアできます

            </div>

          </div>



          <button

            type="button"

            onClick={handleShareToX}

            style={{

              width: '100%',

              padding: '14px 18px',

              background: '#fff',

              color: '#000',

              borderRadius: '999px',

              fontSize: '15px',

              fontWeight: 900,

            }}

          >

            Xでシェア

          </button>



          <button

            type="button"

            onClick={() => navigate('/profile')}

            style={{

              width: '100%',

              marginTop: '12px',

              padding: '14px 18px',

              background: '#111',

              color: '#fff',

              border: '1px solid #333',

              borderRadius: '999px',

              fontSize: '15px',

              fontWeight: 800,

            }}

          >

            プロフィールに戻る

          </button>

        </div>

      </main>

    )

  }



  return (

    <main className="app">

      <div

        className="card"

        style={{

          paddingTop: 0,

        }}

      >

        <header

          style={{

            position: 'sticky',

            top: 0,

            zIndex: 20,

            margin: '0 -20px',

            padding: '15px 20px',

            display: 'flex',

            alignItems: 'center',

            gap: '12px',

            background: 'rgba(0, 0, 0, 0.95)',

            borderBottom: '1px solid #242424',

            backdropFilter: 'blur(14px)',

            WebkitBackdropFilter: 'blur(14px)',

          }}

        >

          <button

            type="button"

            onClick={() => navigate('/profile')}

            aria-label="戻る"

            style={{

              width: '34px',

              height: '34px',

              padding: 0,

              display: 'flex',

              alignItems: 'center',

              justifyContent: 'center',

              flexShrink: 0,

              background: 'transparent',

              color: '#fff',

              borderRadius: '50%',

              fontSize: '27px',

              fontWeight: 300,

            }}

          >

            ‹

          </button>

          <div

            style={{

              fontSize: '18px',

              fontWeight: 800,

            }}

          >

            トーナメントを記録

          </div>

        </header>

        <div

          style={{

            padding: '24px 0 8px',

          }}

        >

          <div

            style={{

              fontSize: '22px',

              fontWeight: 800,

              letterSpacing: '-0.5px',

            }}

          >

            トーナメント記録

          </div>

          <p

            style={{

              margin: '8px 0 0',

              color: '#777',

              fontSize: '13px',

              lineHeight: 1.6,

            }}

          >

            結果に関係なく記録を続けることで、

            あなたのポーカー傾向を分析できます。

          </p>

        </div>

        <div

          style={{

            marginTop: '14px',

            padding: '14px 15px',

            background: '#0d0d0d',

            border: '1px solid #242424',

            borderRadius: '14px',

          }}

        >

          <div

            style={{

              fontSize: '13px',

              fontWeight: 800,

            }}

          >

            圏外のトーナメントも記録がおすすめです

          </div>

          <div

            style={{

              marginTop: '5px',

              color: '#777',

              fontSize: '12px',

              lineHeight: 1.6,

            }}

          >

            インマネできなかったトーナメントも記録すると、

            ITM率・回収率・ROI・参加タイミング別の成績などを

            より正確に分析できます。

          </div>

        </div>

        <div

          style={{

            display: 'flex',

            flexDirection: 'column',

            gap: '22px',

            marginTop: '24px',

          }}

        >

          <label>

            <div style={labelStyle}>

              トーナメント名

              <span style={optionalStyle}>必須</span>

            </div>

            <input

              type="text"

              placeholder="例：JOPT Tokyo Main Event"

              value={tournamentName}

              onChange={(e) =>

                setTournamentName(e.target.value)

              }

              maxLength={100}

            />

          </label>

          <label>

            <div style={labelStyle}>

              開催日

              <span style={optionalStyle}>必須</span>

            </div>

            <input

              type="date"

              value={playedAt}

              onChange={(e) =>

                setPlayedAt(e.target.value)

              }

            />

          </label>

          <label>

            <div style={labelStyle}>

              店舗・シリーズ

              <span style={optionalStyle}>任意</span>

            </div>

            <input

              type="text"

              placeholder="例：JOPT / Poker Room ○○"

              value={venue}

              onChange={(e) =>

                setVenue(e.target.value)

              }

              maxLength={100}

            />

          </label>

          <div>

            <div style={labelStyle}>

              順位

              <span style={optionalStyle}>必須</span>

            </div>

            <div

              style={{

                display: 'grid',

                gridTemplateColumns: '1fr auto',

                gap: '10px',

              }}

            >

              <div

                style={{

                  position: 'relative',

                }}

              >

                <input

                  type="number"

                  inputMode="numeric"

                  min="1"

                  placeholder="例：3"

                  value={rank}

                  disabled={rankUnknown}

                  onChange={(e) =>

                    setRank(e.target.value)

                  }

                  style={{

                    paddingRight: '42px',

                    opacity: rankUnknown ? 0.45 : 1,

                  }}

                />

                <span

                  style={{

                    position: 'absolute',

                    right: '14px',

                    top: '50%',

                    transform: 'translateY(-50%)',

                    color: '#777',

                    fontSize: '13px',

                    pointerEvents: 'none',

                  }}

                >

                  位

                </span>

              </div>

              <button

                type="button"

                onClick={() => {

                  const next = !rankUnknown

                  setRankUnknown(next)

                  if (next) {

                    setRank('')

                  }

                }}

                style={{

                  padding: '0 15px',

                  background: rankUnknown

                    ? '#f5f5f5'

                    : '#111',

                  color: rankUnknown

                    ? '#000'

                    : '#aaa',

                  border: rankUnknown

                    ? '1px solid #f5f5f5'

                    : '1px solid #2d2d2d',

                  borderRadius: '12px',

                  fontSize: '13px',

                  fontWeight: 700,

                  whiteSpace: 'nowrap',

                }}

              >

                順位不明

              </button>

            </div>

          </div>

          <label>

            <div style={labelStyle}>

              参加人数

              <span style={optionalStyle}>任意</span>

            </div>

            <div

              style={{

                position: 'relative',

              }}

            >

              <input

                type="number"

                inputMode="numeric"

                min="1"

                placeholder="例：250"

                value={entryCount}

                onChange={(e) =>

                  setEntryCount(e.target.value)

                }

                style={{

                  paddingRight: '42px',

                }}

              />

              <span

                style={{

                  position: 'absolute',

                  right: '14px',

                  top: '50%',

                  transform: 'translateY(-50%)',

                  color: '#777',

                  fontSize: '13px',

                  pointerEvents: 'none',

                }}

              >

                人

              </span>

            </div>

          </label>

          <div>

            <div style={labelStyle}>結果</div>

            <button

              type="button"

              onClick={() => setIsItm(!isItm)}

              style={{

                width: '100%',

                padding: '14px 15px',

                display: 'flex',

                alignItems: 'center',

                gap: '12px',

                textAlign: 'left',

                background: isItm

                  ? '#171717'

                  : '#0d0d0d',

                color: '#fff',

                border: isItm

                  ? '1px solid #666'

                  : '1px solid #2d2d2d',

                borderRadius: '14px',

              }}

            >

              <div

                style={{

                  width: '21px',

                  height: '21px',

                  flexShrink: 0,

                  display: 'flex',

                  alignItems: 'center',

                  justifyContent: 'center',

                  borderRadius: '6px',

                  background: isItm

                    ? '#fff'

                    : 'transparent',

                  color: '#000',

                  border: isItm

                    ? '1px solid #fff'

                    : '1px solid #555',

                  fontSize: '14px',

                  fontWeight: 900,

                }}

              >

                {isItm ? '✓' : ''}

              </div>

              <div>

                <div

                  style={{

                    fontSize: '14px',

                    fontWeight: 700,

                  }}

                >

                  インマネした

                </div>

                <div

                  style={{

                    marginTop: '3px',

                    color: '#777',

                    fontSize: '12px',

                  }}

                >

                  ITM率の分析に使用します

                </div>

              </div>

            </button>

          </div>

          <div

            style={{

              height: '1px',

              background: '#242424',

            }}

          />

          <div>

            <div

              style={{

                marginBottom: '14px',

                fontSize: '16px',

                fontWeight: 800,

              }}

            >

              参加費・獲得額

            </div>

            <div

              style={{

                display: 'flex',

                flexDirection: 'column',

                gap: '18px',

              }}

            >

              <label>

                <div style={labelStyle}>

                  参加費

                  <span style={optionalStyle}>

                    1エントリーあたり

                  </span>

                </div>

                <div

                  style={{

                    position: 'relative',

                  }}

                >

                  <input

                    type="number"

                    inputMode="numeric"

                    min="0"

                    placeholder="例：5000"

                    value={entryFee}

                    onChange={(e) =>

                      handleEntryFeeChange(

                        e.target.value

                      )

                    }

                    style={{

                      paddingRight: '42px',

                    }}

                  />

                  <span

                    style={{

                      position: 'absolute',

                      right: '14px',

                      top: '50%',

                      transform:

                        'translateY(-50%)',

                      color: '#777',

                      fontSize: '13px',

                      pointerEvents: 'none',

                    }}

                  >

                    円

                  </span>

                </div>

              </label>

              <label>

                <div style={labelStyle}>

                  使用エントリー数

                  <span style={optionalStyle}>

                    何機

                  </span>

                </div>

                <div

                  style={{

                    position: 'relative',

                  }}

                >

                  <input

                    type="number"

                    inputMode="numeric"

                    min="1"

                    step="1"

                    value={bullets}

                    onChange={(e) =>

                      handleBulletsChange(

                        e.target.value

                      )

                    }

                    style={{

                      paddingRight: '42px',

                    }}

                  />

                  <span

                    style={{

                      position: 'absolute',

                      right: '14px',

                      top: '50%',

                      transform:

                        'translateY(-50%)',

                      color: '#777',

                      fontSize: '13px',

                      pointerEvents: 'none',

                    }}

                  >

                    機

                  </span>

                </div>

              </label>

              <div>

                <div style={labelStyle}>

                  総参加費

                </div>

                {!totalFeeEdited ? (

                  <div

                    style={{

                      padding: '13px 14px',

                      display: 'flex',

                      alignItems: 'center',

                      justifyContent:

                        'space-between',

                      gap: '12px',

                      background: '#0d0d0d',

                      border:

                        '1px solid #242424',

                      borderRadius: '12px',

                    }}

                  >

                    <div>

                      <div

                        style={{

                          fontSize: '16px',

                          fontWeight: 800,

                        }}

                      >

                        {formatYen(

                          calculatedTotalFee()

                        )}

                      </div>

                      <div

                        style={{

                          marginTop: '3px',

                          color: '#666',

                          fontSize: '11px',

                        }}

                      >

                        参加費 × 使用エントリー数

                      </div>

                    </div>

                    <button

                      type="button"

                      onClick={() => {

                        setTotalEntryFee(

                          calculatedTotalFee()

                        )

                        setTotalFeeEdited(true)

                      }}

                      style={{

                        padding: '8px 11px',

                        background: '#181818',

                        color: '#ddd',

                        border:

                          '1px solid #333',

                        borderRadius: '999px',

                        fontSize: '12px',

                        fontWeight: 700,

                        whiteSpace: 'nowrap',

                      }}

                    >

                      修正する

                    </button>

                  </div>

                ) : (

                  <>

                    <div

                      style={{

                        position: 'relative',

                      }}

                    >

                      <input

                        type="number"

                        inputMode="numeric"

                        min="0"

                        value={totalEntryFee}

                        onChange={(e) =>

                          setTotalEntryFee(

                            e.target.value

                          )

                        }

                        style={{

                          paddingRight: '42px',

                        }}

                      />

                      <span

                        style={{

                          position: 'absolute',

                          right: '14px',

                          top: '50%',

                          transform:

                            'translateY(-50%)',

                          color: '#777',

                          fontSize: '13px',

                          pointerEvents: 'none',

                        }}

                      >

                        円

                      </span>

                    </div>

                    <button

                      type="button"

                      onClick={() => {

                        setTotalFeeEdited(false)

                        setTotalEntryFee('')

                      }}

                      style={{

                        marginTop: '8px',

                        padding: 0,

                        background: 'transparent',

                        color: '#888',

                        fontSize: '12px',

                        fontWeight: 600,

                      }}

                    >

                      自動計算に戻す

                    </button>

                  </>

                )}

              </div>

              <label>

                <div style={labelStyle}>

                  獲得額（相当額）

                </div>

                <div

                  style={{

                    position: 'relative',

                  }}

                >

                  <input

                    type="number"

                    inputMode="numeric"

                    min="0"

                    placeholder="0"

                    value={prizeAmount}

                    onChange={(e) =>

                      setPrizeAmount(

                        e.target.value

                      )

                    }

                    style={{

                      paddingRight: '42px',

                    }}

                  />

                  <span

                    style={{

                      position: 'absolute',

                      right: '14px',

                      top: '50%',

                      transform:

                        'translateY(-50%)',

                      color: '#777',

                      fontSize: '13px',

                      pointerEvents: 'none',

                    }}

                  >

                    円

                  </span>

                </div>

                <div

                  style={{

                    marginTop: '7px',

                    color: '#666',

                    fontSize: '11px',

                    lineHeight: 1.5,

                  }}

                >

                  チケット・商品などを獲得した場合は、

                  その相当額を入力してください。

                </div>

              </label>

            </div>

          </div>

          <div

            style={{

              height: '1px',

              background: '#242424',

            }}

          />

          <div>

            <div style={labelStyle}>

              参加タイミング

            </div>

            <div

              style={{

                display: 'flex',

                gap: '8px',

              }}

            >

              <button

                type="button"

                onClick={() =>

                  setEntryTiming('early')

                }

                style={choiceButton(

                  entryTiming === 'early'

                )}

              >

                開始付近

              </button>

              <button

                type="button"

                onClick={() =>

                  setEntryTiming('middle')

                }

                style={choiceButton(

                  entryTiming === 'middle'

                )}

              >

                中盤

              </button>

              <button

                type="button"

                onClick={() =>

                  setEntryTiming('late')

                }

                style={choiceButton(

                  entryTiming === 'late'

                )}

              >

                レイト付近

              </button>

            </div>

          </div>

          <div

            style={{

              height: '1px',

              background: '#242424',

            }}

          />

          <div>

            <button

              type="button"

              onClick={() =>

                setShowDetails(!showDetails)

              }

              style={{

                width: '100%',

                padding: '13px 0',

                display: 'flex',

                alignItems: 'center',

                justifyContent: 'space-between',

                background: 'transparent',

                color: '#fff',

                fontSize: '14px',

                fontWeight: 800,

                textAlign: 'left',

              }}

            >

              <span>詳細を追加</span>

              <span

                style={{

                  color: '#777',

                  fontSize: '18px',

                  transform: showDetails

                    ? 'rotate(180deg)'

                    : 'rotate(0deg)',

                  transition:

                    'transform 0.15s ease',

                }}

              >

                ⌄

              </span>

            </button>

            {showDetails && (

              <div

                style={{

                  display: 'flex',

                  flexDirection: 'column',

                  gap: '18px',

                  paddingTop: '10px',

                }}

              >

                <label>

                  <div style={labelStyle}>

                    参加時BB

                    <span style={optionalStyle}>

                      任意

                    </span>

                  </div>

                  <div

                    style={{

                      position: 'relative',

                    }}

                  >

                    <input

                      type="number"

                      inputMode="decimal"

                      min="0.1"

                      step="0.1"

                      placeholder="例：25"

                      value={entryBb}

                      onChange={(e) =>

                        setEntryBb(

                          e.target.value

                        )

                      }

                      style={{

                        paddingRight: '42px',

                      }}

                    />

                    <span

                      style={{

                        position: 'absolute',

                        right: '14px',

                        top: '50%',

                        transform:

                          'translateY(-50%)',

                        color: '#777',

                        fontSize: '13px',

                        pointerEvents: 'none',

                      }}

                    >

                      BB

                    </span>

                  </div>

                </label>

                <label>

                  <div style={labelStyle}>

                    ゲーム種別

                    <span style={optionalStyle}>

                      任意

                    </span>

                  </div>

                  <select

                    value={gameType}

                    onChange={(e) =>

                      setGameType(

                        e.target.value

                      )

                    }

                  >

                    <option value="">

                      選択しない

                    </option>

                    <option value="NLH">

                      NLH

                    </option>

                    <option value="PLO">

                      PLO

                    </option>

                    <option value="MIX">

                      MIX

                    </option>

                    <option value="OTHER">

                      その他

                    </option>

                  </select>

                </label>

                <label>

                  <div style={labelStyle}>

                    獲得内容

                    <span style={optionalStyle}>

                      任意

                    </span>

                  </div>

                  <input

                    type="text"

                    placeholder="例：JOPT Main Event Ticket"

                    value={prizeDescription}

                    onChange={(e) =>

                      setPrizeDescription(

                        e.target.value

                      )

                    }

                    maxLength={150}

                  />

                  <div

                    style={{

                      marginTop: '7px',

                      color: '#666',

                      fontSize: '11px',

                      lineHeight: 1.5,

                    }}

                  >

                    チケット・商品などを獲得した場合に

                    内容を残せます。

                  </div>

                </label>

              </div>

            )}

          </div>

          <label>

            <div style={labelStyle}>

              メモ

              <span style={optionalStyle}>任意</span>

            </div>

            <textarea

              placeholder="トーナメントについてのメモ..."

              value={memo}

              onChange={(e) =>

                setMemo(e.target.value)

              }

              maxLength={500}

              rows={4}

            />

          </label>

          <div

            style={{

              height: '1px',

              background: '#242424',

            }}

          />

          <div>

            <div style={labelStyle}>公開設定</div>

            <div

              style={{

                display: 'flex',

                flexDirection: 'column',

                gap: '10px',

              }}

            >

              <button

                type="button"

                onClick={() =>

                  handlePublicChange(false)

                }

                style={{

                  width: '100%',

                  padding: '14px',

                  display: 'flex',

                  alignItems: 'center',

                  gap: '12px',

                  textAlign: 'left',

                  background: !isPublic

                    ? '#1b1b1b'

                    : '#0d0d0d',

                  color: '#fff',

                  border: !isPublic

                    ? '1px solid #666'

                    : '1px solid #2d2d2d',

                  borderRadius: '14px',

                }}

              >

                <span

                  style={{

                    fontSize: '20px',

                  }}

                >

                  🔒

                </span>

                <div>

                  <div

                    style={{

                      fontSize: '14px',

                      fontWeight: 700,

                    }}

                  >

                    非公開

                  </div>

                  <div

                    style={{

                      marginTop: '3px',

                      color: '#777',

                      fontSize: '12px',

                    }}

                  >

                    自分だけがこの記録を確認できます

                  </div>

                </div>

                <div

                  style={{

                    marginLeft: 'auto',

                    width: '18px',

                    height: '18px',

                    borderRadius: '50%',

                    border: !isPublic

                      ? '5px solid #fff'

                      : '1px solid #555',

                  }}

                />

              </button>

              <button

                type="button"

                onClick={() =>

                  handlePublicChange(true)

                }

                style={{

                  width: '100%',

                  padding: '14px',

                  display: 'flex',

                  alignItems: 'center',

                  gap: '12px',

                  textAlign: 'left',

                  background: isPublic

                    ? '#1b1b1b'

                    : '#0d0d0d',

                  color: '#fff',

                  border: isPublic

                    ? '1px solid #666'

                    : '1px solid #2d2d2d',

                  borderRadius: '14px',

                }}

              >

                <span

                  style={{

                    fontSize: '20px',

                  }}

                >

                  🌐

                </span>

                <div>

                  <div

                    style={{

                      fontSize: '14px',

                      fontWeight: 700,

                    }}

                  >

                    公開

                  </div>

                  <div

                    style={{

                      marginTop: '3px',

                      color: '#777',

                      fontSize: '12px',

                    }}

                  >

                    他のプレイヤーもこの記録を確認できます

                  </div>

                </div>

                <div

                  style={{

                    marginLeft: 'auto',

                    width: '18px',

                    height: '18px',

                    borderRadius: '50%',

                    border: isPublic

                      ? '5px solid #fff'

                      : '1px solid #555',

                  }}

                />

              </button>

            </div>

            <div

              style={{

                marginTop: '9px',

                color: '#666',

                fontSize: '12px',

                lineHeight: 1.5,

              }}

            >

              公開設定はあとから変更できます。

            </div>

          </div>

          {isPublic && (

            <div>

              <button

                type="button"

                onClick={() =>

                  setIsFeatured(!isFeatured)

                }

                style={{

                  width: '100%',

                  padding: '14px 15px',

                  display: 'flex',

                  alignItems: 'center',

                  gap: '12px',

                  textAlign: 'left',

                  background: isFeatured

                    ? '#171717'

                    : '#0d0d0d',

                  color: '#fff',

                  border: isFeatured

                    ? '1px solid #666'

                    : '1px solid #2d2d2d',

                  borderRadius: '14px',

                }}

              >

                <div

                  style={{

                    width: '21px',

                    height: '21px',

                    flexShrink: 0,

                    display: 'flex',

                    alignItems: 'center',

                    justifyContent: 'center',

                    borderRadius: '6px',

                    background: isFeatured

                      ? '#fff'

                      : 'transparent',

                    color: '#000',

                    border: isFeatured

                      ? '1px solid #fff'

                      : '1px solid #555',

                    fontSize: '14px',

                    fontWeight: 900,

                  }}

                >

                  {isFeatured ? '✓' : ''}

                </div>

                <div>

                  <div

                    style={{

                      fontSize: '14px',

                      fontWeight: 700,

                    }}

                  >

                    主なトーナメント実績に表示

                  </div>

                  <div

                    style={{

                      marginTop: '3px',

                      color: '#777',

                      fontSize: '12px',

                      lineHeight: 1.5,

                    }}

                  >

                    プロフィール上部に表示する代表的な実績として設定します

                  </div>

                </div>

              </button>

            </div>

          )}

        </div>

        <div

        style={{

          marginTop: '22px',

          padding: '16px',

          background: '#0d0d0d',

          border: '1px solid #242424',

          borderRadius: '14px',

        }}

      >

        <button

          type="button"

          onClick={() => setShareToTimeline(!shareToTimeline)}

          style={{

            width: '100%',

            padding: 0,

            display: 'flex',

            alignItems: 'center',

            gap: '12px',

            textAlign: 'left',

            background: 'transparent',

            color: '#fff',

          }}

        >

          <div

            style={{

              width: '21px',

              height: '21px',

              flexShrink: 0,

              display: 'flex',

              alignItems: 'center',

              justifyContent: 'center',

              borderRadius: '6px',

              background: shareToTimeline ? '#fff' : 'transparent',

              color: '#000',

              border: shareToTimeline ? '1px solid #fff' : '1px solid #555',

              fontSize: '14px',

              fontWeight: 900,

            }}

          >

            {shareToTimeline ? '✓' : ''}

          </div>

          <div>

            <div style={{ fontSize: '14px', fontWeight: 800 }}>

              タイムラインにも投稿する

            </div>

            <div style={{ marginTop: '3px', color: '#777', fontSize: '12px', lineHeight: 1.5 }}>

              トーナメント結果を結果カード付きでシェアします

            </div>

          </div>

        </button>

        {shareToTimeline && (

          <div style={{ marginTop: '14px' }}>

            <textarea

              placeholder="例：今日めっちゃ勝った🔥"

              value={timelineComment}

              onChange={(e) => setTimelineComment(e.target.value)}

              maxLength={500}

              rows={3}

            />

            <div style={{ marginTop: '7px', color: '#666', fontSize: '11px', lineHeight: 1.5 }}>

              コメントは空欄でも投稿できます。

            </div>

          </div>

        )}

      </div>

      {message && (

          <div

            style={{

              marginTop: '18px',

              color:

                message === '保存中...'

                  ? '#777'

                  : '#ff7777',

              fontSize: '12px',

              textAlign: 'center',

            }}

          >

            {message}

          </div>

        )}

        <button

          type="button"

          onClick={handleSave}

          disabled={isSaving}

          style={{

            width: '100%',

            marginTop: '26px',

            padding: '14px 18px',

            background: '#fff',

            color: '#000',

            borderRadius: '999px',

            fontSize: '15px',

            fontWeight: 800,

          }}

        >

          {isSaving

            ? '保存中...'

            : 'トーナメント記録を保存'}

        </button>

      </div>

    </main>

  )

}

export default PokerResultCreate
