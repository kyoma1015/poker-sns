import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { supabase } from './supabase'
import './PlayerTypeDiagnosis.css'
import { loadShareImage, encodeSharePng } from './playerTypeShareImage'
import { parseQuestions, LatestRequest } from './playerTypeQuestions'
import { topPersonalTraits, personalAdvice } from './playerTypePresentation'

type Option = {
  id: string
  order: number
  text: string
}

type Question = {
  id: string
  key: string
  order: number
  text: string
  options: Option[]
}

type SavedResult = {
  result_id: string
  result_type_key: string
  animal_name_ja: string
  catchphrase: string
  confidence: number
  top_margin: number
  core_answer_count: number
  is_public: boolean
  completed_at: string
}

type ResultDetail = SavedResult & {
  animal_name_en: string
  description: string
  behavior_text: string
  strength_text: string
  weakness_text: string
  perceived_text: string
  best_situation_text: string
  trait_scores: Record<string, number>
  discriminator_scores: Record<string, number>
}

const QUESTION_COUNT = 50

const animalEmoji: Record<string, string> = {
  lion: '🦁',
  tiger: '🐯',
  leopard: '🐆',
  bison: '🦬',
  gorilla: '🦍',
  rhino: '🦏',
  shark: '🦈',
  owl: '🦉',
  eagle: '🦅',
  elephant: '🐘',
  giraffe: '🦒',
  wolf: '🐺',
  hyena: '🐾',
  cat: '🐈',
  chameleon: '🦎',
  dolphin: '🐬',
  fox: '🦊',
  snake: '🐍',
  raccoon: '🦝',
  turtle: '🐢',
  rabbit: '🐇',
  crocodile: '🐊',
  hedgehog: '🦔',
  deer: '🦌',
  sloth: '🦥',
  dog: '🐕',
  bear: '🐻',
  bull: '🐄',
  badger: '🦡',
  monkey: '🐒',
  magpie: '🐦‍⬛',
  penguin: '🐧',
  horse: '🐎',
  squirrel: '🐿️',
  mountain_goat: '🐐',
  otter: '🦦',
}


function PlayerTypeDiagnosis() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const imageResultId = searchParams.get('result')
  const clickLock = useRef(false)
  const questionRequest = useRef(new LatestRequest())
  const resultRequest = useRef(new LatestRequest())
  const questionPending = useRef(false)
  const sharePending = useRef(false)
  const activeResultId = useRef<string | null>(null)
  const savedResultId = searchParams.get('result')
  const imageOperation = useRef({ generation: 0, pending: false })

  const [screen, setScreen] = useState<'intro' | 'quiz' | 'result'>('intro')
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answerIds, setAnswerIds] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingQuestions, setLoadingQuestions] = useState(!savedResultId)
  const [questionError, setQuestionError] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState<SavedResult | null>(null)
  const [detail, setDetail] = useState<ResultDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [isOwner, setIsOwner] = useState<boolean | null>(null)
  const [sharePosting, setSharePosting] = useState(false)
  const [shareMessage, setShareMessage] = useState('')
  const [shareEditorOpen, setShareEditorOpen] = useState(false)
  const [shareText, setShareText] = useState('')
  const [externalShareError, setExternalShareError] = useState('')
  const [imageSaving, setImageSaving] = useState(false)

  useEffect(() => {
    const operation = imageOperation.current
    operation.generation++
    operation.pending = false
    setImageSaving(false)
    setExternalShareError('')
    return () => {
      operation.generation++
      operation.pending = false
    }
  }, [result?.result_id, imageResultId])

  useEffect(() => {
    const questionsGate = questionRequest.current
    const resultsGate = resultRequest.current
    void loadQuestions()
    return () => {
      questionsGate.invalidate()
      questionPending.current = false
      resultsGate.invalidate()
      activeResultId.current = null
      sharePending.current = false
    }
  }, [])

  async function loadQuestions() {
    if (questionPending.current) return
    questionPending.current = true
    const request = questionRequest.current.start()
    setLoadingQuestions(!activeResultId.current)
    setQuestionError('')
    try {
      const { data, error: rpcError } = await supabase.rpc('get_player_type_v2_questions')
      if (!questionRequest.current.isCurrent(request)) return
      if (rpcError) throw rpcError
      setQuestions(parseQuestions(data))
    } catch {
      if (!questionRequest.current.isCurrent(request)) return
      setQuestions([])
      setQuestionError('質問を読み込めませんでした。通信状況やログイン状態を確認して、もう一度お試しください。')
    } finally {
      if (questionRequest.current.isCurrent(request)) {
        questionPending.current = false
        setLoadingQuestions(false)
      }
    }
  }

  const currentQuestion = useMemo(
    () => questions[currentIndex] ?? null,
    [questions, currentIndex],
  )

  const visibleNumber = currentIndex + 1
  const progress = Math.min(100, (visibleNumber / QUESTION_COUNT) * 100)

  function startDiagnosis() {
    imageOperation.current.generation++
    imageOperation.current.pending = false
    sharePending.current = false
    resultRequest.current.invalidate()
    activeResultId.current = null
    setShareEditorOpen(false)
    setSharePosting(false)
    setImageSaving(false)
    setShareMessage('')
    setExternalShareError('')
    setIsOwner(null)
    setDetailLoading(false)
    if (questions.length !== QUESTION_COUNT) {
      navigate('/player-type', { replace: true })
      setResult(null)
      setDetail(null)
      setScreen('intro')
      void loadQuestions()
      return
    }
    // A restarted diagnosis must not retain the previous result's deep link.
    if (searchParams.has('result')) navigate('/player-type', { replace: true })

    setScreen('quiz')
    setCurrentIndex(0)
    setAnswerIds([])
    setResult(null)
    setDetail(null)
    setError('')
    setLoading(false)
    clickLock.current = false
  }

  async function chooseOption(optionId: string) {
    if (loading || clickLock.current || !currentQuestion) return
    if (answerIds.length !== currentIndex) return

    clickLock.current = true
    setError('')

    const nextAnswers = [...answerIds, optionId]

    if (currentIndex < QUESTION_COUNT - 1) {
      setAnswerIds(nextAnswers)
      setCurrentIndex((value) => value + 1)

      // Prevent a rapid double-click from answering the next question too.
      window.setTimeout(() => {
        clickLock.current = false
      }, 0)
      return
    }

    setLoading(true)
    const request = resultRequest.current.start()

    try {
      await saveResult(nextAnswers, request)
    } catch {
      if (!resultRequest.current.isCurrent(request)) return
      setError('結果を保存できませんでした。通信状況を確認して、最後の回答をもう一度選んでください。')
    } finally {
      if (resultRequest.current.isCurrent(request)) {
        setLoading(false)
        clickLock.current = false
      }
    }
  }

  async function saveResult(finalAnswers: string[], request: number) {
    if (finalAnswers.length !== QUESTION_COUNT) {
      setError(
        `回答数が正しくありません（${finalAnswers.length}/${QUESTION_COUNT}）`,
      )
      return
    }

    const { data, error: saveError } = await supabase.rpc(
      'complete_player_type_v2_diagnosis',
      {
        p_option_ids: finalAnswers,
        p_is_public: true,
      },
    )

    if (!resultRequest.current.isCurrent(request)) return

    if (saveError) {
      // IMPORTANT:
      // The 50th answer is not committed to answerIds until the RPC succeeds.
      // A retry therefore sends exactly 50 answers instead of duplicating Q50.
      setError('結果を保存できませんでした。通信状況を確認して、最後の回答をもう一度選んでください。')
      return
    }

    const saved = (data?.[0] ?? null) as SavedResult | null

    if (!saved) {
      setError('保存された診断結果を取得できませんでした。')
      return
    }

    setAnswerIds(finalAnswers)
    setLoading(false)
    clickLock.current = false
    setResult(saved)
    // Persist the newly created result ID in the browser URL (refresh/share/back).
    navigate(`/player-type?result=${encodeURIComponent(saved.result_id)}`, { replace: true })
    setIsOwner(true)
    setScreen('result')
    void loadSavedResult(saved.result_id)
  }

  async function loadSavedResult(resultId: string) {
    const request = resultRequest.current.start()
    activeResultId.current = resultId
    // Share drafts and async outcomes belong to this result only.
    setShareEditorOpen(false)
    setShareText('')
    setShareMessage('')
    setSharePosting(false)
    sharePending.current = false
    setExternalShareError('')
    setImageSaving(false)
    setLoadingQuestions(false)
    setError('')
    setResult(null)
    setDetail(null)
    setIsOwner(null)
    setScreen('result')
    setDetailLoading(true)
    try {
      const { data, error: detailError } = await supabase.rpc(
        'get_player_type_v2_result_detail', { p_result_id: resultId },
      )
      if (!resultRequest.current.isCurrent(request)) return
      if (detailError) throw detailError
      const row = (data?.[0] ?? null) as ResultDetail | null
      if (!row || row.result_id !== resultId) throw new Error('not found')
      const { data: ownedResult, error: ownerError } = await supabase.rpc(
        'is_my_player_type_v2_result', { p_result_id: resultId },
      )
      if (!resultRequest.current.isCurrent(request)) return
      if (ownerError) throw ownerError
      setIsOwner(ownedResult === true)
      setResult(row)
      setDetail(row)
    } catch {
      if (!resultRequest.current.isCurrent(request)) return
      setError('診断結果を読み込めませんでした。公開状態や通信状況を確認し、もう一度お試しください。')
    } finally {
      if (resultRequest.current.isCurrent(request)) setDetailLoading(false)
    }
  }

  function restart() {
    startDiagnosis()
  }

  useEffect(() => {
    if (savedResultId) {
      if (savedResultId !== activeResultId.current) void loadSavedResult(savedResultId)
    } else if (activeResultId.current) {
      resultRequest.current.invalidate()
      activeResultId.current = null
      setResult(null)
      setDetail(null)
      setIsOwner(null)
      setDetailLoading(false)
      setError('')
      setScreen('intro')
    }
  }, [savedResultId])

  if (screen === 'result' && !result) {
    return (
      <main className="ptd-page">
        <div className="ptd-shell ptd-center">
          {detailLoading ? <p role="status">診断結果を読み込んでいます...</p> : <>
            <p className="ptd-error" role="alert">{error}</p>
            <button className="ptd-secondary" type="button" onClick={() => savedResultId && void loadSavedResult(savedResultId)}>結果を再読み込み</button>
            <button className="ptd-secondary" type="button" onClick={restart}>診断の最初へ</button>
          </>}
        </div>
      </main>
    )
  }

  if (loadingQuestions) {
    return (
      <main className="ptd-page">
        <div className="ptd-shell ptd-center">
          <div className="ptd-spinner" />
          <p>診断を準備しています...</p>
        </div>
      </main>
    )
  }

  if (screen === 'intro') {
    return (
      <main className="ptd-page">
        <div className="ptd-shell">
          <button className="ptd-back" onClick={() => navigate(-1)}>
            ← 戻る
          </button>

          <section className="ptd-hero">
            <div className="ptd-kicker">POKER ID PLAYER TYPE</div>

            <div className="ptd-animal-row" aria-hidden="true">
              <span>🦁</span>
              <span>🦉</span>
              <span>🦈</span>
              <span>🦊</span>
              <span>🐺</span>
            </div>

            <h1>
              あなたは、どんな
              <br />
              ポーカープレイヤー？
            </h1>

            <p className="ptd-lead">
              50個の質問から、あなたの判断傾向を分析。
              36種類の動物タイプから、最も近いプレイヤータイプを診断します。
            </p>

            <p style={{ color: '#c9b88d', fontSize: 13, lineHeight: 1.7, margin: '16px 0' }}>この診断はプレイヤーの強さや技術の優劣を評価するものではなく、プレイスタイルの特徴や傾向を表すものです。</p>

            <div className="ptd-time">
              <strong>全50問</strong>
              <span>精度を重視した固定50問の診断です</span>
            </div>

            <div className="ptd-note">
              <span>✓ 正解・不正解なし</span>
              <span>✓ 直感で回答</span>
              <span>✓ 全50問</span>
            </div>

            {questionError && <div className="ptd-error" role="alert">{questionError}</div>}
            {questionError && <button className="ptd-secondary" type="button" onClick={() => void loadQuestions()}>質問を再読み込み</button>}

            <button
              className="ptd-primary"
              disabled={questions.length !== QUESTION_COUNT}
              onClick={startDiagnosis}
            >
              診断をはじめる
            </button>

            <p className="ptd-small">
              深く考えすぎず、実戦で自分が取りやすい行動を選んでください。
            </p>
          </section>
        </div>
      </main>
    )
  }

  function openShareEditor() {
    if (!result || isOwner !== true) return
    setShareText(`プレイヤータイプ診断の結果は「${result.animal_name_ja}」でした！\n\n`)
    setShareMessage('')
    setShareEditorOpen(true)
  }

  async function shareToTimeline() {
    if (!result || isOwner !== true || sharePosting || sharePending.current || !shareText.trim() || shareText.length > 500) return
    const request = resultRequest.current.capture()
    sharePending.current = true
    setSharePosting(true)
    setShareMessage('')
    try {
      const { data: { user }, error: authError } = await supabase.auth.getUser()
      if (!resultRequest.current.isCurrent(request)) return
      if (authError || !user) throw new Error('ログイン情報を確認できませんでした')
      const { error: postError } = await supabase.from('posts').insert({
        user_id: user.id,
        post_type: 'result',
        result_type: 'player_type',
        result_id: result.result_id,
        content: shareText.trim(),
      })
      if (!resultRequest.current.isCurrent(request)) return
      if (postError) throw postError
      setShareMessage('タイムラインに投稿しました。')
      setShareEditorOpen(false)
    } catch {
      if (!resultRequest.current.isCurrent(request)) return
      setShareMessage('投稿に失敗しました。通信状況を確認して、もう一度お試しください。')
    } finally {
      if (resultRequest.current.isCurrent(request)) {
        sharePending.current = false
        setSharePosting(false)
      }
    }
  }

  async function createShareImage(): Promise<Blob> {
    if (!result) throw new Error('診断結果がありません')
    if (!detail) throw new Error('詳細分析を読み込み中です。少し待ってからお試しください')

    const canvas = document.createElement('canvas')
    canvas.width = 1080
    canvas.height = 1500
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('画像作成に対応していないブラウザです')

    const background = ctx.createLinearGradient(0, 0, 1080, 1500)
    background.addColorStop(0, '#17130c')
    background.addColorStop(0.55, '#080808')
    background.addColorStop(1, '#20170b')
    ctx.fillStyle = background
    ctx.fillRect(0, 0, 1080, 1500)
    ctx.strokeStyle = '#b9954d'
    ctx.lineWidth = 5
    ctx.strokeRect(40, 40, 1000, 1420)
    ctx.strokeStyle = '#564323'
    ctx.lineWidth = 2
    ctx.strokeRect(58, 58, 964, 1384)

    ctx.textAlign = 'center'
    ctx.fillStyle = '#d8b56a'
    ctx.font = 'bold 42px sans-serif'
    ctx.fillText('POKER ID', 540, 124)
    ctx.font = '24px sans-serif'
    ctx.fillText('PLAYER TYPE DIAGNOSIS', 540, 169)

    const animal = await loadShareImage(`/animals/${result.result_type_key}.png`)
    // Keep the original animal artwork, without cropping or stretching.
    ctx.drawImage(animal, 260, 196, 560, 560)

    ctx.fillStyle = '#bda56f'
    ctx.font = '23px sans-serif'
    ctx.fillText('YOUR PLAYER TYPE', 540, 788)
    ctx.fillStyle = '#fff3d3'
    ctx.font = 'bold 72px sans-serif'
    ctx.fillText(result.animal_name_ja, 540, 870, 900)

    const drawingContext = ctx

    function drawWrappedText(value: string, centerX: number, startY: number, maxWidth: number, lineHeight: number, maxLines: number) {
      const lines: string[] = []
      let line = ''
      for (const char of Array.from(value.replace(/\s+/g, ' ').trim())) {
        if (drawingContext.measureText(line + char).width > maxWidth && line) {
          lines.push(line)
          line = char
        } else {
          line += char
        }
      }
      if (line) lines.push(line)
      lines.slice(0, maxLines).forEach((text, index) => {
        const truncated = index === maxLines - 1 && lines.length > maxLines
          ? `${text.slice(0, -2)}…` : text
        drawingContext.fillText(truncated, centerX, startY + index * lineHeight, maxWidth)
      })
      return Math.min(lines.length, maxLines)
    }

    ctx.fillStyle = '#e3cb94'
    ctx.font = '30px sans-serif'
    drawWrappedText(result.catchphrase, 540, 929, 880, 40, 2)

    ctx.strokeStyle = '#6c532a'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(132, 1010)
    ctx.lineTo(948, 1010)
    ctx.stroke()

    ctx.fillStyle = '#d8b56a'
    ctx.font = 'bold 28px sans-serif'
    ctx.fillText('特に強く出ている3つの傾向', 540, 1062)

    const traits = topPersonalTraits(detail)
    ctx.textAlign = 'left'
    ctx.font = 'bold 29px sans-serif'
    traits.forEach((trait, index) => {
      const y = 1123 + index * 67
      ctx.fillStyle = '#b9954d'
      ctx.fillText(`0${index + 1}`, 145, y)
      ctx.fillStyle = '#fff0cc'
      ctx.fillText(trait.label, 225, y, 710)
    })

    if (traits.length === 0) {
      ctx.textAlign = 'center'
      ctx.fillStyle = '#e3cb94'
      ctx.font = '25px sans-serif'
      drawWrappedText(detail.description, 540, 1150, 770, 39, 3)
    }

    ctx.textAlign = 'center'
    ctx.strokeStyle = '#6c532a'
    ctx.beginPath()
    ctx.moveTo(132, 1350)
    ctx.lineTo(948, 1350)
    ctx.stroke()
    ctx.fillStyle = '#f1d59a'
    ctx.font = 'bold 28px sans-serif'
    ctx.fillText('あなたはどのタイプ？', 540, 1380)
    ctx.font = '22px sans-serif'
    ctx.fillText('全50問・36種類の動物タイプ｜Poker IDで無料診断', 540, 1411)
    ctx.font = '19px sans-serif'
    ctx.fillStyle = '#d8c8a4'
    ctx.fillText('※強さや技術の優劣ではなく、プレイスタイルの傾向を表します。', 540, 1440, 890)

    return await encodeSharePng(canvas)
  }

  function downloadShareImage(blob: Blob) {
    if (!result) return
    const url = URL.createObjectURL(blob)
    let link: HTMLAnchorElement | null = null
    let downloadFailed = false
    try {
      link = document.createElement('a')
      link.href = url
      link.download = `PokerID_${result.result_type_key}_${result.result_id.slice(0, 8)}.png`
      document.body.appendChild(link)
      link.click()
    } catch (error) {
      downloadFailed = true
      throw error
    } finally {
      try {
        link?.remove()
      } catch (error) {
        // Preserve the original download error if cleanup also fails.
        if (!downloadFailed) throw error
      } finally {
        window.setTimeout(() => URL.revokeObjectURL(url), 30000)
      }
    }
  }

  async function saveShareImage() {
    const operation = imageOperation.current
    if (!result || !detail || operation.pending) return
    const generation = operation.generation
    operation.pending = true
    setImageSaving(true)
    setExternalShareError('')
    try {
      const image = await createShareImage()
      if (operation.generation !== generation) return
      downloadShareImage(image)
    } catch {
      // Selectively inherit PR60's public generic message, never raw exceptions.
      if (operation.generation !== generation) return
      setExternalShareError('画像の保存に失敗しました。もう一度お試しください。')
    } finally {
      if (operation.generation === generation) {
        operation.pending = false
        setImageSaving(false)
      }
    }
  }

  function shareToX() {
    if (!result) return
    const message = `Poker IDのプレイヤータイプ診断は「${result.animal_name_ja}」！\n${result.catchphrase}\n\nあなたは何タイプ？ #PokerID #ポーカー`
    const intent = new URL('https://twitter.com/intent/tweet')
    intent.searchParams.set('text', message)
    intent.searchParams.set('url', `https://poker-sns-vert.vercel.app/share/player-type/${encodeURIComponent(result.result_id)}`)
    window.open(intent.toString(), '_blank', 'noopener,noreferrer')
  }

  if (screen === 'result' && result) {
    const emoji = animalEmoji[result.result_type_key] ?? '♠️'
    const personalTraits = detail ? topPersonalTraits(detail) : []

    return (
      <main className="ptd-page">
        <div className="ptd-shell">
          <section className="ptd-result">
            <div className="ptd-kicker">{isOwner === false ? "PLAYER TYPE" : "YOUR PLAYER TYPE"}</div>
            <div className="ptd-result-animal" style={{ width: 'min(100%, 320px)', height: 'auto', margin: '14px auto', fontSize: 64 }}>
              {Object.prototype.hasOwnProperty.call(animalEmoji, result.result_type_key) ? (
                <img src={`/animals/${result.result_type_key}.png`} alt={`${result.animal_name_ja}のキャラクター`} style={{ display: 'block', width: '100%', aspectRatio: '1 / 1', objectFit: 'contain', borderRadius: 20 }} />
              ) : emoji}
            </div>
            <p className="ptd-result-label">{isOwner === false ? "このプレイヤーのタイプ" : "あなたのプレイヤータイプは"}</p>
            <h1>{result.animal_name_ja}</h1>
            <div className="ptd-catchphrase">{result.catchphrase}</div>

            <p style={{ color: '#c9b88d', fontSize: 12, lineHeight: 1.7, margin: '14px 0' }}>この診断はプレイヤーの強さや技術の優劣を評価するものではなく、プレイスタイルの特徴や傾向を表すものです。</p>

            <div className="ptd-result-meta">
              <span>{result.core_answer_count}問回答</span>
            </div>

            {detailLoading && (
              <div className="ptd-detail-loading">詳細結果を分析しています...</div>
            )}

            {error && <div className="ptd-error">{error}</div>}

            {detail && (
              <div className="ptd-detail">
                <section className="ptd-detail-card ptd-detail-main">
                  <div className="ptd-detail-kicker">{isOwner === false ? "このプレイヤーの特徴" : "あなたはこんなプレイヤー"}</div>
                  <p>{detail.description}</p>

                  {personalTraits.length > 0 && (
                    <>
                      <h2>特に強く出ている3つの傾向</h2>
                      <div className="ptd-trait-list">
                        {personalTraits.map((trait) => (
                          <div className="ptd-trait" key={trait.key}>
                            <strong>{trait.label}</strong>
                            <p>{trait.text}</p>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </section>

                <section className="ptd-detail-card">
                  <div className="ptd-detail-kicker">実戦で出やすい行動</div>
                  <p>{detail.behavior_text}</p>
                </section>

                <section className="ptd-detail-card">
                  <div className="ptd-detail-kicker">強み</div>
                  <p>{detail.strength_text}</p>
                </section>

                <section className="ptd-detail-card">
                  <div className="ptd-detail-kicker">ハマりやすい弱点</div>
                  <p>{detail.weakness_text}</p>
                </section>

                <section className="ptd-detail-card">
                  <div className="ptd-detail-kicker">周りからはこう見えやすい</div>
                  <p>{detail.perceived_text}</p>
                </section>

                <section className="ptd-detail-card">
                  <div className="ptd-detail-kicker">相性のいい状況</div>
                  <p>{detail.best_situation_text}</p>
                </section>

                <section className="ptd-detail-card ptd-advice-card">
                  <div className="ptd-detail-kicker">{isOwner === false ? "このタイプへのアドバイス" : "あなたへの一言"}</div>
                  <p>{personalAdvice(detail)}</p>
                </section>
              </div>
            )}

            {isOwner === true && (
              <div className="ptd-share-area">
                <section className="ptd-share-panel" aria-label="診断結果をシェア">
                  <h2 className="ptd-share-heading">診断結果をシェア</h2>
                  <p style={{ fontSize: 12, color: '#b6a77e', lineHeight: 1.6 }}>※プレイヤータイプは強さや技術の優劣を示すものではありません。</p>
                  <button className="ptd-share-x" type="button" onClick={shareToX}>
                    <span aria-hidden="true">𝕏</span> Xでシェア
                  </button>
                  <button className="ptd-share-save" type="button" disabled={imageSaving || !detail} onClick={() => void saveShareImage()}>
                    <span aria-hidden="true">↓</span> {imageSaving ? '画像を作成中...' : '画像を保存'}
                  </button>
                  {externalShareError && <p className="ptd-error" role="alert">{externalShareError}</p>}
                </section>

                <div className="ptd-share-actions">
                  {!shareEditorOpen ? (
                    <button className="ptd-share-action" type="button" onClick={openShareEditor}>
                      <span>Poker IDのタイムラインに投稿</span><span aria-hidden="true">›</span>
                    </button>
                  ) : (
                    <div className="ptd-share-editor">
                      <div className="ptd-detail-kicker">投稿にひとこと添える</div>
                      <textarea aria-label="診断結果の投稿文" value={shareText} onChange={(e) => setShareText(e.target.value)} maxLength={500} rows={5} placeholder="めっちゃ当たってる！みんなは何タイプ？" className="ptd-share-textarea" />
                      <div className="ptd-share-count">{shareText.length}/500</div>
                      <p className="ptd-share-note">診断結果カードは自動で添付されます。</p>
                      <button className="ptd-primary" type="button" disabled={sharePosting || !shareText.trim()} onClick={() => void shareToTimeline()}>
                        {sharePosting ? '投稿中...' : 'この内容で投稿する'}
                      </button>
                      <button className="ptd-secondary" type="button" disabled={sharePosting} onClick={() => setShareEditorOpen(false)}>キャンセル</button>
                    </div>
                  )}
                  {shareMessage && <p className="ptd-result-hint" role="status">{shareMessage}</p>}
                  <button className="ptd-share-action ptd-share-retry" type="button" onClick={restart}>
                    <span>もう一度診断する</span><span aria-hidden="true">↻</span>
                  </button>
                </div>
              </div>
            )}

            {isOwner === false && (
              <button className="ptd-secondary" type="button" onClick={() => navigate(-1)}>
                Poker IDに戻る
              </button>
            )}
          </section>
        </div>
      </main>
    )
  }

  return (
    <main className="ptd-page">
      <div className="ptd-shell">
        <header className="ptd-quiz-header">
          <button className="ptd-back" onClick={() => navigate(-1)}>
            ×
          </button>

          <div className="ptd-progress-wrap">
            <div className="ptd-progress-copy">
              <strong>
                {visibleNumber} / {QUESTION_COUNT}
              </strong>
              <span>{Math.round(progress)}%</span>
            </div>

            <div className="ptd-progress-track">
              <div
                className="ptd-progress-bar"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </header>

        {currentQuestion && (
          <section className="ptd-question-card">
            <div className="ptd-question-number">
              QUESTION {visibleNumber}
            </div>

            <h2>{currentQuestion.text}</h2>

            <div className="ptd-options">
              {currentQuestion.options.map((option) => (
                <button
                  key={option.id}
                  className="ptd-option"
                  disabled={loading}
                  onClick={() => void chooseOption(option.id)}
                >
                  <span className="ptd-option-letter">
                    {String.fromCharCode(64 + option.order)}
                  </span>
                  <span>{option.text}</span>
                </button>
              ))}
            </div>

            {loading && <div className="ptd-calculating">分析中...</div>}
            {error && <div className="ptd-error">{error}</div>}
          </section>
        )}

        <p className="ptd-quiz-foot">
          正解はありません。一番自分に近いものを選んでください。
          <span style={{ display: 'block', marginTop: 8 }}>※プレイヤータイプは強さや技術の優劣を示すものではありません。</span>
        </p>
      </div>
    </main>
  )
}

export default PlayerTypeDiagnosis
