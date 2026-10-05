import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from './supabase'
type PlayType = 'live' | 'online'
type RecordType = 'session' | 'daily'
type VenuePreset = {
  venue: string
  game_type: string
  small_blind: number
  big_blind: number
  currency: string
}
const CURRENCIES = [
  'JPY',
  'USD',
  'EUR',
  'GBP',
  'KRW',
  'CNY',
  'HKD',
  'TWD',
  'AUD',
  'CAD',
  'SGD',
  'PHP',
  'THB',
  'VND',
]
function getToday() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
function formatNumber(value: number, maximumFractionDigits = 2) {
  return new Intl.NumberFormat('ja-JP', {
    maximumFractionDigits,
  }).format(value)
}
function CashGameCreate() {
  const navigate = useNavigate()
  const [userId, setUserId] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [playType, setPlayType] = useState<PlayType>('live')
  const [recordType, setRecordType] = useState<RecordType>('session')
  const [playedAt, setPlayedAt] = useState(getToday())
  const [venue, setVenue] = useState('')
  const [gameType, setGameType] = useState('NLH')
  const [smallBlind, setSmallBlind] = useState('')
  const [bigBlind, setBigBlind] = useState('')
  const [currency, setCurrency] = useState('JPY')
  const [buyInAmount, setBuyInAmount] = useState('')
  const [cashOutAmount, setCashOutAmount] = useState('')
  const [dailyProfitAmount, setDailyProfitAmount] = useState('')
  const [playHours, setPlayHours] = useState('')
  const [playMinutesPart, setPlayMinutesPart] = useState('')
  const [memo, setMemo] = useState('')
  const [isPublic, setIsPublic] = useState(false)
const [postToTimeline, setPostToTimeline] = useState(false)
const [timelineComment, setTimelineComment] = useState('')
  const [exchangeRate, setExchangeRate] = useState<number | null>(1)
  const [exchangeRateDate, setExchangeRateDate] = useState('')
  const [exchangeLoading, setExchangeLoading] = useState(false)
  const [exchangeError, setExchangeError] = useState('')
  const [venuePresets, setVenuePresets] = useState<VenuePreset[]>([])
  useEffect(() => {
    const initialize = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser()
      if (!user) {
        navigate('/login')
        return
      }
      setUserId(user.id)
      const { data, error } = await supabase
        .from('cash_game_results')
        .select(
          'venue, game_type, small_blind, big_blind, currency, created_at'
        )
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
      if (!error && data) {
        const seen = new Set<string>()
        const presets: VenuePreset[] = []
        for (const row of data) {
          const key = row.venue.trim().toLowerCase()
          if (!key || seen.has(key)) continue
          seen.add(key)
          presets.push({
            venue: row.venue,
            game_type: row.game_type,
            small_blind: Number(row.small_blind),
            big_blind: Number(row.big_blind),
            currency: row.currency,
          })
        }
        setVenuePresets(presets)
      }
      setLoading(false)
    }
    initialize()
  }, [navigate])
  useEffect(() => {
    if (playType === 'live' && recordType === 'daily') {
      setRecordType('session')
    }
  }, [playType, recordType])
  useEffect(() => {
    let cancelled = false
    const fetchExchangeRate = async () => {
      setExchangeError('')
      setExchangeRateDate('')
      if (!playedAt || !currency) {
        setExchangeRate(null)
        return
      }
      if (currency === 'JPY') {
        setExchangeRate(1)
        setExchangeRateDate(playedAt)
        return
      }
      setExchangeLoading(true)
      setExchangeRate(null)
      try {
        const url =
          `https\://api.frankfurter.dev/v2/rate/` +
          `${currency.toLowerCase()}/jpy?date=${playedAt}`
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error('為替レートを取得できませんでした。')
        }
        const data = await response.json()
        if (
          !data ||
          typeof data.rate !== 'number' ||
          !Number.isFinite(data.rate) ||
          data.rate <= 0
        ) {
          throw new Error('為替レートを取得できませんでした。')
        }
        if (!cancelled) {
          setExchangeRate(data.rate)
          setExchangeRateDate(data.date ?? playedAt)
        }
      } catch (error) {
        if (!cancelled) {
          console.error(error)
          setExchangeRate(null)
          setExchangeError(
            'この日付・通貨の為替レートを取得できませんでした。'
          )
        }
      } finally {
        if (!cancelled) {
          setExchangeLoading(false)
        }
      }
    }
    fetchExchangeRate()
    return () => {
      cancelled = true
    }
  }, [playedAt, currency])
  const isDailyOnline =
    playType === 'online' && recordType === 'daily'
  const profitAmount = useMemo(() => {
    if (isDailyOnline) {
      if (dailyProfitAmount.trim() === '') return null
      const value = Number(dailyProfitAmount)
      return Number.isFinite(value) ? value : null
    }
    if (
      buyInAmount.trim() === '' ||
      cashOutAmount.trim() === ''
    ) {
      return null
    }
    const buyIn = Number(buyInAmount)
    const cashOut = Number(cashOutAmount)
    if (!Number.isFinite(buyIn) || !Number.isFinite(cashOut)) {
      return null
    }
    return cashOut - buyIn
  }, [
    isDailyOnline,
    dailyProfitAmount,
    buyInAmount,
    cashOutAmount,
  ])
  const profitJpy = useMemo(() => {
    if (profitAmount === null || exchangeRate === null) {
      return null
    }
    return profitAmount * exchangeRate
  }, [profitAmount, exchangeRate])
  const bbProfit = useMemo(() => {
    if (profitAmount === null || bigBlind.trim() === '') {
      return null
    }
    const bb = Number(bigBlind)
    if (!Number.isFinite(bb) || bb <= 0) {
      return null
    }
    return profitAmount / bb
  }, [profitAmount, bigBlind])
  const totalPlayMinutes = useMemo(() => {
    const hours =
      playHours.trim() === '' ? 0 : Number(playHours)
    const minutes =
      playMinutesPart.trim() === ''
        ? 0
        : Number(playMinutesPart)
    if (
      !Number.isFinite(hours) ||
      !Number.isFinite(minutes)
    ) {
      return 0
    }
    return hours * 60 + minutes
  }, [playHours, playMinutesPart])
  const bbPerHour = useMemo(() => {
    if (
      bbProfit === null ||
      totalPlayMinutes <= 0
    ) {
      return null
    }
    return bbProfit / (totalPlayMinutes / 60)
  }, [bbProfit, totalPlayMinutes])
  const applyVenuePreset = (value: string) => {
    setVenue(value)
    const normalized = value.trim().toLowerCase()
    const preset = venuePresets.find(
      (item) =>
        item.venue.trim().toLowerCase() === normalized
    )
    if (!preset) return
    setGameType(preset.game_type)
    setSmallBlind(String(preset.small_blind))
    setBigBlind(String(preset.big_blind))
    setCurrency(preset.currency)
  }
  const validate = () => {
    if (!playedAt) {
      return '日付を入力してください。'
    }
    if (!venue.trim()) {
      return playType === 'live'
        ? '店舗名を入力してください。'
        : 'サイト名を入力してください。'
    }
    if (!gameType.trim()) {
      return 'ゲーム種別を入力してください。'
    }
    const sb = Number(smallBlind)
    const bb = Number(bigBlind)
    if (
      smallBlind.trim() === '' ||
      !Number.isFinite(sb) ||
      sb <= 0
    ) {
      return 'SBを正しく入力してください。'
    }
    if (
      bigBlind.trim() === '' ||
      !Number.isFinite(bb) ||
      bb <= 0
    ) {
      return 'BBを正しく入力してください。'
    }
    if (sb >= bb) {
      return 'SBはBBより小さい金額にしてください。'
    }
    if (!currency) {
      return '通貨を選択してください。'
    }
    if (isDailyOnline) {
      if (dailyProfitAmount.trim() === '') {
        return 'その日の収支を入力してください。'
      }
      const value = Number(dailyProfitAmount)
      if (!Number.isFinite(value)) {
        return '収支を正しく入力してください。'
      }
    } else {
      if (buyInAmount.trim() === '') {
        return 'バイイン総額を入力してください。'
      }
      if (cashOutAmount.trim() === '') {
        return 'キャッシュアウト額を入力してください。'
      }
      const buyIn = Number(buyInAmount)
      const cashOut = Number(cashOutAmount)
      if (!Number.isFinite(buyIn) || buyIn < 0) {
        return 'バイイン総額を正しく入力してください。'
      }
      if (!Number.isFinite(cashOut) || cashOut < 0) {
        return 'キャッシュアウト額を正しく入力してください。'
      }
    }
    const hours =
      playHours.trim() === '' ? 0 : Number(playHours)
    const minutes =
      playMinutesPart.trim() === ''
        ? 0
        : Number(playMinutesPart)
    if (
      !Number.isFinite(hours) ||
      hours < 0 ||
      !Number.isInteger(hours)
    ) {
      return 'プレイ時間の「時間」を正しく入力してください。'
    }
    if (
      !Number.isFinite(minutes) ||
      minutes < 0 ||
      minutes >= 60 ||
      !Number.isInteger(minutes)
    ) {
      return 'プレイ時間の「分」は0〜59で入力してください。'
    }
    if (totalPlayMinutes <= 0) {
      return 'プレイ時間を入力してください。'
    }
    if (exchangeLoading) {
      return '為替レートを取得中です。少し待ってください。'
    }
    if (exchangeRate === null) {
      return '為替レートを取得できていません。'
    }
    if (profitAmount === null) {
      return '収支を計算できませんでした。'
    }
    return ''
  }
  const handleSave = async () => {
    setErrorMessage('')
    const validationError = validate()
    if (validationError) {
      setErrorMessage(validationError)
      return
    }
    if (
      !userId ||
      profitAmount === null ||
      exchangeRate === null ||
      profitJpy === null
    ) {
      setErrorMessage('保存に必要な情報が不足しています。')
      return
    }
    setSaving(true)
    const buyIn = isDailyOnline
      ? null
      : Number(buyInAmount)
    const cashOut = isDailyOnline
      ? null
      : Number(cashOutAmount)
    const shouldBePublic = postToTimeline ? true : isPublic
  const { data: insertedResult, error } = await supabase
    .from('cash_game_results')
    .insert({
      user_id: userId,
      played_at: playedAt,
      play_type: playType,
      record_type: recordType,
      venue: venue.trim(),
      game_type: gameType.trim(),
      small_blind: Number(smallBlind),
      big_blind: Number(bigBlind),
      currency,
      buy_in_amount: buyIn,
      cash_out_amount: cashOut,
      profit_amount: profitAmount,
      exchange_rate_to_jpy: exchangeRate,
      profit_jpy: Math.round(profitJpy),
      play_minutes: totalPlayMinutes,
      memo: memo.trim() || null,
      is_public: shouldBePublic,
    })
    .select('id')
    .single()
  if (error || !insertedResult) {
    console.error(error)
    setErrorMessage(
      `保存に失敗しました：${error?.message || '記録IDを取得できませんでした。'}`
    )
    setSaving(false)
    return
  }
  if (postToTimeline) {
    const defaultPostText =
      `${venue.trim()}でキャッシュゲームをプレイ。` +
      `${profitAmount >= 0 ? '+' : ''}${formatNumber(profitAmount)} ${currency}`
    const { error: postError } = await supabase.from('posts').insert({
      user_id: userId,
      content: timelineComment.trim() || defaultPostText,
      post_type: 'result',
      result_type: 'cash',
      result_id: insertedResult.id,
    })
    if (postError) {
      console.error(postError)
      setErrorMessage(
        `記録は保存されましたが、タイムライン投稿に失敗しました：${postError.message}`
      )
      setSaving(false)
      return
    }
  }
  setSaving(false)
  navigate('/profile')
  }
  if (loading) {
    return (
      <main className="app">
        <div className="card">
          <p className="sns-muted">読み込み中...</p>
        </div>
      </main>
    )
  }
  return (
    <main className="app">
      <div className="card">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            marginBottom: '24px',
          }}
        >
          <button
            onClick={() => navigate('/profile')}
            style={{
              background: 'transparent',
              color: '#fff',
              padding: '6px 0',
              fontSize: '24px',
            }}
          >
            ‹
          </button>
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: '22px',
                fontWeight: 800,
              }}
            >
              キャッシュゲーム記録
            </h1>
            <div
              className="sns-muted"
              style={{
                marginTop: '4px',
                fontSize: '13px',
              }}
            >
              ライブ・オンラインの成績を記録
            </div>
          </div>
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '8px',
            marginBottom: '24px',
          }}
        >
          <button
            type="button"
            onClick={() => setPlayType('live')}
            style={{
              padding: '12px',
              borderRadius: '12px',
              background:
                playType === 'live' ? '#fff' : '#111',
              color:
                playType === 'live' ? '#000' : '#fff',
              border: '1px solid #333',
              fontWeight: 700,
            }}
          >
            ライブ
          </button>
          <button
            type="button"
            onClick={() => setPlayType('online')}
            style={{
              padding: '12px',
              borderRadius: '12px',
              background:
                playType === 'online' ? '#fff' : '#111',
              color:
                playType === 'online' ? '#000' : '#fff',
              border: '1px solid #333',
              fontWeight: 700,
            }}
          >
            オンライン
          </button>
        </div>
        {playType === 'online' && (
          <div style={{ marginBottom: '24px' }}>
            <div
              style={{
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              記録方法
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '8px',
              }}
            >
              <button
                type="button"
                onClick={() => setRecordType('session')}
                style={{
                  padding: '11px',
                  borderRadius: '12px',
                  background:
                    recordType === 'session'
                      ? '#fff'
                      : '#111',
                  color:
                    recordType === 'session'
                      ? '#000'
                      : '#fff',
                  border: '1px solid #333',
                  fontWeight: 700,
                }}
              >
                セッション
              </button>
              <button
                type="button"
                onClick={() => setRecordType('daily')}
                style={{
                  padding: '11px',
                  borderRadius: '12px',
                  background:
                    recordType === 'daily'
                      ? '#fff'
                      : '#111',
                  color:
                    recordType === 'daily'
                      ? '#000'
                      : '#fff',
                  border: '1px solid #333',
                  fontWeight: 700,
                }}
              >
                1日まとめ
              </button>
            </div>
          </div>
        )}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
          }}
        >
          <label>
            <div
              style={{
                marginBottom: '7px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              日付 *
            </div>
            <input
              type="date"
              value={playedAt}
              max={getToday()}
              onChange={(e) => setPlayedAt(e.target.value)}
            />
          </label>
          <label>
            <div
              style={{
                marginBottom: '7px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              {playType === 'live'
                ? '店舗名 *'
                : 'サイト名 *'}
            </div>
            <input
              type="text"
              list="cash-game-venues"
              value={venue}
              placeholder={
                playType === 'live'
                  ? '例：ARIA Poker Room'
                  : '例：GGPoker'
              }
              onChange={(e) =>
                applyVenuePreset(e.target.value)
              }
            />
            <datalist id="cash-game-venues">
              {venuePresets.map((preset) => (
                <option
                  key={preset.venue}
                  value={preset.venue}
                />
              ))}
            </datalist>
            {venuePresets.length > 0 && (
              <div
                className="sns-muted"
                style={{
                  marginTop: '6px',
                  fontSize: '12px',
                }}
              >
                過去の場所を選ぶと、直近のゲーム・レート・通貨を自動入力します。
              </div>
            )}
          </label>
          <label>
            <div
              style={{
                marginBottom: '7px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              ゲーム *
            </div>
            <select
              value={gameType}
              onChange={(e) =>
                setGameType(e.target.value)
              }
            >
              <option value="NLH">NLH</option>
              <option value="PLO">PLO</option>
              <option value="MIX">MIX</option>
              <option value="その他">その他</option>
            </select>
          </label>
          <div>
            <div
              style={{
                marginBottom: '7px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              ブラインド *
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '10px',
              }}
            >
              <input
                type="number"
                min="0"
                step="any"
                placeholder="SB"
                value={smallBlind}
                onChange={(e) =>
                  setSmallBlind(e.target.value)
                }
              />
              <input
                type="number"
                min="0"
                step="any"
                placeholder="BB"
                value={bigBlind}
                onChange={(e) =>
                  setBigBlind(e.target.value)
                }
              />
            </div>
          </div>
          <label>
            <div
              style={{
                marginBottom: '7px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              通貨 *
            </div>
            <select
              value={currency}
              onChange={(e) =>
                setCurrency(e.target.value)
              }
            >
              {CURRENCIES.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </label>
          {!isDailyOnline ? (
            <>
              <label>
                <div
                  style={{
                    marginBottom: '7px',
                    fontSize: '14px',
                    fontWeight: 700,
                  }}
                >
                  バイイン総額 *
                </div>
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={buyInAmount}
                  placeholder="0"
                  onChange={(e) =>
                    setBuyInAmount(e.target.value)
                  }
                />
              </label>
              <label>
                <div
                  style={{
                    marginBottom: '7px',
                    fontSize: '14px',
                    fontWeight: 700,
                  }}
                >
                  キャッシュアウト額 *
                </div>
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={cashOutAmount}
                  placeholder="0"
                  onChange={(e) =>
                    setCashOutAmount(e.target.value)
                  }
                />
              </label>
            </>
          ) : (
            <label>
              <div
                style={{
                  marginBottom: '7px',
                  fontSize: '14px',
                  fontWeight: 700,
                }}
              >
                その日の収支 *
              </div>
              <input
                type="number"
                step="any"
                value={dailyProfitAmount}
                placeholder="例：230 / -120"
                onChange={(e) =>
                  setDailyProfitAmount(e.target.value)
                }
              />
              <div
                className="sns-muted"
                style={{
                  marginTop: '6px',
                  fontSize: '12px',
                }}
              >
                勝ちはプラス、負けはマイナスで入力
              </div>
            </label>
          )}
          <div>
            <div
              style={{
                marginBottom: '7px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              プレイ時間 *
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '10px',
              }}
            >
              <div>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={playHours}
                  placeholder="時間"
                  onChange={(e) =>
                    setPlayHours(e.target.value)
                  }
                />
              </div>
              <div>
                <input
                  type="number"
                  min="0"
                  max="59"
                  step="1"
                  value={playMinutesPart}
                  placeholder="分"
                  onChange={(e) =>
                    setPlayMinutesPart(e.target.value)
                  }
                />
              </div>
            </div>
          </div>
          <div
            style={{
              padding: '16px',
              border: '1px solid #292929',
              borderRadius: '14px',
              background: '#0b0b0b',
            }}
          >
            <div
              style={{
                fontSize: '14px',
                fontWeight: 800,
                marginBottom: '14px',
              }}
            >
              自動計算
            </div>
            <div
              style={{
                display: 'grid',
                gap: '10px',
                fontSize: '14px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '16px',
                }}
              >
                <span className="sns-muted">収支</span>
                <strong>
                  {profitAmount === null
                    ? '—'
                    : `${
                        profitAmount >= 0 ? '+' : ''
                      }${formatNumber(
                        profitAmount
                      )} ${currency}`}
                </strong>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '16px',
                }}
              >
                <span className="sns-muted">
                  BB収支
                </span>
                <strong>
                  {bbProfit === null
                    ? '—'
                    : `${
                        bbProfit >= 0 ? '+' : ''
                      }${formatNumber(bbProfit)} BB`}
                </strong>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '16px',
                }}
              >
                <span className="sns-muted">
                  BB/h
                </span>
                <strong>
                  {bbPerHour === null
                    ? '—'
                    : `${
                        bbPerHour >= 0 ? '+' : ''
                      }${formatNumber(bbPerHour)} BB/h`}
                </strong>
              </div>
              <div
                style={{
                  height: '1px',
                  background: '#242424',
                  margin: '2px 0',
                }}
              />
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '16px',
                }}
              >
                <span className="sns-muted">
                  為替レート
                </span>
                <strong
                  style={{
                    textAlign: 'right',
                    fontSize: '13px',
                  }}
                >
                  {exchangeLoading
                    ? '取得中...'
                    : exchangeRate === null
                      ? '取得できません'
                      : currency === 'JPY'
                        ? '1 JPY = 1 JPY'
                        : `1 ${currency} = ${formatNumber(
                            exchangeRate,
                            6
                          )} JPY`}
                </strong>
              </div>
              {exchangeRateDate &&
                currency !== 'JPY' && (
                  <div
                    className="sns-muted"
                    style={{
                      fontSize: '11px',
                      textAlign: 'right',
                    }}
                  >
                    レート日付：{exchangeRateDate}
                  </div>
                )}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '16px',
                }}
              >
                <span className="sns-muted">
                  円換算収支
                </span>
                <strong>
                  {profitJpy === null
                    ? '—'
                    : `${
                        profitJpy >= 0 ? '+' : ''
                      }¥${formatNumber(
                        Math.round(profitJpy),
                        0
                      )}`}
                </strong>
              </div>
            </div>
            {exchangeError && (
              <div
                style={{
                  marginTop: '12px',
                  color: '#ff6b6b',
                  fontSize: '12px',
                  lineHeight: 1.5,
                }}
              >
                {exchangeError}
              </div>
            )}
          </div>
          <label>
            <div
              style={{
                marginBottom: '7px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              メモ
            </div>
            <textarea
              rows={4}
              value={memo}
              placeholder="セッションについて自由に記録"
              onChange={(e) =>
                setMemo(e.target.value)
              }
            />
          </label>
          <div
            style={{
              padding: '15px',
              border: '1px solid #292929',
              borderRadius: '14px',
              background: '#0b0b0b',
            }}
          >
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '16px',
                cursor: 'pointer',
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: '14px',
                    fontWeight: 700,
                  }}
                >
                  この記録を公開
                </div>
                <div
                  className="sns-muted"
                  style={{
                    marginTop: '4px',
                    fontSize: '12px',
                    lineHeight: 1.5,
                  }}
                >
                  ONにした記録だけ他のプレイヤーに表示されます
                </div>
              </div>
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => {
                const next = e.target.checked
                setIsPublic(next)
                if (!next) setPostToTimeline(false)
              }}
                style={{
                  width: '20px',
                  height: '20px',
                  flexShrink: 0,
                }}
              />
            </label>
          </div>
          <div
          style={{
            padding: '15px',
            border: '1px solid #292929',
            borderRadius: '14px',
            background: '#0b0b0b',
          }}
        >
          <button
            type="button"
            onClick={() => {
              const next = !postToTimeline
              setPostToTimeline(next)
              if (next) setIsPublic(true)
            }}
            style={{
              width: '100%',
              padding: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '16px',
              background: 'transparent',
              color: '#fff',
              border: 'none',
              textAlign: 'left',
            }}
          >
            <div>
              <div style={{ fontSize: '14px', fontWeight: 700 }}>
                タイムラインにも投稿する
              </div>
              <div className="sns-muted" style={{ marginTop: '4px', fontSize: '12px', lineHeight: 1.5 }}>
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
                  marginTop: '12px',
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
        </div>
        {errorMessage && (
            <div
              style={{
                padding: '12px 14px',
                borderRadius: '12px',
                background: '#241010',
                border: '1px solid #522',
                color: '#ff8c8c',
                fontSize: '13px',
                lineHeight: 1.5,
              }}
            >
              {errorMessage}
            </div>
          )}
          <button
            className="login-button"
            type="button"
            disabled={saving || exchangeLoading}
            onClick={handleSave}
            style={{
              marginTop: '4px',
            }}
          >
            {saving ? '保存中...' : '記録を保存'}
          </button>
        </div>
      </div>
    </main>
  )
}
export default CashGameCreate
