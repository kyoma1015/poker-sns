import { createPollRequest, pollDisplayResult } from './interactiveRequests'
import { useEffect, useRef, useState } from 'react'

import { useNavigate } from 'react-router-dom'
import { validateVideo, uploadPostVideo } from './videoUpload'
import { finalizeUploadedVideo, VIDEO_SERVER_ENABLED } from './videoApi'
import PostVideo from './PostVideo'

import { supabase } from './supabase'
import { usePullToRefresh } from './usePullToRefresh'
import QuoteSourcePreview, { type QuoteSource } from './QuoteSourcePreview'
import { InteractiveCard, type InteractiveItem, type InteractiveResult } from './TimelineInteractive'

const playerTypeEmoji: Record<string, string> = {lion:'🦁',tiger:'🐯',leopard:'🐆',bison:'🦬',gorilla:'🦍',rhino:'🦏',shark:'🦈',owl:'🦉',eagle:'🦅',elephant:'🐘',giraffe:'🦒',wolf:'🐺',hyena:'🐾',cat:'🐈',chameleon:'🦎',dolphin:'🐬',fox:'🦊',snake:'🐍',raccoon:'🦝',turtle:'🐢',rabbit:'🐇',crocodile:'🐊',hedgehog:'🦔',deer:'🦌',sloth:'🦥',dog:'🐕',bear:'🐻',bull:'🐄',badger:'🦡',monkey:'🐒',magpie:'🐦‍⬛',penguin:'🐧',horse:'🐎',squirrel:'🐿️',mountain_goat:'🐐',otter:'🦦'}

type QuotePreview = QuoteSource

type Post = {
  quote_post_id?: string | null
  quotePreview?: QuotePreview | null

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
  repostCount?: number
  repostedByMe?: boolean
  feedKey?: string
  feedActorId?: string
  repostedBy?: { display_name: string; poker_id: string }

  likedByMe: boolean

  commentCount: number

  post_type: 'normal' | 'result'

  result_type: 'tournament' | 'amusement' | 'cash' | 'player_type' | null

  result_id: string | null
  video_path?: string | null
  image_urls?: string[]
  style_snapshot?: { count: number; aggression: number; looseness: number; captured_at: string } | null

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

function Timeline({ profileUserId }: { profileUserId?: string }) {

  const navigate = useNavigate()
  useEffect(() => {
    if (window.location.search.includes('compose=1')) {
      const timer = window.setTimeout(() => document.getElementById('poker-id-post-composer')?.focus(), 80)
      return () => window.clearTimeout(timer)
    }
  }, [])

  const refreshContainerRef = useRef<HTMLElement>(null)
  const [posts, setPosts] = useState<Post[]>([])
  const [interactiveItems, setInteractiveItems] = useState<Record<string, InteractiveItem>>({})
  const [interactiveResults, setInteractiveResults] = useState<Record<string, InteractiveResult>>({})
  const [repostingId, setRepostingId] = useState<string | null>(null)
  const repostingRef = useRef(false)

  const [content, setContent] = useState('')
  const [quoteTarget, setQuoteTarget] = useState<Post | null>(null)
  const [quoteText, setQuoteText] = useState('')
  const [quoteBusy, setQuoteBusy] = useState(false)
  const [repostMenuId, setRepostMenuId] = useState<string | null>(null)
  const [composeOpen, setComposeOpen] = useState(false)
  const [interactiveMode, setInteractiveMode] = useState<'normal'|'poll'>('normal')
  const [pollOptions, setPollOptions] = useState(['',''])
  const [pollHours, setPollHours] = useState(24)
  const [pollAnonymous, setPollAnonymous] = useState(false)
  const [attachmentsOpen, setAttachmentsOpen] = useState(false)
  const [attachmentScreen, setAttachmentScreen] = useState<'menu' | 'results' | 'tournament' | 'amusement' | 'cash' | 'diagnosis'>('menu')
  const [selectedResult, setSelectedResult] = useState<{id:string; type:'tournament'|'amusement'|'cash'; label:string; playedAt:string; data:any}|null>(null)
  const [availableResults, setAvailableResults] = useState<{id:string; type:'tournament'|'amusement'|'cash'; label:string; playedAt:string; data:any}[]>([])
  const [resultsLoading, setResultsLoading] = useState(false)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const videoInputRef = useRef<HTMLInputElement>(null)
  const [videoFile, setVideoFile] = useState<File | null>(null)
  // Retain the exact immutable object path after an uncertain finalize result.
  type PendingVideo = { path: string; owner: string; content: string }
  const [pendingVideo, setPendingVideo] = useState<PendingVideo | null>(null)
  const pendingVideoRef = useRef<PendingVideo | null>(null)
  // Session-scoped recovery; never persist credentials or delete by path.
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('poker-id-pending-video-v1')
      if (!raw) return
      const value: unknown = JSON.parse(raw)
      if (!value || typeof value !== 'object') return
      const record = value as Record<string, unknown>
      const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
      if (typeof record.owner !== 'string' || !uuid.test(record.owner) ||
          typeof record.path !== 'string' ||
          !record.path.startsWith(record.owner + '/') ||
          !/^[0-9a-f-]{36}\.(mp4|webm)$/.test(record.path.slice(record.owner.length + 1)) ||
          typeof record.content !== 'string' || record.content.length > 10000) return
      const staged = { owner: record.owner, path: record.path, content: record.content }
      pendingVideoRef.current = staged
      setPendingVideo(staged)
      setContent(staged.content)
      setComposeOpen(true)
    } catch { /* Untrusted or unavailable session storage: stay fail-closed. */ }
  }, [])
  const videoSubmitInFlightRef = useRef(false)
  const [videoPreview, setVideoPreview] = useState<string | null>(null)
  useEffect(() => { if (!videoFile) { setVideoPreview(null); return }; const url = URL.createObjectURL(videoFile); setVideoPreview(url); return () => URL.revokeObjectURL(url) }, [videoFile])
  const [imageFiles, setImageFiles] = useState<File[]>([])
  const [imagePreviews, setImagePreviews] = useState<string[]>([])
  const [selectedDiagnosis, setSelectedDiagnosis] = useState<{ result_id: string; animal_name_ja: string; catchphrase: string; result_type_key: string; completed_at: string } | null>(null)
  const [diagnoses, setDiagnoses] = useState<{ result_id: string; animal_name_ja: string; catchphrase: string; result_type_key: string; completed_at: string }[]>([])
  const [styleSnapshot, setStyleSnapshot] = useState<{ count: number; aggression: number; looseness: number; captured_at: string } | null>(null)
  const [attachmentBusy, setAttachmentBusy] = useState(false)
  useEffect(() => { const urls = imageFiles.map(file => URL.createObjectURL(file)); setImagePreviews(urls); return () => urls.forEach(url => URL.revokeObjectURL(url)) }, [imageFiles])

  const [currentUserId, setCurrentUserId] = useState('')

  const [message, setMessage] = useState('')
  const [postMenuId, setPostMenuId] = useState<string | null>(null)
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const deletingRef = useRef(false)

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

    // 元投稿とリポストされた投稿の双方を参照できるよう、元投稿はまとめて取得する。
    const postQuery = supabase.from('posts').select('*').order('created_at', { ascending: false })
    const { data: postData, error: postError } = await postQuery

    if (postError) {

      console.error(postError)

      setMessage(

        `投稿の取得に失敗しました：${postError.message}`

      )

      return

    }

    if (!postData || postData.length === 0) {

      setPosts([])
      setInteractiveItems({})
      setInteractiveResults({})

      setMessage('')

      return

    }

    const postIdsForInteractive = postData.map(row => row.id)
    const { data: interactiveRows, error: interactiveError } = await supabase.from('post_interactive').select('*').in('post_id',postIdsForInteractive)
    if (interactiveError) { setMessage(`アンケート情報の取得に失敗しました：${interactiveError.message}`); return }
    const visibleInteractiveIds = postIdsForInteractive.filter(id => !(interactiveRows || []).some(row => row.post_id === id && row.kind === 'question'))
    const { data: responseRows, error: responseError } = await supabase.rpc('get_interactive_results_v4', { p_post_ids: visibleInteractiveIds })
    if (responseError) { setMessage(`回答情報の取得に失敗しました：${responseError.message}`); return }
    setInteractiveItems(Object.fromEntries((interactiveRows||[]).map(row=>[row.post_id,row as InteractiveItem])))
    setInteractiveResults(Object.fromEntries(((responseRows||[]) as InteractiveResult[]).map(row=>[row.post_id,pollDisplayResult((interactiveRows || []).find(item => item.post_id === row.post_id)?.is_anonymous !== false,row)])))
    const { data: repostRows, error: repostError } = await supabase
      .from('post_reposts').select('post_id,user_id,created_at')
    if (repostError) { setMessage(`リポストの取得に失敗しました：${repostError.message}`); return }
    // ブロックした相手・ブロックされた相手のリポストは表示しない。
    const { data: blockRows, error: blockError } = await supabase.from('user_blocks')
      .select('blocker_id,blocked_id').or(`blocker_id.eq.${user.id},blocked_id.eq.${user.id}`)
    if (blockError) { setMessage(`ブロック情報の取得に失敗しました：${blockError.message}`); return }
    const blockedIds = new Set((blockRows || []).map(row => row.blocker_id === user.id ? row.blocked_id : row.blocker_id))
    const permittedPosts = postData.filter(row => !blockedIds.has(row.user_id) && visibleInteractiveIds.includes(row.id))
    const permittedIds = new Set(permittedPosts.map(row => row.id))
    const validReposts = (repostRows || []).filter(row => permittedIds.has(row.post_id) && !blockedIds.has(row.user_id))

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

        console.error('リングゲーム結果取得エラー:', error)

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

          [...postData.map(post => post.user_id), ...validReposts.map(repost => repost.user_id)]

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

    const quoteSourceById = new Map(postsWithData.filter(source => !blockedIds.has(source.user_id)).map(source => [source.id, source]))
    const postsWithQuotes = postsWithData.map(item => {
      const source = item.quote_post_id ? quoteSourceById.get(item.quote_post_id) : null
      return { ...item, quotePreview: source ? { id: source.id, user_id: source.user_id, content: source.content,
        profile: source.profile ? { display_name: source.profile.display_name, poker_id: source.profile.poker_id } : undefined,
        image_urls: source.image_urls, result_type: source.result_type, resultData: source.resultData || source.amusementResultData || source.cashResultData || null, playerTypeData: source.playerTypeData, style_snapshot: source.style_snapshot } : null }
    })
    const repostCountByPost = new Map<string, number>()
    for (const row of validReposts) repostCountByPost.set(row.post_id, (repostCountByPost.get(row.post_id) || 0) + 1)
    const myReposted = new Set(validReposts.filter(row => row.user_id === user.id).map(row => row.post_id))
    const originalCards = postsWithQuotes.filter(post => !blockedIds.has(post.user_id)).map(post => ({
      ...post, feedKey: `post:${post.id}`, feedActorId: post.user_id,
      repostCount: repostCountByPost.get(post.id) || 0, repostedByMe: myReposted.has(post.id),
    }))
    const originalById = new Map(originalCards.map(post => [post.id, post]))
    const repostCards: Post[] = validReposts.flatMap(row => {
      const original = originalById.get(row.post_id)
      const sharer = profiles?.find(profile => profile.id === row.user_id)
      if (!original || !sharer) return []
      return [{ ...original, feedKey: `repost:${row.user_id}:${row.post_id}`,
        feedActorId: row.user_id, created_at: row.created_at,
        repostedBy: { display_name: sharer.display_name, poker_id: sharer.poker_id } }]
    })
    setPosts([...originalCards, ...repostCards].sort((a,b) => Date.parse(b.created_at) - Date.parse(a.created_at)))

    setMessage('')

  }

  const { pullDistance, isRefreshing, refreshError } = usePullToRefresh(refreshContainerRef, {
    onRefresh: loadPosts,
    enabled: !profileUserId && !composeOpen && !attachmentsOpen && !deleteTargetId && !isPosting && !attachmentBusy,
  })

  useEffect(() => {

    loadPosts()

  }, [profileUserId])

  useEffect(() => {
    if (profileUserId) return
    const open = () => setComposeOpen(true)
    window.addEventListener('poker-id-open-compose', open)
    if (new URLSearchParams(window.location.search).get('compose') === '1') {
      setComposeOpen(true)
      navigate('/timeline', { replace: true })
    }
    return () => window.removeEventListener('poker-id-open-compose', open)
  }, [profileUserId, navigate])

  const loadShareableResults = async () => {
    setResultsLoading(true)
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) { setResultsLoading(false); return }
    const sources = [
      { table: 'poker_results', type: 'tournament' as const, label: 'トーナメント' },
      { table: 'amusement_ring_results', type: 'amusement' as const, label: 'リングゲーム' },
      { table: 'cash_game_results', type: 'cash' as const, label: 'キャッシュ' },
    ]
    const lists = await Promise.all(sources.map(async source => {
      const { data, error } = await supabase.from(source.table).select('*').eq('user_id', user.id).order('played_at', { ascending: false }).limit(30)
      if (error) { console.error(error); return [] }
      return (data || []).map(item => ({ id: String(item.id), type: source.type, label: `${source.label} · ${String(item.tournament_name || item.venue || '記録')}`, playedAt: String(item.played_at || ''), data: item }))
    }))
    setAvailableResults(lists.flat())
    setResultsLoading(false)
  }

  const toggleAttachments = () => {
    setAttachmentsOpen(open => !open)
    setAttachmentScreen('menu')
  }

  const chooseResultCategory = (type: 'tournament' | 'amusement' | 'cash') => {
    setAttachmentScreen(type)
    void loadShareableResults()
  }

  const renderAttachmentPicker = () => {
    const optionStyle = { display: 'block', width: '100%', padding: '11px 12px', textAlign: 'left' as const, background: '#202020', color: '#eee', borderRadius: 9, marginBottom: 7, fontSize: 13, border: '1px solid #333' }
    const backButton = (target: 'menu' | 'results') => <button type="button" onClick={() => setAttachmentScreen(target)} style={{ width: 'auto', background: 'transparent', color: '#bbb', padding: '5px 0', fontSize: 12 }}>‹ 戻る</button>
    return <div style={{ marginTop: 12, padding: 12, background: '#151515', border: '1px solid #333', borderRadius: 12, maxHeight: 320, overflowY: 'auto' }}>
      {attachmentScreen === 'menu' ? <>
        <div style={{ fontSize: 12, color: '#aaa', marginBottom: 10 }}>添付するものを選択</div>
        <button type="button" style={optionStyle} onClick={() => { imageInputRef.current?.click(); setAttachmentsOpen(false) }}>▧　画像を添付（最大4枚・各5MB）</button>
        <button type="button" style={optionStyle} onClick={() => { videoInputRef.current?.click(); setAttachmentsOpen(false) }}>▶　動画を選択（最大30秒・20MB）</button>
        <button type="button" style={optionStyle} onClick={() => { void loadDiagnoses() }}>♧　自己診断を添付　›</button>
        <button type="button" style={optionStyle} onClick={() => { void loadStyleSnapshot() }}>♙　自分への他者評価を添付（3人以上）</button>
        <button type="button" style={optionStyle} onClick={() => setAttachmentScreen('results')}>♠　戦績を添付　›</button>
      </> : attachmentScreen === 'diagnosis' ? <>
        {backButton('menu')}
        <div style={{ fontSize: 12, color: '#aaa', marginBottom: 10 }}>保存済みの自己診断を選択</div>
        {attachmentBusy ? <p>読み込み中...</p> : diagnoses.length === 0 ? <p style={{ color: '#aaa', fontSize: 12 }}>診断結果がありません。</p> : diagnoses.map(item => <button type="button" key={item.result_id} style={optionStyle} onClick={() => { setSelectedDiagnosis(item); setSelectedResult(null); setAttachmentsOpen(false); setAttachmentScreen('menu') }}>{playerTypeEmoji[item.result_type_key] || '♠'} {item.animal_name_ja} · {item.completed_at?.slice(0,10) || '日付不明'}</button>)}
      </> : attachmentScreen === 'results' ? <>
        {backButton('menu')}
        <div style={{ fontSize: 12, color: '#aaa', margin: '8px 0 10px' }}>戦績の種類を選択</div>
        <button type="button" style={optionStyle} onClick={() => chooseResultCategory('tournament')}>🏆　トーナメント戦績　›</button>
        <button type="button" style={optionStyle} onClick={() => chooseResultCategory('amusement')}>♠　リングゲーム戦績　›</button>
        <button type="button" style={optionStyle} onClick={() => chooseResultCategory('cash')}>♦　キャッシュゲーム戦績　›</button>
      </> : <>
        {backButton('results')}
        <div style={{ fontSize: 12, color: '#aaa', margin: '8px 0 10px' }}>保存済みの{attachmentScreen === 'tournament' ? 'トーナメント' : attachmentScreen === 'amusement' ? 'リングゲーム' : 'キャッシュゲーム'}戦績を選択</div>
        {resultsLoading ? <p style={{ fontSize: 12 }}>読み込み中...</p> : availableResults.filter(result => result.type === attachmentScreen).length === 0 ? <p style={{ fontSize: 12, color: '#888' }}>この種類の戦績はありません。</p> : availableResults.filter(result => result.type === attachmentScreen).map(result => <button key={result.type + result.id} type="button" style={optionStyle} onClick={() => { setSelectedResult(result); setSelectedDiagnosis(null); setAttachmentsOpen(false); setAttachmentScreen('menu') }}><span style={{ display: 'block', fontWeight: 700 }}>{result.label}</span><span style={{ display: 'block', color: '#aaa', fontSize: 12, marginTop: 4 }}>プレイ日：{result.playedAt ? new Date(result.playedAt.slice(0,10) + 'T00:00:00').toLocaleDateString('ja-JP') : '日付不明'}</span></button>)}
      </>}
    </div>
  }


  const loadDiagnoses = async () => {
    setAttachmentBusy(true)
    const { data, error } = await supabase.rpc('get_my_latest_player_type_v2')
    if (error) { setMessage(`診断取得エラー：${error.message}`); setAttachmentBusy(false); return }
    setDiagnoses((data || []).map((item: any) => ({ result_id: String(item.result_id), animal_name_ja: String(item.animal_name_ja || ''), catchphrase: String(item.catchphrase || ''), result_type_key: String(item.result_type_key || ''), completed_at: String(item.completed_at || '') })))
    setAttachmentScreen('diagnosis')
    setAttachmentBusy(false)
  }

  const loadStyleSnapshot = async () => {
    setAttachmentBusy(true)
    const { data, error } = await supabase.rpc('get_my_post_style_snapshot')
    setAttachmentBusy(false)
    if (error) { setMessage(`他者評価取得エラー：${error.message}（SQLの適用を確認してください）`); return }
    const row = Array.isArray(data) ? data[0] : data
    if (!row || Number(row.count) < 3) { setMessage('他者評価は3人以上集まると添付できます。'); return }
    setStyleSnapshot({ count: Number(row.count), aggression: Number(row.aggression), looseness: Number(row.looseness), captured_at: new Date().toISOString() })
    setAttachmentsOpen(false)
    setMessage('')
  }

  const chooseVideo = async (file: File | undefined) => {
    if (!file) return
    if (pendingVideoRef.current || videoSubmitInFlightRef.current) { setMessage('保留中の動画を先に再試行してください。'); return }
    if (imageFiles.length || selectedResult || selectedDiagnosis || styleSnapshot || interactiveMode !== 'normal') { setMessage('動画は画像・戦績・診断・アンケートと同時に添付できません。'); return }
    const error = await validateVideo(file)
    if (error) { setMessage(error); return }
    // Re-check after async metadata validation: finalize may have started meanwhile.
    if (pendingVideoRef.current || videoSubmitInFlightRef.current) { setMessage('保留中の動画を先に再試行してください。'); return }
    setVideoFile(file)
    setMessage(VIDEO_SERVER_ENABLED ? '' : '動画のプレビューを確認できます。サーバーAPIの安全確認が終わるまで投稿は無効です。')
  }

  const chooseImages = (files: FileList | null) => {
    if (videoFile || pendingVideoRef.current) { setMessage('動画と画像は同時に添付できません。'); return }

    if (!files) return
    const selected = Array.from(files)
    if (selected.some(file => !['image/jpeg','image/png','image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024)) { setMessage('画像はJPEG・PNG・WebP、各5MB以内にしてください。'); return }
    if (imageFiles.length + selected.length > 4) { setMessage('画像は1投稿につき4枚までです。'); return }
    setImageFiles(previous => [...previous, ...selected])
    setMessage('')
  }

  const choosePostMode = (mode: 'normal'|'poll') => {
    if (mode !== 'normal' && (imageFiles.length || videoFile || pendingVideoRef.current || selectedResult || selectedDiagnosis || styleSnapshot)) {
      setMessage('添付を外してからアンケートに切り替えてください。')
      return
    }
    setInteractiveMode(current => current === mode ? 'normal' : mode)
    setAttachmentsOpen(false)
    setMessage('')
  }

  const renderPostModeButtons = () => (
    <div style={{display:'flex',alignItems:'center',gap:4,flexWrap:'nowrap',whiteSpace:'nowrap'}}>
      <button type="button" disabled={interactiveMode !== 'normal'} onClick={toggleAttachments} style={{width:'auto',padding:'6px 6px',border:'1px solid #333',background:'#181818',borderRadius:9,color:'#ddd',fontSize:11}}>＋ 添付</button>
      {(['poll'] as const).map(mode=><button key={mode} type="button" onClick={()=>choosePostMode(mode)} aria-pressed={interactiveMode===mode} style={{width:'auto',padding:'6px 6px',border:'1px solid '+(interactiveMode===mode?'#ddd':'#333'),background:interactiveMode===mode?'#393939':'#181818',borderRadius:9,color:'#ddd',fontSize:11}}>📊 アンケート</button>)}
    </div>
  )

  const renderInteractiveFields = () => interactiveMode==='poll' ? (
    <div style={{marginTop:10,display:'grid',gap:8}}>
      {pollOptions.map((value,index)=><input key={index} aria-label={`選択肢${index+1}`} placeholder={`${String.fromCharCode(65+index)}：選択肢${index+1}`} maxLength={80} value={value} onChange={e=>setPollOptions(prev=>prev.map((v,i)=>i===index?e.target.value:v))} style={{width:'100%',boxSizing:'border-box',padding:10,borderRadius:8,border:'1px solid #444',background:'#202020',color:'#fff'}}/>)}
      <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
        {pollOptions.length<4&&<button type="button" onClick={()=>setPollOptions(prev=>[...prev,''])} style={{width:'auto',padding:'7px 10px',border:'1px solid #444',background:'#181818',borderRadius:9,color:'#ddd',fontSize:12}}>＋ 選択肢</button>}
        {pollOptions.length>2&&<button type="button" onClick={()=>setPollOptions(prev=>prev.slice(0,-1))} style={{width:'auto',padding:'8px 12px',border:'1px solid #444',background:'#181818',borderRadius:9,color:'#ddd',fontSize:12}}>− 削除</button>}
        <label style={{fontSize:12,color:'#ccc'}}>投票期限 <select value={pollHours} onChange={e=>setPollHours(Number(e.target.value))} style={{background:'#222',color:'#fff',padding:7}}>{[1,6,24,72,168].map(h=><option key={h} value={h}>{h<24?`${h}時間`:`${h/24}日`}</option>)}</select></label>
      </div>
      <div style={{display:'grid',gap:8}}><label style={{fontSize:12,color:'#ccc'}}>投票方式</label><div style={{display:'flex',gap:8}}>{([{anonymous:false,label:'記名投票'},{anonymous:true,label:'匿名投票'}] as const).map(mode=><button key={mode.label} type="button" aria-pressed={pollAnonymous===mode.anonymous} onClick={()=>setPollAnonymous(mode.anonymous)} style={{width:'auto',padding:'8px 12px',borderRadius:9,border:'1px solid '+(pollAnonymous===mode.anonymous?'#ddd':'#444'),background:pollAnonymous===mode.anonymous?'#383838':'#181818',color:'#eee',fontSize:12}}>{mode.label}</button>)}</div><p style={{fontSize:12,color:'#aaa',margin:0}}>{pollAnonymous?'投票者と投票先は公開されません。':'投票者の名前・Poker IDと投票先が公開されます。'} 投稿後の変更はできません。</p></div>
    </div>
  ) : null

  const canSubmitPost = Boolean(content.trim() || (interactiveMode==='normal' && (selectedResult || selectedDiagnosis || styleSnapshot || imageFiles.length || videoFile || pendingVideo)))
    && (interactiveMode!=='poll'||(pollOptions.every(o=>o.trim()) && new Set(pollOptions.map(o=>o.trim().toLowerCase())).size===pollOptions.length))

  const handlePost = async () => {
    if (interactiveMode !== 'normal') {
      if (isPosting) return
      if (!canSubmitPost) { setMessage('投稿内容と選択肢を確認してください。'); return }
      setIsPosting(true)
      setMessage('')
      try {
        const request = createPollRequest(interactiveMode, content, pollOptions, pollHours, pollAnonymous)
        const { error } = await supabase.rpc('create_interactive_post_v4', request)
        if (error) throw error
        setContent('')
        setInteractiveMode('normal')
        setPollOptions(['',''])
        setPollHours(24)
        setPollAnonymous(false)
        setComposeOpen(false)
        await loadPosts()
      } catch (error) {
        setMessage(`投稿できませんでした：${error instanceof Error?error.message:'不明なエラー'}`)
      } finally { setIsPosting(false) }
      return
    }


    if (videoFile || pendingVideoRef.current) {
      if (isPosting || videoSubmitInFlightRef.current) return
      if (!VIDEO_SERVER_ENABLED) {
        setMessage('動画投稿はサーバーAPIの安全確認待ちです。')
        return
      }
      if (imageFiles.length || selectedResult || selectedDiagnosis || styleSnapshot) {
        setMessage('動画は他の添付と同時に投稿できません。')
        return
      }
      videoSubmitInFlightRef.current = true
      setIsPosting(true)
      setMessage('動画を検証・投稿中...')
      try {
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (authError || !user) throw new Error('ログイン情報を確認してください。')
        if (videoFile && !pendingVideoRef.current) {
          const videoError = await validateVideo(videoFile)
          if (videoError) throw new Error(videoError)
        }
        // Never upload a second object after an ambiguous server outcome.
        // Retrying must use the same path and original content fingerprint.
        if (pendingVideoRef.current && (pendingVideoRef.current.owner !== user.id || pendingVideoRef.current.content !== content.trim())) {
          throw new Error('前回の投稿内容またはアカウントが異なります。元の内容で再試行してください。')
        }
        const path = pendingVideoRef.current?.path ?? (videoFile ? await uploadPostVideo(user.id, videoFile) : '')
        if (!path) throw new Error('動画を再選択してください。')
        if (!pendingVideoRef.current) {
          const staged = { path, owner: user.id, content: content.trim() }
          pendingVideoRef.current = staged
          setPendingVideo(staged)
          try { sessionStorage.setItem('poker-id-pending-video-v1', JSON.stringify(staged)) } catch { /* Recovery unavailable; do not delete staged media. */ }
        }
        await finalizeUploadedVideo(path, content.trim())
        pendingVideoRef.current = null
        setPendingVideo(null)
        try { sessionStorage.removeItem('poker-id-pending-video-v1') } catch { /* best effort */ }
        setVideoFile(null)
        setContent('')
        setComposeOpen(false)
        setAttachmentsOpen(false)
        setMessage('')
        await loadPosts()
      } catch (error) {
        setMessage(`動画を投稿できませんでした：${error instanceof Error ? error.message : '不明なエラー'}。アップロード済みファイルは安全な回収対象として保持されます。`)
      } finally {
        videoSubmitInFlightRef.current = false
        setIsPosting(false)
      }
      return
    }

    const trimmedContent =

      content.trim()

    if (!trimmedContent && !selectedResult && !selectedDiagnosis && !styleSnapshot && imageFiles.length === 0) {

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

    const uploadedPaths: string[] = []
    const uploadedUrls: string[] = []
    for (const file of imageFiles) {
      const ext = file.type === 'image/png' ? 'png' : file.type === 'image/webp' ? 'webp' : 'jpg'
      const path = `${user.id}/${crypto.randomUUID()}.${ext}`
      const { error: uploadError } = await supabase.storage.from('post-images').upload(path, file, { contentType: file.type, upsert: false })
      if (uploadError) {
        await Promise.all(uploadedPaths.map(path => supabase.storage.from('post-images').remove([path])))
        setMessage(`画像アップロード失敗：${uploadError.message}`); setIsPosting(false); return
      }
      uploadedPaths.push(path)
      uploadedUrls.push(supabase.storage.from('post-images').getPublicUrl(path).data.publicUrl)
    }
    const { error } = await supabase

      .from('posts')

      .insert({

        user_id: user.id,

        content: trimmedContent,
        post_type: selectedResult || selectedDiagnosis ? 'result' : 'normal',
        result_type: selectedResult?.type || (selectedDiagnosis ? 'player_type' : null),
        result_id: selectedResult?.id || selectedDiagnosis?.result_id || null,
        image_urls: uploadedUrls,
        style_snapshot: styleSnapshot,

      })

    if (error) {
      if (uploadedPaths.length) await supabase.storage.from('post-images').remove(uploadedPaths)
      console.error(error)

      setMessage(

        `投稿できませんでした：${error.message}`

      )

      setIsPosting(false)

      return

    }

    setContent('')
    setInteractiveMode('normal')
    setSelectedResult(null)
    setSelectedDiagnosis(null)
    setStyleSnapshot(null)
    setImageFiles([])
    setComposeOpen(false)
    setAttachmentsOpen(false)
    setAttachmentScreen('menu')

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

  const publishQuote = async () => {
    if (!quoteTarget || quoteBusy) return
    const trimmed = quoteText.trim()
    if (!trimmed) { setMessage('引用コメントを入力してください。'); return }
    setQuoteBusy(true)
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user || user.id !== currentUserId) throw new Error('ログインを確認してください。')
      const { error } = await supabase.from('posts').insert({ user_id: user.id, content: trimmed,
        post_type: 'normal', result_type: null, result_id: null, quote_post_id: quoteTarget.id })
      if (error) throw error
      setQuoteTarget(null); setQuoteText(''); setRepostMenuId(null); setMessage('')
      await loadPosts()
    } catch (error) {
      setMessage(`引用リポストに失敗しました：${error instanceof Error ? error.message : '不明なエラー'}`)
    } finally { setQuoteBusy(false) }
  }

  const handleRepost = async (post: Post) => {
    if (!currentUserId || repostingRef.current) return
    repostingRef.current = true
    setRepostingId(post.id)
    try {
      const { data: { user }, error: authError } = await supabase.auth.getUser()
      if (authError || !user || user.id !== currentUserId) throw new Error('ログイン情報を確認できません。')
      const { error } = post.repostedByMe
        ? await supabase.from('post_reposts').delete().eq('post_id', post.id).eq('user_id', user.id)
        : await supabase.from('post_reposts').insert({ post_id: post.id, user_id: user.id })
      if (error) throw error
      setMessage('')
      await loadPosts()
    } catch (error) {
      setMessage(`リポスト操作に失敗しました：${error instanceof Error ? error.message : '不明なエラー'}`)
    } finally {
      repostingRef.current = false
      setRepostingId(null)
    }
  }

  const handleDelete = async () => {
    if (!deleteTargetId || deletingRef.current) return
    deletingRef.current = true
    setIsDeleting(true)
    const postId = deleteTargetId
    try {
      const { data: { user }, error: authError } = await supabase.auth.getUser()
      if (authError || !user || !currentUserId || user.id !== currentUserId) {
        setMessage('ログイン情報を確認できません。再ログインしてお試しください。')
        return
      }
      const target = posts.find(post => post.id === postId)
      if (!target || target.user_id !== user.id) {
        setMessage('自分の投稿以外は削除できません。')
        return
      }
      // A published video must not be deleted until a generation-fenced
      // cleanup transaction is proven. The legacy remove() has no ABA fence.
      if (target.video_path) {
        setMessage('動画付き投稿の削除は安全な回収処理の検証待ちです。')
        return
      }
      const { error } = await supabase
        .from('posts')
        .delete()
        .eq('id', postId)
        .eq('user_id', user.id)
      if (error) {
        console.error(error)
        setMessage(`削除できませんでした：${error.message}`)
        return
      }
      setDeleteTargetId(null)
      setPostMenuId(null)
      setMessage('')
      await loadPosts()
    } finally {
      deletingRef.current = false
      setIsDeleting(false)
    }
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

  const visiblePosts = posts.filter(post => {
    const actorId = post.feedActorId || post.user_id
    if (profileUserId) return actorId === profileUserId
    return timelineMode === 'all' || actorId === currentUserId || followingIds.includes(actorId)
  })

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

              RING GAME

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



  const renderStyleSnapshot = (snapshot: { count: number; aggression: number; looseness: number; captured_at: string }) => <div style={{ padding: 16, border: '1px solid #555', borderRadius: 12, margin: '8px 0', background: '#171717' }}><strong>♙ 他者評価 · プレイスタイル</strong><div style={{ fontSize: 13, color: '#bbb', marginTop: 8 }}>匿名評価 {snapshot.count}人の集計（投稿時点）</div><div style={{ marginTop: 8 }}>攻撃性 {snapshot.aggression.toFixed(1)} / 100　·　ルース度 {snapshot.looseness.toFixed(1)} / 100</div></div>

  const renderSelectedResultPreview = () => {
    if (!selectedResult && !selectedDiagnosis && !styleSnapshot && imageFiles.length === 0 && !videoFile) return null
    const previewPost = {
      resultData: selectedResult?.type === 'tournament' ? selectedResult?.data : null,
      amusementResultData: selectedResult?.type === 'amusement' ? selectedResult?.data : null,
      cashResultData: selectedResult?.type === 'cash' ? selectedResult?.data : null,
    } as Post
    return <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 7 }}>
        <span style={{ fontSize: 12, color: '#aaa', fontWeight: 700 }}>添付プレビュー（投稿時の表示）</span>
        <button type="button" onClick={() => { setSelectedResult(null); setSelectedDiagnosis(null); setStyleSnapshot(null); setImageFiles([]); setVideoFile(null) }} aria-label="添付を解除" style={{ width: 'auto', padding: '4px 9px', background: '#292929', border: '1px solid #444', borderRadius: 8, color: '#ddd', fontSize: 12 }}>× 解除</button>
      </div>
      {selectedResult?.type === 'tournament' && renderTournamentResultCard(previewPost)}
      {selectedResult?.type === 'amusement' && renderAmusementResultCard(previewPost)}
      {selectedResult?.type === 'cash' && renderCashResultCard(previewPost)}
      {selectedDiagnosis && <div style={{ border: '1px solid #92733a', borderRadius: 12, padding: 16, color: '#f6e5bf' }}>♧ 自己診断：{playerTypeEmoji[selectedDiagnosis.result_type_key]} {selectedDiagnosis.animal_name_ja}<div style={{ fontSize: 12 }}>{selectedDiagnosis.catchphrase}</div></div>}
      {styleSnapshot && renderStyleSnapshot(styleSnapshot)}
      {videoPreview && <video controls preload="metadata" src={videoPreview} style={{ width: '100%', maxHeight: 360, borderRadius: 10 }} />}
      {pendingVideo && <p role="status" style={{ fontSize: 12, color: '#e6c27a' }}>動画はアップロード済みです。投稿確定に失敗した場合は、内容を変更せず「投稿」から同じStorageファイルを再試行してください。再読み込み後も同じタブなら再試行できます。新規アップロードや無条件削除は行いません。</p>}
      {imagePreviews.length > 0 && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 8, marginTop: 8 }}>{imagePreviews.map((url, i) => <div key={url} style={{ position: 'relative' }}><img src={url} alt={`添付画像${i+1}`} style={{ width: '100%', maxHeight: 220, objectFit: 'cover', borderRadius: 8 }}/><button type="button" onClick={() => setImageFiles(files => files.filter((_, index) => index !== i))} style={{ position: 'absolute', right: 4, top: 4, width: 'auto', background: '#222', color: '#fff' }}>×</button></div>)}</div>}
    </div>
  }

  return (
    <>
      {deleteTargetId && (
        <div role="presentation" style={{ position: 'fixed', inset: 0, zIndex: 1000, background: '#000b', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div role="alertdialog" aria-modal="true" aria-labelledby="post-delete-title" aria-describedby="post-delete-description" style={{ width: '100%', maxWidth: 360, padding: 22, borderRadius: 16, background: '#1a1a1a', border: '1px solid #444', boxShadow: '0 12px 40px #000b' }}>
            <h3 id="post-delete-title" style={{ margin: '0 0 12px', fontSize: 18 }}>投稿を削除しますか？</h3>
            <p id="post-delete-description" style={{ color: '#bbb', fontSize: 14, lineHeight: 1.6, margin: '0 0 22px' }}>この操作は取り消せません。</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button type="button" disabled={isDeleting} onClick={() => setDeleteTargetId(null)} style={{ width: 'auto', padding: '10px 16px', borderRadius: 10, background: '#333', color: '#fff' }}>キャンセル</button>
              <button type="button" disabled={isDeleting} onClick={() => void handleDelete()} style={{ width: 'auto', padding: '10px 16px', borderRadius: 10, background: '#b73535', color: '#fff', opacity: isDeleting ? 0.6 : 1 }}>{isDeleting ? '削除中...' : '削除する'}</button>
            </div>
          </div>
        </div>
      )}
    <main ref={refreshContainerRef} className={profileUserId ? undefined : "app"}>

      <div

        className={profileUserId ? undefined : "card"}

        style={{

          paddingTop: 0,

        }}

      >

        {!profileUserId && (isRefreshing || pullDistance > 0 || refreshError) && (
          <div role="status" aria-live="polite" style={{ textAlign: 'center', fontSize: 12, color: refreshError ? '#ff9999' : '#aaa', padding: '9px 4px', minHeight: 20 }}>
            {refreshError || (isRefreshing ? '更新中...' : pullDistance >= 76 ? '離して更新' : '下に引っ張って更新')}
          </div>
        )}

        {!profileUserId && <>{/* ホームのコンパクトなツール導線。スクロール時は投稿と一緒に隠れる */}
        <section style={{ padding: '12px 0 13px', borderBottom: '1px solid #242424' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 9 }}>
            <strong style={{ fontSize: 13 }}>♠ ポーカーツール</strong>
            <button type="button" onClick={() => navigate('/tools')} style={{ width: 'auto', padding: '2px 0', background: 'transparent', color: '#bbb', fontSize: 11 }}>すべて見る ›</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 7 }}>
            {[
              { label: 'TDAクイズ', sub: '裁定を学ぶ', icon: '♠', url: '/tda' },
              { label: 'TDA検索', sub: 'ルールを調べる', icon: '⌕', url: '/tda' },
              { label: '実戦記録', sub: '今日の成績', icon: '▥', url: '/results' },
            ].map((tool) => (
              <button key={tool.label} type="button" onClick={() => navigate(tool.url)} style={{ minWidth: 0, padding: '11px 3px 9px', border: '1px solid #2c2c2c', borderRadius: 12, background: '#151515', color: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <span style={{ fontSize: 21, lineHeight: 1.1 }}>{tool.icon}</span>
                <span style={{ fontSize: 12, fontWeight: 800, whiteSpace: 'nowrap' }}>{tool.label}</span>
                <span style={{ fontSize: 10, color: '#999', whiteSpace: 'nowrap' }}>{tool.sub}</span>
              </button>
            ))}
          </div>
          <button type="button" onClick={() => navigate('/tools')} style={{ width: '100%', marginTop: 11, padding: '7px 2px 1px', background: 'transparent', color: '#aaa', fontSize: 11, textAlign: 'center', border: 0, lineHeight: 1.5 }}>
            ✦ ポットオッズ計算など、便利なツールをもっと見る →
          </button>
        </section>

        {/* 投稿作成：既存の入力・添付・送信状態は保持したまま視認性のみ改善 */}

        <section

          style={{

            margin: '0 -20px',

            padding: '18px 20px 20px',

            background: 'linear-gradient(180deg, #161616 0%, #101010 100%)',

            borderBottom:

              '8px solid #0b0b0b',

          }}

        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span aria-hidden="true" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, borderRadius: 9, background: '#292929', color: '#fff', fontSize: 18 }}>＋</span>
              <span style={{ fontWeight: 800, fontSize: 15, letterSpacing: '0.1px' }}>投稿を作成</span>
            </div>
            <span style={{ color: '#888', fontSize: 11 }}>ポーカーの話をシェア</span>
          </div>

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

              width: '100%',
              boxSizing: 'border-box',
              padding: '14px 15px',

              background: '#202020',

              border: '1px solid #444',

              borderRadius: 13,
              color: '#fff',

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

              gap: '5px',

              marginTop: '10px',

            }}

          >

            <div style={{minWidth:0,flex:'1 1 auto',overflowX:'auto'}}>{renderPostModeButtons()}</div>
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

              disabled={isPosting || !canSubmitPost}

              style={{

                width: 'auto',

                minWidth: '58px',

                padding:

                  '8px 10px',

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

          {renderInteractiveFields()}
          <input ref={imageInputRef} type="file" accept="image/jpeg,image/png,image/webp" multiple hidden onChange={e => { chooseImages(e.target.files); e.target.value = '' }} />
          <input ref={videoInputRef} type="file" accept="video/mp4,video/webm" hidden onChange={e => { void chooseVideo(e.target.files?.[0]); e.target.value = '' }} />
          {attachmentsOpen && renderAttachmentPicker()}
          {renderSelectedResultPreview()}
        </section>

        {/* タイムライン切り替え */}

        <div

          style={{

            position: 'sticky',

            top: '58px',

            zIndex: 19,

            background: '#080808',

            boxShadow: '0 -4px 0 #080808',

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

            おすすめ

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

        </>}
        {!profileUserId && composeOpen && <div role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) setComposeOpen(false) }} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.8)', zIndex: 9999, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', overflowY: 'auto', padding: '8vh 12px 24px' }}>
          <div role="dialog" aria-modal="true" aria-label="新しい投稿" style={{ width: '100%', maxWidth: 560, background: '#111', border: '1px solid #333', borderRadius: 18, padding: 20, color: '#fff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}><strong>新しい投稿</strong><button type="button" onClick={() => setComposeOpen(false)} style={{ width: 'auto', background: 'transparent', color: '#ccc', fontSize: 22 }}>×</button></div>
            <textarea autoFocus placeholder="ポーカーについて何を投稿する？" maxLength={500} value={content} onChange={e => setContent(e.target.value)} style={{ width: '100%', minHeight: 180, padding: 8, background: 'transparent', color: '#fff', border: 'none', fontSize: 17, resize: 'vertical' }}/>
            {renderPostModeButtons()}
            {renderInteractiveFields()}
            {attachmentsOpen && renderAttachmentPicker()}
            {renderSelectedResultPreview()}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 18 }}><span style={{ color: '#888', fontSize: 12 }}>{content.length}/500</span><button type="button" disabled={isPosting || !canSubmitPost} onClick={handlePost} style={{ width: 'auto', borderRadius: 99, background: '#fff', color: '#000', padding: '10px 24px', fontWeight: 800 }}>{isPosting ? '投稿中...' : '投稿する'}</button></div>
            {message && <div style={{ color: '#ccc', marginTop: 10, fontSize: 12 }}>{message}</div>}
          </div>
        </div>}
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

                  key={post.feedKey || post.id}

                  style={{

                    padding:

                      '17px 20px 13px',

                    borderBottom:

                      '1px solid #242424',

                  }}

                >

                  {post.repostedBy && (
                    <div style={{ color: '#aaa', fontSize: 12, marginBottom: 10, textAlign: 'left' }}>
                      ↻ {post.repostedBy.display_name} (@{post.repostedBy.poker_id}) がリポスト
                    </div>
                  )}
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

                        {currentUserId === post.user_id && !post.repostedBy && (
                          <div style={{ position: 'relative', marginLeft: 'auto', flexShrink: 0 }}>
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation()
                                setPostMenuId(openId => openId === post.id ? null : post.id)
                              }}
                              aria-label="投稿メニューを開く"
                              aria-expanded={postMenuId === post.id}
                              aria-haspopup="menu"
                              title="投稿メニュー"
                              style={{ width: 28, height: 28, padding: 0, background: 'transparent', color: '#aaa', borderRadius: '50%', fontSize: 18, lineHeight: 1 }}
                            >
                              ⋯
                            </button>
                            {postMenuId === post.id && (
                              <div role="menu" aria-label="投稿の操作" style={{ position: 'absolute', top: 30, right: 0, zIndex: 10, minWidth: 150, padding: 5, background: '#222', border: '1px solid #444', borderRadius: 10, boxShadow: '0 6px 20px #000a' }}>
                                <button
                                  type="button"
                                  role="menuitem"
                                  onClick={(event) => {
                                    event.stopPropagation()
                                    setPostMenuId(null)
                                    setDeleteTargetId(post.id)
                                  }}
                                  style={{ display: 'block', width: '100%', textAlign: 'left', padding: '10px 12px', border: 0, borderRadius: 7, background: 'transparent', color: '#ff9999', fontSize: 13 }}
                                >
                                  投稿を削除
                                </button>
                                <button
                                  type="button"
                                  role="menuitem"
                                  onClick={(event) => { event.stopPropagation(); setPostMenuId(null) }}
                                  style={{ display: 'block', width: '100%', textAlign: 'left', padding: '10px 12px', border: 0, borderRadius: 7, background: 'transparent', color: '#ccc', fontSize: 13 }}
                                >
                                  閉じる
                                </button>
                              </div>
                            )}
                          </div>
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

                      {interactiveItems[post.id] && <InteractiveCard item={interactiveItems[post.id]} result={interactiveResults[post.id]} onUpdated={loadPosts} isOwner={post.user_id===currentUserId} ownerName={post.profile?.display_name||post.profile?.poker_id||'募集者'} />}
                      {post.quote_post_id && (
                        <QuoteSourcePreview source={post.quotePreview} onOpen={post.quotePreview ? () => navigate(`/post/${post.quotePreview!.id}`) : undefined} />
                      )}
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
                        <div style={{ marginTop: 12, color: '#b9a781', fontSize: 11, lineHeight: 1.6 }}>※プレイヤータイプは強さや技術の優劣を示すものではありません。</div>
                        <div style={{ marginTop: 14, fontSize: 12, color: '#d4b777' }}>診断結果を見る →</div>
                      </button>
                    )}

                    {post.style_snapshot && renderStyleSnapshot(post.style_snapshot)}
                    {post.video_path && <PostVideo postId={post.id} />}
                    {Array.isArray(post.image_urls) && post.image_urls.length > 0 && <div style={{ display: 'grid', gridTemplateColumns: post.image_urls.length > 1 ? 'repeat(2,minmax(0,1fr))' : '1fr', gap: 5, margin: '10px 0 14px' }}>{post.image_urls.map((url, i) => <a key={`${post.id}-${i}`} href={url} target="_blank" rel="noopener noreferrer"><img src={url} alt={`投稿画像${i+1}`} loading="lazy" style={{ width: '100%', maxHeight: 460, objectFit: 'cover', borderRadius: 10 }}/></a>)}</div>}
                    {/* アクション */}
                      <style>{`
  .poker-feed-actions > button, .poker-feed-actions > div > button {
    width:100% !important; min-width:0 !important; box-sizing:border-box;
    display:flex !important; align-items:center !important; justify-content:center !important;
    flex-wrap:nowrap !important; white-space:nowrap !important;
    padding:9px 0 !important; font-size:clamp(11px, 3.3vw, 13px) !important;
    font-weight:500 !important; gap:3px !important; line-height:1.25 !important;
    overflow:visible !important;
  }
  .poker-feed-actions > div { min-width:0 !important; }
  .poker-feed-actions .poker-action-icon {
    display:inline-flex; align-items:center; justify-content:center;
    font-size:clamp(16px, 4.5vw, 18px) !important; line-height:1 !important;
    flex-shrink:0;
  }
  .poker-feed-actions .poker-action-label { font-size:inherit !important; line-height:inherit !important; white-space:nowrap !important; }
  @media (min-width:440px) {
    .poker-feed-actions > button, .poker-feed-actions > div > button { font-size:13px !important; gap:5px !important; }
  }
`}</style>
                      <div className="poker-feed-actions"
                        style={{
                          display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', alignItems: 'center', gap: '3px',

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

                          <span className="poker-action-icon"

                            style={{

                              fontSize:

                                '19px',

                              lineHeight: 1,

                            }}

                          >

                            ♧

                          </span>

                          <span className="poker-action-label">コメント</span>
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

                          <span className="poker-action-icon"

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

                          <span className="poker-action-label">いいね</span>
                          {post.likeCount >

                            0 && (

                            <span>

                              {

                                post.likeCount

                              }

                            </span>

                          )}

                        </button>

                        <div style={{ position: 'relative', minWidth: 0 }}>
                          <button type="button" disabled={repostingId !== null}
                            aria-label="リポストの選択" aria-expanded={repostMenuId === post.feedKey}
                            onClick={() => setRepostMenuId(old => old === post.feedKey ? null : (post.feedKey || post.id))}
                            style={{ width: 'auto', padding: '5px 0', border: 0, background: 'transparent',
                              color: post.repostedByMe ? '#8dd5b0' : '#888', fontSize: 12, whiteSpace: 'nowrap' }}>
                            <span className="poker-action-icon">↻</span><span className="poker-action-label">リポスト</span>
                            {(post.repostCount || 0) > 0 ? post.repostCount : ''}
                          </button>
                          {repostMenuId === (post.feedKey || post.id) && <div style={{ position: 'absolute', zIndex: 15,
                            right: 0, bottom: '100%', minWidth: 176, padding: 6, border: '1px solid #555',
                            borderRadius: 10, background: '#252525', boxShadow: '0 6px 24px #000a' }}>
                            <button type="button" disabled={repostingId !== null} onClick={() => { setRepostMenuId(null); void handleRepost(post) }}
                              style={{ width: '100%', textAlign: 'left', padding: 10, background: 'transparent', color: '#eee', fontSize: 13 }}>
                              ↻ {post.repostedByMe ? 'リポストを解除' : 'リポスト'}</button>
                            <button type="button" onClick={() => { setQuoteTarget(post); setQuoteText(''); setRepostMenuId(null) }}
                              style={{ width: '100%', textAlign: 'left', padding: 10, background: 'transparent', color: '#eee', fontSize: 13 }}>
                              ▤ 引用して投稿</button>
                          </div>}
                        </div>
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

                              '13px',

                            lineHeight: 1,

                          }}

                        >

                          <span className="poker-action-icon">↗</span><span className="poker-action-label">シェア</span>

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

      {quoteTarget && <div role="dialog" aria-modal="true" aria-label="引用リポスト" style={{ position: 'fixed', zIndex: 1000,
        inset: 0, background: '#000b', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
        <div style={{ width: '100%', maxWidth: 480, padding: 18, background: '#1d1d1d', border: '1px solid #555', borderRadius: 16 }}>
          <h3 style={{ marginTop: 0 }}>引用して投稿</h3>
          <textarea autoFocus value={quoteText} onChange={event => setQuoteText(event.target.value)} maxLength={1000}
            placeholder="この投稿についてコメントを書く..." disabled={quoteBusy}
            style={{ width: '100%', minHeight: 110, padding: 10, boxSizing: 'border-box', color: '#fff', background: '#111', borderRadius: 8 }} />
          <div style={{ maxHeight: '36vh', overflowY: 'auto', marginTop: 8 }}>
            <QuoteSourcePreview compact source={{ ...quoteTarget, resultData: quoteTarget.resultData || quoteTarget.amusementResultData || quoteTarget.cashResultData || null }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 12 }}>
            <button type="button" disabled={quoteBusy} onClick={() => { setQuoteTarget(null); setQuoteText('') }} style={{ width: 'auto', minWidth: 106, minHeight: 42, padding: '10px 16px', fontSize: 13, fontWeight: 700, background: '#272727', color: '#efefef', border: '1px solid #515151', borderRadius: 11, cursor: 'pointer' }}>キャンセル</button>
            <button type="button" disabled={quoteBusy || !quoteText.trim()} onClick={() => void publishQuote()}
              style={{ width: 'auto', minWidth: 106, minHeight: 42, padding: '10px 16px', fontSize: 13, fontWeight: 750, background: '#323029', color: '#f0d99b', border: '1px solid #726343', borderRadius: 11, cursor: 'pointer' }}>{quoteBusy ? '投稿中...' : '投稿する'}</button>
          </div>
        </div>
      </div>}
    </main>
    </>
  )

}

export default Timeline
