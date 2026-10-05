import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'
type PastRingResult = {
  venue: string
  game_type: string
  small_blind: number
  big_blind: number
  played_at: string
  created_at: string
}
function getToday() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
function AmusementRingCreate() {
  const navigate = useNavigate()
  const [playedAt, setPlayedAt] = useState(getToday())
  const [venue, setVenue] = useState('')
  const [gameType, setGameType] = useState('NLH')
  const [smallBlind, setSmallBlind] = useState('')
  const [bigBlind, setBigBlind] = useState('')
  const [startingStack, setStartingStack] = useState('')
  const [additionalStack, setAdditionalStack] = useState('0')
  const [endingStack, setEndingStack] = useState('')
  const [playHours, setPlayHours] = useState('')
  const [playMinutes, setPlayMinutes] = useState('')
  const [memo, setMemo] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [postToTimeline, setPostToTimeline] = useState(false)
  const [timelineComment, setTimelineComment] = useState('')
  const [pastResults, setPastResults] = useState<PastRingResult[]>([])
  const [message, setMessage] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  useEffect(() => {
    const loadPastResults = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser()
      if (!user) {
        navigate('/login')
        return
      }
      const { data, error } = await supabase
        .from('amusement_ring_results')
        .select(
          'venue, game_type, small_blind, big_blind, played_at, created_at'
        )
        .eq('user_id', user.id)
        .order('played_at', { ascending: false })
        .order('created_at', { ascending: false })
      if (error) {
        console.error(error)
        return
      }
      setPastResults(data || [])
    }
    loadPastResults()
  }, [navigate])
  const venueSuggestions = useMemo(() => {
    const uniqueVenues: string[] = []
    for (const result of pastResults) {
      const trimmedVenue = result.venue.trim()
      if (
        trimmedVenue &&
        !uniqueVenues.some(
          (existing) =>
            existing.toLocaleLowerCase('ja-JP') ===
            trimmedVenue.toLocaleLowerCase('ja-JP')
        )
      ) {
        uniqueVenues.push(trimmedVenue)
      }
    }
    return uniqueVenues
  }, [pastResults])
  const applyVenuePreset = (venueName: string) => {
    setVenue(venueName)
    const normalizedVenue = venueName.trim().toLocaleLowerCase('ja-JP')
    if (!normalizedVenue) return
    const latest = pastResults.find(
      (result) =>
        result.venue.trim().toLocaleLowerCase('ja-JP') === normalizedVenue
    )
    if (!latest) return
    setGameType(latest.game_type || 'NLH')
    setSmallBlind(String(latest.small_blind))
    setBigBlind(String(latest.big_blind))
  }
  const calculated = useMemo(() => {
    const bb = Number(bigBlind)
    const start = Number(startingStack)
    const additional = Number(additionalStack || 0)
    const end = Number(endingStack)
    const hours = Number(playHours || 0)
    const minutes = Number(playMinutes || 0)
    const totalMinutes = hours * 60 + minutes
    if (
      !bigBlind ||
      !startingStack ||
      !endingStack ||
      !Number.isFinite(bb) ||
      !Number.isFinite(start) ||
      !Number.isFinite(additional) ||
      !Number.isFinite(end) ||
      bb <= 0
    ) {
      return null
    }
    const startingBb = start / bb
    const totalInvestedStack = start + additional
    const chipProfit = end - totalInvestedStack
    const bbProfit = chipProfit / bb
    const bbPerHour =
      totalMinutes > 0 ? bbProfit / (totalMinutes / 60) : null
    return {
      startingBb,
      totalInvestedStack,
      chipProfit,
      bbProfit,
      bbPerHour,
      totalMinutes,
    }
  }, [
    bigBlind,
    startingStack,
    additionalStack,
    endingStack,
    playHours,
    playMinutes,
  ])
  const saveResult = async () => {
    setMessage('')
    const trimmedVenue = venue.trim()
    if (!playedAt) {
      setMessage('日付を入力してください。')
      return
    }
    if (!trimmedVenue) {
      setMessage('店舗名を入力してください。')
      return
    }
    if (!gameType) {
      setMessage('ゲーム種別を選択してください。')
      return
    }
    const sb = Number(smallBlind)
    const bb = Number(bigBlind)
    const start = Number(startingStack)
    const additional = Number(additionalStack || 0)
    const end = Number(endingStack)
    const hours = Number(playHours || 0)
    const minutes = Number(playMinutes || 0)
    const totalMinutes = hours * 60 + minutes
    if (!smallBlind || !Number.isFinite(sb) || sb <= 0) {
      setMessage('SBを正しく入力してください。')
      return
    }
    if (!bigBlind || !Number.isFinite(bb) || bb <= 0) {
      setMessage('BBを正しく入力してください。')
      return
    }
    if (sb >= bb) {
      setMessage('BBはSBより大きい数字を入力してください。')
      return
    }
    if (!startingStack || !Number.isFinite(start) || start < 0) {
      setMessage('開始スタックを正しく入力してください。')
      return
    }
    if (!Number.isFinite(additional) || additional < 0) {
      setMessage('追加スタックを正しく入力してください。')
      return
    }
    if (!endingStack || !Number.isFinite(end) || end < 0) {
      setMessage('終了スタックを正しく入力してください。')
      return
    }
    if (
      !Number.isInteger(hours) ||
      hours < 0 ||
      !Number.isInteger(minutes) ||
      minutes < 0 ||
      minutes > 59 ||
      totalMinutes <= 0
    ) {
      setMessage('プレイ時間を正しく入力してください。')
      return
    }
    setIsSaving(true)
    const {
      data: { user },
    } = await supabase.auth.getUser()
    if (!user) {
      setIsSaving(false)
      navigate('/login')
      return
    }
    const shouldBePublic = postToTimeline ? true : isPublic

    const { data: insertedResult, error } = await supabase
      .from('amusement_ring_results')
      .insert({
        user_id: user.id,
        played_at: playedAt,
        venue: trimmedVenue,
        game_type: gameType,
        small_blind: sb,
        big_blind: bb,
        starting_stack: start,
        additional_stack: additional,
        ending_stack: end,
        play_minutes: totalMinutes,
        memo: memo.trim() || null,
        is_public: shouldBePublic,
      })
      .select('id')
      .single()

    if (error || !insertedResult) {
      console.error(error)
      setMessage(
        `保存に失敗しました：${error?.message || '記録IDを取得できませんでした。'}`
      )
      setIsSaving(false)
      return
    }

    if (postToTimeline) {
      const bbProfit = (end - (start + additional)) / bb
      const defaultPostText =
        `${trimmedVenue}でアミューズリングをプレイ。` +
        `${bbProfit >= 0 ? '+' : ''}${bbProfit.toFixed(1)}BB`

      const { error: postError } = await supabase.from('posts').insert({
        user_id: user.id,
        content: timelineComment.trim() || defaultPostText,
        post_type: 'result',
        result_type: 'amusement',
        result_id: insertedResult.id,
      })

      if (postError) {
        console.error(postError)
        setMessage(
          `記録は保存されましたが、タイムライン投稿に失敗しました：${postError.message}`
        )
        setIsSaving(false)
        return
      }
    }

    setIsSaving(false)
    navigate('/profile')
  }
  const inputLabelStyle = {
    display: 'block',
    marginBottom: '7px',
    color: '#bbb',
    fontSize: '12px',
    fontWeight: 700,
  } as const
  const sectionStyle = {
    padding: '20px 0',
    borderBottom: '1px solid #242424',
  } as const
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
            gap: '14px',
            background: 'rgba(0, 0, 0, 0.92)',
            borderBottom: '1px solid #242424',
            backdropFilter: 'blur(14px)',
            WebkitBackdropFilter: 'blur(14px)',
          }}
        >
          <button
            onClick={() => navigate('/profile')}
            style={{
              width: '36px',
              height: '36px',
              padding: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'transparent',
              color: '#fff',
              borderRadius: '50%',
              fontSize: '23px',
            }}
          >
            ‹
          </button>
          <div>
            <div
              style={{
                fontSize: '18px',
                fontWeight: 800,
              }}
            >
              アミューズリング記録
            </div>
            <div
              style={{
                marginTop: '2px',
                color: '#666',
                fontSize: '11px',
              }}
            >
              BBベースでセッションを記録
            </div>
          </div>
        </header>
        <section style={sectionStyle}>
          <label style={inputLabelStyle}>日付 *</label>
          <input
            type="date"
            value={playedAt}
            onChange={(e) => setPlayedAt(e.target.value)}
          />
        </section>
        <section style={sectionStyle}>
          <label style={inputLabelStyle}>店舗名 *</label>
          <input
            type="text"
            list="amusement-ring-venues"
            value={venue}
            onChange={(e) => applyVenuePreset(e.target.value)}
            placeholder="例：Poker ○○"
          />
          <datalist id="amusement-ring-venues">
            {venueSuggestions.map((venueName) => (
              <option key={venueName} value={venueName} />
            ))}
          </datalist>
          <div
            style={{
              marginTop: '7px',
              color: '#666',
              fontSize: '11px',
              lineHeight: 1.5,
            }}
          >
            過去に登録した店舗を選ぶと、前回のゲーム種別・SB・BBを自動入力します。
          </div>
        </section>
        <section style={sectionStyle}>
          <label style={inputLabelStyle}>ゲーム種別 *</label>
          <select
            value={gameType}
            onChange={(e) => setGameType(e.target.value)}
          >
            <option value="NLH">NLH</option>
            <option value="PLO">PLO</option>
            <option value="MIX">MIX</option>
            <option value="その他">その他</option>
          </select>
        </section>
        <section style={sectionStyle}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px',
            }}
          >
            <div>
              <label style={inputLabelStyle}>SB *</label>
              <input
                type="number"
                inputMode="numeric"
                min="1"
                value={smallBlind}
                onChange={(e) => setSmallBlind(e.target.value)}
                placeholder="100"
              />
            </div>
            <div>
              <label style={inputLabelStyle}>BB *</label>
              <input
                type="number"
                inputMode="numeric"
                min="1"
                value={bigBlind}
                onChange={(e) => setBigBlind(e.target.value)}
                placeholder="200"
              />
            </div>
          </div>
        </section>
        <section style={sectionStyle}>
          <div
            style={{
              fontSize: '15px',
              fontWeight: 800,
              marginBottom: '15px',
            }}
          >
            スタック
          </div>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
            }}
          >
            <div>
              <label style={inputLabelStyle}>開始スタック *</label>
              <input
                type="number"
                inputMode="numeric"
                min="0"
                value={startingStack}
                onChange={(e) => setStartingStack(e.target.value)}
                placeholder="60000"
              />
            </div>
            <div>
              <label style={inputLabelStyle}>追加スタック</label>
              <input
                type="number"
                inputMode="numeric"
                min="0"
                value={additionalStack}
                onChange={(e) => setAdditionalStack(e.target.value)}
                placeholder="0"
              />
              <div
                style={{
                  marginTop: '7px',
                  color: '#666',
                  fontSize: '11px',
                }}
              >
                途中で追加したチップの合計。なければ0。
              </div>
            </div>
            <div>
              <label style={inputLabelStyle}>終了スタック *</label>
              <input
                type="number"
                inputMode="numeric"
                min="0"
                value={endingStack}
                onChange={(e) => setEndingStack(e.target.value)}
                placeholder="80000"
              />
            </div>
          </div>
        </section>
        <section style={sectionStyle}>
          <label style={inputLabelStyle}>プレイ時間 *</label>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px',
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
                min="0"
                value={playHours}
                onChange={(e) => setPlayHours(e.target.value)}
                placeholder="3"
                style={{
                  paddingRight: '45px',
                }}
              />
              <span
                style={{
                  position: 'absolute',
                  right: '14px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#777',
                  fontSize: '12px',
                  pointerEvents: 'none',
                }}
              >
                時間
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
                max="59"
                value={playMinutes}
                onChange={(e) => setPlayMinutes(e.target.value)}
                placeholder="30"
                style={{
                  paddingRight: '35px',
                }}
              />
              <span
                style={{
                  position: 'absolute',
                  right: '14px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#777',
                  fontSize: '12px',
                  pointerEvents: 'none',
                }}
              >
                分
              </span>
            </div>
          </div>
        </section>
        {calculated && (
          <section style={sectionStyle}>
            <div
              style={{
                fontSize: '15px',
                fontWeight: 800,
              }}
            >
              このセッション
            </div>
            <div
              style={{
                marginTop: '13px',
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '9px',
              }}
            >
              <div
                style={{
                  padding: '13px',
                  background: '#0d0d0d',
                  border: '1px solid #292929',
                  borderRadius: '13px',
                }}
              >
                <div
                  style={{
                    color: '#777',
                    fontSize: '10px',
                  }}
                >
                  開始時
                </div>
                <div
                  style={{
                    marginTop: '4px',
                    fontSize: '17px',
                    fontWeight: 800,
                  }}
                >
                  {calculated.startingBb.toFixed(1)}BB
                </div>
              </div>
              <div
                style={{
                  padding: '13px',
                  background: '#0d0d0d',
                  border: '1px solid #292929',
                  borderRadius: '13px',
                }}
              >
                <div
                  style={{
                    color: '#777',
                    fontSize: '10px',
                  }}
                >
                  BB収支
                </div>
                <div
                  style={{
                    marginTop: '4px',
                    fontSize: '17px',
                    fontWeight: 800,
                  }}
                >
                  {calculated.bbProfit >= 0 ? '+' : ''}
                  {calculated.bbProfit.toFixed(1)}BB
                </div>
              </div>
              <div
                style={{
                  padding: '13px',
                  background: '#0d0d0d',
                  border: '1px solid #292929',
                  borderRadius: '13px',
                }}
              >
                <div
                  style={{
                    color: '#777',
                    fontSize: '10px',
                  }}
                >
                  BB / h
                </div>
                <div
                  style={{
                    marginTop: '4px',
                    fontSize: '17px',
                    fontWeight: 800,
                  }}
                >
                  {calculated.bbPerHour === null
                    ? '-'
                    : `${calculated.bbPerHour >= 0 ? '+' : ''}${calculated.bbPerHour.toFixed(1)}`}
                </div>
              </div>
              <div
                style={{
                  padding: '13px',
                  background: '#0d0d0d',
                  border: '1px solid #292929',
                  borderRadius: '13px',
                }}
              >
                <div
                  style={{
                    color: '#777',
                    fontSize: '10px',
                  }}
                >
                  総投入スタック
                </div>
                <div
                  style={{
                    marginTop: '4px',
                    fontSize: '17px',
                    fontWeight: 800,
                  }}
                >
                  {calculated.totalInvestedStack.toLocaleString()}
                </div>
              </div>
            </div>
          </section>
        )}
        <section style={sectionStyle}>
          <label style={inputLabelStyle}>メモ</label>
          <textarea
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            placeholder="セッションの振り返りなど"
            rows={4}
          />
        </section>
        <section style={sectionStyle}>
          <div
            style={{
              fontSize: '15px',
              fontWeight: 800,
            }}
          >
            公開設定
          </div>
          <button
            type="button"
            onClick={() => setIsPublic((current) => !current)}
            style={{
              width: '100%',
              marginTop: '13px',
              padding: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '15px',
              background: '#0d0d0d',
              color: '#fff',
              border: '1px solid #292929',
              borderRadius: '13px',
              textAlign: 'left',
            }}
          >
            <div>
              <div
                style={{
                  fontSize: '13px',
                  fontWeight: 700,
                }}
              >
                {isPublic ? '公開' : '非公開'}
              </div>
              <div
                style={{
                  marginTop: '4px',
                  color: '#666',
                  fontSize: '11px',
                }}
              >
                {isPublic
                  ? '他のプレイヤーにもこの記録を表示します'
                  : 'この記録は自分だけが確認できます'}
              </div>
            </div>
            <div
              style={{
                width: '44px',
                height: '25px',
                padding: '3px',
                background: isPublic ? '#fff' : '#292929',
                borderRadius: '999px',
                transition: 'background .15s ease',
              }}
            >
              <div
                style={{
                  width: '19px',
                  height: '19px',
                  marginLeft: isPublic ? '19px' : 0,
                  background: isPublic ? '#000' : '#777',
                  borderRadius: '50%',
                  transition: 'margin .15s ease',
                }}
              />
            </div>
          </button>
        </section>
        <section style={sectionStyle}>
        <div style={{ fontSize: '15px', fontWeight: 800 }}>
          タイムライン投稿
        </div>

        <button
          type="button"
          onClick={() => {
            const next = !postToTimeline
            setPostToTimeline(next)
            if (next) setIsPublic(true)
          }}
          style={{
            width: '100%',
            marginTop: '13px',
            padding: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '15px',
            background: '#0d0d0d',
            color: '#fff',
            border: '1px solid #292929',
            borderRadius: '13px',
            textAlign: 'left',
          }}
        >
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700 }}>
              タイムラインにも投稿する
            </div>
            <div
              style={{
                marginTop: '4px',
                color: '#666',
                fontSize: '11px',
                lineHeight: 1.5,
              }}
            >
              {postToTimeline
                ? 'この記録を公開して、結果カード付きで投稿します'
                : '保存だけして、タイムラインには投稿しません'}
            </div>
          </div>

          <div
            style={{
              width: '44px',
              height: '25px',
              padding: '3px',
              background: postToTimeline ? '#fff' : '#292929',
              borderRadius: '999px',
              transition: 'background .15s ease',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: '19px',
                height: '19px',
                marginLeft: postToTimeline ? '19px' : 0,
                background: postToTimeline ? '#000' : '#777',
                borderRadius: '50%',
                transition: 'margin .15s ease',
              }}
            />
          </div>
        </button>

        {postToTimeline && (
          <>
            <div
              style={{
                marginTop: '10px',
                padding: '10px 12px',
                color: '#aaa',
                background: '#111',
                border: '1px solid #292929',
                borderRadius: '11px',
                fontSize: '11px',
                lineHeight: 1.5,
              }}
            >
              タイムラインに投稿する場合、この記録は公開になります。
            </div>

            <textarea
              value={timelineComment}
              onChange={(e) => setTimelineComment(e.target.value)}
              placeholder="投稿にひとこと追加（任意）"
              rows={3}
              maxLength={280}
              style={{ marginTop: '12px' }}
            />
          </>
        )}
      </section>

      {message && (
          <div
            style={{
              marginTop: '18px',
              padding: '12px 14px',
              color: '#ff9d9d',
              background: '#1a0d0d',
              border: '1px solid #442222',
              borderRadius: '12px',
              fontSize: '12px',
              lineHeight: 1.5,
            }}
          >
            {message}
          </div>
        )}
        <button
          onClick={saveResult}
          disabled={isSaving}
          style={{
            width: '100%',
            marginTop: '22px',
            padding: '14px 18px',
            background: '#fff',
            color: '#000',
            borderRadius: '999px',
            fontSize: '14px',
            fontWeight: 800,
          }}
        >
          {isSaving ? '保存中...' : 'アミューズリング記録を保存'}
        </button>
      </div>
    </main>
  )
}
export default AmusementRingCreate
