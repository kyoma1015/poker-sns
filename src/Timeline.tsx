import { useEffect, useState } from 'react'

import { useNavigate } from 'react-router-dom'

import { supabase } from './supabase'

const playerTypeEmoji: Record<string, string> = {lion:'🦁',tiger:'🐯',leopard:'🐆',bison:'🦬',gorilla:'🦍',rhino:'🦏',shark:'🦈',owl:'🦉',eagle:'🦅',elephant:'🐘',giraffe:'🦒',wolf:'🐺',hyena:'🐾',cat:'🐈',chameleon:'🦎',dolphin:'🐬',fox:'🦊',snake:'🐍',raccoon:'🦝',turtle:'🐢',rabbit:'🐇',crocodile:'🐊',hedgehog:'🦔',deer:'🦌',sloth:'🦥',dog:'🐕',bear:'🐻',bull:'🐄',badger:'🦡',monkey:'🐒',magpie:'🐦‍⬛',penguin:'🐧',horse:'🐎',squirrel:'🐿️',mountain_goat:'🐐',otter:'🦦'}

type Post = {

  id: string

  user_id: string

  content: string

  created_at: string

  profile?: {

    display_name: string

    poker_id: string

    avatar_url: string | null

  }

  likeCount: number

  likedByMe: boolean

  commentCount: number

  post_type: 'normal' | 'result'

  result_type: 'tournament' | 'amusement' | 'cash' | 'player_type' | null

  result_id: string | null

  playerTypeData?: { animal_name_ja: string; catchphrase: string; result_type_key: string } | null
  resultData?: {

    tournament_name: string

    rank: number | null

    rank_unknown: boolean

    entry_count: number | null

    is_itm: boolean

    total_entry_fee: number | null

    prize_amount: number

    venue: string | null

    played_at: string

  } | null

  amusementResultData?: {

    venue: string

    game_type: string

    small_blind: number

    big_blind: number

    starting_stack: number

    additional_stack: number

    ending_stack: number

    play_minutes: number

    played_at: string

  } | null

  cashResultData?: {

    played_at: string

    play_type: 'live' | 'online'

    record_type: 'session' | 'daily'

    venue: string

    game_type: string

    small_blind: number

    big_blind: number

    currency: string

    profit_amount: number

    profit_jpy: number

    play_minutes: number

  } | null

}

type TimelineMode = 'following' | 'all'

function Timeline() {

  const navigate = useNavigate()
  useEffect(() => {
    if (window.location.search.includes('compose=1')) {
      const timer = window.setTimeout(() => document.getElementById('poker-id-post-composer')?.focus(), 80)
      return () => window.clearTimeout(timer)
    }
  }, [])

  const [posts, setPosts] = useState<Post[]>([])

  const [content, setContent] = useState('')

  const [currentUserId, setCurrentUserId] = useState('')

  const [message, setMessage] = useState('')

  const [isPosting, setIsPosting] = useState(false)

  const [timelineMode, setTimelineMode] =

    useState<TimelineMode>('following')

  const [followingIds, setFollowingIds] =

    useState<string[]>([])

  const loadPosts = async () => {

    const {

      data: { user },

    } = await supabase.auth.getUser()

    if (!user) {

      navigate('/login')

      return

    }

    setCurrentUserId(user.id)

    const { data: followData, error: followError } =

      await supabase

        .from('follows')

        .select('following_id')

        .eq('follower_id', user.id)

    if (followError) {

      console.error(followError)

      setMessage(

        `フォロー情報の取得に失敗しました：${followError.message}`

      )

      return

    }

    const loadedFollowingIds =

      followData?.map(

        (follow) => follow.following_id

      ) || []

    setFollowingIds(loadedFollowingIds)

    const { data: postData, error: postError } =

      await supabase

        .from('posts')

        .select('*')

        .order('created_at', {

          ascending: false,

        })

    if (postError) {

      console.error(postError)

      setMessage(

        `投稿の取得に失敗しました：${postError.message}`

      )

      return

    }

    if (!postData || postData.length === 0) {

      setPosts([])

      setMessage('')

      return

    }

    const tournamentResultIds = postData

      .filter(

        (post) =>

          post.post_type === 'result' &&

          post.result_type === 'tournament' &&

          post.result_id

      )

      .map((post) => post.result_id as string)

    let tournamentResults: any[] = []

    if (tournamentResultIds.length > 0) {

      const { data, error } = await supabase

        .from('poker_results')

        .select(

          'id, tournament_name, rank, rank_unknown, entry_count, is_itm, total_entry_fee, prize_amount, venue, played_at'

        )

        .in('id', tournamentResultIds)

      if (error) {

        console.error('トーナメント結果取得エラー:', error)

      } else {

        tournamentResults = data || []

      }

    }

    const amusementResultIds = postData

      .filter(

        (post) =>

          post.post_type === 'result' &&

          post.result_type === 'amusement' &&

          post.result_id

      )

      .map((post) => post.result_id as string)

    let amusementResults: any[] = []

    if (amusementResultIds.length > 0) {

      const { data, error } = await supabase

        .from('amusement_ring_results')

        .select(

          'id, venue, game_type, small_blind, big_blind, starting_stack, additional_stack, ending_stack, play_minutes, played_at'

        )

        .in('id', amusementResultIds)

      if (error) {

        console.error('アミューズリング結果取得エラー:', error)

      } else {

        amusementResults = data || []

      }

    }

  const cashResultIds = postData

    .filter(

      (post) =>

        post.post_type === 'result' &&

        post.result_type === 'cash' &&

        post.result_id

    )

    .map((post) => post.result_id as string)

  let cashResults: any[] = []

  if (cashResultIds.length > 0) {

    const { data, error } = await supabase

      .from('cash_game_results')

      .select(

        'id, played_at, play_type, record_type, venue, game_type, small_blind, big_blind, currency, profit_amount, profit_jpy, play_minutes'

      )

      .in('id', cashResultIds)

    if (error) {

      console.error('キャッシュゲーム結果取得エラー:', error)

    } else {

      cashResults = data || []

    }

  }



    const playerTypeResultIds = [...new Set(postData
      .filter((post) => post.post_type === 'result' && post.result_type === 'player_type' && post.result_id)
      .map((post) => post.result_id as string))]
    const playerTypeResults = new Map<string, { animal_name_ja: string; catchphrase: string; result_type_key: string }>()
    await Promise.all(playerTypeResultIds.map(async (resultId) => {
      const { data, error } = await supabase.rpc('get_player_type_v2_result_detail', { p_result_id: resultId })
      if (error) { console.error('プレイヤータイプ取得エラー:', error); return }
      const row = Array.isArray(data) ? data[0] : data
      if (row) playerTypeResults.set(resultId, {
        animal_name_ja: String(row.animal_name_ja || ''),
        catchphrase: String(row.catchphrase || ''),
        result_type_key: String(row.result_type_key || ''),
      })
    }))

    const postIds = postData.map(

      (post) => post.id

    )

    const { data: likes, error: likesError } =

      await supabase

        .from('post_likes')

        .select('post_id, user_id')

        .in('post_id', postIds)

    if (likesError) {

      console.error(likesError)

      setMessage(

        `いいね情報の取得に失敗しました：${likesError.message}`

      )

      return

    }

    const {

      data: comments,

      error: commentsError,

    } = await supabase

      .from('post_comments')

      .select('post_id')

      .in('post_id', postIds)

    if (commentsError) {

      console.error(commentsError)

      setMessage(

        `コメント情報の取得に失敗しました：${commentsError.message}`

      )

      return

    }

    const postUserIds = [

      ...new Set(

        postData.map(

          (post) => post.user_id

        )

      ),

    ]

    const {

      data: profiles,

      error: profileError,

    } = await supabase

      .from('profiles')

      .select(

        'id, display_name, poker_id, avatar_url'

      )

      .in('id', postUserIds)

    if (profileError) {

      console.error(profileError)

      setMessage(

        `プロフィールの取得に失敗しました：${profileError.message}`

      )

      return

    }

    const postsWithData: Post[] =

      postData.map((post) => {

        const profile = profiles?.find(

          (item) =>

            item.id === post.user_id

        )

        const postLikes =

          likes?.filter(

            (like) =>

              like.post_id === post.id

          ) || []

        const commentCount =

          comments?.filter(

            (comment) =>

              comment.post_id === post.id

          ).length || 0

        return {

          ...post,

          profile: profile

            ? {

                display_name:

                  profile.display_name,

                poker_id:

                  profile.poker_id,

                avatar_url:

                  profile.avatar_url,

              }

            : undefined,

          likeCount: postLikes.length,

          likedByMe: postLikes.some(

            (like) =>

              like.user_id === user.id

          ),

          commentCount,

          playerTypeData: post.result_type === 'player_type' && post.result_id
            ? playerTypeResults.get(post.result_id) || null : null,
          resultData:

            post.post_type === 'result' &&

            post.result_type === 'tournament' &&

            post.result_id

              ? tournamentResults.find(

                  (result) => result.id === post.result_id

                ) || null

              : null,

          amusementResultData:

            post.post_type === 'result' &&

            post.result_type === 'amusement' &&

            post.result_id

              ? amusementResults.find(

                  (result) => result.id === post.result_id

                ) || null

              : null,

        cashResultData:

          post.post_type === 'result' &&

          post.result_type === 'cash' &&

          post.result_id

            ? cashResults.find((result) => result.id === post.result_id) || null

            : null,

        }

      })

    setPosts(postsWithData)

    setMessage('')

  }

  useEffect(() => {

    loadPosts()

  }, [])

  const handlePost = async () => {

    const trimmedContent =

      content.trim()

    if (!trimmedContent) {

      setMessage(

        '投稿内容を入力してください。'

      )

      return

    }

    const {

      data: { user },

    } = await supabase.auth.getUser()

    if (!user) {

      setMessage(

        'ログイン情報が確認できませんでした。'

      )

      return

    }

    setIsPosting(true)

    setMessage('投稿中...')

    const { error } = await supabase

      .from('posts')

      .insert({

        user_id: user.id,

        content: trimmedContent,

      })

    if (error) {

      console.error(error)

      setMessage(

        `投稿できませんでした：${error.message}`

      )

      setIsPosting(false)

      return

    }

    setContent('')

    setMessage('')

    setIsPosting(false)

    await loadPosts()

  }

  const handleLike = async (

    post: Post

  ) => {

    if (!currentUserId) return

    if (post.likedByMe) {

      const { error } = await supabase

        .from('post_likes')

        .delete()

        .eq('post_id', post.id)

        .eq(

          'user_id',

          currentUserId

        )

      if (error) {

        console.error(error)

        setMessage(

          `いいねを解除できませんでした：${error.message}`

        )

        return

      }

    } else {

      const { error } = await supabase

        .from('post_likes')

        .insert({

          post_id: post.id,

          user_id: currentUserId,

        })

      if (error) {

        console.error(error)

        setMessage(

          `いいねできませんでした：${error.message}`

        )

        return

      }

      if (

        post.user_id !==

        currentUserId

      ) {

        const {

          error:

            notificationError,

        } = await supabase

          .from('notifications')

          .insert({

            user_id:

              post.user_id,

            actor_id:

              currentUserId,

            type: 'like',

            post_id: post.id,

          })

        if (

          notificationError &&

          notificationError.code !==

            '23505'

        ) {

          console.error(

            'いいね通知作成エラー:',

            notificationError

          )

        }

      }

    }

    setMessage('')

    await loadPosts()

  }

  const handleDelete = async (

    postId: string

  ) => {

    const { error } = await supabase

      .from('posts')

      .delete()

      .eq('id', postId)

    if (error) {

      console.error(error)

      setMessage(

        `削除できませんでした：${error.message}`

      )

      return

    }

    setMessage('')

    await loadPosts()

  }

  const handleProfileClick = (

    userId: string

  ) => {

    if (

      userId === currentUserId

    ) {

      navigate('/profile')

      return

    }

    navigate(

      `/player/${userId}`

    )

  }

  const visiblePosts =

    timelineMode === 'all'

      ? posts

      : posts.filter(

          (post) =>

            post.user_id ===

              currentUserId ||

            followingIds.includes(

              post.user_id

            )

        )

  const formatPostTime = (

    createdAt: string

  ) => {

    const created =

      new Date(createdAt)

    const now = new Date()

    const difference =

      now.getTime() -

      created.getTime()

    const minutes = Math.floor(

      difference / 60000

    )

    if (minutes < 1) {

      return 'たった今'

    }

    if (minutes < 60) {

      return `${minutes}分`

    }

    const hours = Math.floor(

      minutes / 60

    )

    if (hours < 24) {

      return `${hours}時間`

    }

    const days = Math.floor(

      hours / 24

    )

    if (days < 7) {

      return `${days}日`

    }

    return created.toLocaleDateString(

      'ja-JP',

      {

        month: 'numeric',

        day: 'numeric',

      }

    )

  }

  const formatPlayedDate = (value: string) => {

    const [year, month, day] = value.split('-')

    if (!year || !month || !day) return value

    return `${year}.${month}.${day}`

  }

  const formatResultMoney = (value: number | null | undefined) => {

    if (value === null || value === undefined) return '—'

    return `¥${Number(value).toLocaleString('ja-JP')}`

  }

  const renderTournamentResultCard = (post: Post) => {

    const result = post.resultData

    if (!result) return null

    let icon = '♠'

    let badge = 'TOURNAMENT'

    if (!result.rank_unknown && result.rank === 1) {

      icon = '🏆'

      badge = 'WINNER'

    } else if (!result.rank_unknown && result.rank === 2) {

      icon = '🥈'

      badge = '2ND PLACE'

    } else if (!result.rank_unknown && result.rank === 3) {

      icon = '🥉'

      badge = '3RD PLACE'

    } else if (result.is_itm) {

      icon = '♦'

      badge = 'ITM'

    }

    const prize = Number(result.prize_amount || 0)

    const entry = result.total_entry_fee

    const profit = entry === null ? null : prize - Number(entry)

    return (

      <div

        style={{

          margin: '2px 0 13px',

          padding: '16px',

          border: '1px solid #303030',

          borderRadius: '16px',

          background:

            result.rank === 1

              ? 'linear-gradient(145deg, #1d1a0c 0%, #0d0d0d 62%)'

              : '#0d0d0d',

          overflow: 'hidden',

        }}

      >

        <div

          style={{

            display: 'flex',

            alignItems: 'center',

            justifyContent: 'space-between',

            gap: '12px',

          }}

        >

          <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>

            <span style={{ fontSize: '26px', lineHeight: 1 }}>{icon}</span>

            <span

              style={{

                fontSize: '12px',

                fontWeight: 900,

                letterSpacing: '0.8px',

              }}

            >

              {badge}

            </span>

          </div>

          <div style={{ textAlign: 'right', flexShrink: 0 }}>

            <div

              style={{

                color: '#aaa',

                fontSize: '11px',

                fontWeight: 800,

                letterSpacing: '0.3px',

              }}

            >

              {formatPlayedDate(result.played_at)}

            </div>

            <div

              style={{

                marginTop: '3px',

                color: '#666',

                fontSize: '10px',

                fontWeight: 800,

                letterSpacing: '0.6px',

              }}

            >

              TOURNAMENT RESULT

            </div>

          </div>

        </div>

        <div

          style={{

            marginTop: '13px',

            fontSize: '17px',

            fontWeight: 850,

            lineHeight: 1.35,

          }}

        >

          {result.tournament_name}

        </div>

        {result.venue && (

          <div style={{ marginTop: '4px', color: '#777', fontSize: '12px' }}>

            {result.venue}

          </div>

        )}

        <div

          style={{

            marginTop: '15px',

            display: 'flex',

            alignItems: 'baseline',

            gap: '7px',

            flexWrap: 'wrap',

          }}

        >

          <span

            style={{

              fontSize:

                result.rank !== null && result.rank <= 3 ? '28px' : '23px',

              fontWeight: 900,

              letterSpacing: '-0.8px',

            }}

          >

            {result.rank_unknown || result.rank === null

              ? '順位不明'

              : `${result.rank}位`}

          </span>

          {result.entry_count !== null && (

            <span style={{ color: '#777', fontSize: '13px', fontWeight: 650 }}>

              / {result.entry_count.toLocaleString('ja-JP')} Entries

            </span>

          )}

        </div>

        <div

          style={{

            marginTop: '15px',

            paddingTop: '13px',

            borderTop: '1px solid #242424',

            display: 'grid',

            gridTemplateColumns:

              profit === null ? '1fr 1fr' : '1fr 1fr 1fr',

            gap: '10px',

          }}

        >

          <div>

            <div style={{ color: '#666', fontSize: '10px' }}>PRIZE VALUE</div>

            <div style={{ marginTop: '3px', fontSize: '13px', fontWeight: 800 }}>

              {formatResultMoney(prize)}

            </div>

          </div>

          <div>

            <div style={{ color: '#666', fontSize: '10px' }}>ENTRY</div>

            <div style={{ marginTop: '3px', fontSize: '13px', fontWeight: 800 }}>

              {formatResultMoney(entry)}

            </div>

          </div>

          {profit !== null && (

            <div>

              <div style={{ color: '#666', fontSize: '10px' }}>PROFIT</div>

              <div style={{ marginTop: '3px', fontSize: '13px', fontWeight: 900 }}>

                {profit > 0 ? '+' : ''}

                {formatResultMoney(profit)}

              </div>

            </div>

          )}

        </div>

      </div>

    )

  }

  const renderAmusementResultCard = (post: Post) => {

    const result = post.amusementResultData

    if (!result || !result.big_blind) return null

    const invested =

      Number(result.starting_stack) + Number(result.additional_stack || 0)

    const chipProfit = Number(result.ending_stack) - invested

    const bbProfit = chipProfit / Number(result.big_blind)

    const hours = Number(result.play_minutes) / 60

    const bbPerHour = hours > 0 ? bbProfit / hours : null

    let badge = 'WIN'

    let symbol = '▲'

    let accent = '#d7d7d7'

    let background =

      'linear-gradient(145deg, #101510 0%, #0d0d0d 68%)'

    let border = '#344034'

    if (bbProfit >= 100) {

      badge = 'BIG WIN'

      symbol = '♠'

      accent = '#ffffff'

      background =

        'linear-gradient(145deg, #1c2416 0%, #0d0d0d 68%)'

      border = '#536344'

    } else if (bbProfit >= 0) {

      badge = 'WIN'

      symbol = '▲'

      accent = '#e4e4e4'

      background =

        'linear-gradient(145deg, #111611 0%, #0d0d0d 68%)'

      border = '#344034'

    } else if (bbProfit > -100) {

      badge = 'LOSS'

      symbol = '▼'

      accent = '#b8b8b8'

      background =

        'linear-gradient(145deg, #151111 0%, #0d0d0d 68%)'

      border = '#3d3030'

    } else {

      badge = 'BIG LOSS'

      symbol = '▼'

      accent = '#d0d0d0'

      background =

        'linear-gradient(145deg, #241313 0%, #0d0d0d 68%)'

      border = '#654040'

    }

    const formatBB = (value: number) =>

      `${value > 0 ? '+' : ''}${Number(value.toFixed(1))}BB`

    const formatHours = (minutes: number) => {

      const h = Math.floor(minutes / 60)

      const m = minutes % 60

      if (h > 0 && m > 0) return `${h}時間${m}分`

      if (h > 0) return `${h}時間`

      return `${m}分`

    }

    return (

      <div

        style={{

          margin: '2px 0 13px',

          padding: '16px',

          border: `1px solid ${border}`,

          borderRadius: '16px',

          background,

          overflow: 'hidden',

        }}

      >

        <div

          style={{

            display: 'flex',

            alignItems: 'center',

            justifyContent: 'space-between',

            gap: '12px',

          }}

        >

          <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>

            <span

              style={{

                width: '27px',

                height: '27px',

                display: 'inline-flex',

                alignItems: 'center',

                justifyContent: 'center',

                border: `1px solid ${border}`,

                borderRadius: '50%',

                color: accent,

                fontSize: '14px',

                fontWeight: 900,

              }}

            >

              {symbol}

            </span>

            <span

              style={{

                color: accent,

                fontSize: '12px',

                fontWeight: 900,

                letterSpacing: '0.9px',

              }}

            >

              {badge}

            </span>

          </div>

          <div style={{ textAlign: 'right', flexShrink: 0 }}>

            <div

              style={{

                color: '#aaa',

                fontSize: '11px',

                fontWeight: 800,

                letterSpacing: '0.3px',

              }}

            >

              {formatPlayedDate(result.played_at)}

            </div>

            <div

              style={{

                marginTop: '3px',

                color: '#666',

                fontSize: '10px',

                fontWeight: 800,

                letterSpacing: '0.6px',

              }}

            >

              AMUSEMENT RING

            </div>

          </div>

        </div>

        <div

          style={{

            marginTop: '13px',

            fontSize: '17px',

            fontWeight: 850,

            lineHeight: 1.35,

          }}

        >

          {result.venue}

        </div>

        <div

          style={{

            marginTop: '4px',

            color: '#777',

            fontSize: '12px',

          }}

        >

          {result.game_type}　{Number(result.small_blind).toLocaleString('ja-JP')} /{' '}

          {Number(result.big_blind).toLocaleString('ja-JP')}

        </div>

        <div

          style={{

            marginTop: '16px',

            display: 'flex',

            alignItems: 'baseline',

            gap: '8px',

            flexWrap: 'wrap',

          }}

        >

          <span

            style={{

              color: accent,

              fontSize: bbProfit >= 100 || bbProfit <= -100 ? '31px' : '28px',

              fontWeight: 950,

              letterSpacing: '-1px',

            }}

          >

            {formatBB(bbProfit)}

          </span>

        </div>

        <div

          style={{

            marginTop: '15px',

            paddingTop: '13px',

            borderTop: `1px solid ${border}`,

            display: 'grid',

            gridTemplateColumns: '1fr 1fr',

            gap: '10px',

          }}

        >

          <div>

            <div style={{ color: '#666', fontSize: '10px' }}>BB / HOUR</div>

            <div

              style={{

                marginTop: '3px',

                color: accent,

                fontSize: '13px',

                fontWeight: 850,

              }}

            >

              {bbPerHour === null ? '—' : formatBB(bbPerHour)}

            </div>

          </div>

          <div>

            <div style={{ color: '#666', fontSize: '10px' }}>PLAY TIME</div>

            <div

              style={{

                marginTop: '3px',

                fontSize: '13px',

                fontWeight: 800,

              }}

            >

              {formatHours(Number(result.play_minutes))}

            </div>

          </div>

        </div>

      </div>

    )

  }



  const renderCashResultCard = (post: Post) => {

    const result = post.cashResultData

    if (!result || !result.big_blind) return null

    const profitJpy = Number(result.profit_jpy || 0)

    const bbProfit = Number(result.profit_amount || 0) / Number(result.big_blind)

    const hours = Number(result.play_minutes) / 60

    const bbPerHour = hours > 0 ? bbProfit / hours : null

    const isWin = profitJpy >= 0

    const accent = isWin ? '#f2f2f2' : '#c7c7c7'

    const border = isWin ? '#3c4437' : '#493535'

    const background = isWin

      ? 'linear-gradient(145deg, #171b14 0%, #0d0d0d 68%)'

      : 'linear-gradient(145deg, #1c1212 0%, #0d0d0d 68%)'

    const formatBB = (value: number) =>

      `${value > 0 ? '+' : ''}${Number(value.toFixed(1))}BB`

    const formatHours = (minutes: number) => {

      const h = Math.floor(minutes / 60)

      const m = minutes % 60

      if (h > 0 && m > 0) return `${h}時間${m}分`

      if (h > 0) return `${h}時間`

      return `${m}分`

    }

    return (

      <div style={{ margin: '2px 0 13px', padding: '16px', border: `1px solid ${border}`, borderRadius: '16px', background, overflow: 'hidden' }}>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>

          <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>

            <span style={{ width: '27px', height: '27px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', border: `1px solid ${border}`, borderRadius: '50%', color: accent, fontSize: '14px', fontWeight: 900 }}>

              {isWin ? '▲' : '▼'}

            </span>

            <span style={{ color: accent, fontSize: '12px', fontWeight: 900, letterSpacing: '0.9px' }}>

              {isWin ? 'WIN' : 'LOSS'}

            </span>

          </div>

          <div style={{ textAlign: 'right', flexShrink: 0 }}>

            <div style={{ color: '#aaa', fontSize: '11px', fontWeight: 800, letterSpacing: '0.3px' }}>

              {formatPlayedDate(result.played_at)}

            </div>

            <div style={{ marginTop: '3px', color: '#666', fontSize: '10px', fontWeight: 800, letterSpacing: '0.6px' }}>

              {result.play_type === 'online' ? 'ONLINE CASH' : 'LIVE CASH'}

            </div>

          </div>

        </div>

        <div style={{ marginTop: '13px', fontSize: '17px', fontWeight: 850, lineHeight: 1.35 }}>

          {result.venue}

        </div>

        <div style={{ marginTop: '4px', color: '#777', fontSize: '12px' }}>

          {result.game_type}　{Number(result.small_blind).toLocaleString('ja-JP')} / {Number(result.big_blind).toLocaleString('ja-JP')} {result.currency}

        </div>

        <div style={{ marginTop: '16px' }}>

          <div style={{ color: accent, fontSize: '30px', fontWeight: 950, letterSpacing: '-1px' }}>

            {profitJpy > 0 ? '+' : ''}{profitJpy.toLocaleString('ja-JP')}円

          </div>

          <div style={{ marginTop: '5px', color: '#888', fontSize: '13px', fontWeight: 750 }}>

            {formatBB(bbProfit)}

          </div>

        </div>

        <div style={{ marginTop: '15px', paddingTop: '13px', borderTop: `1px solid ${border}`, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>

          <div>

            <div style={{ color: '#666', fontSize: '10px' }}>BB / HOUR</div>

            <div style={{ marginTop: '3px', color: accent, fontSize: '13px', fontWeight: 850 }}>

              {bbPerHour === null ? '—' : formatBB(bbPerHour)}

            </div>

          </div>

          <div>

            <div style={{ color: '#666', fontSize: '10px' }}>PLAY TIME</div>

            <div style={{ marginTop: '3px', fontSize: '13px', fontWeight: 800 }}>

              {formatHours(Number(result.play_minutes))}

            </div>

          </div>

        </div>

      </div>

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

        {/* ホームのコンパクトなツール導線。スクロール時は投稿と一緒に隠れる */}
        <section style={{ padding: '12px 0 13px', borderBottom: '1px solid #242424' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 9 }}>
            <strong style={{ fontSize: 13 }}>♠ ポーカーツール</strong>
            <button type="button" onClick={() => window.dispatchEvent(new Event('poker-id-open-menu'))} style={{ width: 'auto', padding: '2px 0', background: 'transparent', color: '#999', fontSize: 11 }}>すべて見る ›</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 7 }}>
            {[
              { label: 'TDAクイズ', sub: '裁定を学ぶ', icon: '♠', url: '/tda' },
              { label: 'TDA検索', sub: 'ルールを調べる', icon: '⌕', url: '/tda' },
              { label: '実戦記録', sub: '今日の成績', icon: '▥', url: '/profile' },
            ].map((tool) => (
              <button key={tool.label} type="button" onClick={() => navigate(tool.url)} style={{ minWidth: 0, padding: '11px 3px 9px', border: '1px solid #2c2c2c', borderRadius: 12, background: '#151515', color: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <span style={{ fontSize: 21, lineHeight: 1.1 }}>{tool.icon}</span>
                <span style={{ fontSize: 12, fontWeight: 800, whiteSpace: 'nowrap' }}>{tool.label}</span>
                <span style={{ fontSize: 10, color: '#999', whiteSpace: 'nowrap' }}>{tool.sub}</span>
              </button>
            ))}
          </div>
        </section>

        {/* タイムライン切り替え */}

        <div

          style={{

            display: 'grid',

            gridTemplateColumns:

              '1fr 1fr',

            margin: '0 -20px',

            borderBottom:

              '1px solid #242424',

          }}

        >

          <button

            onClick={() =>

              setTimelineMode(

                'following'

              )

            }

            style={{

              position: 'relative',

              padding: '16px 8px',

              background:

                'transparent',

              color:

                timelineMode ===

                'following'

                  ? '#fff'

                  : '#777',

              fontSize: '14px',

              fontWeight:

                timelineMode ===

                'following'

                  ? 700

                  : 500,

              borderRadius: 0,

            }}

          >

            フォロー中

            {timelineMode ===

              'following' && (

              <span

                style={{

                  position:

                    'absolute',

                  left: '32%',

                  right: '32%',

                  bottom: 0,

                  height: '3px',

                  borderRadius:

                    '999px',

                  background:

                    '#fff',

                }}

              />

            )}

          </button>

          <button

            onClick={() =>

              setTimelineMode(

                'all'

              )

            }

            style={{

              position: 'relative',

              padding: '16px 8px',

              background:

                'transparent',

              color:

                timelineMode ===

                'all'

                  ? '#fff'

                  : '#777',

              fontSize: '14px',

              fontWeight:

                timelineMode ===

                'all'

                  ? 700

                  : 500,

              borderRadius: 0,

            }}

          >

            すべて

            {timelineMode ===

              'all' && (

              <span

                style={{

                  position:

                    'absolute',

                  left: '32%',

                  right: '32%',

                  bottom: 0,

                  height: '3px',

                  borderRadius:

                    '999px',

                  background:

                    '#fff',

                }}

              />

            )}

          </button>

        </div>

        {/* 投稿作成 */}

        <section

          style={{

            margin: '0 -20px',

            padding: '18px 20px',

            borderBottom:

              '8px solid #0b0b0b',

          }}

        >

          <textarea

            id="poker-id-post-composer"
            placeholder="いま何してる？ ポーカーの話をしよう。"

            value={content}

            onChange={(e) =>

              setContent(

                e.target.value

              )

            }

            maxLength={500}

            style={{

              minHeight: '78px',

              padding: 0,

              background:

                'transparent',

              border: 'none',

              borderRadius: 0,

              fontSize: '16px',

              lineHeight: 1.55,

              resize: 'none',

            }}

          />

          <div

            style={{

              display: 'flex',

              alignItems: 'center',

              justifyContent:

                'space-between',

              gap: '15px',

              marginTop: '10px',

            }}

          >

            <span

              style={{

                color:

                  content.length >

                  450

                    ? '#ddd'

                    : '#666',

                fontSize: '12px',

              }}

            >

              {content.length}/500

            </span>

            <button

              onClick={handlePost}

              disabled={

                isPosting ||

                !content.trim()

              }

              style={{

                width: 'auto',

                minWidth: '86px',

                padding:

                  '9px 18px',

                borderRadius:

                  '999px',

                background: '#fff',

                color: '#000',

                fontSize: '14px',

                fontWeight: 800,

              }}

            >

              {isPosting

                ? '投稿中...'

                : '投稿'}

            </button>

          </div>

        </section>

        {message && (

          <div

            style={{

              margin: '12px 0',

              padding:

                '11px 13px',

              borderRadius:

                '10px',

              background: '#111',

              color: '#aaa',

              fontSize: '13px',

            }}

          >

            {message}

          </div>

        )}

        {/* 投稿一覧 */}

        <section

          style={{

            margin: '0 -20px',

          }}

        >

          {visiblePosts.length ===

          0 ? (

            <div

              style={{

                padding:

                  '70px 25px',

                textAlign:

                  'center',

              }}

            >

              <div

                style={{

                  fontSize: '35px',

                  marginBottom:

                    '14px',

                }}

              >

                ♠

              </div>

              <div

                style={{

                  fontWeight: 700,

                  marginBottom:

                    '7px',

                }}

              >

                まだ投稿がありません

              </div>

              <div

                style={{

                  color: '#777',

                  fontSize: '14px',

                  lineHeight: 1.5,

                }}

              >

                {timelineMode ===

                'following'

                  ? 'プレイヤーをフォローすると、ここに投稿が表示されます。'

                  : '最初の投稿をしてみましょう。'}

              </div>

            </div>

          ) : (

            visiblePosts.map(

              (post) => (

                <article

                  key={post.id}

                  style={{

                    padding:

                      '17px 20px 13px',

                    borderBottom:

                      '1px solid #242424',

                  }}

                >

                  <div

                    style={{

                      display: 'flex',

                      alignItems:

                        'flex-start',

                      gap: '11px',

                    }}

                  >

                    {/* アバター */}

                    <div

                      onClick={() =>

                        handleProfileClick(

                          post.user_id

                        )

                      }

                      style={{

                        cursor:

                          'pointer',

                        flexShrink: 0,

                      }}

                    >

                      {post.profile

                        ?.avatar_url ? (

                        <img

                          src={

                            post

                              .profile

                              .avatar_url

                          }

                          alt={`${post.profile.display_name}のプロフィール画像`}

                          style={{

                            width:

                              '46px',

                            height:

                              '46px',

                            borderRadius:

                              '50%',

                            objectFit:

                              'cover',

                            border:

                              '1px solid #333',

                            display:

                              'block',

                          }}

                        />

                      ) : (

                        <div

                          className="sns-avatar-fallback"

                        >

                          ♠

                        </div>

                      )}

                    </div>

                    <div

                      style={{

                        flex: 1,

                        minWidth: 0,

                      }}

                    >

                      {/* 名前 */}

                      <div

                        style={{

                          display:

                            'flex',

                          alignItems:

                            'center',

                          gap: '6px',

                          minWidth: 0,

                        }}

                      >

                        <button

                          onClick={() =>

                            handleProfileClick(

                              post.user_id

                            )

                          }

                          style={{

                            width:

                              'auto',

                            maxWidth:

                              '45%',

                            padding: 0,

                            background:

                              'transparent',

                            color:

                              '#f5f5f5',

                            border: 0,

                            borderRadius: 0,

                            fontSize:

                              '15px',

                            fontWeight:

                              700,

                            overflow:

                              'hidden',

                            textOverflow:

                              'ellipsis',

                            whiteSpace:

                              'nowrap',

                          }}

                        >

                          {post

                            .profile

                            ?.display_name ||

                            'Unknown Player'}

                        </button>

                        <span

                          style={{

                            color:

                              '#777',

                            fontSize:

                              '13px',

                            overflow:

                              'hidden',

                            textOverflow:

                              'ellipsis',

                            whiteSpace:

                              'nowrap',

                          }}

                        >

                          @

                          {post

                            .profile

                            ?.poker_id ||

                            'unknown'}

                        </span>

                        <span

                          style={{

                            color:

                              '#555',

                            fontSize:

                              '12px',

                          }}

                        >

                          ·

                        </span>

                        <span

                          style={{

                            color:

                              '#777',

                            fontSize:

                              '12px',

                            whiteSpace:

                              'nowrap',

                          }}

                        >

                          {formatPostTime(

                            post.created_at

                          )}

                        </span>

                        {currentUserId ===

                          post.user_id && (

                          <button

                            onClick={() =>

                              handleDelete(

                                post.id

                              )

                            }

                            aria-label="投稿を削除"

                            title="削除"

                            style={{

                              width:

                                '28px',

                              height:

                                '28px',

                              marginLeft:

                                'auto',

                              padding: 0,

                              flexShrink: 0,

                              background:

                                'transparent',

                              color:

                                '#666',

                              borderRadius:

                                '50%',

                              fontSize:

                                '18px',

                              lineHeight: 1,

                            }}

                          >

                            ⋯

                          </button>

                        )}

                      </div>

                      {/* 投稿本文 */}

                      <div

                        onClick={() =>

                          navigate(

                            `/post/${post.id}`

                          )

                        }

                        style={{

                          cursor:

                            'pointer',

                          padding:

                            '5px 0 12px',

                        }}

                      >

                        <p

                          style={{

                            margin: 0,

                            whiteSpace:

                              'pre-wrap',

                            wordBreak:

                              'break-word',

                            fontSize:

                              '15px',

                            lineHeight:

                              1.6,

                            color:

                              '#ededed',

                          }}

                        >

                          {post.content}

                        </p>

                      </div>

                      {post.post_type === 'result' &&

                      post.result_type === 'tournament' &&

                      renderTournamentResultCard(post)}

                    {post.post_type === 'result' &&

                      post.result_type === 'amusement' &&

                      renderAmusementResultCard(post)}

                    {post.post_type === 'result' &&

                      post.result_type === 'cash' &&

                      renderCashResultCard(post)}



                    {post.post_type === 'result' && post.result_type === 'player_type' && post.result_id && (
                      <button type="button" onClick={() => navigate(`/player-type?result=${post.result_id}`)}
                        style={{ display: 'block', width: '100%', textAlign: 'left', padding: '20px', margin: '5px 0 14px', borderRadius: 16, border: '1px solid #92733a', background: 'linear-gradient(145deg, #251d0f, #0c0c0c 75%)', color: '#f6e5bf', cursor: 'pointer' }}>
                        <div style={{ fontSize: 11, fontWeight: 900, letterSpacing: 2, color: '#c9a75e' }}>POKER ID · PLAYER TYPE</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 10 }}>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: 28, fontWeight: 900 }}>{post.playerTypeData?.animal_name_ja || 'プレイヤータイプ診断'}</div>
                            {post.playerTypeData?.catchphrase && <div style={{ fontSize: 14, lineHeight: 1.6, marginTop: 6 }}>{post.playerTypeData.catchphrase}</div>}
                          </div>
                          <div aria-hidden="true" style={{ flexShrink: 0, width: 96, height: 96, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 16, overflow: 'hidden', background: '#0b0906', border: '1px solid #5b4926', fontSize: 66, lineHeight: 1 }}>
                            {post.playerTypeData?.result_type_key && Object.prototype.hasOwnProperty.call(playerTypeEmoji, post.playerTypeData.result_type_key) ? (
                              <img src={`/animals/${post.playerTypeData.result_type_key}.png`} alt="" style={{ display: 'block', width: '100%', height: '100%', objectFit: 'cover' }} />
                            ) : (playerTypeEmoji[post.playerTypeData?.result_type_key ?? ''] ?? '♠️')}
                          </div>
                        </div>
                        <div style={{ marginTop: 14, fontSize: 12, color: '#d4b777' }}>診断結果を見る →</div>
                      </button>
                    )}

                    {/* アクション */}

                      <div

                        style={{

                          display:

                            'flex',

                          alignItems:

                            'center',

                          gap: '24px',

                          marginTop:

                            '2px',

                        }}

                      >

                        <button

                          onClick={() =>

                            navigate(

                              `/post/${post.id}`

                            )

                          }

                          aria-label="コメント"

                          style={{

                            width:

                              'auto',

                            padding:

                              '5px 0',

                            background:

                              'transparent',

                            color:

                              '#777',

                            borderRadius: 0,

                            display:

                              'flex',

                            alignItems:

                              'center',

                            gap: '6px',

                            fontSize:

                              '13px',

                            fontWeight:

                              500,

                          }}

                        >

                          <span

                            style={{

                              fontSize:

                                '19px',

                              lineHeight: 1,

                            }}

                          >

                            ♧

                          </span>

                          {post.commentCount >

                            0 && (

                            <span>

                              {

                                post.commentCount

                              }

                            </span>

                          )}

                        </button>

                        <button

                          onClick={() =>

                            handleLike(

                              post

                            )

                          }

                          aria-label={

                            post.likedByMe

                              ? 'いいねを解除'

                              : 'いいね'

                          }

                          style={{

                            width:

                              'auto',

                            padding:

                              '5px 0',

                            background:

                              'transparent',

                            color:

                              post.likedByMe

                                ? '#ff4d6d'

                                : '#777',

                            borderRadius: 0,

                            display:

                              'flex',

                            alignItems:

                              'center',

                            gap: '6px',

                            fontSize:

                              '13px',

                            fontWeight:

                              500,

                          }}

                        >

                          <span

                            style={{

                              fontSize:

                                '20px',

                              lineHeight: 1,

                            }}

                          >

                            {post.likedByMe

                              ? '♥'

                              : '♡'}

                          </span>

                          {post.likeCount >

                            0 && (

                            <span>

                              {

                                post.likeCount

                              }

                            </span>

                          )}

                        </button>

                        <button

                          onClick={() => {

                            if (

                              navigator

                                .share

                            ) {

                              navigator

                                .share({

                                  title:

                                    'Poker ID',

                                  text:

                                    post.content,

                                  url: `${window.location.origin}/post/${post.id}`,

                                })

                            } else {

                              navigator.clipboard?.writeText(

                                `${window.location.origin}/post/${post.id}`

                              )

                            }

                          }}

                          aria-label="シェア"

                          style={{

                            width:

                              'auto',

                            padding:

                              '5px 0',

                            background:

                              'transparent',

                            color:

                              '#777',

                            borderRadius: 0,

                            fontSize:

                              '19px',

                            lineHeight: 1,

                          }}

                        >

                          ↗

                        </button>

                      </div>

                    </div>

                  </div>

                </article>

              )

            )

          )}

        </section>

      </div>

    </main>

  )

}

export default Timeline
