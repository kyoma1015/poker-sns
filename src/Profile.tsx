    import { useEffect, useState } from 'react'
    import { useNavigate } from 'react-router-dom'
    import { supabase } from './supabase'
    type PokerResult = {
      id: string
      tournament_name: string
      played_at: string
      rank: number | null
      entry_count: number | null
      venue: string | null
      rank_unknown: boolean
      is_itm: boolean
      prize_amount: number | null
      prize_description: string | null
      entry_fee: number | null
      bullets: number
      total_entry_fee: number | null
      entry_timing: string | null
      entry_bb: number | null
      game_type: string | null
      is_featured: boolean
      memo: string | null
      is_public: boolean
    }
    type AmusementRingResult = {
      id: string
      played_at: string
      venue: string
      game_type: string
      small_blind: number
      big_blind: number
      starting_stack: number
      additional_stack: number
      ending_stack: number
      play_minutes: number
      memo: string | null
      is_public: boolean
    }
    type CashGameResult = {
      id: string
      played_at: string
      play_type: 'live' | 'online'
      record_type: 'session' | 'daily'
      venue: string
      game_type: string
      small_blind: number
      big_blind: number
      currency: string
      buy_in_amount: number | null
      cash_out_amount: number | null
      profit_amount: number
      exchange_rate_to_jpy: number
      profit_jpy: number
      play_minutes: number
      memo: string | null
      is_public: boolean
    }
    type TrendPoint = { label: string; value: number; detail: string }
    function CumulativeTrendChart({ title, subtitle, points, valueFormatter }: { title: string; subtitle: string; points: TrendPoint[]; valueFormatter: (value: number) => string }) {
      if (points.length === 0) return null
      const width = 520, height = 220, padLeft = 18, padRight = 18, padTop = 22, padBottom = 34
      const values = [0, ...points.map((point) => point.value)]
      const rawMin = Math.min(...values), rawMax = Math.max(...values)
      const span = rawMax - rawMin || Math.max(Math.abs(rawMax), 1)
      const minValue = rawMin - span * 0.12, maxValue = rawMax + span * 0.12
      const chartWidth = width - padLeft - padRight, chartHeight = height - padTop - padBottom
      const xFor = (index: number) => points.length === 1 ? padLeft + chartWidth / 2 : padLeft + (index / (points.length - 1)) * chartWidth
      const yFor = (value: number) => padTop + ((maxValue - value) / (maxValue - minValue)) * chartHeight
      const path = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${xFor(index)} ${yFor(point.value)}`).join(' ')
      const zeroY = yFor(0), latest = points[points.length - 1]
      return (
        <div style={{ padding: '15px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start' }}>
            <div><div style={{ fontSize: '13px', fontWeight: 800 }}>{title}</div><div style={{ marginTop: '4px', color: '#666', fontSize: '10px' }}>{subtitle}</div></div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}><div style={{ color: '#777', fontSize: '9px' }}>現在</div><div style={{ marginTop: '3px', fontSize: '15px', fontWeight: 800 }}>{valueFormatter(latest.value)}</div></div>
          </div>
          <div style={{ marginTop: '13px', width: '100%', overflow: 'hidden' }}>
            <svg viewBox={`0 0 ${width} ${height}`} style={{ display: 'block', width: '100%', height: 'auto' }} role="img" aria-label={title}>
              <line x1={padLeft} y1={zeroY} x2={width - padRight} y2={zeroY} stroke="#343434" strokeWidth="1" strokeDasharray="5 5" />
              <path d={path} fill="none" stroke="#f2f2f2" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              {points.map((point, index) => <circle key={`${point.label}-${index}`} cx={xFor(index)} cy={yFor(point.value)} r="4.5" fill="#fff" stroke="#000" strokeWidth="2"><title>{`${point.label} / ${valueFormatter(point.value)} / ${point.detail}`}</title></circle>)}
              <text x={padLeft} y={height - 9} fill="#666" fontSize="10">{points[0].label}</text>
              <text x={width - padRight} y={height - 9} fill="#666" fontSize="10" textAnchor="end">{latest.label}</text>
            </svg>
          </div>
          <div style={{ marginTop: '2px', color: '#555', fontSize: '9px', lineHeight: 1.5 }}>点にカーソルを合わせると、その時点の累積値と記録内容を確認できます。</div>
        </div>
      )
    }
    type PlayerTypeSummary = {
      result_id: string
      result_type_key: string
      animal_name_ja: string
      catchphrase: string
      is_public: boolean
      completed_at: string
    }


    function Profile({ recordsOnly = false }: { recordsOnly?: boolean }) {
      const navigate = useNavigate()
      const [profile, setProfile] =
        useState<any>(null)
      const [favoriteVenues, setFavoriteVenues] = useState<{ id: string; name: string }[]>([])
      const [followingCount, setFollowingCount] =
        useState(0)
      const [followerCount, setFollowerCount] =
        useState(0)
      const [
        averageAggression,
        setAverageAggression,
      ] = useState<number | null>(null)
      const [
        averageLooseness,
        setAverageLooseness,
      ] = useState<number | null>(null)
      const [ratingCount, setRatingCount] =
        useState(0)
      const [pokerResults, setPokerResults] =
        useState<PokerResult[]>([])
      const [amusementRingResults, setAmusementRingResults] =
        useState<AmusementRingResult[]>([])
      const [cashGameResults, setCashGameResults] =
        useState<CashGameResult[]>([])
      const [cashGraphMode, setCashGraphMode] = useState<'jpy' | 'bb'>('jpy')
      const [profileTab, setProfileTab] = useState<'pokerId' | 'records'>('pokerId')
      const [recordTab, setRecordTab] = useState<'tournament' | 'amusement' | 'cash'>('tournament')
      const [playerType, setPlayerType] = useState<PlayerTypeSummary | null>(null)
      useEffect(() => {
        const loadProfile = async () => {
          const {
            data: { user },
          } = await supabase.auth.getUser()
          if (!user) {
            navigate('/login')
            return
          }
          const { data, error } =
            await supabase
              .from('profiles')
              .select('*')
              .eq('id', user.id)
              .maybeSingle()
          if (error) {
            console.error(error)
            return
          }
          if (!data) {
            navigate('/profile/edit')
            return
          }
          setProfile(data)

          const { data: playerTypeRows, error: playerTypeError } = await supabase.rpc(
            'get_my_latest_player_type_v2',
          )
          if (playerTypeError) {
            console.error('プレイヤータイプ取得エラー:', playerTypeError)
          } else {
            setPlayerType((playerTypeRows?.[0] ?? null) as PlayerTypeSummary | null)
          }

          const { data: favoriteVenueLinks, error: favoriteVenueError } = await supabase
            .from('user_favorite_venues')
            .select('venue_id')
            .eq('user_id', user.id)

          if (favoriteVenueError) {
            console.error('よく行く店舗取得エラー:', favoriteVenueError)
          } else {
            const venueIds = (favoriteVenueLinks || []).map((item) => item.venue_id)
            if (venueIds.length > 0) {
              const { data: venueRows, error: venueRowsError } = await supabase
                .from('poker_venues')
                .select('id, name')
                .in('id', venueIds)
                .order('name', { ascending: true })

              if (venueRowsError) {
                console.error('店舗情報取得エラー:', venueRowsError)
              } else {
                setFavoriteVenues(venueRows || [])
              }
            } else {
              setFavoriteVenues([])
            }
          }

          const {
            data: results,
            error: resultsError,
          } = await supabase
            .from('poker_results')
            .select(
              'id, tournament_name, played_at, rank, entry_count, venue, rank_unknown, is_itm, prize_amount, prize_description, entry_fee, bullets, total_entry_fee, entry_timing, entry_bb, game_type, memo, is_public, is_featured, created_at'
            )
            .eq('user_id', user.id)
            .order('played_at', {
              ascending: false,
            })
            .order('created_at', {
              ascending: false,
            })
          if (resultsError) {
            console.error(resultsError)
          } else {
            setPokerResults(results || [])
          }
          const { data: ringResults, error: ringResultsError } = await supabase
            .from('amusement_ring_results')
            .select('id, played_at, venue, game_type, small_blind, big_blind, starting_stack, additional_stack, ending_stack, play_minutes, memo, is_public, created_at')
            .eq('user_id', user.id)
            .order('played_at', { ascending: false })
            .order('created_at', { ascending: false })
          if (ringResultsError) {
            console.error(ringResultsError)
          } else {
            setAmusementRingResults(ringResults || [])
          }
          const { data: cashResults, error: cashResultsError } = await supabase
            .from('cash_game_results')
            .select('id, played_at, play_type, record_type, venue, game_type, small_blind, big_blind, currency, buy_in_amount, cash_out_amount, profit_amount, exchange_rate_to_jpy, profit_jpy, play_minutes, memo, is_public, created_at')
            .eq('user_id', user.id)
            .order('played_at', { ascending: false })
            .order('created_at', { ascending: false })
          if (cashResultsError) {
            console.error(cashResultsError)
          } else {
            setCashGameResults(cashResults || [])
          }
          const { count: following } =
            await supabase
              .from('follows')
              .select('*', {
                count: 'exact',
                head: true,
              })
              .eq(
                'follower_id',
                user.id
              )
          setFollowingCount(
            following || 0
          )
          const { count: followers } =
            await supabase
              .from('follows')
              .select('*', {
                count: 'exact',
                head: true,
              })
              .eq(
                'following_id',
                user.id
              )
          setFollowerCount(
            followers || 0
          )
          const {
            data: ratings,
            error: ratingsError,
          } = await supabase
            .from(
              'player_style_ratings'
            )
            .select(
              'aggression, looseness'
            )
            .eq(
              'rated_user_id',
              user.id
            )
          if (ratingsError) {
            console.error(
              ratingsError
            )
            return
          }
          if (
            ratings &&
            ratings.length > 0
          ) {
            const aggressionTotal =
              ratings.reduce(
                (total, rating) =>
                  total +
                  rating.aggression,
                0
              )
            const loosenessTotal =
              ratings.reduce(
                (total, rating) =>
                  total +
                  rating.looseness,
                0
              )
            setAverageAggression(
              Math.round(
                aggressionTotal /
                  ratings.length
              )
            )
            setAverageLooseness(
              Math.round(
                loosenessTotal /
                  ratings.length
              )
            )
            setRatingCount(
              ratings.length
            )
          } else {
            setAverageAggression(null)
            setAverageLooseness(null)
            setRatingCount(0)
          }
        }
        loadProfile()
      }, [navigate])
      if (!profile) {
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
      const featuredResults = pokerResults.filter(
        (result) => result.is_public && result.is_featured
      )
      const tournamentCount = pokerResults.length
      const itmCount = pokerResults.filter((result) => result.is_itm).length
      const itmRate = tournamentCount > 0 ? (itmCount / tournamentCount) * 100 : 0
      const totalInvested = pokerResults.reduce((sum, result) => sum + (result.total_entry_fee ?? 0), 0)
      const totalEarned = pokerResults.reduce((sum, result) => sum + (result.prize_amount ?? 0), 0)
      const profit = totalEarned - totalInvested
      const roi = totalInvested > 0 ? (profit / totalInvested) * 100 : null
      const totalBullets = pokerResults.reduce((sum, result) => sum + (result.bullets ?? 1), 0)
      const averageBullets = tournamentCount > 0 ? totalBullets / tournamentCount : 0
      const hasMissingFee = pokerResults.some((result) => result.total_entry_fee === null)
      const allItm = tournamentCount > 0 && itmCount === tournamentCount
      const analysisStatus = (() => {
        if (tournamentCount < 10) {
          return {
            mark: '🔴',
            label: 'データ不足',
            text: `あと${10 - tournamentCount}件記録すると、傾向分析を確認できるようになります。`,
          }
        }
        if (allItm || hasMissingFee) {
          return {
            mark: '🟡',
            label: 'データに偏りがある可能性',
            text: '記録内容に偏りや不足があるため、分析結果は参考値として確認してください。',
          }
        }
        if (tournamentCount < 30) {
          return {
            mark: '🟡',
            label: '参考データ',
            text: '分析はできますが、まだ記録数が少ないため参考値です。30件以上で傾向が安定しやすくなります。',
          }
        }
        return {
          mark: '🟢',
          label: '分析可能',
          text: '記録数が十分に集まっています。現在のデータからプレイ傾向を分析できます。',
        }
      })()
      const canShowTrendAnalysis = tournamentCount >= 10 && !allItm
      const timingLabels: Record<string, string> = {
        early: '開始付近',
        middle: '中盤',
        late: 'レイト付近',
      }
      const timingAnalysis = ['early', 'middle', 'late'].map((timing) => {
        const results = pokerResults.filter((result) => result.entry_timing === timing)
        const count = results.length
        const itm = results.filter((result) => result.is_itm).length
        const invested = results.reduce((sum, result) => sum + (result.total_entry_fee ?? 0), 0)
        const earned = results.reduce((sum, result) => sum + (result.prize_amount ?? 0), 0)
        const timingProfit = earned - invested
        const timingRoi = invested > 0 ? (timingProfit / invested) * 100 : null
        const bullets = results.reduce((sum, result) => sum + (result.bullets ?? 1), 0)
        return {
          timing,
          label: timingLabels[timing],
          count,
          itmRate: count > 0 ? (itm / count) * 100 : null,
          roi: timingRoi,
          averageProfit: count > 0 ? timingProfit / count : null,
          averageBullets: count > 0 ? bullets / count : null,
        }
      })
      const timingGroupsWithEnoughData = timingAnalysis.filter((group) => group.count >= 5)
      const canCompareTiming = canShowTrendAnalysis && timingGroupsWithEnoughData.length >= 2
      const bestTimingByRoi = canCompareTiming
        ? [...timingGroupsWithEnoughData]
            .filter((group) => group.roi !== null)
            .sort((a, b) => (b.roi ?? -Infinity) - (a.roi ?? -Infinity))[0] ?? null
        : null
      const buildGroupStats = (results: PokerResult[]) => {
        const count = results.length
        const itm = results.filter((result) => result.is_itm).length
        const invested = results.reduce((sum, result) => sum + (result.total_entry_fee ?? 0), 0)
        const earned = results.reduce((sum, result) => sum + (result.prize_amount ?? 0), 0)
        const groupProfit = earned - invested
        const bullets = results.reduce((sum, result) => sum + (result.bullets ?? 1), 0)
        return {
          count,
          itmRate: count > 0 ? (itm / count) * 100 : null,
          roi: invested > 0 ? (groupProfit / invested) * 100 : null,
          averageProfit: count > 0 ? groupProfit / count : null,
          averageBullets: count > 0 ? bullets / count : null,
        }
      }
      const venueAnalysis = Object.entries(
        pokerResults.reduce<Record<string, PokerResult[]>>((groups, result) => {
          const venue = result.venue?.trim()
          if (!venue) return groups
          const key = venue.toLocaleLowerCase('ja-JP')
          if (!groups[key]) groups[key] = []
          groups[key].push(result)
          return groups
        }, {})
      )
        .map(([, results]) => ({ label: results[0].venue?.trim() || '会場不明', ...buildGroupStats(results) }))
        .sort((a, b) => b.count - a.count)
      const comparableVenues = venueAnalysis.filter((group) => group.count >= 5 && group.roi !== null)
      const bestVenue = comparableVenues.length >= 2
        ? [...comparableVenues].sort((a, b) => (b.roi ?? -Infinity) - (a.roi ?? -Infinity))[0]
        : null
      const buyinBands = [
        { label: '〜¥4,999', min: 0, max: 4999 },
        { label: '¥5,000〜¥9,999', min: 5000, max: 9999 },
        { label: '¥10,000〜¥19,999', min: 10000, max: 19999 },
        { label: '¥20,000〜', min: 20000, max: Infinity },
      ].map((band) => {
        const results = pokerResults.filter((result) => result.entry_fee !== null && result.entry_fee >= band.min && result.entry_fee <= band.max)
        return { label: band.label, ...buildGroupStats(results) }
      })
      const comparableBuyins = buyinBands.filter((group) => group.count >= 5 && group.roi !== null)
      const bestBuyin = comparableBuyins.length >= 2
        ? [...comparableBuyins].sort((a, b) => (b.roi ?? -Infinity) - (a.roi ?? -Infinity))[0]
        : null
      const bulletAnalysis = [
        { label: '1機', results: pokerResults.filter((result) => (result.bullets ?? 1) === 1) },
        { label: '複数機', results: pokerResults.filter((result) => (result.bullets ?? 1) >= 2) },
      ].map((group) => ({ label: group.label, ...buildGroupStats(group.results) }))
      const canCompareBullets = bulletAnalysis.every((group) => group.count >= 5 && group.roi !== null)
      const bestBulletGroup = canCompareBullets
        ? [...bulletAnalysis].sort((a, b) => (b.roi ?? -Infinity) - (a.roi ?? -Infinity))[0]
        : null
      const monthAnalysis = Object.entries(
        pokerResults.reduce<Record<string, PokerResult[]>>((groups, result) => {
          const month = result.played_at.slice(0, 7)
          if (!groups[month]) groups[month] = []
          groups[month].push(result)
          return groups
        }, {})
      )
        .map(([month, results]) => ({ month, ...buildGroupStats(results) }))
        .sort((a, b) => b.month.localeCompare(a.month))
        .slice(0, 6)
      const ringSessionCount = amusementRingResults.length
      const ringTotalMinutes = amusementRingResults.reduce((sum, result) => sum + result.play_minutes, 0)
      const ringTotalBb = amusementRingResults.reduce((sum, result) => {
        const invested = result.starting_stack + result.additional_stack
        return sum + (result.ending_stack - invested) / result.big_blind
      }, 0)
      const ringWinCount = amusementRingResults.filter((result) => {
        const invested = result.starting_stack + result.additional_stack
        return result.ending_stack > invested
      }).length
      const ringWinRate = ringSessionCount > 0 ? (ringWinCount / ringSessionCount) * 100 : 0
      const ringBbPerHour = ringTotalMinutes > 0 ? ringTotalBb / (ringTotalMinutes / 60) : null
      const ringAverageBb = ringSessionCount > 0 ? ringTotalBb / ringSessionCount : 0
      const formatBb = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(1)}BB`
      const formatHours = (minutes: number) => {
        const hours = Math.floor(minutes / 60)
        const mins = minutes % 60
        return mins === 0 ? `${hours}時間` : `${hours}時間${mins}分`
      }
      const formatYen = (value: number) => `${value < 0 ? '-' : ''}¥${Math.abs(value).toLocaleString()}`
      const formatPercent = (value: number) => `${value.toFixed(1)}%`
      const cashStats = (rows: CashGameResult[]) => {
        const count = rows.length
        const minutes = rows.reduce((sum, r) => sum + r.play_minutes, 0)
        const yen = rows.reduce((sum, r) => sum + Number(r.profit_jpy), 0)
        const bb = rows.reduce((sum, r) => sum + Number(r.profit_amount) / Number(r.big_blind), 0)
        const wins = rows.filter((r) => Number(r.profit_amount) > 0).length
        return {
          count, minutes, yen, bb,
          winRate: count ? wins / count * 100 : 0,
          bbPerHour: minutes ? bb / (minutes / 60) : null,
        }
      }
      const cashAll = cashStats(cashGameResults)
      const cashLive = cashStats(cashGameResults.filter((r) => r.play_type === 'live'))
      const cashOnline = cashStats(cashGameResults.filter((r) => r.play_type === 'online'))
      const cashGroups = (keyFn: (r: CashGameResult) => string) =>
        Object.entries(cashGameResults.reduce<Record<string, CashGameResult[]>>((groups, r) => {
          const key = keyFn(r)
          if (!groups[key]) groups[key] = []
          groups[key].push(r)
          return groups
        }, {}))
          .map(([label, rows]) => ({ label, ...cashStats(rows) }))
          .sort((a, b) => b.count - a.count)
      const cashVenueGroups = cashGroups((r) => `${r.venue} ・ ${r.play_type === 'live' ? 'ライブ' : 'オンライン'}`)
      const cashGameGroups = cashGroups((r) => r.game_type || 'その他')
      const cashRateGroups = cashGroups((r) => `${r.currency} ${Number(r.small_blind).toLocaleString()}/${Number(r.big_blind).toLocaleString()}`)
      const cashMonthGroups = cashGroups((r) => r.played_at.slice(0, 7))
        .sort((a, b) => b.label.localeCompare(a.label))
        .slice(0, 6)
      const cashBb = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(1)}BB`
      const cashBbh = (value: number | null) => value === null ? '—' : `${value >= 0 ? '+' : ''}${value.toFixed(1)}BB/h`
      const shortDate = (date: string) => {
        const [, month, day] = date.split('-')
        return `${Number(month)}/${Number(day)}`
      }
      const tournamentTrend = [...pokerResults].sort((a, b) => a.played_at.localeCompare(b.played_at)).reduce<TrendPoint[]>((points, result) => {
        const previous = points.length ? points[points.length - 1].value : 0
        const resultProfit = Number(result.prize_amount ?? 0) - Number(result.total_entry_fee ?? 0)
        points.push({ label: shortDate(result.played_at), value: previous + resultProfit, detail: `${result.tournament_name} / 今回 ${formatYen(Math.round(resultProfit))}` })
        return points
      }, [])
      const ringTrend = [...amusementRingResults].sort((a, b) => a.played_at.localeCompare(b.played_at)).reduce<TrendPoint[]>((points, result) => {
        const previous = points.length ? points[points.length - 1].value : 0
        const invested = Number(result.starting_stack) + Number(result.additional_stack)
        const sessionBb = (Number(result.ending_stack) - invested) / Number(result.big_blind)
        points.push({ label: shortDate(result.played_at), value: previous + sessionBb, detail: `${result.venue} / 今回 ${formatBb(sessionBb)}` })
        return points
      }, [])
      const cashTrendJpy = [...cashGameResults].sort((a, b) => a.played_at.localeCompare(b.played_at)).reduce<TrendPoint[]>((points, result) => {
        const previous = points.length ? points[points.length - 1].value : 0
        const sessionProfit = Number(result.profit_jpy)
        points.push({ label: shortDate(result.played_at), value: previous + sessionProfit, detail: `${result.venue} / 今回 ${formatYen(Math.round(sessionProfit))}` })
        return points
      }, [])
      const cashTrendBb = [...cashGameResults].sort((a, b) => a.played_at.localeCompare(b.played_at)).reduce<TrendPoint[]>((points, result) => {
        const previous = points.length ? points[points.length - 1].value : 0
        const sessionBb = Number(result.profit_amount) / Number(result.big_blind)
        points.push({ label: shortDate(result.played_at), value: previous + sessionBb, detail: `${result.venue} / 今回 ${cashBb(sessionBb)}` })
        return points
      }, [])
      return (
        <main className="app">
          <div
            className="card"
            style={{
              paddingTop: 0,
            }}
          >
            {!recordsOnly && (<>
            {/* 上部ヘッダー */}
            <header
              style={{
                position: 'sticky',
                top: 0,
                zIndex: 20,
                margin: '0 -20px',
                padding: '15px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent:
                  'space-between',
                background:
                  'rgba(0, 0, 0, 0.92)',
                borderBottom:
                  '1px solid #242424',
                backdropFilter:
                  'blur(14px)',
                WebkitBackdropFilter:
                  'blur(14px)',
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: '19px',
                    fontWeight: 800,
                    letterSpacing:
                      '-0.4px',
                  }}
                >
                  プロフィール
                </div>
                <div
                  style={{
                    marginTop: '2px',
                    color: '#666',
                    fontSize: '11px',
                  }}
                >
                  Poker ID
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                onClick={() => navigate('/settings')}
                style={{ width: 'auto', padding: '8px 12px', background: 'transparent', color: '#fff', border: '1px solid #3a3a3a', borderRadius: '999px', fontSize: '13px', fontWeight: 700 }}
              >
                設定
              </button>
              <button
                onClick={() =>
                  navigate(
                    '/profile/edit'
                  )
                }
                style={{
                  width: 'auto',
                  padding:
                    '8px 15px',
                  background:
                    'transparent',
                  color: '#fff',
                  border:
                    '1px solid #3a3a3a',
                  borderRadius:
                    '999px',
                  fontSize: '13px',
                  fontWeight: 700,
                }}
              >
                編集
              </button>
              </div>
            </header>
            {/* プロフィール上部 */}
            <section
              style={{
                padding:
                  '26px 0 22px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems:
                    'flex-start',
                  justifyContent:
                    'space-between',
                  gap: '20px',
                }}
              >
                {profile.avatar_url ? (
                  <img
                    src={
                      profile.avatar_url
                    }
                    alt={`${profile.display_name}のプロフィール画像`}
                    style={{
                      width: '92px',
                      height: '92px',
                      borderRadius:
                        '50%',
                      objectFit:
                        'cover',
                      border:
                        '2px solid #333',
                      flexShrink: 0,
                    }}
                  />
                ) : (
                  <div
                    style={{
                      width: '92px',
                      height: '92px',
                      borderRadius:
                        '50%',
                      background:
                        '#171717',
                      border:
                        '2px solid #333',
                      display: 'flex',
                      alignItems:
                        'center',
                      justifyContent:
                        'center',
                      fontSize: '35px',
                      flexShrink: 0,
                    }}
                  >
                    ♠
                  </div>
                )}
                <div
                  style={{
                    flex: 1,
                    display: 'flex',
                    justifyContent:
                      'flex-end',
                    gap: '30px',
                    paddingTop:
                      '17px',
                  }}
                >
                  <button
                    onClick={() =>
                      navigate(
                        `/player/${profile.id}/following`
                      )
                    }
                    style={{
                      width: 'auto',
                      padding: 0,
                      background:
                        'transparent',
                      color: '#fff',
                      borderRadius: 0,
                      textAlign:
                        'center',
                    }}
                  >
                    <div
                      style={{
                        fontSize:
                          '18px',
                        fontWeight: 800,
                      }}
                    >
                      {followingCount}
                    </div>
                    <div
                      style={{
                        marginTop:
                          '4px',
                        color: '#777',
                        fontSize:
                          '12px',
                        fontWeight: 500,
                      }}
                    >
                      フォロー
                    </div>
                  </button>
                  <button
                    onClick={() =>
                      navigate(
                        `/player/${profile.id}/followers`
                      )
                    }
                    style={{
                      width: 'auto',
                      padding: 0,
                      background:
                        'transparent',
                      color: '#fff',
                      borderRadius: 0,
                      textAlign:
                        'center',
                    }}
                  >
                    <div
                      style={{
                        fontSize:
                          '18px',
                        fontWeight: 800,
                      }}
                    >
                      {followerCount}
                    </div>
                    <div
                      style={{
                        marginTop:
                          '4px',
                        color: '#777',
                        fontSize:
                          '12px',
                        fontWeight: 500,
                      }}
                    >
                      フォロワー
                    </div>
                  </button>
                </div>
              </div>
              {/* 名前 */}
              <div
                style={{
                  marginTop: '17px',
                }}
              >
                <h1
                  style={{
                    margin: 0,
                    fontSize: '23px',
                    lineHeight: 1.25,
                    fontWeight: 800,
                    letterSpacing:
                      '-0.5px',
                  }}
                >
                  {profile.display_name}
                </h1>
                <div
                  style={{
                    marginTop: '4px',
                    color: '#777',
                    fontSize: '14px',
                  }}
                >
                  @{profile.poker_id}
                </div>
              </div>
              {/* 自己紹介 */}
              <p
                style={{
                  margin:
                    '17px 0 0',
                  color: profile.bio
                    ? '#e8e8e8'
                    : '#777',
                  fontSize: '14px',
                  lineHeight: 1.65,
                  whiteSpace:
                    'pre-wrap',
                  wordBreak:
                    'break-word',
                }}
              >
                {profile.bio ||
                  '自己紹介はまだありません'}
              </p>
              {/* ポーカー情報 */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '8px',
                  marginTop: '17px',
                }}
              >
                <div
                  style={{
                    padding:
                      '7px 11px',
                    background: '#111',
                    border:
                      '1px solid #292929',
                    borderRadius:
                      '999px',
                    color: '#bbb',
                    fontSize: '12px',
                  }}
                >
                  ♠ ポーカー歴{' '}
                  <strong
                    style={{
                      color: '#fff',
                    }}
                  >
                    {profile.poker_years ||
                      '-'}
                    年
                  </strong>
                </div>
                <div
                  style={{
                    padding:
                      '7px 11px',
                    background: '#111',
                    border:
                      '1px solid #292929',
                    borderRadius:
                      '999px',
                    color: '#bbb',
                    fontSize: '12px',
                  }}
                >
                  メイン{' '}
                  <strong
                    style={{
                      color: '#fff',
                    }}
                  >
                    {profile.main_game ||
                      '-'}
                  </strong>
                </div>
                {favoriteVenues.map((venue) => (
                  <div
                    key={venue.id}
                    style={{
                      padding: '7px 11px',
                      background: '#111',
                      border: '1px solid #292929',
                      borderRadius: '999px',
                      color: '#bbb',
                      fontSize: '12px',
                    }}
                  >
                    📍 よく行く店舗{' '}
                    <strong style={{ color: '#fff' }}>{venue.name}</strong>
                  </div>
                ))}
              </div>
            </section>
            </>)}
            {recordsOnly && (
              <section style={{ padding: '18px 0 10px' }}>
                <button type="button" onClick={() => navigate('/tools')} style={{ width: 'auto', padding: 0, background: 'transparent', color: '#aaa', fontSize: 13 }}>← ポーカーツールに戻る</button>
                <h1 style={{ fontSize: 24, margin: '18px 0 8px' }}>実戦記録</h1>
                <div style={{ background: '#121212', border: '1px solid #303030', borderRadius: 14, padding: 16, lineHeight: 1.7 }}>
                  <strong>すべてのプレイが、あなたのデータになる。</strong>
                  <p style={{ color: '#aaa', fontSize: 13, margin: '6px 0 0' }}>勝った日も、負けた日も。結果に関係なく毎回記録することで、収支の推移やプレイ傾向をより正確に分析できます。</p>
                </div>
              </section>
            )}
            {!recordsOnly && (<>
            {/* プロフィールメニュー */}
            <div
              style={{
                margin: '0 -20px',
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                borderTop: '1px solid #242424',
                borderBottom: '1px solid #242424',
              }}
            >
              {[
                { key: 'pokerId', label: 'Poker ID' },
                { key: 'records', label: '記録' },
              ].map((tab) => {
                const active = profileTab === tab.key
                return (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => tab.key === 'records' ? navigate('/results') : setProfileTab('pokerId')}
                    style={{
                      position: 'relative',
                      padding: '15px 8px',
                      background: 'transparent',
                      color: active ? '#fff' : '#666',
                      borderRadius: 0,
                      fontSize: '14px',
                      fontWeight: active ? 700 : 600,
                    }}
                  >
                    {tab.label}
                    {active && (
                      <span
                        style={{
                          position: 'absolute',
                          left: '30%',
                          right: '30%',
                          bottom: 0,
                          height: '3px',
                          borderRadius: '999px',
                          background: '#fff',
                        }}
                      />
                    )}
                  </button>
                )
              })}
              <button
                type="button"
                onClick={() => navigate('/timeline')}
                style={{
                  position: 'relative',
                  padding: '15px 8px',
                  background: 'transparent',
                  color: '#666',
                  borderRadius: 0,
                  fontSize: '14px',
                  fontWeight: 600,
                }}
              >
                投稿
              </button>
            </div>
            </>)}
            {recordsOnly && (
              <div
                style={{
                  margin: '16px 0 4px',
                  padding: '4px',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
                  gap: '4px',
                  background: '#0d0d0d',
                  border: '1px solid #242424',
                  borderRadius: '14px',
                }}
              >
                {[
                  { key: 'tournament', label: 'トーナメント' },
                  { key: 'amusement', label: 'アミューズ' },
                  { key: 'cash', label: 'キャッシュ' },
                ].map((tab) => {
                  const active = recordTab === tab.key
                  return (
                    <button
                      key={tab.key}
                      type="button"
                      onClick={() => setRecordTab(tab.key as 'tournament' | 'amusement' | 'cash')}
                      style={{
                        padding: '10px 5px',
                        background: active ? '#fff' : 'transparent',
                        color: active ? '#000' : '#777',
                        borderRadius: '10px',
                        fontSize: '11px',
                        fontWeight: 800,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {tab.label}
                    </button>
                  )
                })}
              </div>
            )}
            {!recordsOnly && profileTab === 'pokerId' && (
              <>
            {/* 主なトーナメント実績 */}
          {featuredResults.length > 0 && (
            <section
              style={{
                padding: '23px 0',
                borderBottom: '1px solid #242424',
              }}
            >
              <div style={{ fontSize: '17px', fontWeight: 800 }}>
                主なトーナメント実績
              </div>
              <div style={{ marginTop: '5px', color: '#666', fontSize: '12px' }}>
                公開中の記録から選んだ主な実績
              </div>
              <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {featuredResults.map((result) => (
                  <div
                    key={result.id}
                    style={{
                      padding: '16px',
                      background: '#0d0d0d',
                      border: '1px solid #303030',
                      borderRadius: '16px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start' }}>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: '15px', fontWeight: 800, lineHeight: 1.4, wordBreak: 'break-word' }}>
                          {result.tournament_name}
                        </div>
                        <div style={{ marginTop: '5px', color: '#777', fontSize: '11px' }}>
                          {new Date(`${result.played_at}T00:00:00`).toLocaleDateString('ja-JP')}
                          {result.venue ? ` ・ ${result.venue}` : ''}
                        </div>
                      </div>
                      <div style={{ padding: '5px 9px', borderRadius: '999px', background: '#171717', border: '1px solid #333', fontSize: '11px', fontWeight: 800, flexShrink: 0 }}>
                        ★ 実績
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '13px' }}>
                      <div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', fontSize: '12px', fontWeight: 800 }}>
                        {result.rank_unknown ? '順位不明' : result.rank !== null ? `${result.rank}位` : '順位不明'}
                        {result.entry_count !== null ? ` / ${result.entry_count}人` : ''}
                      </div>
                      {result.is_itm && (
                        <div style={{ padding: '6px 9px', background: '#101a14', border: '1px solid #24402d', borderRadius: '8px', color: '#8fcf9f', fontSize: '11px', fontWeight: 800 }}>
                          ITM
                        </div>
                      )}
                      {result.prize_amount !== null && result.prize_amount > 0 && (
                        <div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', fontSize: '11px', fontWeight: 700 }}>
                          プライズ相当額 ¥{result.prize_amount.toLocaleString()}
                        </div>
                      )}
                    </div>
                    {result.prize_description && (
                      <div style={{ marginTop: '10px', color: '#999', fontSize: '11px', lineHeight: 1.5 }}>
                        プライズ内容：{result.prize_description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* プレイヤータイプ診断 */}
          <section
            style={{
              padding: '23px 0',
              borderBottom: '1px solid #242424',
            }}
          >
            <div style={{ fontSize: '17px', fontWeight: 800 }}>
              プレイヤータイプ
            </div>
            <div style={{ marginTop: '5px', color: '#666', fontSize: '12px' }}>
              50問の診断から見たあなたのプレースタイル
            </div>

            {playerType ? (
              <button
                type="button"
                onClick={() => navigate(`/player-type?result=${playerType.result_id}`)}
                style={{
                  width: '100%',
                  marginTop: '15px',
                  padding: '17px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  background: '#0d0d0d',
                  border: '1px solid #3b3423',
                  borderRadius: '16px',
                  color: '#fff',
                  textAlign: 'left',
                }}
              >
                <div
                  style={{
                    width: 'clamp(100px, 27vw, 132px)',
                    aspectRatio: '1 / 1',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    background: '#15130e',
                    border: '1px solid #403821',
                    borderRadius: '16px',
                    overflow: 'hidden',
                  }}
                >
                  <img
                    src={`/animals/${playerType.result_type_key}.png`}
                    alt={`${playerType.animal_name_ja}の3Dマスコット`}
                    loading="lazy"
                    style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '15px', display: 'block' }}
                  />
                </div>

                <div style={{ minWidth: 0, flex: 1 }}>
                  <div
                    style={{
                      color: '#d6b45d',
                      fontSize: '11px',
                      fontWeight: 800,
                      letterSpacing: '.08em',
                    }}
                  >
                    YOUR PLAYER TYPE
                  </div>
                  <div
                    style={{
                      marginTop: '3px',
                      fontSize: '20px',
                      fontWeight: 900,
                    }}
                  >
                    {playerType.animal_name_ja}
                  </div>
                  <div
                    style={{
                      marginTop: '4px',
                      color: '#aaa',
                      fontSize: '12px',
                      lineHeight: 1.5,
                    }}
                  >
                    {playerType.catchphrase}
                  </div>
                  <div
                    style={{
                      marginTop: '9px',
                      color: '#d6b45d',
                      fontSize: '11px',
                      fontWeight: 800,
                    }}
                  >
                    診断結果を見る →
                  </div>
                </div>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => navigate('/player-type')}
                style={{
                  width: '100%',
                  marginTop: '15px',
                  padding: '17px',
                  background: '#0d0d0d',
                  border: '1px solid #303030',
                  borderRadius: '16px',
                  color: '#fff',
                  textAlign: 'left',
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: 800 }}>
                  プレイヤータイプを診断する
                </div>
                <div style={{ marginTop: '5px', color: '#777', fontSize: '12px', lineHeight: 1.5 }}>
                  50問に答えて、36種類の動物から自分のタイプを診断
                </div>
              </button>
            )}
          </section>

          {/* プレイスタイル */}
            <section
              style={{
                padding:
                  '25px 0 15px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems:
                    'center',
                  justifyContent:
                    'space-between',
                  gap: '15px',
                }}
              >
                <div>
                  <h2
                    style={{
                      margin: 0,
                      fontSize:
                        '18px',
                      fontWeight: 800,
                    }}
                  >
                    プレイスタイル
                  </h2>
                  <div
                    style={{
                      marginTop:
                        '5px',
                      color: '#666',
                      fontSize:
                        '12px',
                    }}
                  >
                    他のプレイヤーから見たあなた
                  </div>
                </div>
                {ratingCount > 0 && (
                  <div
                    style={{
                      padding:
                        '6px 10px',
                      background: '#111',
                      border:
                        '1px solid #292929',
                      borderRadius:
                        '999px',
                      color: '#999',
                      fontSize:
                        '11px',
                    }}
                  >
                    {ratingCount}人が評価
                  </div>
                )}
              </div>
              {/* 評価0人 */}
              {ratingCount === 0 && (
                <div
                  style={{
                    marginTop: '18px',
                    padding:
                      '35px 20px',
                    background:
                      '#0d0d0d',
                    border:
                      '1px solid #242424',
                    borderRadius:
                      '16px',
                    textAlign:
                      'center',
                  }}
                >
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      margin:
                        '0 auto 13px',
                      display: 'flex',
                      alignItems:
                        'center',
                      justifyContent:
                        'center',
                      background:
                        '#171717',
                      border:
                        '1px solid #292929',
                      borderRadius:
                        '50%',
                      fontSize:
                        '21px',
                    }}
                  >
                    ♠
                  </div>
                  <div
                    style={{
                      fontSize:
                        '14px',
                      fontWeight: 700,
                    }}
                  >
                    まだ評価がありません
                  </div>
                  <div
                    style={{
                      marginTop:
                        '6px',
                      color: '#666',
                      fontSize:
                        '12px',
                      lineHeight: 1.5,
                    }}
                  >
                    一緒にプレイした人から
                    <br />
                    評価が集まると表示されます
                  </div>
                </div>
              )}
              {/* 評価1〜2人 */}
              {ratingCount > 0 &&
                ratingCount < 3 && (
                  <div
                    style={{
                      marginTop:
                        '18px',
                      padding:
                        '27px 18px',
                      border:
                        '1px solid #292929',
                      borderRadius:
                        '16px',
                      background:
                        '#0d0d0d',
                      textAlign:
                        'center',
                    }}
                  >
                    <div
                      style={{
                        width: '46px',
                        height: '46px',
                        margin:
                          '0 auto 14px',
                        display: 'flex',
                        alignItems:
                          'center',
                        justifyContent:
                          'center',
                        background:
                          '#171717',
                        border:
                          '1px solid #292929',
                        borderRadius:
                          '50%',
                        fontSize:
                          '20px',
                      }}
                    >
                      ◌
                    </div>
                    <div
                      style={{
                        fontSize:
                          '15px',
                        fontWeight: 700,
                      }}
                    >
                      評価データを集計中
                    </div>
                    <div
                      style={{
                        marginTop:
                          '10px',
                        fontSize:
                          '13px',
                        color: '#aaa',
                      }}
                    >
                      現在 {ratingCount}人
                    </div>
                    <div
                      style={{
                        marginTop:
                          '7px',
                        fontSize:
                          '12px',
                        color: '#666',
                        lineHeight: 1.5,
                      }}
                    >
                      匿名性を保つため、
                      3人以上の評価が集まると
                      <br />
                      プレイスタイルが表示されます
                    </div>
                    <div
                      style={{
                        width: '180px',
                        maxWidth: '100%',
                        height: '5px',
                        margin:
                          '18px auto 0',
                        background:
                          '#222',
                        borderRadius:
                          '999px',
                        overflow:
                          'hidden',
                      }}
                    >
                      <div
                        style={{
                          width: `${
                            (ratingCount /
                              3) *
                            100
                          }%`,
                          height: '100%',
                          background:
                            '#fff',
                          borderRadius:
                            '999px',
                        }}
                      />
                    </div>
                    <div
                      style={{
                        marginTop:
                          '7px',
                        color: '#555',
                        fontSize:
                          '10px',
                      }}
                    >
                      {ratingCount} / 3
                    </div>
                  </div>
                )}
              {/* 評価3人以上 */}
              {ratingCount >= 3 &&
                averageAggression !==
                  null &&
                averageLooseness !==
                  null && (
                  <div
                    style={{
                      marginTop:
                        '18px',
                      padding: '18px',
                      background:
                        '#0d0d0d',
                      border:
                        '1px solid #292929',
                      borderRadius:
                        '16px',
                    }}
                  >
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns:
                          '34px 1fr',
                        gridTemplateRows:
                          'auto auto',
                        columnGap: '8px',
                        alignItems:
                          'stretch',
                      }}
                    >
                      {/* 左縦軸 */}
                      <div
                        style={{
                          gridColumn: 1,
                          gridRow: 1,
                          position:
                            'relative',
                          minHeight: 0,
                        }}
                      >
                        <span
                          style={{
                            position:
                              'absolute',
                            top: 0,
                            left: '50%',
                            transform:
                              'translateX(-50%)',
                            color: '#777',
                            fontSize:
                              '9px',
                            fontWeight: 700,
                            writingMode:
                              'vertical-rl',
                          }}
                        >
                          TIGHT
                        </span>
                        <span
                          style={{
                            position:
                              'absolute',
                            bottom: 0,
                            left: '50%',
                            transform:
                              'translateX(-50%)',
                            color: '#777',
                            fontSize:
                              '9px',
                            fontWeight: 700,
                            writingMode:
                              'vertical-rl',
                          }}
                        >
                          LOOSE
                        </span>
                      </div>
                      {/* グラフ */}
                      <div
                        style={{
                          gridColumn: 2,
                          gridRow: 1,
                          position:
                            'relative',
                          width: '100%',
                          aspectRatio:
                            '1 / 1',
                          border:
                            '1px solid #3a3a3a',
                          borderRadius:
                            '12px',
                          boxSizing:
                            'border-box',
                          background: '#111',
                          overflow:
                            'hidden',
                        }}
                      >
                        {/* 4象限背景 */}
                        <div
                          style={{
                            position:
                              'absolute',
                            left: 0,
                            top: 0,
                            width: '50%',
                            height: '50%',
                            background:
                              'rgba(80, 130, 255, 0.05)',
                          }}
                        />
                        <div
                          style={{
                            position:
                              'absolute',
                            right: 0,
                            top: 0,
                            width: '50%',
                            height: '50%',
                            background:
                              'rgba(80, 220, 140, 0.05)',
                          }}
                        />
                        <div
                          style={{
                            position:
                              'absolute',
                            left: 0,
                            bottom: 0,
                            width: '50%',
                            height: '50%',
                            background:
                              'rgba(255, 210, 80, 0.05)',
                          }}
                        />
                        <div
                          style={{
                            position:
                              'absolute',
                            right: 0,
                            bottom: 0,
                            width: '50%',
                            height: '50%',
                            background:
                              'rgba(255, 80, 100, 0.05)',
                          }}
                        />
                        {/* 中央線 */}
                        <div
                          style={{
                            position:
                              'absolute',
                            left: '50%',
                            top: 0,
                            bottom: 0,
                            width: '1px',
                            background:
                              '#333',
                          }}
                        />
                        <div
                          style={{
                            position:
                              'absolute',
                            top: '50%',
                            left: 0,
                            right: 0,
                            height: '1px',
                            background:
                              '#333',
                          }}
                        />
                        {/* 象限名 */}
                        <div
                          style={{
                            position:
                              'absolute',
                            left: '25%',
                            top: '25%',
                            transform:
                              'translate(-50%, -50%)',
                            color:
                              '#53627d',
                            fontSize:
                              '14px',
                            fontWeight: 800,
                          }}
                        >
                          TP
                        </div>
                        <div
                          style={{
                            position:
                              'absolute',
                            left: '75%',
                            top: '25%',
                            transform:
                              'translate(-50%, -50%)',
                            color:
                              '#527a61',
                            fontSize:
                              '14px',
                            fontWeight: 800,
                          }}
                        >
                          TAG
                        </div>
                        <div
                          style={{
                            position:
                              'absolute',
                            left: '25%',
                            top: '75%',
                            transform:
                              'translate(-50%, -50%)',
                            color:
                              '#7d714d',
                            fontSize:
                              '14px',
                            fontWeight: 800,
                          }}
                        >
                          LP
                        </div>
                        <div
                          style={{
                            position:
                              'absolute',
                            left: '75%',
                            top: '75%',
                            transform:
                              'translate(-50%, -50%)',
                            color:
                              '#80525a',
                            fontSize:
                              '14px',
                            fontWeight: 800,
                          }}
                        >
                          LAG
                        </div>
                        {/* 平均評価 */}
                        <div
                          style={{
                            position:
                              'absolute',
                            left: `${averageAggression}%`,
                            top: `${averageLooseness}%`,
                            width: '20px',
                            height: '20px',
                            borderRadius:
                              '50%',
                            background:
                              '#fff',
                            border:
                              '4px solid #000',
                            boxShadow:
                              '0 0 0 2px rgba(255,255,255,0.35)',
                            transform:
                              'translate(-50%, -50%)',
                            boxSizing:
                              'border-box',
                          }}
                        />
                      </div>
                      {/* 横軸 */}
                      <div
                        style={{
                          gridColumn: 2,
                          gridRow: 2,
                          display: 'flex',
                          justifyContent:
                            'space-between',
                          paddingTop:
                            '8px',
                          color: '#777',
                          fontSize:
                            '9px',
                          fontWeight: 700,
                        }}
                      >
                        <span>
                          PASSIVE
                        </span>
                        <span>
                          AGGRESSIVE
                        </span>
                      </div>
                    </div>
                    <div
                      style={{
                        marginTop:
                          '17px',
                        paddingTop:
                          '14px',
                        borderTop:
                          '1px solid #222',
                        color: '#777',
                        fontSize:
                          '11px',
                        textAlign:
                          'center',
                      }}
                    >
                      {ratingCount}
                      人の匿名評価から算出
                    </div>
                  </div>
                )}
            </section>
              </>
            )}
            {recordsOnly && recordTab === 'cash' && (
              <>
            {/* キャッシュゲーム記録 */}
            <section style={{ marginTop: '10px', padding: '23px 0', borderTop: '1px solid #242424' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '17px', fontWeight: 800 }}>キャッシュゲーム</div>
                  <div style={{ marginTop: '5px', color: '#666', fontSize: '12px' }}>ライブ・オンラインの収支を記録・分析</div>
                </div>
                <button onClick={() => navigate('/profile/cash-game/new')} style={{ width: 'auto', padding: '8px 13px', background: '#fff', color: '#000', borderRadius: '999px', fontSize: '12px', fontWeight: 800, flexShrink: 0 }}>
                  ＋ 記録を追加
                </button>
              </div>
              {cashAll.count === 0 ? (
                <div style={{ marginTop: '16px', padding: '25px 20px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '16px', textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700 }}>まだキャッシュゲーム記録がありません</div>
                  <div style={{ marginTop: '6px', color: '#666', fontSize: '12px', lineHeight: 1.6 }}>記録すると、円換算収支・BB収支・BB/hなどを自動集計します。</div>
                </div>
              ) : (
                <>
                  <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                    <div style={{ fontSize: '14px', fontWeight: 800 }}>収支推移</div>
                    <div style={{ display: 'flex', padding: '3px', background: '#111', border: '1px solid #292929', borderRadius: '999px' }}>
                      <button type="button" onClick={() => setCashGraphMode('jpy')} style={{ width: 'auto', padding: '6px 10px', borderRadius: '999px', background: cashGraphMode === 'jpy' ? '#fff' : 'transparent', color: cashGraphMode === 'jpy' ? '#000' : '#777', fontSize: '10px', fontWeight: 800 }}>円換算</button>
                      <button type="button" onClick={() => setCashGraphMode('bb')} style={{ width: 'auto', padding: '6px 10px', borderRadius: '999px', background: cashGraphMode === 'bb' ? '#fff' : 'transparent', color: cashGraphMode === 'bb' ? '#000' : '#777', fontSize: '10px', fontWeight: 800 }}>BB</button>
                    </div>
                  </div>
                  <div style={{ marginTop: '10px' }}>
                    <CumulativeTrendChart title={cashGraphMode === 'jpy' ? '累積収支' : '累積BB収支'} subtitle={cashGraphMode === 'jpy' ? '保存済み為替レートで円換算' : '各記録のBB収支を累積'} points={cashGraphMode === 'jpy' ? cashTrendJpy : cashTrendBb} valueFormatter={cashGraphMode === 'jpy' ? (value) => formatYen(Math.round(value)) : cashBb} />
                  </div>
                  <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '9px' }}>
                    {[
                      ['記録数', `${cashAll.count}件`],
                      ['総プレイ時間', formatHours(cashAll.minutes)],
                      ['総収支', formatYen(Math.round(cashAll.yen))],
                      ['総BB収支', cashBb(cashAll.bb)],
                      ['勝率', `${cashAll.winRate.toFixed(1)}%`],
                      ['BB / h', cashBbh(cashAll.bbPerHour)],
                    ].map(([label, value]) => (
                      <div key={label} style={{ padding: '14px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '14px' }}>
                        <div style={{ color: '#777', fontSize: '10px', fontWeight: 700 }}>{label}</div>
                        <div style={{ marginTop: '6px', color: '#fff', fontSize: '17px', fontWeight: 800, wordBreak: 'break-word' }}>{value}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: '20px', fontSize: '14px', fontWeight: 800 }}>ライブ / オンライン別</div>
                  <div style={{ marginTop: '10px', display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '9px' }}>
                    {[['ライブ', cashLive], ['オンライン', cashOnline]].map(([label, raw]) => {
                      const stats = raw as ReturnType<typeof cashStats>
                      return (
                        <div key={label as string} style={{ padding: '13px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '14px' }}>
                          <div style={{ fontSize: '12px', fontWeight: 800 }}>{label as string}</div>
                          <div style={{ marginTop: '8px', fontSize: '15px', fontWeight: 800 }}>{formatYen(Math.round(stats.yen))}</div>
                          <div style={{ marginTop: '5px', color: '#888', fontSize: '10px', lineHeight: 1.6 }}>{stats.count}件 ・ {cashBb(stats.bb)}<br />{cashBbh(stats.bbPerHour)}</div>
                        </div>
                      )
                    })}
                  </div>
                  {[
                    ['場所・サイト別', cashVenueGroups],
                    ['ゲーム別', cashGameGroups],
                    ['レート別', cashRateGroups],
                    ['月別', cashMonthGroups],
                  ].map(([title, rawGroups]) => {
                    const groups = rawGroups as ReturnType<typeof cashGroups>
                    return (
                      <div key={title as string} style={{ marginTop: '20px' }}>
                        <div style={{ fontSize: '14px', fontWeight: 800 }}>{title as string}</div>
                        <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {groups.map((group) => (
                            <div key={group.label} style={{ padding: '12px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '12px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                                <strong style={{ fontSize: '11px' }}>{group.label}</strong>
                                <span style={{ color: '#666', fontSize: '9px' }}>{group.count}件</span>
                              </div>
                              <div style={{ marginTop: '8px', color: '#aaa', fontSize: '10px', lineHeight: 1.6 }}>
                                {formatYen(Math.round(group.yen))} ・ {cashBb(group.bb)} ・ {cashBbh(group.bbPerHour)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                  <div style={{ marginTop: '22px', fontSize: '14px', fontWeight: 800 }}>記録一覧</div>
                  <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {cashGameResults.map((result) => {
                      const bbResult = Number(result.profit_amount) / Number(result.big_blind)
                      const bbh = result.play_minutes ? bbResult / (result.play_minutes / 60) : null
                      return (
                        <div key={result.id} style={{ padding: '16px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '16px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start' }}>
                            <div style={{ minWidth: 0 }}>
                              <div style={{ fontSize: '15px', fontWeight: 800 }}>{result.venue}</div>
                              <div style={{ marginTop: '5px', color: '#666', fontSize: '11px', lineHeight: 1.5 }}>
                                {new Date(`${result.played_at}T00:00:00`).toLocaleDateString('ja-JP')} ・ {result.play_type === 'live' ? 'ライブ' : 'オンライン'}
                                {result.play_type === 'online' && result.record_type === 'daily' ? '・1日まとめ' : ''} ・ {result.game_type} ・ {result.currency} {Number(result.small_blind).toLocaleString()}/{Number(result.big_blind).toLocaleString()}
                              </div>
                              <div style={{ marginTop: '7px', display: 'inline-flex', padding: '4px 8px', background: result.is_public ? '#101a14' : '#171717', border: result.is_public ? '1px solid #24402d' : '1px solid #303030', borderRadius: '999px', color: result.is_public ? '#8fcf9f' : '#999', fontSize: '10px', fontWeight: 700 }}>
                                {result.is_public ? '🌐 公開' : '🔒 非公開'}
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', flexShrink: 0 }}>
                              <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '14px', fontWeight: 800 }}>{formatYen(Math.round(Number(result.profit_jpy)))}</div>
                                <div style={{ marginTop: '4px', color: '#888', fontSize: '10px' }}>{cashBb(bbResult)}</div>
                              </div>
                              <button
                                type="button"
                                aria-label="キャッシュゲーム記録を編集"
                                onClick={() => navigate(`/profile/cash-game/${result.id}/edit`)}
                                style={{
                                  width: '34px',
                                  height: '34px',
                                  padding: 0,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  background: '#151515',
                                  color: '#bbb',
                                  border: '1px solid #303030',
                                  borderRadius: '50%',
                                  fontSize: '18px',
                                  fontWeight: 800,
                                  lineHeight: 1,
                                  flexShrink: 0,
                                }}
                              >
                                ⋯
                              </button>
                            </div>
                          </div>
                          <div style={{ marginTop: '13px', display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '7px' }}>
                            {[
                              ['元通貨収支', `${Number(result.profit_amount) >= 0 ? '+' : ''}${Number(result.profit_amount).toLocaleString()} ${result.currency}`],
                              ['プレイ時間', formatHours(result.play_minutes)],
                              ['BB / h', cashBbh(bbh)],
                            ].map(([label, value]) => (
                              <div key={label} style={{ padding: '9px', background: '#141414', borderRadius: '9px' }}>
                                <div style={{ color: '#666', fontSize: '8px' }}>{label}</div>
                                <div style={{ marginTop: '3px', color: '#ddd', fontSize: '10px', fontWeight: 800, wordBreak: 'break-word' }}>{value}</div>
                              </div>
                            ))}
                          </div>
                          {result.currency !== 'JPY' && <div style={{ marginTop: '9px', color: '#666', fontSize: '10px' }}>保存レート：1 {result.currency} = {Number(result.exchange_rate_to_jpy).toFixed(4)} JPY</div>}
                          {result.memo && <div style={{ marginTop: '13px', paddingTop: '12px', borderTop: '1px solid #222', color: '#888', fontSize: '12px', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{result.memo}</div>}
                        </div>
                      )
                    })}
                  </div>
                </>
              )}
            </section>
              </>
            )}
            {recordsOnly && recordTab === 'amusement' && (
              <>
            {/* アミューズリング記録 */}
            <section style={{ marginTop: '10px', padding: '23px 0', borderTop: '1px solid #242424' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '17px', fontWeight: 800 }}>アミューズリング</div>
                  <div style={{ marginTop: '5px', color: '#666', fontSize: '12px' }}>BBベースでリングセッションを記録・集計</div>
                </div>
                <button
                  onClick={() => navigate('/profile/amusement-ring/new')}
                  style={{ width: 'auto', padding: '8px 13px', background: '#fff', color: '#000', borderRadius: '999px', fontSize: '12px', fontWeight: 800, flexShrink: 0 }}
                >
                  ＋ 記録を追加
                </button>
              </div>
              {ringSessionCount === 0 ? (
                <div style={{ marginTop: '16px', padding: '25px 20px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '16px', textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700 }}>まだアミューズリング記録がありません</div>
                  <div style={{ marginTop: '6px', color: '#666', fontSize: '12px', lineHeight: 1.6 }}>セッションを記録すると、BB収支やBB/hなどを自動集計します。</div>
                </div>
              ) : (
                <>
                  <div style={{ marginTop: '16px' }}>
                    <CumulativeTrendChart title="累積BB収支" subtitle="セッションごとのBB収支を時系列で累積" points={ringTrend} valueFormatter={formatBb} />
                  </div>
                  <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '9px' }}>
                    {[
                      ['セッション数', `${ringSessionCount}回`],
                      ['総プレイ時間', formatHours(ringTotalMinutes)],
                      ['総BB収支', formatBb(ringTotalBb)],
                      ['勝率', `${ringWinRate.toFixed(1)}%`],
                      ['平均BB / セッション', formatBb(ringAverageBb)],
                      ['BB / h', ringBbPerHour === null ? '—' : `${ringBbPerHour >= 0 ? '+' : ''}${ringBbPerHour.toFixed(1)}`],
                    ].map(([label, value]) => (
                      <div key={label} style={{ padding: '14px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '14px' }}>
                        <div style={{ color: '#777', fontSize: '10px', fontWeight: 700 }}>{label}</div>
                        <div style={{ marginTop: '6px', color: '#fff', fontSize: '17px', fontWeight: 800, wordBreak: 'break-word' }}>{value}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: '18px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {amusementRingResults.map((result) => {
                      const invested = result.starting_stack + result.additional_stack
                      const bbResult = (result.ending_stack - invested) / result.big_blind
                      const bbPerHour = result.play_minutes > 0 ? bbResult / (result.play_minutes / 60) : null
                      const startingBb = result.starting_stack / result.big_blind
                      return (
                        <div key={result.id} style={{ padding: '16px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '16px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start' }}>
                            <div style={{ minWidth: 0 }}>
                              <div style={{ color: '#fff', fontSize: '15px', fontWeight: 800, wordBreak: 'break-word' }}>{result.venue}</div>
                              <div style={{ marginTop: '5px', color: '#666', fontSize: '11px' }}>
                                {new Date(`${result.played_at}T00:00:00`).toLocaleDateString('ja-JP')} ・ {result.game_type} ・ {result.small_blind.toLocaleString()}/{result.big_blind.toLocaleString()}
                              </div>
                              <div style={{ marginTop: '7px', display: 'inline-flex', padding: '4px 8px', background: result.is_public ? '#101a14' : '#171717', border: result.is_public ? '1px solid #24402d' : '1px solid #303030', borderRadius: '999px', color: result.is_public ? '#8fcf9f' : '#999', fontSize: '10px', fontWeight: 700 }}>
                                {result.is_public ? '🌐 公開' : '🔒 非公開'}
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                              <div style={{ padding: '6px 10px', background: '#171717', border: '1px solid #303030', borderRadius: '999px', color: '#fff', fontSize: '12px', fontWeight: 800 }}>
                                {formatBb(bbResult)}
                              </div>
                              <button
                                onClick={() => navigate(`/profile/amusement-ring/${result.id}/edit`)}
                                aria-label="アミューズリング記録を編集"
                                style={{
                                  width: '32px',
                                  height: '32px',
                                  padding: 0,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  background: 'transparent',
                                  color: '#aaa',
                                  borderRadius: '50%',
                                  fontSize: '20px',
                                  lineHeight: 1,
                                }}
                              >
                                ⋯
                              </button>
                            </div>
                          </div>
                          <div style={{ marginTop: '13px', display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '7px' }}>
                            {[
                              ['開始時', `${startingBb.toFixed(0)}BB`],
                              ['プレイ時間', formatHours(result.play_minutes)],
                              ['BB / h', bbPerHour === null ? '—' : `${bbPerHour >= 0 ? '+' : ''}${bbPerHour.toFixed(1)}`],
                            ].map(([label, value]) => (
                              <div key={label} style={{ padding: '9px', background: '#141414', borderRadius: '9px' }}>
                                <div style={{ color: '#666', fontSize: '8px' }}>{label}</div>
                                <div style={{ marginTop: '3px', color: '#ddd', fontSize: '10px', fontWeight: 800 }}>{value}</div>
                              </div>
                            ))}
                          </div>
                          {result.memo && (
                            <div style={{ marginTop: '13px', paddingTop: '12px', borderTop: '1px solid #222', color: '#888', fontSize: '12px', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                              {result.memo}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </>
              )}
            </section>
              </>
            )}
            {recordsOnly && recordTab === 'tournament' && (
              <>
            {/* トーナメント記録 */}
            <section
              style={{
                marginTop: '10px',
                padding: '21px 0',
                borderTop:
                  '1px solid #242424',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems:
                    'center',
                  justifyContent:
                    'space-between',
                  gap: '15px',
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize:
                        '17px',
                      fontWeight: 800,
                    }}
                  >
                    トーナメント記録
                  </div>
                  <div
                    style={{
                      marginTop:
                        '5px',
                      color: '#666',
                      fontSize:
                        '12px',
                    }}
                  >
                    トーナメントの記録
                  </div>
                </div>
                <button
                  onClick={() =>
                    navigate(
                      '/profile/results/new'
                    )
                  }
                  style={{
                    width: 'auto',
                    padding:
                      '8px 13px',
                    background: '#fff',
                    color: '#000',
                    borderRadius:
                      '999px',
                    fontSize: '12px',
                    fontWeight: 800,
                  }}
                >
                  ＋ 記録を追加
                </button>
              </div>
              {pokerResults.length ===
              0 ? (
                <div
                  style={{
                    marginTop:
                      '18px',
                    padding:
                      '30px 20px',
                    background:
                      '#0d0d0d',
                    border:
                      '1px solid #242424',
                    borderRadius:
                      '16px',
                    textAlign:
                      'center',
                  }}
                >
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      margin:
                        '0 auto 13px',
                      display: 'flex',
                      alignItems:
                        'center',
                      justifyContent:
                        'center',
                      background:
                        '#171717',
                      border:
                        '1px solid #292929',
                      borderRadius:
                        '50%',
                      fontSize:
                        '21px',
                    }}
                  >
                    ♠
                  </div>
                  <div
                    style={{
                      fontSize:
                        '14px',
                      fontWeight: 700,
                    }}
                  >
                    まだトーナメント記録がありません
                  </div>
                  <div
                    style={{
                      marginTop:
                        '6px',
                      color: '#666',
                      fontSize:
                        '12px',
                      lineHeight: 1.5,
                    }}
                  >
                    大会の結果をPoker IDに
                    <br />
                    記録していきましょう
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    marginTop:
                      '18px',
                    display: 'flex',
                    flexDirection:
                      'column',
                    gap: '10px',
                  }}
                >
                  <CumulativeTrendChart title="累積損益" subtitle="プライズ相当額 − 総参加費を大会ごとに累積" points={tournamentTrend} valueFormatter={(value) => formatYen(Math.round(value))} />
            {/* トーナメント分析 */}
            <section style={{ marginTop: '10px', padding: '23px 0', borderTop: '1px solid #242424' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '17px', fontWeight: 800 }}>トーナメント分析</div>
                  <div style={{ marginTop: '5px', color: '#666', fontSize: '12px' }}>記録したトーナメントから自動集計</div>
                </div>
                <div style={{ padding: '6px 10px', background: '#111', border: '1px solid #292929', borderRadius: '999px', color: '#bbb', fontSize: '11px', fontWeight: 700, whiteSpace: 'nowrap' }}>
                  {analysisStatus.mark} {analysisStatus.label}
                </div>
              </div>
              {tournamentCount === 0 ? (
                <div style={{ marginTop: '16px', padding: '20px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '16px', color: '#777', fontSize: '12px', lineHeight: 1.6 }}>
                  トーナメントを記録すると、ITM率・収支・ROIなどがここに自動表示されます。
                </div>
              ) : (
                <>
                  <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '9px' }}>
                    {[
                      ['総参加数', `${tournamentCount}回`],
                      ['ITM率', formatPercent(itmRate)],
                      ['総参加費', formatYen(totalInvested)],
                      ['総プライズ相当額', formatYen(totalEarned)],
                      ['収支', formatYen(profit)],
                      ['ROI', roi === null ? '—' : formatPercent(roi)],
                      ['平均使用エントリー数', `${averageBullets.toFixed(2)}機`],
                    ].map(([label, value]) => (
                      <div key={label} style={{ padding: '14px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '14px' }}>
                        <div style={{ color: '#777', fontSize: '10px', fontWeight: 700 }}>{label}</div>
                        <div style={{ marginTop: '6px', color: '#fff', fontSize: '17px', fontWeight: 800, wordBreak: 'break-word' }}>{value}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: '11px', padding: '13px 14px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '14px', color: '#999', fontSize: '11px', lineHeight: 1.6 }}>
                    <strong style={{ color: '#ddd' }}>{analysisStatus.mark} {analysisStatus.label}</strong>
                    <div style={{ marginTop: '4px' }}>{analysisStatus.text}</div>
                    {allItm && (
                      <div style={{ marginTop: '9px', paddingTop: '9px', borderTop: '1px solid #222', color: '#c9a96e' }}>
                        ⚠️ 登録されているトーナメントがすべてITMです。圏外のトーナメントも記録すると、より正確な分析結果を確認できます。
                      </div>
                    )}
                    {hasMissingFee && (
                      <div style={{ marginTop: '7px', color: '#777' }}>
                        ※ 参加費が未入力の記録があります。総参加費・収支・ROIは入力済みデータをもとに計算しています。
                      </div>
                    )}
                  </div>
                  {(() => {
                    const sectionStatus = tournamentCount < 10
                      ? { mark: '🔴', label: 'データ不足' }
                      : tournamentCount < 30 || allItm || hasMissingFee
                        ? { mark: '🟡', label: '参考データ' }
                        : { mark: '🟢', label: '分析可能' }
                    const statusBadge = (
                      <span style={{ color: '#999', fontSize: '10px', fontWeight: 700, whiteSpace: 'nowrap' }}>
                        {sectionStatus.mark} {sectionStatus.label}
                      </span>
                    )
                    const groupCard = (group: { label: string; count: number; itmRate: number | null; roi: number | null; averageProfit: number | null; averageBullets: number | null }, showBullets = false) => (
                      <div key={group.label} style={{ padding: '11px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '11px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'center' }}>
                          <strong style={{ color: '#ddd', fontSize: '11px' }}>{group.label}</strong>
                          <span style={{ color: group.count >= 5 ? '#999' : '#666', fontSize: '9px' }}>
                            {group.count}件{group.count < 5 ? ' ・ 比較には不足' : ''}
                          </span>
                        </div>
                        {group.count > 0 ? (
                          <div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: showBullets ? 'repeat(2, minmax(0, 1fr))' : 'repeat(3, minmax(0, 1fr))', gap: '6px' }}>
                            {[
                              ['ITM率', group.itmRate === null ? '—' : formatPercent(group.itmRate)],
                              ['ROI', group.roi === null ? '—' : formatPercent(group.roi)],
                              ['平均収支', group.averageProfit === null ? '—' : formatYen(Math.round(group.averageProfit))],
                              ...(showBullets ? [['平均使用', group.averageBullets === null ? '—' : `${group.averageBullets.toFixed(2)}機`]] : []),
                            ].map(([label, value]) => (
                              <div key={label} style={{ padding: '8px', background: '#131313', borderRadius: '8px' }}>
                                <div style={{ color: '#666', fontSize: '8px' }}>{label}</div>
                                <div style={{ marginTop: '3px', color: '#ddd', fontSize: '10px', fontWeight: 800 }}>{value}</div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ marginTop: '7px', color: '#666', fontSize: '10px' }}>該当する記録はまだありません。</div>
                        )}
                      </div>
                    )
                    const lockedText = tournamentCount < 10
                      ? `あと${10 - tournamentCount}件記録すると、傾向分析を確認できるようになります。`
                      : null
                    return (
                      <>
                        <div style={{ marginTop: '11px', padding: '13px 14px', background: '#101010', border: '1px solid #242424', borderRadius: '14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                            <strong style={{ color: '#ddd', fontSize: '12px' }}>参加タイミング別分析</strong>
                            {statusBadge}
                          </div>
                          {lockedText ? (
                            <div style={{ marginTop: '7px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>{lockedText}</div>
                          ) : (
                            <>
                              <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '7px' }}>
                                {timingAnalysis.map((group) => groupCard(group, true))}
                              </div>
                              <div style={{ marginTop: '9px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>
                                {canCompareTiming && bestTimingByRoi
                                  ? `現在の記録では「${bestTimingByRoi.label}」のROIが最も高い傾向があります。比較対象は各5件以上のグループです。`
                                  : '比較コメントを出すには、少なくとも2つの参加タイミングで各5件以上の記録が必要です。'}
                              </div>
                            </>
                          )}
                        </div>
                        <div style={{ marginTop: '11px', padding: '13px 14px', background: '#101010', border: '1px solid #242424', borderRadius: '14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                            <strong style={{ color: '#ddd', fontSize: '12px' }}>会場別分析</strong>
                            {statusBadge}
                          </div>
                          {lockedText ? (
                            <div style={{ marginTop: '7px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>{lockedText}</div>
                          ) : venueAnalysis.length === 0 ? (
                            <div style={{ marginTop: '7px', color: '#666', fontSize: '10px' }}>会場が入力された記録がありません。</div>
                          ) : (
                            <>
                              <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '7px' }}>{venueAnalysis.map((group) => groupCard(group))}</div>
                              <div style={{ marginTop: '9px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>
                                {bestVenue ? `現在の記録では「${bestVenue.label}」のROIが最も高い傾向があります。` : '会場を比較するには、少なくとも2会場で各5件以上の記録が必要です。'}
                              </div>
                            </>
                          )}
                        </div>
                        <div style={{ marginTop: '11px', padding: '13px 14px', background: '#101010', border: '1px solid #242424', borderRadius: '14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                            <strong style={{ color: '#ddd', fontSize: '12px' }}>参加費帯別分析</strong>
                            {statusBadge}
                          </div>
                          {lockedText ? (
                            <div style={{ marginTop: '7px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>{lockedText}</div>
                          ) : (
                            <>
                              <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '7px' }}>{buyinBands.map((group) => groupCard(group))}</div>
                              <div style={{ marginTop: '9px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>
                                {bestBuyin ? `現在の記録では「${bestBuyin.label}」のROIが最も高い傾向があります。` : '参加費帯を比較するには、少なくとも2つの価格帯で各5件以上の記録が必要です。'}
                              </div>
                            </>
                          )}
                        </div>
                        <div style={{ marginTop: '11px', padding: '13px 14px', background: '#101010', border: '1px solid #242424', borderRadius: '14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                            <strong style={{ color: '#ddd', fontSize: '12px' }}>1機 vs 複数機</strong>
                            {statusBadge}
                          </div>
                          {lockedText ? (
                            <div style={{ marginTop: '7px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>{lockedText}</div>
                          ) : (
                            <>
                              <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '7px' }}>{bulletAnalysis.map((group) => groupCard(group, true))}</div>
                              <div style={{ marginTop: '9px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>
                                {bestBulletGroup ? `現在の記録では「${bestBulletGroup.label}」のROIが高い傾向があります。` : '1機・複数機の両方が各5件以上になると比較コメントを表示します。'}
                              </div>
                            </>
                          )}
                        </div>
                        <div style={{ marginTop: '11px', padding: '13px 14px', background: '#101010', border: '1px solid #242424', borderRadius: '14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                            <strong style={{ color: '#ddd', fontSize: '12px' }}>月別推移</strong>
                            {statusBadge}
                          </div>
                          {lockedText ? (
                            <div style={{ marginTop: '7px', color: '#777', fontSize: '10px', lineHeight: 1.6 }}>{lockedText}</div>
                          ) : monthAnalysis.length === 0 ? (
                            <div style={{ marginTop: '7px', color: '#666', fontSize: '10px' }}>月別データはまだありません。</div>
                          ) : (
                            <>
                              <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {monthAnalysis.map((group) => {
                                  const monthProfit = group.averageProfit === null ? 0 : group.averageProfit * group.count
                                  const maxAbsProfit = Math.max(...monthAnalysis.map((item) => Math.abs((item.averageProfit ?? 0) * item.count)), 1)
                                  const barWidth = Math.max(4, Math.round((Math.abs(monthProfit) / maxAbsProfit) * 100))
                                  return (
                                    <div key={group.month} style={{ padding: '11px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '11px' }}>
                                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
                                        <strong style={{ color: '#ddd', fontSize: '11px' }}>{group.month.replace('-', '年')}月</strong>
                                        <span style={{ color: group.count >= 5 ? '#999' : '#666', fontSize: '9px' }}>{group.count}件{group.count < 5 ? ' ・ 参考' : ''}</span>
                                      </div>
                                      <div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '6px' }}>
                                        {[
                                          ['ITM率', group.itmRate === null ? '—' : formatPercent(group.itmRate)],
                                          ['ROI', group.roi === null ? '—' : formatPercent(group.roi)],
                                          ['収支', formatYen(Math.round(monthProfit))],
                                        ].map(([label, value]) => (
                                          <div key={label} style={{ padding: '8px', background: '#131313', borderRadius: '8px' }}>
                                            <div style={{ color: '#666', fontSize: '8px' }}>{label}</div>
                                            <div style={{ marginTop: '3px', color: '#ddd', fontSize: '10px', fontWeight: 800 }}>{value}</div>
                                          </div>
                                        ))}
                                      </div>
                                      <div style={{ marginTop: '8px', height: '5px', background: '#1d1d1d', borderRadius: '999px', overflow: 'hidden' }}>
                                        <div style={{ width: `${barWidth}%`, height: '100%', background: monthProfit >= 0 ? '#d8d8d8' : '#666', borderRadius: '999px' }} />
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                              <div style={{ marginTop: '8px', color: '#666', fontSize: '9px', lineHeight: 1.5 }}>
                                直近6か月を表示。バーは月ごとの収支規模を相対表示しています。各月5件未満は参考値です。
                              </div>
                            </>
                          )}
                        </div>
                      </>
                    )
                  })()}
                  <div style={{ marginTop: '11px', padding: '13px 14px', background: '#101010', border: '1px solid #242424', borderRadius: '14px', color: '#888', fontSize: '11px', lineHeight: 1.65 }}>
                    <strong style={{ color: '#ccc' }}>すべてのトーナメントを記録しよう</strong>
                    <div style={{ marginTop: '4px' }}>インマネできなかったトーナメントも記録すると、ITM率やROI、参加タイミング別の成績など、より正確なプレイ傾向を分析できます。</div>
                  </div>
                </>
              )}
            </section>
                  {pokerResults.map(
                    (result) => (
                      <div
                        key={result.id}
                        style={{
                          padding:
                            '16px',
                          background:
                            '#0d0d0d',
                          border:
                            '1px solid #242424',
                          borderRadius:
                            '16px',
                        }}
                      >
                        <div
                          style={{
                            display:
                              'flex',
                            alignItems:
                              'flex-start',
                            justifyContent:
                              'space-between',
                            gap: '12px',
                          }}
                        >
                          <div
                            style={{
                              minWidth: 0,
                            }}
                          >
                            <div
                              style={{
                                color:
                                  '#fff',
                                fontSize:
                                  '15px',
                                fontWeight:
                                  800,
                                lineHeight:
                                  1.4,
                                wordBreak:
                                  'break-word',
                              }}
                            >
                              {
                                result.tournament_name
                              }
                            </div>
                            <div
                              style={{
                                marginTop: '7px',
                                display: 'inline-flex',
                                alignItems: 'center',
                                padding: '4px 8px',
                                background: result.is_public
                                  ? '#101a14'
                                  : '#171717',
                                border: result.is_public
                                  ? '1px solid #24402d'
                                  : '1px solid #303030',
                                borderRadius: '999px',
                                color: result.is_public
                                  ? '#8fcf9f'
                                  : '#999',
                                fontSize: '10px',
                                fontWeight: 700,
                              }}
                            >
                              {result.is_public
                                ? '🌐 公開'
                                : '🔒 非公開'}
                            </div>
                            <div
                              style={{
                                marginTop:
                                  '5px',
                                color:
                                  '#666',
                                fontSize:
                                  '11px',
                              }}
                            >
                              {new Date(
                                `${result.played_at}T00:00:00`
                              ).toLocaleDateString(
                                'ja-JP'
                              )}
                            </div>
                          </div>
                          <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            flexShrink: 0,
                          }}
                        >
                          {result.rank !==
                            null && (
                            <div
                              style={{
                                padding:
                                  '6px 10px',
                                background:
                                  '#171717',
                                border:
                                  '1px solid #303030',
                                borderRadius:
                                  '999px',
                                color:
                                  '#fff',
                                fontSize:
                                  '12px',
                                fontWeight:
                                  800,
                              }}
                            >
                              {result.rank}位
                            </div>
                          )}
                          <button
                            onClick={() =>
                              navigate(
                                `/profile/results/${result.id}/edit`
                              )
                            }
                            aria-label="トーナメント記録を編集"
                            style={{
                              width: '32px',
                              height: '32px',
                              padding: 0,
                              display: 'flex',
                              alignItems:
                                'center',
                              justifyContent:
                                'center',
                              background:
                                'transparent',
                              color: '#aaa',
                              borderRadius:
                                '50%',
                              fontSize: '20px',
                              lineHeight: 1,
                            }}
                          >
                            ⋯
                          </button>
                        </div>
                        </div>
                        {(result.entry_count !==
                          null ||
                          result.prize_amount !==
                            null) && (
                          <div
                            style={{
                              display:
                                'flex',
                              flexWrap:
                                'wrap',
                              gap: '8px',
                              marginTop:
                                '13px',
                            }}
                          >
                            {result.entry_count !==
                              null && (
                              <div
                                style={{
                                  padding:
                                    '6px 9px',
                                  background:
                                    '#141414',
                                  borderRadius:
                                    '8px',
                                  color:
                                    '#aaa',
                                  fontSize:
                                    '11px',
                                }}
                              >
                                {result.rank !==
                                null
                                  ? `${result.rank}位 / ${result.entry_count}人`
                                  : `${result.entry_count}人参加`}
                              </div>
                            )}
                            {result.prize_amount !==
                              null && (
                              <div
                                style={{
                                  padding:
                                    '6px 9px',
                                  background:
                                    '#141414',
                                  borderRadius:
                                    '8px',
                                  color:
                                    '#fff',
                                  fontSize:
                                    '11px',
                                  fontWeight:
                                    700,
                                }}
                              >
                                ¥
                                {result.prize_amount.toLocaleString()}
                              </div>
                            )}
                          </div>
                        )}
                        {result.memo && (
                          <div
                            style={{
                              marginTop:
                                '13px',
                              paddingTop:
                                '12px',
                              borderTop:
                                '1px solid #222',
                              color: '#888',
                              fontSize:
                                '12px',
                              lineHeight:
                                1.6,
                              whiteSpace:
                                'pre-wrap',
                              wordBreak:
                                'break-word',
                            }}
                          >
                            {result.memo}
                          </div>
                        )}
                      </div>
                    )
                  )}
                </div>
              )}
            </section>
              </>
            )}
          </div>
        </main>
      )
    }
    export default Profile
