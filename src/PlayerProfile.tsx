        import { useEffect, useState } from 'react'
        import {
          useNavigate,
          useParams,
        } from 'react-router-dom'
        import { supabase } from './supabase'
        type PokerResult = {
          id: string
          tournament_name: string
          played_at: string
          rank: number | null
          entry_count: number | null
          prize_amount: number | null
          venue: string | null
          is_itm: boolean
          entry_fee: number | null
          bullets: number
          total_entry_fee: number | null
          entry_timing: string | null
          rank_unknown: boolean
          is_featured: boolean
          entry_bb: number | null
          game_type: string | null
          prize_description: string | null
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
        type PlayerTypeSummary = {
          result_id: string
          result_type_key: string
          animal_name_ja: string
          catchphrase: string
          completed_at: string
        }

        const playerTypeEmoji: Record<string, string> = {
          lion: '🦁', tiger: '🐯', leopard: '🐆', bison: '🦬', gorilla: '🦍',
          rhino: '🦏', shark: '🦈', owl: '🦉', eagle: '🦅', elephant: '🐘',
          giraffe: '🦒', wolf: '🐺', hyena: '🐾', cat: '🐈', chameleon: '🦎',
          dolphin: '🐬', fox: '🦊', snake: '🐍', raccoon: '🦝', turtle: '🐢',
          rabbit: '🐇', crocodile: '🐊', hedgehog: '🦔', deer: '🦌', sloth: '🦥',
          dog: '🐕', bear: '🐻', bull: '🐄', badger: '🦡', monkey: '🐒',
          magpie: '🐦‍⬛', penguin: '🐧', horse: '🐎', squirrel: '🐿️',
          mountain_goat: '🐐', otter: '🦦',
        }

        function PlayerProfile() {
          const { id } = useParams()
          const navigate = useNavigate()
          const [profile, setProfile] =
            useState<any>(null)
          const [isFollowing, setIsFollowing] =
            useState(false)
          const [currentUserId, setCurrentUserId] =
            useState('')
          const [blockStatus, setBlockStatus] = useState<'loading' | 'none' | 'blocked' | 'blockedBy'>('loading')
          const [blockBusy, setBlockBusy] = useState(false)
          const [blockError, setBlockError] = useState('')
          const [isMuted, setIsMuted] = useState(false)
          const [muteBusy, setMuteBusy] = useState(false)
          const [muteError, setMuteError] = useState('')
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
          const [cashGameResults, setCashGameResults] = useState<CashGameResult[]>([])
          const [activeTab, setActiveTab] = useState<'poker' | 'records'>('poker')
          const [recordTab, setRecordTab] = useState<'tournament' | 'ring' | 'cash'>('tournament')
          const [playerType, setPlayerType] = useState<PlayerTypeSummary | null>(null)
          useEffect(() => {
            const loadProfile = async () => {
              if (!id) return
              const {
                data: { user },
              } = await supabase.auth.getUser()
              if (!user) {
                navigate('/login')
                return
              }
              setCurrentUserId(user.id)
              const { data: muteRow, error: muteLoadError } = await supabase
                .from('user_mutes').select('muted_id')
                .eq('muter_id', user.id).eq('muted_id', id).maybeSingle()
              if (muteLoadError) setMuteError('ミュート状態を取得できませんでした。')
              else { setIsMuted(!!muteRow); setMuteError('') }
              const { data: blockRows, error: blockLoadError } = await supabase.from('user_blocks')
                .select('blocker_id, blocked_id')
                .or(`and(blocker_id.eq.${user.id},blocked_id.eq.${id}),and(blocker_id.eq.${id},blocked_id.eq.${user.id})`)
              if (blockLoadError) { setBlockError('ブロック状態の取得に失敗しました。'); setBlockStatus('loading'); return }
              const mine = (blockRows || []).some(row => row.blocker_id === user.id)
              const theirs = (blockRows || []).some(row => row.blocker_id === id)
              setBlockStatus(mine ? 'blocked' : theirs ? 'blockedBy' : 'none')
              if (mine || theirs) {
                const { data: minimalProfile } = await supabase.from('profiles').select('id, display_name, poker_id').eq('id', id).maybeSingle()
                setProfile(minimalProfile || { id, display_name: 'ユーザー', poker_id: '' })
                return
              }
              if (user.id === id) {
                navigate('/profile')
                return
              }
              const { data, error } =
                await supabase
                  .from('profiles')
                  .select('*')
                  .eq('id', id)
                  .single()
              if (error) {
                console.error(error)
                return
              }
              setProfile(data)

              const { data: playerTypeRows, error: playerTypeError } = await supabase.rpc(
                'get_public_latest_player_type_v2',
                { p_user_id: id },
              )
              if (playerTypeError) {
                console.error('公開プレイヤータイプ取得エラー:', playerTypeError)
              } else {
                setPlayerType((playerTypeRows?.[0] ?? null) as PlayerTypeSummary | null)
              }

              const { data: favoriteVenueLinks, error: favoriteVenueError } = await supabase
                .from('user_favorite_venues')
                .select('venue_id')
                .eq('user_id', id)

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
                  'id, tournament_name, played_at, rank, entry_count, prize_amount, memo, is_public, venue, is_itm, entry_fee, bullets, total_entry_fee, entry_timing, rank_unknown, is_featured, entry_bb, game_type, prize_description, created_at'
                )
                .eq('user_id', id)
                .eq('is_public', true)
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
                .eq('user_id', id)
                .eq('is_public', true)
                .order('played_at', { ascending: false })
                .order('created_at', { ascending: false })
              if (ringResultsError) {
                console.error(ringResultsError)
              } else {
                setAmusementRingResults(ringResults || [])
              }
              const { count: following } =
                await supabase
                  .from('follows')
                  .select('*', {
                    count: 'exact',
                    head: true,
                  })
                  .eq('follower_id', id)
              setFollowingCount(following || 0)
              const { count: followers } =
                await supabase
                  .from('follows')
                  .select('*', {
                    count: 'exact',
                    head: true,
                  })
                  .eq('following_id', id)
              setFollowerCount(followers || 0)
              const { data: ratingSummary, error: ratingsError } = await supabase.rpc(
                'get_player_style_rating_summary',
                { p_user_id: id }
              )
              if (ratingsError) {
                console.error('匿名評価集計エラー:', ratingsError)
                setAverageAggression(null)
                setAverageLooseness(null)
                setRatingCount(0)
              } else {
                const summary = ratingSummary?.[0]
                setRatingCount(Number(summary?.rating_count ?? 0))
                setAverageAggression(summary?.average_aggression == null ? null : Number(summary.average_aggression))
                setAverageLooseness(summary?.average_looseness == null ? null : Number(summary.average_looseness))
              }
              const { data: followData } =
                await supabase
                  .from('follows')
                  .select('id')
                  .eq('follower_id', user.id)
                  .eq('following_id', id)
                  .maybeSingle()
              setIsFollowing(!!followData)
              const { data: cashResults, error: cashResultsError } = await supabase
                .from('cash_game_results')
                .select(
                  'id, played_at, play_type, record_type, venue, game_type, small_blind, big_blind, currency, buy_in_amount, cash_out_amount, profit_amount, exchange_rate_to_jpy, profit_jpy, play_minutes, memo, is_public, created_at'
                )
                .eq('user_id', id)
                .eq('is_public', true)
                .order('played_at', { ascending: false })
                .order('created_at', { ascending: false })
              if (cashResultsError) {
                console.error(cashResultsError)
              } else {
                setCashGameResults(cashResults || [])
              }
            }
            loadProfile()
          }, [id, navigate])
          const handleBlockToggle = async () => {
            if (!id || !currentUserId || blockBusy) return
            const willBlock = blockStatus !== 'blocked'
            if (willBlock && !window.confirm('このユーザーをブロックしますか？相互のフォローが解除され、DMできなくなります。')) return
            setBlockBusy(true)
            setBlockError('')
            const query = supabase.from('user_blocks')
            const { error } = willBlock
              ? await query.insert({ blocker_id: currentUserId, blocked_id: id })
              : await query.delete().eq('blocker_id', currentUserId).eq('blocked_id', id)
            if (error) { setBlockError(error.message) }
            else {
              setBlockStatus(willBlock ? 'blocked' : 'none')
              if (willBlock) { setIsFollowing(false); setFollowerCount(count => Math.max(0, count - (isFollowing ? 1 : 0))) }
              else { window.location.reload() }
            }
            setBlockBusy(false)
          }
          const handleMuteToggle = async () => {
            if (!id || !currentUserId || muteBusy || blockStatus !== 'none' || muteError) return
            setMuteBusy(true)
            const { error } = isMuted
              ? await supabase.from('user_mutes').delete().eq('muter_id', currentUserId).eq('muted_id', id)
              : await supabase.from('user_mutes').insert({ muter_id: currentUserId, muted_id: id })
            if (error) setMuteError(`ミュート操作に失敗しました：${error.message}`)
            else setIsMuted(!isMuted)
            setMuteBusy(false)
          }
          const handleFollow = async () => {
            if (blockStatus !== 'none') return
            const {
              data: { user },
            } = await supabase.auth.getUser()
            if (!user || !id) return
            const { error } = await supabase
              .from('follows')
              .insert({
                follower_id: user.id,
                following_id: id,
              })
            if (error) {
              console.error(error)
              return
            }
            const {
              error: notificationError,
            } = await supabase
              .from('notifications')
              .insert({
                user_id: id,
                actor_id: user.id,
                type: 'follow',
                post_id: null,
              })
            if (notificationError) {
              console.error(
                '通知作成エラー:',
                notificationError
              )
            }
            setIsFollowing(true)
            setFollowerCount(
              (count) => count + 1
            )
          }
          const handleUnfollow = async () => {
            const {
              data: { user },
            } = await supabase.auth.getUser()
            if (!user || !id) return
            const { error } = await supabase
              .from('follows')
              .delete()
              .eq('follower_id', user.id)
              .eq('following_id', id)
            if (error) {
              console.error(error)
              return
            }
            setIsFollowing(false)
            setFollowerCount(
              (count) =>
                Math.max(count - 1, 0)
            )
          }
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
          return (
            <main className="app">
              <div
                className="card"
                style={{
                  paddingTop: 0,
                }}
              >
                {/* ヘッダー */}
                <header
                  style={{
                    position: 'sticky',
                    top: 0,
                    zIndex: 20,
                    margin: '0 -20px',
                    padding: '12px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '13px',
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
                  <button
                    onClick={() =>
                      navigate(-1)
                    }
                    aria-label="戻る"
                    style={{
                      width: '38px',
                      height: '38px',
                      padding: 0,
                      flexShrink: 0,
                      background:
                        'transparent',
                      color: '#fff',
                      borderRadius: '50%',
                      fontSize: '25px',
                      lineHeight: 1,
                    }}
                  >
                    ‹
                  </button>
                  <div
                    style={{
                      minWidth: 0,
                    }}
                  >
                    <div
                      style={{
                        overflow: 'hidden',
                        textOverflow:
                          'ellipsis',
                        whiteSpace: 'nowrap',
                        fontSize: '17px',
                        fontWeight: 800,
                      }}
                    >
                      {profile.display_name}
                    </div>
                    <div
                      style={{
                        marginTop: '1px',
                        color: '#666',
                        fontSize: '11px',
                      }}
                    >
                      @{profile.poker_id}
                    </div>
                  </div>
                </header>
                {/* プロフィール上部 */}
                <section
                  style={{
                    padding: '26px 0 18px',
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
                          objectFit: 'cover',
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
                    {/* フォロー数 */}
                    <div
                      style={{
                        flex: 1,
                        display: 'flex',
                        justifyContent:
                          'flex-end',
                        gap: '30px',
                        paddingTop: '17px',
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
                            fontSize: '18px',
                            fontWeight: 800,
                          }}
                        >
                          {followingCount}
                        </div>
                        <div
                          style={{
                            marginTop: '4px',
                            color: '#777',
                            fontSize: '12px',
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
                            fontSize: '18px',
                            fontWeight: 800,
                          }}
                        >
                          {followerCount}
                        </div>
                        <div
                          style={{
                            marginTop: '4px',
                            color: '#777',
                            fontSize: '12px',
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
                      margin: '17px 0 0',
                      color: profile.bio
                        ? '#e8e8e8'
                        : '#777',
                      fontSize: '14px',
                      lineHeight: 1.65,
                      whiteSpace: 'pre-wrap',
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
                  {blockError && <p style={{ color: '#ff8585', fontSize: '12px' }}>{blockError}</p>}
                  <div style={{ marginTop: '14px' }}>
                    <button type="button" onClick={handleBlockToggle} disabled={blockBusy || blockStatus === 'loading' || blockStatus === 'blockedBy'}
                      style={{ background: '#171717', border: '1px solid #444', color: blockStatus === 'blocked' ? '#fff' : '#ff8b8b', padding: '9px 15px', borderRadius: '12px', fontSize: '13px' }}>
                      {blockStatus === 'blocked' ? 'ブロックを解除' : blockStatus === 'blockedBy' ? 'このユーザーは表示できません' : 'このユーザーをブロック'}
                    </button>
                  </div>
                  {blockStatus === 'none' && currentUserId !== profile.id && (
                    <div style={{ marginTop: '9px' }}>
                      {muteError && <p style={{ color: '#ff8585', fontSize: '12px' }}>{muteError}</p>}
                      <button type="button" onClick={handleMuteToggle} disabled={muteBusy || !!muteError}
                        style={{ background: '#171717', border: '1px solid #444', color: '#ddd', padding: '9px 15px', borderRadius: '12px', fontSize: '13px' }}>
                        {muteBusy ? '処理中...' : isMuted ? 'ミュートを解除' : 'このユーザーをミュート'}
                      </button>
                    </div>
                  )}
                  {blockStatus !== 'none' && <p style={{ color: '#aaa', marginTop: '15px' }}>このユーザーとの交流は制限されています。</p>}
                  {/* アクション */}
                  {blockStatus === 'none' && currentUserId !==
                    profile.id && (
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns:
                          '1fr 1fr',
                        gap: '9px',
                        marginTop: '20px',
                      }}
                    >
                      <button
                        onClick={
                          isFollowing
                            ? handleUnfollow
                            : handleFollow
                        }
                        style={{
                          padding:
                            '11px 14px',
                          borderRadius:
                            '999px',
                          background:
                            isFollowing
                              ? '#111'
                              : '#fff',
                          color:
                            isFollowing
                              ? '#fff'
                              : '#000',
                          border:
                            isFollowing
                              ? '1px solid #383838'
                              : '1px solid #fff',
                          fontSize: '14px',
                          fontWeight: 800,
                        }}
                      >
                        {isFollowing
                          ? 'フォロー中'
                          : 'フォロー'}
                      </button>
                      <button
                        onClick={() =>
                          navigate(
                            `/dm/${profile.id}`
                          )
                        }
                        style={{
                          padding:
                            '11px 14px',
                          borderRadius:
                            '999px',
                          background:
                            '#111',
                          color: '#fff',
                          border:
                            '1px solid #383838',
                          fontSize: '14px',
                          fontWeight: 700,
                        }}
                      >
                        メッセージ
                      </button>
                    </div>
                  )}
                </section>
                {/* メインタブ */}
              <div style={{ margin: '0 -20px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', borderTop: '1px solid #242424', borderBottom: '1px solid #242424' }}>
                {[
                  { key: 'poker', label: 'Poker ID' },
                  { key: 'records', label: '記録' },
                ].map((tab) => {
                  const active = activeTab === tab.key
                  return (
                    <button key={tab.key} onClick={() => setActiveTab(tab.key as 'poker' | 'records')} style={{ position: 'relative', padding: '15px 8px', background: 'transparent', color: active ? '#fff' : '#666', borderRadius: 0, fontSize: '14px', fontWeight: active ? 700 : 600 }}>
                      {tab.label}
                      {active && <span style={{ position: 'absolute', left: '30%', right: '30%', bottom: 0, height: '3px', borderRadius: '999px', background: '#fff' }} />}
                    </button>
                  )
                })}
                <button onClick={() => navigate('/timeline')} style={{ padding: '15px 8px', background: 'transparent', color: '#666', borderRadius: 0, fontSize: '14px', fontWeight: 600 }}>投稿</button>
              </div>
              {blockStatus === 'none' && activeTab === 'records' && (
                <div style={{ margin: '16px 0 2px', padding: '4px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '13px' }}>
                  {[
                    { key: 'tournament', label: 'トーナメント' },
                    { key: 'ring', label: 'アミューズ' },
                    { key: 'cash', label: 'キャッシュ' },
                  ].map((tab) => {
                    const active = recordTab === tab.key
                    return (
                      <button key={tab.key} onClick={() => setRecordTab(tab.key as 'tournament' | 'ring' | 'cash')} style={{ padding: '10px 5px', background: active ? '#222' : 'transparent', color: active ? '#fff' : '#777', borderRadius: '10px', fontSize: '11px', fontWeight: active ? 800 : 600 }}>
                        {tab.label}
                      </button>
                    )
                  })}
                </div>
              )}
              {blockStatus === 'none' && activeTab === 'poker' && (
                <>
              {/* 公開プレイヤータイプ診断 */}
              {playerType && (
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
                    50問の診断から見たこのプレイヤーのスタイル
                  </div>

                  <button
                    type="button"
                    onClick={() => navigate(`/player-type?result=${playerType.result_id}`)}
                    style={{
                      width: '100%',
                      marginTop: '15px',
                      padding: '17px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '14px',
                      background: '#0d0d0d',
                      border: '1px solid #3b3423',
                      borderRadius: '16px',
                      color: '#fff',
                      textAlign: 'left',
                    }}
                  >
                    <div
                      style={{
                        width: 'clamp(88px, 24vw, 120px)',
                        height: 'clamp(88px, 24vw, 120px)',
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        overflow: 'hidden',
                        background: '#15130e',
                        border: '1px solid #403821',
                        borderRadius: '16px',
                        fontSize: '40px',
                      }}
                    >
                      <span aria-hidden="true">{playerTypeEmoji[playerType.result_type_key] ?? '♠️'}</span>
                      {Object.prototype.hasOwnProperty.call(playerTypeEmoji, playerType.result_type_key) && (
                        <img
                          src={`/animals/${playerType.result_type_key}.png`}
                          alt={`${playerType.animal_name_ja}のプレイヤータイプ画像`}
                          loading="lazy"
                          onError={(event) => { event.currentTarget.style.display = 'none' }}
                          style={{
                            position: 'absolute',
                            inset: 0,
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                          }}
                        />
                      )}
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
                        PLAYER TYPE
                      </div>
                      <div style={{ marginTop: '3px', fontSize: '20px', fontWeight: 900 }}>
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
                    </div>

                    <div
                      style={{
                        flexShrink: 0,
                        color: '#d6b45d',
                        fontSize: '20px',
                        lineHeight: 1,
                      }}
                      aria-hidden="true"
                    >
                      ›
                    </div>
                  </button>

                  <div
                    style={{
                      marginTop: '9px',
                      color: '#777',
                      fontSize: '11px',
                      textAlign: 'right',
                    }}
                  >
                    診断結果を見る
                  </div>
                </section>
              )}

              {/* プレイスタイル */}
                <section
                  style={{
                    padding: '25px 0 15px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent:
                        'space-between',
                      gap: '12px',
                    }}
                  >
                    <div>
                      <h2
                        style={{
                          margin: 0,
                          fontSize: '18px',
                          fontWeight: 800,
                        }}
                      >
                        プレイスタイル
                      </h2>
                      <div
                        style={{
                          marginTop: '5px',
                          color: '#666',
                          fontSize: '12px',
                        }}
                      >
                        プレイヤーからの匿名評価
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
                          fontSize: '11px',
                          whiteSpace:
                            'nowrap',
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
                          fontSize: '21px',
                        }}
                      >
                        ♠
                      </div>
                      <div
                        style={{
                          fontSize: '14px',
                          fontWeight: 700,
                        }}
                      >
                        まだ評価がありません
                      </div>
                      <div
                        style={{
                          marginTop: '6px',
                          color: '#666',
                          fontSize: '12px',
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
                          marginTop: '18px',
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
                            fontSize: '20px',
                          }}
                        >
                          ◌
                        </div>
                        <div
                          style={{
                            fontSize: '15px',
                            fontWeight: 700,
                          }}
                        >
                          評価データを集計中
                        </div>
                        <div
                          style={{
                            marginTop: '10px',
                            fontSize: '13px',
                            color: '#aaa',
                          }}
                        >
                          現在 {ratingCount}人
                        </div>
                        <div
                          style={{
                            marginTop: '7px',
                            fontSize: '12px',
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
                            background: '#222',
                            borderRadius:
                              '999px',
                            overflow: 'hidden',
                          }}
                        >
                          <div
                            style={{
                              width: `${
                                (ratingCount / 3) *
                                100
                              }%`,
                              height: '100%',
                              background: '#fff',
                              borderRadius:
                                '999px',
                            }}
                          />
                        </div>
                        <div
                          style={{
                            marginTop: '7px',
                            color: '#555',
                            fontSize: '10px',
                          }}
                        >
                          {ratingCount} / 3
                        </div>
                      </div>
                    )}
                  {/* 評価3人以上 */}
                  {ratingCount >= 3 &&
                    averageAggression !== null &&
                    averageLooseness !== null && (
                      <div
                        style={{
                          marginTop: '18px',
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
                          {/* 縦軸 */}
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
                                fontSize: '9px',
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
                                fontSize: '9px',
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
                            {/* 象限背景 */}
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
                            {/* 平均評価点 */}
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
                              paddingTop: '8px',
                              color: '#777',
                              fontSize: '9px',
                              fontWeight: 700,
                            }}
                          >
                            <span>PASSIVE</span>
                            <span>AGGRESSIVE</span>
                          </div>
                        </div>
                        <div
                          style={{
                            marginTop: '17px',
                            paddingTop: '14px',
                            borderTop:
                              '1px solid #222',
                            color: '#777',
                            fontSize: '11px',
                            textAlign:
                              'center',
                          }}
                        >
                          {ratingCount}人の匿名評価から算出
                        </div>
                      </div>
                    )}
                  {/* 評価ボタン */}
                  {blockStatus === 'none' && currentUserId !==
                    profile.id && (
                    <button
                      onClick={() =>
                        navigate(
                          `/player/${profile.id}/rate`
                        )
                      }
                      style={{
                        width: '100%',
                        marginTop: '13px',
                        padding: '12px',
                        background: '#111',
                        color: '#fff',
                        border:
                          '1px solid #333',
                        borderRadius:
                          '12px',
                        fontSize: '13px',
                        fontWeight: 700,
                      }}
                    >
                      このプレイヤーを評価する
                    </button>
                  )}
                </section>
                {/* 主なトーナメント実績 */}
                {pokerResults.some((result) => result.is_featured) && (
                  <section style={{ marginTop: '10px', padding: '21px 0', borderTop: '1px solid #242424' }}>
                    <div style={{ fontSize: '17px', fontWeight: 800 }}>主なトーナメント実績</div>
                    <div style={{ marginTop: '5px', color: '#666', fontSize: '12px' }}>このプレイヤーが選んだ主な実績</div>
                    <div style={{ marginTop: '18px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {pokerResults.filter((result) => result.is_featured).map((result) => (
                        <div key={`featured-${result.id}`} style={{ padding: '17px', background: '#0d0d0d', border: '1px solid #343434', borderRadius: '16px' }}>
                          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                            <div style={{ minWidth: 0 }}>
                              <div style={{ color: '#fff', fontSize: '15px', fontWeight: 800, lineHeight: 1.4, wordBreak: 'break-word' }}>{result.tournament_name}</div>
                              <div style={{ marginTop: '5px', color: '#666', fontSize: '11px' }}>
                                {new Date(`${result.played_at}T00:00:00`).toLocaleDateString('ja-JP')}
                                {result.venue ? ` ・ ${result.venue}` : ''}
                              </div>
                            </div>
                            <div style={{ flexShrink: 0, padding: '6px 10px', background: '#171717', border: '1px solid #383838', borderRadius: '999px', color: '#fff', fontSize: '12px', fontWeight: 800 }}>
                              {result.rank_unknown ? '順位不明' : result.rank !== null ? `${result.rank}位` : '順位不明'}
                            </div>
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '13px' }}>
                            {result.entry_count !== null && (
                              <div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', color: '#aaa', fontSize: '11px' }}>{result.entry_count}人参加</div>
                            )}
                            {result.is_itm && (
                              <div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', color: '#fff', fontSize: '11px', fontWeight: 700 }}>ITM</div>
                            )}
                            {result.prize_amount !== null && result.prize_amount > 0 && (
                              <div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', color: '#fff', fontSize: '11px', fontWeight: 700 }}>プライズ相当額 ¥{result.prize_amount.toLocaleString()}</div>
                            )}
                          </div>
                          {result.prize_description && (
                            <div style={{ marginTop: '12px', color: '#aaa', fontSize: '12px', lineHeight: 1.6 }}>獲得内容：{result.prize_description}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}
                  </>
              )}
              {activeTab === 'records' && recordTab === 'ring' && (
                <>
              {/* アミューズリング記録 */}
              {amusementRingResults.length > 0 && (() => {
                const rows = amusementRingResults.map((result) => {
                  const invested = result.starting_stack + result.additional_stack
                  const bbProfit = result.big_blind > 0 ? (result.ending_stack - invested) / result.big_blind : 0
                  const hours = result.play_minutes / 60
                  const bbPerHour = hours > 0 ? bbProfit / hours : 0
                  const startingBb = result.big_blind > 0 ? result.starting_stack / result.big_blind : 0
                  return { ...result, bbProfit, bbPerHour, startingBb, hours }
                })
                const signed = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(1)}`
                return (
                  <section style={{ marginTop: '10px', padding: '21px 0', borderTop: '1px solid #242424' }}>
                    <div style={{ fontSize: '17px', fontWeight: 800 }}>アミューズリング記録</div>
                    <div style={{ marginTop: '5px', color: '#666', fontSize: '12px' }}>公開設定されたセッションのみ表示しています</div>
                    <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {rows.map((result) => (
                        <div key={result.id} style={{ padding: '16px', background: '#0d0d0d', border: '1px solid #242424', borderRadius: '16px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start' }}>
                            <div style={{ minWidth: 0 }}><div style={{ color: '#fff', fontSize: '15px', fontWeight: 800 }}>{result.venue}</div><div style={{ marginTop: '5px', color: '#666', fontSize: '11px' }}>{new Date(`${result.played_at}T00:00:00`).toLocaleDateString('ja-JP')} ・ {result.game_type} ・ {result.small_blind}/{result.big_blind}</div></div>
                            <div style={{ flexShrink: 0, textAlign: 'right' }}><div style={{ fontSize: '15px', fontWeight: 800 }}>{signed(result.bbProfit)}BB</div><div style={{ marginTop: '3px', color: '#777', fontSize: '10px' }}>{signed(result.bbPerHour)} BB/h</div></div>
                          </div>
                          <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '7px' }}><div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', color: '#aaa', fontSize: '11px' }}>開始 {result.startingBb.toFixed(1)}BB</div><div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', color: '#aaa', fontSize: '11px' }}>{Math.floor(result.play_minutes / 60)}時間{result.play_minutes % 60 > 0 ? `${result.play_minutes % 60}分` : ''}</div></div>
                          {result.memo && <div style={{ marginTop: '13px', paddingTop: '12px', borderTop: '1px solid #222', color: '#888', fontSize: '12px', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{result.memo}</div>}
                        </div>
                      ))}
                    </div>
                  </section>
                )
              })()}
                </>
              )}
              {activeTab === 'records' && recordTab === 'cash' && (
                <>
              {/* キャッシュゲーム記録 */}
              {cashGameResults.length > 0 && (
                <section style={{ marginTop: '10px', padding: '21px 0', borderTop: '1px solid #242424' }}>
                  <div style={{ fontSize: '17px', fontWeight: 800 }}>キャッシュゲーム記録</div>
                  <div style={{ marginTop: '5px', color: '#666', fontSize: '12px' }}>
                    公開設定された記録のみ表示しています
                  </div>
                  <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {cashGameResults.map((result) => {
                      const bbProfit =
                        Number(result.big_blind) > 0
                          ? Number(result.profit_amount) / Number(result.big_blind)
                          : 0
                      const hours = result.play_minutes / 60
                      const bbPerHour = hours > 0 ? bbProfit / hours : 0
                      const signedBb = (value: number) =>
                        `${value >= 0 ? '+' : ''}${value.toFixed(1)}`
                      return (
                        <div
                          key={result.id}
                          style={{
                            padding: '16px',
                            background: '#0d0d0d',
                            border: '1px solid #242424',
                            borderRadius: '16px',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start' }}>
                            <div style={{ minWidth: 0 }}>
                              <div style={{ color: '#fff', fontSize: '15px', fontWeight: 800, wordBreak: 'break-word' }}>
                                {result.venue}
                              </div>
                              <div style={{ marginTop: '5px', color: '#666', fontSize: '11px', lineHeight: 1.5 }}>
                                {new Date(`${result.played_at}T00:00:00`).toLocaleDateString('ja-JP')}
                                {' ・ '}
                                {result.play_type === 'live' ? 'ライブ' : 'オンライン'}
                                {result.play_type === 'online' && result.record_type === 'daily' ? ' ・ 1日まとめ' : ''}
                                {' ・ '}
                                {result.game_type}
                                {' ・ '}
                                {result.currency} {Number(result.small_blind).toLocaleString()}/{Number(result.big_blind).toLocaleString()}
                              </div>
                            </div>
                            <div style={{ flexShrink: 0, textAlign: 'right' }}>
                              <div style={{ color: '#fff', fontSize: '15px', fontWeight: 800 }}>
                                {signedBb(bbProfit)}BB
                              </div>
                              <div style={{ marginTop: '3px', color: '#777', fontSize: '10px' }}>
                                {signedBb(bbPerHour)} BB/h
                              </div>
                            </div>
                          </div>
                          <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '7px' }}>
                            <div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', color: '#aaa', fontSize: '11px' }}>
                              収支 {Number(result.profit_amount) >= 0 ? '+' : ''}
                              {Number(result.profit_amount).toLocaleString()} {result.currency}
                            </div>
                            <div style={{ padding: '6px 9px', background: '#141414', borderRadius: '8px', color: '#aaa', fontSize: '11px' }}>
                              {Math.floor(result.play_minutes / 60)}時間
                              {result.play_minutes % 60 > 0 ? `${result.play_minutes % 60}分` : ''}
                            </div>
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
                </section>
              )}
                </>
              )}
              {activeTab === 'records' && recordTab === 'tournament' && (
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
                  <div>
                    <div
                      style={{
                        fontSize: '17px',
                        fontWeight: 800,
                      }}
                    >
                      トーナメント記録
                    </div>
                    <div
                      style={{
                        marginTop: '5px',
                        color: '#666',
                        fontSize: '12px',
                      }}
                    >
                      トーナメントの記録
                    </div>
                  </div>
                  {pokerResults.length === 0 ? (
                    <div
                      style={{
                        marginTop: '18px',
                        padding: '30px 20px',
                        background: '#0d0d0d',
                        border:
                          '1px solid #242424',
                        borderRadius: '16px',
                        textAlign: 'center',
                      }}
                    >
                      <div
                        style={{
                          width: '48px',
                          height: '48px',
                          margin:
                            '0 auto 13px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent:
                            'center',
                          background: '#171717',
                          border:
                            '1px solid #292929',
                          borderRadius: '50%',
                          fontSize: '21px',
                        }}
                      >
                        ♠
                      </div>
                      <div
                        style={{
                          fontSize: '14px',
                          fontWeight: 700,
                        }}
                      >
                        まだトーナメント記録がありません
                      </div>
                      <div
                        style={{
                          marginTop: '6px',
                          color: '#666',
                          fontSize: '12px',
                          lineHeight: 1.5,
                        }}
                      >
                        このプレイヤーの公開記録が登録されると
                        <br />
                        ここに表示されます
                      </div>
                    </div>
                  ) : (
                    <div
                      style={{
                        marginTop: '18px',
                        display: 'flex',
                        flexDirection:
                          'column',
                        gap: '10px',
                      }}
                    >
                      {pokerResults.map(
                        (result) => (
                          <div
                            key={result.id}
                            style={{
                              padding: '16px',
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
                                display: 'flex',
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
                                    color: '#fff',
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
                                    marginTop:
                                      '5px',
                                    color: '#666',
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
                              {result.rank !==
                                null && (
                                <div
                                  style={{
                                    flexShrink: 0,
                                    padding:
                                      '6px 10px',
                                    background:
                                      '#171717',
                                    border:
                                      '1px solid #303030',
                                    borderRadius:
                                      '999px',
                                    color: '#fff',
                                    fontSize:
                                      '12px',
                                    fontWeight:
                                      800,
                                  }}
                                >
                                  {result.rank}位
                                </div>
                              )}
                            </div>
                            {(result.entry_count !==
                              null ||
                              result.prize_amount !==
                                null) && (
                              <div
                                style={{
                                  display: 'flex',
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
                                      color: '#aaa',
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
                                      color: '#fff',
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
        export default PlayerProfile
