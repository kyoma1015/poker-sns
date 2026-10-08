import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { supabase } from './supabase'
import './PlayerTypeDiagnosis.css'

type QuestionRow = {
  question_id: string
  question_key: string
  question_order: number
  question_text: string
  option_id: string
  option_order: number
  option_text: string
}

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


const traitCopy: Record<string, { label: string; text: string }> = {
  initiative: { label: '自分から動く', text: '受け身で待つより、自分からアクションを起こして相手に判断を迫る傾向があります。' },
  risk_tolerance: { label: 'リスクを取れる', text: 'リスクがあること自体を理由に避けるより、見返りがあるなら踏み込める傾向があります。' },
  patience: { label: '待てる', text: 'すぐ結果を取りにいかず、より条件の良い場面まで待てる傾向があります。' },
  analytical: { label: '理屈から組み立てる', text: 'その場の印象だけでなく、レンジやアクションの流れを整理して判断する傾向があります。' },
  player_read: { label: '相手を見る', text: '一般論だけでなく、目の前の相手の反応や傾向を意思決定へ強く反映します。' },
  adaptability: { label: '戦い方を変えられる', text: '相手や卓の傾向が変われば、自分の基準に固執せず戦い方も変えられる側です。' },
  deception: { label: 'イメージを利用する', text: '相手が自分をどう見ているかまで考え、その予想を外す選択を使いやすい傾向があります。' },
  value_directness: { label: '取れる時に取り切る', text: '有利だと判断した場面では、回りくどくせず利益を取りにいく傾向があります。' },
  threat_sensitivity: { label: '危険信号を拾う', text: '状況が悪化したサインを軽視せず、損失が大きくなる前に警戒できる側です。' },
  novelty: { label: '新しい選択を試す', text: 'いつもの形だけに固定せず、新しい戦術やラインを試すことへの抵抗が小さい傾向があります。' },
  stability: { label: '基準がぶれにくい', text: '短期的な結果や空気に流されすぎず、自分の基準を保ちやすい傾向があります。' },
  confidence: { label: '判断を信じられる', text: '根拠を持って決めた後は、自分の判断を信じて実行しやすい側です。' },
  exploit: { label: '弱点を利益に変える', text: '相手の偏りやミスを見つけると、普段の戦い方から変えてでもそこを狙う傾向があります。' },
  tempo: { label: '反応が速い', text: '弱さや変化を感じたとき、様子見を長く続けるより早めにアクションへ移しやすい傾向があります。' },
  learning_receptivity: { label: '学びを取り込む', text: '自分だけの感覚に閉じず、他者の考えや新しい知識をプレーへ取り込みやすい側です。' },
  overview: { label: '卓全体を見る', text: '一人の相手だけでなく、テーブル全体の傾向や力関係まで見て判断する傾向があります。' },
  planning_horizon: { label: '先まで考える', text: '今の一手だけでなく、その後のストリートや展開まで見越してプランを作る傾向があります。' },
  history_use: { label: '過去の情報を使う', text: '以前のショーダウンや行動履歴を覚え、現在の判断材料として使いやすい側です。' },
  small_edge_accumulation: { label: '小さな利益を積む', text: '派手な一撃だけでなく、小さな有利を繰り返し拾うことを重視する傾向があります。' },
  action_efficiency: { label: '無駄な複雑さを減らす', text: '薄い利益のために難しい判断を増やすより、効率の良い場面へ集中する傾向があります。' },
  interaction_read: { label: '相手との読み合いを見る', text: '自分と相手の間で起きている読み合いや、相手からの見られ方を判断へ反映しやすい側です。' },
  pressure_resistance: { label: '圧力に崩れにくい', text: '強いベットやプレッシャーを受けても、それだけで判断を曲げにくい傾向があります。' },
  independent_judgment: { label: '自分の根拠で決める', text: '周囲と意見が違っても、自分なりの根拠があるなら判断を保てる側です。' },
  selective_burst: { label: '勝負所で一気に行く', text: '常に攻め続けるより、ここだと判断した場面で攻撃量を大きく上げる傾向があります。' },
  pot_size_comfort: { label: '大きなポットを怖がらない', text: 'ポットが大きくなること自体には過度に萎縮せず、必要なら大きな勝負へ入れる側です。' },
  fun_orientation: { label: '面白さも大事にする', text: '利益だけでなく「この展開をやってみたい」という面白さも意思決定へ入りやすい傾向があります。' },
  attack_momentum: { label: '攻めの流れを続ける', text: '一度作った攻撃の流れを簡単には手放さず、継続して圧力をかけやすい側です。' },
  balance_awareness: { label: '偏りすぎを避ける', text: '相手に簡単に対応されないよう、自分のベットやレイズの頻度が偏りすぎないことを意識する傾向があります。' },
  retreat_response: { label: '危険なら引き返せる', text: '途中で状況が悪化したと判断すれば、最初のプランに固執せず撤退へ切り替えられる側です。' },
  improvisation: { label: 'その場で組み直せる', text: '予定外の展開でも、その場で増えた情報を使って新しいプランを作り直す傾向があります。' },
  stimulus_orientation: { label: '動きのある展開を好む', text: '静かに待ち続けるより、判断やアクションが多い展開に入りやすい傾向があります。' },
  collision_avoidance: { label: '難しい衝突を避ける', text: '利益がありそうでも、後で大きく難しい衝突になりやすいなら最初から見送る傾向があります。' },
}

function topPersonalTraits(detail: ResultDetail) {
  const all = { ...detail.trait_scores, ...detail.discriminator_scores }
  return Object.entries(all)
    .filter(([key, value]) => traitCopy[key] && Number.isFinite(Number(value)))
    .sort((a, b) => Number(b[1]) - Number(a[1]))
    .slice(0, 3)
    .map(([key]) => ({ key, ...traitCopy[key] }))
}

function personalAdvice(detail: ResultDetail) {
  const s = { ...detail.trait_scores, ...detail.discriminator_scores }
  const value = (key: string) => Number(s[key] ?? 0)

  if (value('initiative') > 0 && value('confidence') > 0 && value('threat_sensitivity') <= 0) {
    return '自分から動ける強みはそのままに、途中で前提が崩れたサインだけは意識して拾うと、攻撃性がさらに安定します。'
  }
  if (value('exploit') > 0 && value('adaptability') > 0) {
    return '相手に合わせて変えられるのが武器です。少ないサンプルだけで調整しすぎていないかを途中で確認すると、その強みをより活かせます。'
  }
  if (value('analytical') > 0 && value('action_efficiency') < 0) {
    return '深く考えられるのが武器です。薄い場面まで複雑にしすぎない基準を持つと、思考力を重要な局面へ集中できます。'
  }
  if (value('fun_orientation') > 0 && value('risk_tolerance') > 0) {
    return '面白い展開へ踏み込めるのが持ち味です。「面白い」と「利益がある」を一度だけ切り分ける癖をつけると、楽しさを残したままリークを抑えられます。'
  }
  if (value('attack_momentum') > 0 && value('adaptability') <= 0) {
    return '攻めを継続できるのが武器です。相手やボードの変化で攻撃理由が消えたときだけ、流れをリセットできるとさらに強くなります。'
  }
  if (value('patience') > 0 && value('selective_burst') > 0) {
    return '待てることと勝負所で踏み込めることの両方が武器です。待つこと自体が目的になっていないかだけ確認すると、取り逃しを減らせます。'
  }
  return 'このタイプの持ち味を消して平均型になる必要はありません。自分の強い判断軸を残しながら、外れたときに修正できる余地だけ持っておくのが相性の良い伸ばし方です。'
}

function PlayerTypeDiagnosis() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const clickLock = useRef(false)

  const [screen, setScreen] = useState<'intro' | 'quiz' | 'result'>('intro')
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answerIds, setAnswerIds] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingQuestions, setLoadingQuestions] = useState(true)
  const [error, setError] = useState('')
  const [result, setResult] = useState<SavedResult | null>(null)
  const [detail, setDetail] = useState<ResultDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [isOwner, setIsOwner] = useState<boolean | null>(null)
  const [sharePosting, setSharePosting] = useState(false)
  const [shareMessage, setShareMessage] = useState('')
  const [shareEditorOpen, setShareEditorOpen] = useState(false)
  const [shareText, setShareText] = useState('')

  useEffect(() => {
    void loadQuestions()
  }, [])

  async function loadQuestions() {
    setLoadingQuestions(true)
    setError('')

    const { data, error: rpcError } = await supabase.rpc(
      'get_player_type_v2_questions',
    )

    if (rpcError) {
      setError(`質問を読み込めませんでした：${rpcError.message}`)
      setLoadingQuestions(false)
      return
    }

    const rows = (data ?? []) as QuestionRow[]
    const map = new Map<string, Question>()

    rows.forEach((row) => {
      const existing = map.get(row.question_id)

      if (existing) {
        existing.options.push({
          id: row.option_id,
          order: row.option_order,
          text: row.option_text,
        })
      } else {
        map.set(row.question_id, {
          id: row.question_id,
          key: row.question_key,
          order: row.question_order,
          text: row.question_text,
          options: [
            {
              id: row.option_id,
              order: row.option_order,
              text: row.option_text,
            },
          ],
        })
      }
    })

    const grouped = Array.from(map.values())
      .map((question) => ({
        ...question,
        options: [...question.options].sort((a, b) => a.order - b.order),
      }))
      .sort((a, b) => a.order - b.order)

    if (grouped.length !== QUESTION_COUNT) {
      setError(
        `質問数が正しくありません（${grouped.length}/${QUESTION_COUNT}）`,
      )
      setQuestions([])
    } else {
      setQuestions(grouped)
    }

    setLoadingQuestions(false)
  }

  const currentQuestion = useMemo(
    () => questions[currentIndex] ?? null,
    [questions, currentIndex],
  )

  const visibleNumber = currentIndex + 1
  const progress = Math.min(100, (visibleNumber / QUESTION_COUNT) * 100)

  function startDiagnosis() {
    if (questions.length !== QUESTION_COUNT) return

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

    try {
      await saveResult(nextAnswers)
    } finally {
      setLoading(false)
      clickLock.current = false
    }
  }

  async function saveResult(finalAnswers: string[]) {
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

    if (saveError) {
      // IMPORTANT:
      // The 50th answer is not committed to answerIds until the RPC succeeds.
      // A retry therefore sends exactly 50 answers instead of duplicating Q50.
      setError(`結果を保存できませんでした：${saveError.message}`)
      return
    }

    const saved = (data?.[0] ?? null) as SavedResult | null

    if (!saved) {
      setError('保存された診断結果を取得できませんでした。')
      return
    }

    setAnswerIds(finalAnswers)
    setResult(saved)
    setIsOwner(true)
    setScreen('result')
    void loadResultDetail(saved.result_id)
  }

  async function loadSavedResult(resultId: string) {
    setLoadingQuestions(false)
    setError('')
    setDetail(null)
    setIsOwner(null)
    setDetailLoading(true)

    const { data, error: detailError } = await supabase.rpc(
      'get_player_type_v2_result_detail',
      { p_result_id: resultId },
    )

    if (detailError) {
      setError(`保存済みの診断結果を読み込めませんでした：${detailError.message}`)
      setDetailLoading(false)
      return
    }

    const row = (data?.[0] ?? null) as ResultDetail | null

    if (!row) {
      setError('保存済みの診断結果が見つかりませんでした。')
      setDetailLoading(false)
      return
    }

    // Ownership is checked by a security-definer RPC; never query the protected table directly.
    const { data: ownedResult, error: ownerError } = await supabase.rpc(
      'is_my_player_type_v2_result',
      { p_result_id: resultId },
    )
    if (ownerError) {
      setError(`診断結果の所有者を確認できませんでした：${ownerError.message}`)
      setDetailLoading(false)
      return
    }
    setIsOwner(ownedResult === true)

    setResult({
      result_id: row.result_id,
      result_type_key: row.result_type_key,
      animal_name_ja: row.animal_name_ja,
      catchphrase: row.catchphrase,
      confidence: row.confidence,
      top_margin: row.top_margin,
      core_answer_count: row.core_answer_count,
      is_public: row.is_public,
      completed_at: row.completed_at,
    })
    setDetail(row)
    setScreen('result')
    setDetailLoading(false)
  }

  async function loadResultDetail(resultId: string) {
    setDetailLoading(true)

    const { data, error: detailError } = await supabase.rpc(
      'get_player_type_v2_result_detail',
      { p_result_id: resultId },
    )

    if (detailError) {
      setError(`詳細結果を読み込めませんでした：${detailError.message}`)
      setDetailLoading(false)
      return
    }

    const row = (data?.[0] ?? null) as ResultDetail | null
    setDetail(row)
    setDetailLoading(false)
  }

  function restart() {
    startDiagnosis()
  }

  useEffect(() => {
    const savedResultId = searchParams.get('result')
    if (!savedResultId) return
    void loadSavedResult(savedResultId)
  }, [searchParams])

  useEffect(() => {
    if (screen !== 'result' || !result?.result_id || detail || detailLoading) return
    void loadResultDetail(result.result_id)
  }, [screen, result?.result_id, detail, detailLoading])

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

            <div className="ptd-time">
              <strong>全50問</strong>
              <span>精度を重視した固定50問の診断です</span>
            </div>

            <div className="ptd-note">
              <span>✓ 正解・不正解なし</span>
              <span>✓ 直感で回答</span>
              <span>✓ 全50問</span>
            </div>

            {error && <div className="ptd-error">{error}</div>}

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
    if (!result || isOwner !== true || sharePosting || !shareText.trim() || shareText.length > 500) return
    setSharePosting(true)
    setShareMessage('')
    try {
      const { data: { user }, error: authError } = await supabase.auth.getUser()
      if (authError || !user) throw new Error('ログイン情報を確認できませんでした')
      const { error: postError } = await supabase.from('posts').insert({
        user_id: user.id,
        post_type: 'result',
        result_type: 'player_type',
        result_id: result.result_id,
        content: shareText.trim(),
      })
      if (postError) throw postError
      setShareMessage('タイムラインに投稿しました。')
      setShareEditorOpen(false)
    } catch (e) {
      setShareMessage(`投稿に失敗しました：${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setSharePosting(false)
    }
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
              <>
                {!shareEditorOpen ? (
                  <button className="ptd-primary" type="button" onClick={openShareEditor}>
                    Poker IDのタイムラインに投稿
                  </button>
                ) : (
                  <div style={{ marginTop: 20, padding: 18, border: '1px solid #92733a', borderRadius: 16, background: '#12100c', textAlign: 'left' }}>
                    <div style={{ fontWeight: 800, marginBottom: 12, color: '#e5ca89' }}>投稿にひとこと添える</div>
                    <textarea aria-label="診断結果の投稿文" value={shareText} onChange={(e) => setShareText(e.target.value)} maxLength={500} rows={5} placeholder="めっちゃ当たってる！みんなは何タイプ？" style={{ width: '100%', boxSizing: 'border-box', padding: 12, borderRadius: 10, border: '1px solid #655332', background: '#080808', color: '#fff', fontSize: 15, lineHeight: 1.6, resize: 'vertical' }} />
                    <div style={{ color: '#b9a67c', fontSize: 12, textAlign: 'right', marginTop: 6 }}>{shareText.length}/500</div>
                    <p style={{ fontSize: 12, color: '#b9a67c' }}>診断結果カードは自動で添付されます。</p>
                    <button className="ptd-primary" type="button" disabled={sharePosting || !shareText.trim()} onClick={() => void shareToTimeline()}>
                      {sharePosting ? '投稿中...' : 'この内容で投稿する'}
                    </button>
                    <button className="ptd-secondary" type="button" disabled={sharePosting} onClick={() => setShareEditorOpen(false)}>キャンセル</button>
                  </div>
                )}
                {shareMessage && <p className="ptd-result-hint" role="status">{shareMessage}</p>}
              </>
            )}

            {isOwner === true && (
              <p className="ptd-result-hint">
                診断結果はPoker IDに保存されました。
              </p>
            )}

            <button
              className="ptd-primary"
              onClick={() => isOwner === false ? navigate(-1) : navigate('/profile')}
            >
              {isOwner === false ? 'Poker IDに戻る' : 'Poker IDで見る'}
            </button>

            {isOwner === true && (
              <button className="ptd-secondary" onClick={restart}>
                もう一度診断する
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
        </p>
      </div>
    </main>
  )
}

export default PlayerTypeDiagnosis
