import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { supabase } from './supabase'

type PastRingResult = {
  id: string
  venue: string
  game_type: string
  small_blind: number
  big_blind: number
  played_at: string
  created_at: string
}

function AmusementRingEdit() {
  const navigate = useNavigate()
  const { id } = useParams()

  const [playedAt, setPlayedAt] = useState('')
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

  const [pastResults, setPastResults] = useState<PastRingResult[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    const loadData = async () => {
      if (!id) {
        navigate('/profile')
        return
      }

      const {
        data: { user },
      } = await supabase.auth.getUser()

      if (!user) {
        navigate('/login')
        return
      }

      const { data: result, error: resultError } = await supabase
        .from('amusement_ring_results')
        .select('*')
        .eq('id', id)
        .eq('user_id', user.id)
        .maybeSingle()

      if (resultError) {
        console.error(resultError)
        setMessage(`記録の読み込みに失敗しました：${resultError.message}`)
        setIsLoading(false)
        return
      }

      if (!result) {
        setMessage('記録が見つかりません。')
        setIsLoading(false)
        return
      }

      setPlayedAt(result.played_at)
      setVenue(result.venue)
      setGameType(result.game_type || 'NLH')
      setSmallBlind(String(result.small_blind))
      setBigBlind(String(result.big_blind))
      setStartingStack(String(result.starting_stack))
      setAdditionalStack(String(result.additional_stack ?? 0))
      setEndingStack(String(result.ending_stack))

      const totalMinutes = Number(result.play_minutes || 0)
      setPlayHours(String(Math.floor(totalMinutes / 60)))
      setPlayMinutes(String(totalMinutes % 60))

      setMemo(result.memo || '')
      setIsPublic(Boolean(result.is_public))

      const { data: history, error: historyError } = await supabase
        .from('amusement_ring_results')
        .select(
          'id, venue, game_type, small_blind, big_blind, played_at, created_at'
        )
        .eq('user_id', user.id)
        .neq('id', id)
        .order('played_at', { ascending: false })
        .order('created_at', { ascending: false })

      if (historyError) {
        console.error(historyError)
      } else {
        setPastResults(history || [])
      }

      setIsLoading(false)
    }

    loadData()
  }, [id, navigate])

  const venueSuggestions = useMemo(() => {
    const venues: string[] = []

    const addVenue = (name: string) => {
      const trimmed = name.trim()
      if (!trimmed) return

      const exists = venues.some(
        (existing) =>
          existing.toLocaleLowerCase('ja-JP') ===
          trimmed.toLocaleLowerCase('ja-JP')
      )

      if (!exists) venues.push(trimmed)
    }

    addVenue(venue)

    for (const result of pastResults) {
      addVenue(result.venue)
    }

    return venues
  }, [pastResults, venue])

  const applyVenuePreset = (venueName: string) => {
    setVenue(venueName)

    const normalized = venueName.trim().toLocaleLowerCase('ja-JP')
    if (!normalized) return

    const latest = pastResults.find(
      (result) =>
        result.venue.trim().toLocaleLowerCase('ja-JP') === normalized
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
      endingStack === '' ||
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
    const bbProfit = (end - totalInvestedStack) / bb
    const bbPerHour =
      totalMinutes > 0 ? bbProfit / (totalMinutes / 60) : null

    return {
      startingBb,
      totalInvestedStack,
      bbProfit,
      bbPerHour,
    }
  }, [
    bigBlind,
    startingStack,
    additionalStack,
    endingStack,
    playHours,
    playMinutes,
  ])

  const validate = () => {
    if (!playedAt) return '日付を入力してください。'
    if (!venue.trim()) return '店舗名を入力してください。'
    if (!gameType) return 'ゲーム種別を選択してください。'

    const sb = Number(smallBlind)
    const bb = Number(bigBlind)
    const start = Number(startingStack)
    const additional = Number(additionalStack || 0)
    const end = Number(endingStack)

    const hours = Number(playHours || 0)
    const minutes = Number(playMinutes || 0)
    const totalMinutes = hours * 60 + minutes

    if (!smallBlind || !Number.isFinite(sb) || sb <= 0) {
      return 'SBを正しく入力してください。'
    }

    if (!bigBlind || !Number.isFinite(bb) || bb <= 0) {
      return 'BBを正しく入力してください。'
    }

    if (sb >= bb) {
      return 'BBはSBより大きい数字を入力してください。'
    }

    if (!startingStack || !Number.isFinite(start) || start < 0) {
      return '開始スタックを正しく入力してください。'
    }

    if (!Number.isFinite(additional) || additional < 0) {
      return '追加スタックを正しく入力してください。'
    }

    if (endingStack === '' || !Number.isFinite(end) || end < 0) {
      return '終了スタックを正しく入力してください。'
    }

    if (
      !Number.isInteger(hours) ||
      hours < 0 ||
      !Number.isInteger(minutes) ||
      minutes < 0 ||
      minutes > 59 ||
      totalMinutes <= 0
    ) {
      return 'プレイ時間を正しく入力してください。'
    }

    return null
  }

  const saveResult = async () => {
    setMessage('')

    const validationError = validate()
    if (validationError) {
      setMessage(validationError)
      return
    }

    if (!id) return

    setIsSaving(true)

    const {
      data: { user },
    } = await supabase.auth.getUser()

    if (!user) {
      setIsSaving(false)
      navigate('/login')
      return
    }

    const hours = Number(playHours || 0)
    const minutes = Number(playMinutes || 0)

    const { error } = await supabase
      .from('amusement_ring_results')
      .update({
        played_at: playedAt,
        venue: venue.trim(),
        game_type: gameType,
        small_blind: Number(smallBlind),
        big_blind: Number(bigBlind),
        starting_stack: Number(startingStack),
        additional_stack: Number(additionalStack || 0),
        ending_stack: Number(endingStack),
        play_minutes: hours * 60 + minutes,
        memo: memo.trim() || null,
        is_public: isPublic,
      })
      .eq('id', id)
      .eq('user_id', user.id)

    setIsSaving(false)

    if (error) {
      console.error(error)
      setMessage(`保存に失敗しました：${error.message}`)
      return
    }

    navigate('/profile')
  }

  const deleteResult = async () => {
    if (!id || isDeleting) return

    const confirmed = window.confirm(
      'このアミューズリング記録を削除しますか？\nこの操作は取り消せません。'
    )

    if (!confirmed) return

    setMessage('')
    setIsDeleting(true)

    const {
      data: { user },
    } = await supabase.auth.getUser()

    if (!user) {
      setIsDeleting(false)
      navigate('/login')
      return
    }

    const { error } = await supabase
      .from('amusement_ring_results')
      .delete()
      .eq('id', id)
      .eq('user_id', user.id)

    setIsDeleting(false)

    if (error) {
      console.error(error)
      setMessage(`削除に失敗しました：${error.message}`)
      return
    }

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

  if (isLoading) {
    return (
      <main className="app">
        <div className="card">
          <p
            style={{
              color: '#777',
              textAlign: 'center',
              paddingTop: '80px',
            }}
          >
            読み込み中...
          </p>
        </div>
      </main>
    )
  }

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
            <div style={{ fontSize: '18px', fontWeight: 800 }}>
              アミューズリング記録を編集
            </div>

            <div
              style={{
                marginTop: '2px',
                color: '#666',
                fontSize: '11px',
              }}
            >
              セッション内容を修正
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
            list="amusement-ring-edit-venues"
            value={venue}
            onChange={(e) => applyVenuePreset(e.target.value)}
            placeholder="例：Poker ○○"
          />

          <datalist id="amusement-ring-edit-venues">
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
            過去の店舗を選ぶと、その店舗で最後に使ったゲーム種別・SB・BBを自動入力します。
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
            <div style={{ position: 'relative' }}>
              <input
                type="number"
                inputMode="numeric"
                min="0"
                value={playHours}
                onChange={(e) => setPlayHours(e.target.value)}
                style={{ paddingRight: '45px' }}
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

            <div style={{ position: 'relative' }}>
              <input
                type="number"
                inputMode="numeric"
                min="0"
                max="59"
                value={playMinutes}
                onChange={(e) => setPlayMinutes(e.target.value)}
                style={{ paddingRight: '35px' }}
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
            <div style={{ fontSize: '15px', fontWeight: 800 }}>
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
              {[
                ['開始時', `${calculated.startingBb.toFixed(1)}BB`],
                [
                  'BB収支',
                  `${calculated.bbProfit >= 0 ? '+' : ''}${calculated.bbProfit.toFixed(1)}BB`,
                ],
                [
                  'BB / h',
                  calculated.bbPerHour === null
                    ? '—'
                    : `${calculated.bbPerHour >= 0 ? '+' : ''}${calculated.bbPerHour.toFixed(1)}`,
                ],
                [
                  '総投入スタック',
                  calculated.totalInvestedStack.toLocaleString(),
                ],
              ].map(([label, value]) => (
                <div
                  key={label}
                  style={{
                    padding: '13px',
                    background: '#0d0d0d',
                    border: '1px solid #292929',
                    borderRadius: '13px',
                  }}
                >
                  <div style={{ color: '#777', fontSize: '10px' }}>
                    {label}
                  </div>

                  <div
                    style={{
                      marginTop: '4px',
                      fontSize: '17px',
                      fontWeight: 800,
                    }}
                  >
                    {value}
                  </div>
                </div>
              ))}
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
          <div style={{ fontSize: '15px', fontWeight: 800 }}>
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
              <div style={{ fontSize: '13px', fontWeight: 700 }}>
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
          disabled={isSaving || isDeleting}
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
          {isSaving ? '保存中...' : '変更を保存'}
        </button>

        <button
          onClick={deleteResult}
          disabled={isSaving || isDeleting}
          style={{
            width: '100%',
            marginTop: '12px',
            padding: '13px 18px',
            background: 'transparent',
            color: '#e77',
            border: '1px solid #422',
            borderRadius: '999px',
            fontSize: '13px',
            fontWeight: 700,
          }}
        >
          {isDeleting ? '削除中...' : 'この記録を削除'}
        </button>
      </div>
    </main>
  )
}

export default AmusementRingEdit