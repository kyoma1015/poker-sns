import { useEffect, useState } from 'react'







import { supabase } from './supabase'







type TdaRule = {







  rule_number: number







  title_ja: string







  summary_ja: string | null







  conclusion_ja: string | null







  explanation_ja: string | null







  keywords_ja: string[]







  examples_ja: string[]







  cautions_ja: string[]







  related_rules: number[]







  title_en: string







  body_en: string







}







type TdaAiRule = {



  rule_number: number



  title_ja: string | null



}







type TdaAiResponse = {



  answer: string



  grounded: boolean



  rules: TdaAiRule[]



}







type TdaQuizOption = {

  id: string

  option_order: number

  option_text: string

}



type TdaQuizQuestion = {

  question_id: string

  question_text: string

  difficulty: string | null

  category: string | null

  options: TdaQuizOption[]

}



type TdaQuizRuleRef = {

  rule_number: number

  title_ja: string | null

}



type TdaQuizAnswer = {

  is_correct: boolean

  correct_option_id: string

  explanation: string | null

  rules: TdaQuizRuleRef[]


  total_answers: number

  correct_answers: number

  correct_rate: number | null

}



type TdaQuizFilters = {

  difficulties: string[]

  categories: string[]

}



type TdaTab = 'search' | 'ai' | 'quiz' | 'updates'







const quickSearches = [







  'ワンチップ',







  'ショーダウン順',







  '50%ルール',







  'アウトオブターン',







  'オールイン',







  'クロック',







  'ミスディール',







  '体臭',







]







function TDA() {







  const [activeTab, setActiveTab] = useState<TdaTab>('search')







  const [query, setQuery] = useState('')







  const [results, setResults] = useState<TdaRule[]>([])







  const [loading, setLoading] = useState(false)







  const [searched, setSearched] = useState(false)







  const [openRule, setOpenRule] = useState<number | null>(null)







  const [errorMessage, setErrorMessage] = useState('')







  const [aiQuestion, setAiQuestion] = useState('')



  const [aiLoading, setAiLoading] = useState(false)



  const [aiError, setAiError] = useState('')



  const [aiResult, setAiResult] = useState<TdaAiResponse | null>(null)



  const [quizFilters, setQuizFilters] = useState<TdaQuizFilters>({

    difficulties: [],

    categories: [],

  })

  const [quizDifficulty, setQuizDifficulty] = useState('')

  const [quizCategory, setQuizCategory] = useState('')

  const [quizQuestions, setQuizQuestions] = useState<TdaQuizQuestion[]>([])

  const [quizIndex, setQuizIndex] = useState(0)

  const [quizLoading, setQuizLoading] = useState(false)

  const [quizError, setQuizError] = useState('')

  const [quizStarted, setQuizStarted] = useState(false)

  const [quizSelectedOption, setQuizSelectedOption] = useState<string | null>(null)

  const [quizAnswer, setQuizAnswer] = useState<TdaQuizAnswer | null>(null)

  const [quizAnswerLoading, setQuizAnswerLoading] = useState(false)

  const [quizScore, setQuizScore] = useState(0)

  const [quizFinished, setQuizFinished] = useState(false)
  const [quizMode, setQuizMode] = useState<'normal' | 'hard' | 'wrong'>('normal')









  const loadQuizFilters = async () => {

    const { data, error } = await supabase.rpc('get_tda_quiz_filters')



    if (error) {

      console.error(error)

      return

    }



    const row = Array.isArray(data) ? data[0] : data

    if (!row) return



    setQuizFilters({

      difficulties: Array.isArray(row.difficulties) ? row.difficulties : [],

      categories: Array.isArray(row.categories) ? row.categories : [],

    })

  }



  const startQuiz = async () => {

    if (quizLoading) return



    setQuizLoading(true)

    setQuizError('')

    setQuizFinished(false)

    setQuizStarted(false)

    setQuizQuestions([])

    setQuizIndex(0)

    setQuizScore(0)

    setQuizSelectedOption(null)

    setQuizAnswer(null)



    const { data, error } = await supabase.rpc('get_tda_quiz_questions', {

      p_difficulty: quizDifficulty || null,

      p_category: quizCategory || null,

      p_limit: 10,

    })



    if (error) {

      console.error(error)

      setQuizError('クイズ問題の取得に失敗しました。')

      setQuizLoading(false)

      return

    }



    const questions = (data ?? []) as TdaQuizQuestion[]

    if (questions.length === 0) {

      setQuizError('この条件で出題できる問題がありません。')

      setQuizLoading(false)

      return

    }



    setQuizQuestions(questions)

    setQuizStarted(true)

    setQuizLoading(false)

  }



  const startHardQuiz = async () => {
    if (quizLoading) return

    setQuizLoading(true)
    setQuizError('')
    setQuizFinished(false)
    setQuizStarted(false)
    setQuizQuestions([])
    setQuizIndex(0)
    setQuizScore(0)
    setQuizSelectedOption(null)
    setQuizAnswer(null)

    const { data, error } = await supabase.rpc('get_tda_quiz_hard_questions', {
      p_limit: 10,
    })

    if (error) {
      console.error(error)
      setQuizError('みんなが間違えた問題の取得に失敗しました。')
      setQuizLoading(false)
      return
    }

    const questions = (data ?? []) as TdaQuizQuestion[]
    if (questions.length === 0) {
      setQuizError('まだ集計中です。10回答以上集まった問題から公開されます。')
      setQuizLoading(false)
      return
    }

    setQuizMode('hard')
    setQuizMode('normal')
    setQuizQuestions(questions)
    setQuizStarted(true)
    setQuizLoading(false)
  }


  const startWrongQuiz = async () => {
    if (quizLoading) return

    setQuizLoading(true)
    setQuizError('')
    setQuizFinished(false)
    setQuizStarted(false)
    setQuizQuestions([])
    setQuizIndex(0)
    setQuizScore(0)
    setQuizSelectedOption(null)
    setQuizAnswer(null)

    const { data, error } = await supabase.rpc('get_my_wrong_tda_quiz_questions', {
      p_limit: 10,
    })

    if (error) {
      console.error(error)
      setQuizError('間違えた問題の取得に失敗しました。')
      setQuizLoading(false)
      return
    }

    const questions = (data ?? []) as TdaQuizQuestion[]

    if (questions.length === 0) {
      setQuizError('現在、復習する問題はありません。')
      setQuizLoading(false)
      return
    }

    setQuizMode('wrong')
    setQuizQuestions(questions)
    setQuizStarted(true)
    setQuizLoading(false)
  }


  const answerQuiz = async (optionId: string) => {
    if (quizAnswer || quizAnswerLoading) return

    const question = quizQuestions[quizIndex]
    if (!question) return

    setQuizSelectedOption(optionId)
    setQuizAnswerLoading(true)
    setQuizError('')

    const { data: submitData, error: submitError } = await supabase.rpc(
      'submit_tda_quiz_answer',
      {
        p_question_id: question.question_id,
        p_selected_option_id: optionId,
      },
    )

    if (submitError) {
      console.error(submitError)
      setQuizSelectedOption(null)
      setQuizError('回答の保存・判定に失敗しました。')
      setQuizAnswerLoading(false)
      return
    }

    const submitRow = Array.isArray(submitData) ? submitData[0] : submitData

    if (!submitRow) {
      setQuizSelectedOption(null)
      setQuizError('回答結果を取得できませんでした。')
      setQuizAnswerLoading(false)
      return
    }

    // 既存RPCから根拠Ruleを取得。正誤判定は保存RPCの結果を採用。
    const { data: detailData, error: detailError } = await supabase.rpc(
      'check_tda_quiz_answer',
      {
        p_question_id: question.question_id,
        p_option_id: optionId,
      },
    )

    if (detailError) {
      console.error(detailError)
    }

    const detailRow = Array.isArray(detailData) ? detailData[0] : detailData
    const totalAnswers = Number(submitRow.total_answers ?? 0)
    const correctAnswers = Number(submitRow.correct_answers ?? 0)

    setQuizAnswer({
      is_correct: Boolean(submitRow.is_correct),
      correct_option_id: String(submitRow.correct_option_id),
      explanation: detailRow?.explanation ?? submitRow.explanation ?? null,
      rules: Array.isArray(detailRow?.rules) ? detailRow.rules : [],
      total_answers: totalAnswers,
      correct_answers: correctAnswers,
      correct_rate:
        totalAnswers >= 10 && submitRow.correct_rate !== null
          ? Number(submitRow.correct_rate)
          : null,
    })

    if (submitRow.is_correct) {
      setQuizScore((score) => score + 1)
    }

    setQuizAnswerLoading(false)
  }


  const nextQuizQuestion = () => {

    if (quizIndex >= quizQuestions.length - 1) {

      setQuizFinished(true)

      return

    }



    setQuizIndex((index) => index + 1)

    setQuizSelectedOption(null)

    setQuizAnswer(null)

    setQuizError('')

  }



  const resetQuiz = () => {

    setQuizStarted(false)

    setQuizFinished(false)

    setQuizQuestions([])

    setQuizIndex(0)

    setQuizScore(0)

    setQuizSelectedOption(null)

    setQuizAnswer(null)

    setQuizError('')

  }



  const searchRules = async (text: string) => {







    const trimmed = text.trim()







    if (!trimmed) {







      setResults([])







      setSearched(false)







      setOpenRule(null)







      setErrorMessage('')







      return







    }







    setLoading(true)







    setSearched(true)







    setOpenRule(null)







    setErrorMessage('')







    const { data, error } = await supabase.rpc('search_tda_rules', {







      search_text: trimmed,







    })







    if (error) {







      console.error(error)







      setResults([])







      setErrorMessage('検索中にエラーが発生しました。')







      setLoading(false)







      return







    }







    setResults((data ?? []) as TdaRule[])







    setLoading(false)







  }







  const askTdaAi = async () => {



    const trimmed = aiQuestion.trim()







    if (!trimmed || aiLoading) return







    setAiLoading(true)



    setAiError('')



    setAiResult(null)







    try {



      const response = await fetch('/api/tda-ai', {



        method: 'POST',



        headers: {



          'Content-Type': 'application/json',



        },



        body: JSON.stringify({ question: trimmed }),



      })







      const data = await response.json()







      if (!response.ok) {



        throw new Error(data?.error || 'AIへの質問に失敗しました。')



      }







      setAiResult({



        answer: data.answer ?? '',



        grounded: Boolean(data.grounded),



        rules: Array.isArray(data.rules) ? data.rules : [],



      })



    } catch (error) {



      console.error(error)



      setAiError(



        error instanceof Error



          ? error.message



          : 'AIへの質問中にエラーが発生しました。',



      )



    } finally {



      setAiLoading(false)



    }



  }







  useEffect(() => {







    const timer = window.setTimeout(() => {







      if (query.trim()) {







        searchRules(query)







      } else {







        setResults([])







        setSearched(false)







        setOpenRule(null)







        setErrorMessage('')







      }







    }, 350)







    return () => window.clearTimeout(timer)







  }, [query])







  useEffect(() => {

    if (activeTab === 'quiz' && quizFilters.difficulties.length === 0 && quizFilters.categories.length === 0) {

      loadQuizFilters()

    }

  }, [activeTab])



  const searchRelatedRule = (ruleNumber: number) => {







    setActiveTab('search')







    setQuery(String(ruleNumber))







    window.scrollTo({







      top: 0,







      behavior: 'smooth',







    })







  }







  return (







    <main className="tda-page">







      <div className="tda-container">







        <header className="tda-header">







          <div>







            <div className="tda-eyebrow">Poker ID</div>







            <h1>TDA</h1>







            <p>







              Poker Tournament Directors Association







              <br />







              2026 Rules Version 1.1







            </p>







          </div>







          <div className="tda-source-badge">







            <span />







            公式ルール準拠







          </div>







        </header>







        <nav className="tda-tabs">







          <button







            type="button"







            className={activeTab === 'search' ? 'active' : ''}







            onClick={() => setActiveTab('search')}







          >







            <strong>⌕</strong>







            <span>ルール検索</span>







          </button>







          <button







            type="button"







            className={activeTab === 'ai' ? 'active' : ''}







            onClick={() => setActiveTab('ai')}







          >







            <strong>✦</strong>







            <span>AIに質問</span>







          </button>







          <button







            type="button"







            className={activeTab === 'quiz' ? 'active' : ''}







            onClick={() => setActiveTab('quiz')}







          >







            <strong>✓</strong>







            <span>TDAクイズ</span>







          </button>







          <button







            type="button"







            className={activeTab === 'updates' ? 'active' : ''}







            onClick={() => setActiveTab('updates')}







          >







            <strong>↻</strong>







            <span>更新情報</span>







          </button>







        </nav>







        {activeTab === 'search' && (







          <section className="tda-search-section">







            <div className="tda-search-intro">







              <h2>ルールを検索</h2>







              <p>







                知りたい状況やキーワードを入力してください。







                <br />







                Poker TDA公式ルールをもとに、実戦で分かりやすい形で表示します。







              </p>







            </div>







            <form







              className="tda-search-box"







              onSubmit={(event) => {







                event.preventDefault()







                searchRules(query)







              }}







            >







              <span className="tda-search-icon">⌕</span>







              <input







                value={query}







                onChange={(event) => setQuery(event.target.value)}







                placeholder="例：ワンチップ、ショーダウン順、体臭..."







              />







              {query && (







                <button







                  type="button"







                  className="tda-clear"







                  onClick={() => setQuery('')}







                  aria-label="検索をクリア"







                >







                  ×







                </button>







              )}







            </form>







            <div className="tda-quick">







              <div className="tda-quick-label">よく検索されるルール</div>







              <div className="tda-quick-list">







                {quickSearches.map((item) => (







                  <button







                    key={item}







                    type="button"







                    onClick={() => setQuery(item)}







                  >







                    {item}







                  </button>







                ))}







              </div>







            </div>







            {loading && (







              <div className="tda-status">







                <div className="tda-spinner" />







                <span>検索しています...</span>







              </div>







            )}







            {!loading && errorMessage && (







              <div className="tda-error">{errorMessage}</div>







            )}







            {!loading &&







              !errorMessage &&







              searched &&







              results.length === 0 && (







                <div className="tda-empty">







                  <div className="tda-empty-icon">?</div>







                  <h3>該当するルールが見つかりませんでした</h3>







                  <p>







                    別の言葉に変えて検索してみてください。







                  </p>







                </div>







              )}







            {!loading && results.length > 0 && (







              <div className="tda-results">







                <div className="tda-result-count">







                  {results.length}件のルールが見つかりました







                </div>







                {results.map((rule) => (







                  <article







                    key={rule.rule_number}







                    className="tda-rule-card"







                  >







                    <div className="tda-rule-top">







                      <div className="tda-rule-number">







                        RULE {rule.rule_number}







                      </div>







                      <div className="tda-verified">







                        <span />







                        VERIFIED







                      </div>







                    </div>







                    <h3>{rule.title_ja}</h3>







                    {rule.conclusion_ja && (







                      <section className="tda-content-box tda-conclusion">







                        <div className="tda-content-label">







                          結論







                        </div>







                        <p>{rule.conclusion_ja}</p>







                      </section>







                    )}







                    {rule.explanation_ja && (







                      <section className="tda-content-box tda-explanation">







                        <div className="tda-content-label">







                          わかりやすい解説







                        </div>







                        <p>{rule.explanation_ja}</p>







                      </section>







                    )}







                    {rule.examples_ja &&







                      rule.examples_ja.length > 0 && (







                        <section className="tda-content-box tda-examples">







                          <div className="tda-content-label">







                            具体例







                          </div>







                          <div className="tda-content-list">







                            {rule.examples_ja.map(







                              (example, index) => (







                                <div







                                  className="tda-list-row"







                                  key={index}







                                >







                                  <span className="tda-example-mark">







                                    例







                                  </span>







                                  <p>{example}</p>







                                </div>







                              ),







                            )}







                          </div>







                        </section>







                      )}







                    {rule.cautions_ja &&







                      rule.cautions_ja.length > 0 && (







                        <section className="tda-content-box tda-cautions">







                          <div className="tda-content-label">







                            注意点







                          </div>







                          <div className="tda-content-list">







                            {rule.cautions_ja.map(







                              (caution, index) => (







                                <div







                                  className="tda-list-row"







                                  key={index}







                                >







                                  <span className="tda-caution-mark">







                                    !







                                  </span>







                                  <p>{caution}</p>







                                </div>







                              ),







                            )}







                          </div>







                        </section>







                      )}







                    {rule.related_rules &&







                      rule.related_rules.length > 0 && (







                        <section className="tda-related">







                          <div className="tda-content-label">







                            関連ルール







                          </div>







                          <div className="tda-related-buttons">







                            {rule.related_rules.map(







                              (relatedRule) => (







                                <button







                                  key={relatedRule}







                                  type="button"







                                  onClick={() =>







                                    searchRelatedRule(







                                      relatedRule,







                                    )







                                  }







                                >







                                  Rule {relatedRule}







                                </button>







                              ),







                            )}







                          </div>







                        </section>







                      )}







                    <button







                      type="button"







                      className="tda-official-toggle"







                      onClick={() =>







                        setOpenRule(







                          openRule === rule.rule_number







                            ? null







                            : rule.rule_number,







                        )







                      }







                    >







                      <span>公式原文を見る</span>







                      <span







                        className={







                          openRule === rule.rule_number







                            ? 'tda-arrow open'







                            : 'tda-arrow'







                        }







                      >







                        ▼







                      </span>







                    </button>







                    {openRule === rule.rule_number && (







                      <section className="tda-official">







                        <div className="tda-official-head">







                          Poker TDA 2026 v1.1







                        </div>







                        <h4>







                          Rule {rule.rule_number}:{' '}







                          {rule.title_en}







                        </h4>







                        <p>{rule.body_en}</p>







                        <div className="tda-official-note">







                          ※ 上記が裁定の基準となる公式英語原文です。







                        </div>







                      </section>







                    )}







                  </article>







                ))}







              </div>







            )}







            {!searched && !query && (







              <div className="tda-guide">







                <div className="tda-guide-icon">TDA</div>







                <div>







                  <h3>実戦で迷ったときにすぐ検索</h3>







                  <p>







                    「ワンチップ」「ショーダウン順」







                    「アウトオブターン」など、







                    普段使っている言葉から探せます。







                  </p>







                </div>







              </div>







            )}







          </section>







        )}







        {activeTab === 'ai' && (



          <section className="tda-ai-section">



            <div className="tda-search-intro">



              <h2>AIに質問</h2>



              <p>



                実戦で起きた状況を文章で入力してください。



                <br />



                Poker IDに登録された検証済みTDAルールを根拠に回答します。



              </p>



            </div>







            <form



              className="tda-ai-form"



              onSubmit={(event) => {



                event.preventDefault()



                askTdaAi()



              }}



            >



              <textarea



                value={aiQuestion}



                onChange={(event) => setAiQuestion(event.target.value)}



                placeholder="例：BTNが1000にベット。SBが1500オールイン。BBがコール。BTNに戻ったとき、BTNはレイズできますか？"



                maxLength={1000}



              />







              <div className="tda-ai-form-bottom">



                <span>{aiQuestion.length}/1000</span>



                <button



                  type="submit"



                  disabled={!aiQuestion.trim() || aiLoading}



                >



                  {aiLoading ? '確認中...' : 'TDA AIに質問'}



                </button>



              </div>



            </form>







            <div className="tda-ai-safety">



              <strong>回答方針</strong>



              <p>



                AIの記憶だけでは裁定しません。Poker IDの検証済みTDAデータから



                根拠を取得できない場合は、推測せず判断できない旨を回答します。



              </p>



            </div>







            {aiLoading && (



              <div className="tda-status">



                <div className="tda-spinner" />



                <span>TDAルールを確認しています...</span>



              </div>



            )}







            {!aiLoading && aiError && (



              <div className="tda-error">{aiError}</div>



            )}







            {!aiLoading && aiResult && (



              <article className="tda-ai-answer">



                <div className="tda-rule-top">



                  <div className="tda-rule-number">TDA AI</div>



                  <div className={aiResult.grounded ? 'tda-verified' : 'tda-ai-unverified'}>



                    <span />



                    {aiResult.grounded ? 'GROUNDED' : '根拠不足'}



                  </div>



                </div>







                <h3>回答</h3>



                <div className="tda-ai-answer-body">{aiResult.answer}</div>







                {aiResult.rules.length > 0 && (



                  <section className="tda-related">



                    <div className="tda-content-label">参照された候補ルール</div>



                    <div className="tda-related-buttons">



                      {aiResult.rules.map((rule) => (



                        <button



                          key={rule.rule_number}



                          type="button"



                          onClick={() => searchRelatedRule(rule.rule_number)}



                        >



                          Rule {rule.rule_number}



                          {rule.title_ja ? ` · ${rule.title_ja}` : ''}



                        </button>



                      ))}



                    </div>



                  </section>



                )}







                <div className="tda-ai-disclaimer">



                  ※ 最終的なトーナメント裁定は、そのイベントのフロア・TDの判断が優先される場合があります。



                </div>



              </article>



            )}



          </section>



        )}







        {activeTab === 'quiz' && (

          <section className="tda-quiz-section">

            <div className="tda-search-intro">

              <h2>TDAクイズ</h2>

              <p>

                実戦形式の問題でTDAルールを確認できます。

                <br />

                回答後に正解と解説、根拠となるルールを表示します。

              </p>

            </div>



            {!quizStarted && !quizFinished && (

              <div className="tda-quiz-setup">

                <div className="tda-quiz-select-grid">

                  <label>

                    <span>難易度</span>

                    <select

                      value={quizDifficulty}

                      onChange={(event) => setQuizDifficulty(event.target.value)}

                    >

                      <option value="">すべて</option>

                      {quizFilters.difficulties.map((difficulty) => (

                        <option key={difficulty} value={difficulty}>

                          {difficulty}

                        </option>

                      ))}

                    </select>

                  </label>



                  <label>

                    <span>カテゴリ</span>

                    <select

                      value={quizCategory}

                      onChange={(event) => setQuizCategory(event.target.value)}

                    >

                      <option value="">すべて</option>

                      {quizFilters.categories.map((category) => (

                        <option key={category} value={category}>

                          {category}

                        </option>

                      ))}

                    </select>

                  </label>

                </div>



                <div className="tda-quiz-info">

                  <strong>10問チャレンジ</strong>

                  <p>公開・検証済みの問題からランダムで10問出題します。</p>

                </div>



                <button

                  type="button"

                  className="tda-quiz-start"

                  onClick={startQuiz}

                  disabled={quizLoading}

                >

                  {quizLoading ? '問題を準備中...' : 'クイズを始める'}

                </button>

              <div className="tda-quiz-hard-card">
                <div>
                  <strong>🔥 みんなが間違えた問題</strong>
                  <p>10回答以上集まった問題から、正答率が低い順に最大10問出題します。</p>
                </div>
                <button type="button" onClick={startHardQuiz} disabled={quizLoading}>
                  挑戦する
                </button>
              </div>

              <div className="tda-quiz-wrong-card">
                <div>
                  <strong>↻ 間違えた問題を復習</strong>
                  <p>あなたの最新回答が不正解になっている問題から、最大10問をランダムに出題します。</p>
                </div>
                <button type="button" onClick={startWrongQuiz} disabled={quizLoading}>
                  復習する
                </button>
              </div>

              </div>

            )}



            {quizLoading && (

              <div className="tda-status">

                <div className="tda-spinner" />

                <span>問題を準備しています...</span>

              </div>

            )}



            {!quizLoading && quizError && (

              <div className="tda-error">{quizError}</div>

            )}



            {quizStarted && !quizFinished && quizQuestions[quizIndex] && (

              <div className="tda-quiz-play">

                <div className="tda-quiz-progress-row">

                  <span>

                    {quizMode === 'hard' ? 'HARD QUESTION' : quizMode === 'wrong' ? 'REVIEW QUESTION' : 'QUESTION'} {quizIndex + 1} / {quizQuestions.length}

                  </span>

                  <span>SCORE {quizScore}</span>

                </div>



                <div className="tda-quiz-progress">

                  <span

                    style={{

                      width: `${((quizIndex + 1) / quizQuestions.length) * 100}%`,

                    }}

                  />

                </div>



                <article className="tda-quiz-card">

                  <div className="tda-quiz-meta">

                    {quizQuestions[quizIndex].difficulty && (

                      <span>{quizQuestions[quizIndex].difficulty}</span>

                    )}

                    {quizQuestions[quizIndex].category && (

                      <span>{quizQuestions[quizIndex].category}</span>

                    )}

                  </div>



                  <h3>{quizQuestions[quizIndex].question_text}</h3>



                  <div className="tda-quiz-options">

                    {quizQuestions[quizIndex].options.map((option) => {

                      const isSelected = quizSelectedOption === option.id

                      const isCorrect = quizAnswer?.correct_option_id === option.id

                      const isWrongSelected = Boolean(

                        quizAnswer && isSelected && !quizAnswer.is_correct,

                      )



                      let optionClass = 'tda-quiz-option'

                      if (quizAnswer && isCorrect) optionClass += ' correct'

                      if (isWrongSelected) optionClass += ' wrong'

                      if (isSelected) optionClass += ' selected'



                      return (

                        <button

                          key={option.id}

                          type="button"

                          className={optionClass}

                          onClick={() => answerQuiz(option.id)}

                          disabled={Boolean(quizAnswer) || quizAnswerLoading}

                        >

                          <span className="tda-quiz-option-letter">

                            {String.fromCharCode(65 + option.option_order - 1)}

                          </span>

                          <span>{option.option_text}</span>

                        </button>

                      )

                    })}

                  </div>



                  {quizAnswerLoading && (

                    <div className="tda-quiz-checking">判定中...</div>

                  )}



                  {quizAnswer && (

                    <div

                      className={

                        quizAnswer.is_correct

                          ? 'tda-quiz-result correct'

                          : 'tda-quiz-result wrong'

                      }

                    >

                      <div className="tda-quiz-result-title">

                        {quizAnswer.is_correct ? '正解' : '不正解'}

                      </div>



                      {quizAnswer.explanation && (

                        <p>{quizAnswer.explanation}</p>

                      )}

                    {quizAnswer.correct_rate !== null && (
                      <div className="tda-quiz-community-stat">
                        <span>みんなの正答率</span>
                        <strong>{quizAnswer.correct_rate.toFixed(1)}%</strong>
                        <small>{quizAnswer.total_answers}回答</small>
                      </div>
                    )}



                      {quizAnswer.rules.length > 0 && (

                        <div className="tda-quiz-rules">

                          <span>根拠ルール</span>

                          <div className="tda-related-buttons">

                            {quizAnswer.rules.map((rule) => (

                              <button

                                key={rule.rule_number}

                                type="button"

                                onClick={() => searchRelatedRule(rule.rule_number)}

                              >

                                Rule {rule.rule_number}

                                {rule.title_ja ? ` · ${rule.title_ja}` : ''}

                              </button>

                            ))}

                          </div>

                        </div>

                      )}

                    </div>

                  )}

                </article>



                {quizAnswer && (

                  <button

                    type="button"

                    className="tda-quiz-next"

                    onClick={nextQuizQuestion}

                  >

                    {quizIndex >= quizQuestions.length - 1

                      ? '結果を見る'

                      : '次の問題へ'}

                  </button>

                )}

              </div>

            )}



            {quizFinished && (

              <div className="tda-quiz-finished">

                <div className="tda-quiz-finished-icon">✓</div>

                <div className="tda-quiz-finished-label">RESULT</div>

                <h3>

                  {quizScore} / {quizQuestions.length}

                </h3>

                <p>

                  {quizScore === quizQuestions.length

                    ? '全問正解です。'

                    : quizScore >= Math.ceil(quizQuestions.length * 0.8)

                      ? 'かなり理解できています。'

                      : quizScore >= Math.ceil(quizQuestions.length * 0.5)

                        ? 'もう少しで安定して正解できそうです。'

                        : '解説とルールを確認して、もう一度挑戦してみましょう。'}

                </p>

                <button type="button" onClick={resetQuiz}>

                  もう一度挑戦する

                </button>

              </div>

            )}

          </section>

        )}







        {activeTab === 'updates' && (







          <Placeholder







            icon="↻"







            title="更新情報"







            description="TDAルールの改定内容を、変更前・変更後・実戦への影響まで分かりやすく確認できる機能を追加予定です。"







          />







        )}







      </div>







      <style>{`







        .tda-page {







          min-height: 100vh;







          background:







            radial-gradient(







              circle at top,







              rgba(33, 71, 50, 0.16),







              transparent 340px







            ),







            \#090b0e;







          color: #f4f5f6;







          padding: 24px 16px 110px;







          box-sizing: border-box;







        }







        .tda-container {







          width: 100%;







          max-width: 760px;







          margin: 0 auto;







        }







        .tda-header {







          display: flex;







          justify-content: space-between;







          align-items: flex-start;







          gap: 16px;







          margin-bottom: 24px;







        }







        .tda-eyebrow {







          color: #6e747d;







          font-size: 10px;







          font-weight: 800;







          letter-spacing: 1.6px;







          text-transform: uppercase;







          margin-bottom: 5px;







        }







        .tda-header h1 {







          margin: 0;







          font-size: 32px;







          line-height: 1;







          letter-spacing: -1px;







        }







        .tda-header p {







          margin: 9px 0 0;







          color: #858b94;







          font-size: 11px;







          line-height: 1.55;







        }







        .tda-source-badge {







          flex-shrink: 0;







          display: flex;







          align-items: center;







          gap: 6px;







          padding: 7px 10px;







          border: 1px solid #27372e;







          border-radius: 999px;







          background: #101713;







          color: #9eb3a5;







          font-size: 10px;







          font-weight: 700;







        }







        .tda-source-badge span,







        .tda-verified span {







          width: 6px;







          height: 6px;







          border-radius: 50%;







          background: #5cc47b;







          box-shadow: 0 0 8px rgba(92, 196, 123, .45);







        }







        .tda-tabs {







          display: grid;







          grid-template-columns: repeat(4, 1fr);







          border: 1px solid #20242a;







          border-radius: 14px;







          background: #101216;







          padding: 4px;







          margin-bottom: 28px;







        }







        .tda-tabs button {







          min-width: 0;







          border: 0;







          border-radius: 10px;







          background: transparent;







          color: #777d86;







          padding: 10px 4px;







          cursor: pointer;







          display: flex;







          flex-direction: column;







          align-items: center;







          gap: 4px;







          font-size: 9px;







          font-weight: 700;







        }







        .tda-tabs button strong {







          font-size: 15px;







          line-height: 1;







        }







        .tda-tabs button.active {







          background: #1a1e23;







          color: #f2f3f4;







        }







        .tda-search-intro h2 {







          margin: 0;







          font-size: 21px;







          letter-spacing: -.4px;







        }







        .tda-search-intro p {







          margin: 8px 0 18px;







          color: #7f858e;







          font-size: 12px;







          line-height: 1.7;







        }







        .tda-search-box {







          height: 52px;







          display: flex;







          align-items: center;







          gap: 10px;







          padding: 0 14px;







          border: 1px solid #292e35;







          border-radius: 14px;







          background: #121519;







        }







        .tda-search-box:focus-within {







          border-color: #3c5947;







          box-shadow: 0 0 0 3px rgba(77, 130, 94, .08);







        }







        .tda-search-icon {







          color: #777e87;







          font-size: 20px;







        }







        .tda-search-box input {







          width: 100%;







          min-width: 0;







          border: 0;







          outline: 0;







          background: transparent;







          color: #f1f2f3;







          font-size: 14px;







        }







        .tda-search-box input::placeholder {







          color: #5f656d;







        }







        .tda-clear {







          width: 28px;







          height: 28px;







          border: 0;







          border-radius: 50%;







          background: #252a30;







          color: #a7acb3;







          cursor: pointer;







        }







        .tda-quick {







          margin-top: 16px;







        }







        .tda-quick-label,







        .tda-content-label {







          color: #838992;







          font-size: 10px;







          font-weight: 800;







          letter-spacing: .5px;







        }







        .tda-quick-list {







          display: flex;







          flex-wrap: wrap;







          gap: 7px;







          margin-top: 8px;







        }







        .tda-quick-list button,







        .tda-related-buttons button {







          border: 1px solid #292e34;







          border-radius: 999px;







          background: #121519;







          color: #b6bbc2;







          padding: 7px 11px;







          font-size: 10px;







          cursor: pointer;







        }







        .tda-quick-list button:hover,







        .tda-related-buttons button:hover {







          background: #1b1f24;







        }







        .tda-status {







          display: flex;







          justify-content: center;







          align-items: center;







          gap: 10px;







          padding: 60px 0;







          color: #8b9199;







          font-size: 12px;







        }







        .tda-spinner {







          width: 17px;







          height: 17px;







          border: 2px solid #2b3036;







          border-top-color: #7db38d;







          border-radius: 50%;







          animation: tda-spin .8s linear infinite;







        }







        @keyframes tda-spin {







          to {







            transform: rotate(360deg);







          }







        }







        .tda-error,







        .tda-empty {







          margin-top: 26px;







          padding: 36px 20px;







          border: 1px solid #252a30;







          border-radius: 14px;







          background: #111418;







          text-align: center;







        }







        .tda-error {







          color: #e08b8b;







          font-size: 12px;







        }







        .tda-empty-icon {







          width: 38px;







          height: 38px;







          margin: 0 auto 12px;







          display: flex;







          align-items: center;







          justify-content: center;







          border: 1px solid #30353c;







          border-radius: 50%;







          color: #777d85;







          font-weight: 800;







        }







        .tda-empty h3 {







          margin: 0;







          font-size: 14px;







        }







        .tda-empty p {







          margin: 7px 0 0;







          color: #777d85;







          font-size: 11px;







        }







        .tda-results {







          margin-top: 28px;







        }







        .tda-result-count {







          color: #747a83;







          font-size: 10px;







          margin-bottom: 9px;







        }







        .tda-rule-card {







          border: 1px solid #24292f;







          border-radius: 16px;







          background: #101317;







          padding: 17px;







          margin-bottom: 12px;







          box-shadow: 0 10px 35px rgba(0, 0, 0, .12);







        }







        .tda-rule-top {







          display: flex;







          justify-content: space-between;







          align-items: center;







          gap: 10px;







        }







        .tda-rule-number {







          color: #75a985;







          font-size: 10px;







          font-weight: 900;







          letter-spacing: .7px;







        }







        .tda-verified {







          display: flex;







          align-items: center;







          gap: 5px;







          color: #6f9d7c;







          font-size: 8px;







          font-weight: 800;







        }







        .tda-verified span {







          width: 5px;







          height: 5px;







        }







        .tda-rule-card > h3 {







          margin: 8px 0 15px;







          color: #f1f2f3;







          font-size: 18px;







          line-height: 1.45;







          letter-spacing: -.3px;







        }







        .tda-content-box {







          margin-top: 10px;







          padding: 13px;







          border-radius: 12px;







        }







        .tda-content-box p {







          margin: 7px 0 0;







          font-size: 12px;







          line-height: 1.8;







        }







        .tda-conclusion {







          border: 1px solid #2d4736;







          background: #111a14;







        }







        .tda-conclusion .tda-content-label {







          color: #75a985;







        }







        .tda-conclusion > p {







          color: #edf6ef;







          font-size: 13px;







          font-weight: 700;







        }







        .tda-explanation {







          background: #181b20;







        }







        .tda-explanation > p {







          color: #d3d6da;







        }







        .tda-examples {







          border: 1px solid #252a30;







          background: #14171b;







        }







        .tda-cautions {







          border: 1px solid #393321;







          background: #191711;







        }







        .tda-cautions .tda-content-label {







          color: #c5ad67;







        }







        .tda-content-list {







          margin-top: 8px;







          display: flex;







          flex-direction: column;







          gap: 9px;







        }







        .tda-list-row {







          display: flex;







          align-items: flex-start;







          gap: 9px;







        }







        .tda-list-row p {







          margin: 0;







          color: #d2d5d9;







          font-size: 12px;







          line-height: 1.7;







        }







        .tda-example-mark,







        .tda-caution-mark {







          flex-shrink: 0;







          min-width: 23px;







          height: 20px;







          border-radius: 6px;







          display: flex;







          align-items: center;







          justify-content: center;







          background: #262b31;







          color: #b9bec5;







          font-size: 9px;







          font-weight: 900;







          margin-top: 1px;







        }







        .tda-caution-mark {







          background: #312b1c;







          color: #e0c66f;







        }







        .tda-related {







          margin-top: 14px;







        }







        .tda-related-buttons {







          display: flex;







          flex-wrap: wrap;







          gap: 7px;







          margin-top: 8px;







        }







        .tda-official-toggle {







          width: 100%;







          display: flex;







          align-items: center;







          justify-content: space-between;







          border: 0;







          border-top: 1px solid #24292f;







          background: transparent;







          color: #969ca4;







          padding: 14px 1px 0;







          margin-top: 16px;







          cursor: pointer;







          font-size: 10px;







          font-weight: 700;







        }







        .tda-arrow {







          font-size: 8px;







          transition: transform .2s ease;







        }







        .tda-arrow.open {







          transform: rotate(180deg);







        }







        .tda-official {







          margin-top: 13px;







          padding: 14px;







          border: 1px solid #252a30;







          border-radius: 12px;







          background: #0b0d10;







        }







        .tda-official-head {







          color: #6f9d7c;







          font-size: 9px;







          font-weight: 800;







          margin-bottom: 8px;







        }







        .tda-official h4 {







          margin: 0 0 8px;







          color: #d7dadd;







          font-size: 12px;







          line-height: 1.5;







        }







        .tda-official p {







          margin: 0;







          color: #969ca4;







          font-size: 10px;







          line-height: 1.75;







          white-space: pre-wrap;







        }







        .tda-official-note {







          margin-top: 12px;







          padding-top: 10px;







          border-top: 1px solid #20242a;







          color: #646a72;







          font-size: 9px;







        }







        .tda-guide {







          margin-top: 30px;







          display: flex;







          align-items: center;







          gap: 14px;







          padding: 18px;







          border: 1px solid #20252b;







          border-radius: 14px;







          background: #101317;







        }







        .tda-guide-icon {







          flex-shrink: 0;







          width: 48px;







          height: 48px;







          border-radius: 13px;







          display: flex;







          align-items: center;







          justify-content: center;







          border: 1px solid #2b4133;







          background: #111a14;







          color: #79a989;







          font-size: 11px;







          font-weight: 900;







        }







        .tda-guide h3 {







          margin: 0;







          font-size: 13px;







        }







        .tda-guide p {







          margin: 5px 0 0;







          color: #7d838b;







          font-size: 10px;







          line-height: 1.65;







        }







        .tda-ai-form {



        margin-top: 4px;



        padding: 14px;



        border: 1px solid #292e35;



        border-radius: 14px;



        background: #121519;



      }







      .tda-ai-form textarea {



        width: 100%;



        min-height: 150px;



        resize: vertical;



        box-sizing: border-box;



        border: 0;



        outline: 0;



        background: transparent;



        color: #f1f2f3;



        font: inherit;



        font-size: 14px;



        line-height: 1.75;



      }







      .tda-ai-form textarea::placeholder { color: #5f656d; }







      .tda-ai-form-bottom {



        display: flex;



        align-items: center;



        justify-content: space-between;



        gap: 12px;



        padding-top: 12px;



        margin-top: 8px;



        border-top: 1px solid #24292f;



      }







      .tda-ai-form-bottom > span {



        color: #666d76;



        font-size: 9px;



      }







      .tda-ai-form-bottom button {



        border: 1px solid #34513e;



        border-radius: 10px;



        background: #17301f;



        color: #dff3e5;



        padding: 9px 13px;



        font-size: 11px;



        font-weight: 800;



        cursor: pointer;



      }







      .tda-ai-form-bottom button:disabled {



        opacity: .45;



        cursor: not-allowed;



      }







      .tda-ai-safety {



        margin-top: 12px;



        padding: 12px 13px;



        border: 1px solid #252a30;



        border-radius: 12px;



        background: #101317;



      }







      .tda-ai-safety strong {



        color: #75a985;



        font-size: 10px;



      }







      .tda-ai-safety p {



        margin: 5px 0 0;



        color: #7f858e;



        font-size: 10px;



        line-height: 1.7;



      }







      .tda-ai-answer {



        margin-top: 22px;



        padding: 17px;



        border: 1px solid #294032;



        border-radius: 16px;



        background: #101317;



        box-shadow: 0 10px 35px rgba(0, 0, 0, .12);



      }







      .tda-ai-answer > h3 {



        margin: 8px 0 12px;



        font-size: 18px;



      }







      .tda-ai-answer-body {



        padding: 14px;



        border: 1px solid #2d4736;



        border-radius: 12px;



        background: #111a14;



        color: #edf6ef;



        font-size: 13px;



        line-height: 1.9;



        white-space: pre-wrap;



      }







      .tda-ai-unverified {



        display: flex;



        align-items: center;



        gap: 5px;



        color: #c5ad67;



        font-size: 8px;



        font-weight: 800;



      }







      .tda-ai-unverified span {



        width: 5px;



        height: 5px;



        border-radius: 50%;



        background: #c5ad67;



      }







      .tda-ai-disclaimer {



        margin-top: 15px;



        padding-top: 11px;



        border-top: 1px solid #24292f;



        color: #646a72;



        font-size: 9px;



        line-height: 1.7;



      }







      .tda-quiz-setup,

      .tda-quiz-card,

      .tda-quiz-finished {

        border: 1px solid #24292f;

        border-radius: 16px;

        background: #101317;

        padding: 17px;

      }



      .tda-quiz-select-grid {

        display: grid;

        grid-template-columns: repeat(2, minmax(0, 1fr));

        gap: 10px;

      }



      .tda-quiz-select-grid label {

        display: flex;

        flex-direction: column;

        gap: 7px;

      }



      .tda-quiz-select-grid label > span {

        color: #838992;

        font-size: 10px;

        font-weight: 800;

      }



      .tda-quiz-select-grid select {

        width: 100%;

        height: 42px;

        border: 1px solid #292e35;

        border-radius: 10px;

        outline: 0;

        background: #15191e;

        color: #e7e9eb;

        padding: 0 10px;

        font-size: 12px;

      }



      .tda-quiz-info {

        margin-top: 14px;

        padding: 13px;

        border: 1px solid #2d4736;

        border-radius: 12px;

        background: #111a14;

      }



      .tda-quiz-info strong {

        color: #dff3e5;

        font-size: 12px;

      }



      .tda-quiz-info p {

        margin: 5px 0 0;

        color: #829388;

        font-size: 10px;

        line-height: 1.6;

      }



      .tda-quiz-start,

      .tda-quiz-next,

      .tda-quiz-finished button {

        width: 100%;

        border: 1px solid #34513e;

        border-radius: 11px;

        background: #17301f;

        color: #dff3e5;

        padding: 12px 14px;

        font-size: 12px;

        font-weight: 800;

        cursor: pointer;

      }



      .tda-quiz-start {

        margin-top: 14px;

      }



      .tda-quiz-start:disabled,

      .tda-quiz-option:disabled {

        cursor: default;

      }



      .tda-quiz-progress-row {

        display: flex;

        justify-content: space-between;

        align-items: center;

        color: #7c838b;

        font-size: 9px;

        font-weight: 800;

        letter-spacing: .5px;

      }



      .tda-quiz-progress {

        height: 4px;

        margin: 8px 0 14px;

        border-radius: 999px;

        overflow: hidden;

        background: #20252b;

      }



      .tda-quiz-progress > span {

        display: block;

        height: 100%;

        border-radius: inherit;

        background: #6fa17e;

        transition: width .2s ease;

      }



      .tda-quiz-meta {

        display: flex;

        flex-wrap: wrap;

        gap: 6px;

      }



      .tda-quiz-meta > span {

        border: 1px solid #2a3036;

        border-radius: 999px;

        background: #15191e;

        color: #8d949c;

        padding: 5px 8px;

        font-size: 9px;

        font-weight: 700;

      }



      .tda-quiz-card > h3 {

        margin: 14px 0 16px;

        color: #f1f2f3;

        font-size: 17px;

        line-height: 1.7;

      }



      .tda-quiz-options {

        display: flex;

        flex-direction: column;

        gap: 9px;

      }



      .tda-quiz-option {

        width: 100%;

        display: flex;

        align-items: flex-start;

        gap: 10px;

        border: 1px solid #292e35;

        border-radius: 12px;

        background: #15191e;

        color: #d8dbdf;

        padding: 12px;

        text-align: left;

        font-size: 12px;

        line-height: 1.6;

        cursor: pointer;

      }



      .tda-quiz-option:not(:disabled):hover {

        background: #1a1f24;

        border-color: #3a424b;

      }



      .tda-quiz-option-letter {

        flex-shrink: 0;

        width: 24px;

        height: 24px;

        display: flex;

        align-items: center;

        justify-content: center;

        border-radius: 7px;

        background: #242a30;

        color: #aeb4bb;

        font-size: 10px;

        font-weight: 900;

      }



      .tda-quiz-option.correct {

        border-color: #3f7250;

        background: #122017;

        color: #e3f5e8;

      }



      .tda-quiz-option.correct .tda-quiz-option-letter {

        background: #21472d;

        color: #bfe7c9;

      }



      .tda-quiz-option.wrong {

        border-color: #714040;

        background: #211414;

        color: #f1d9d9;

      }



      .tda-quiz-option.wrong .tda-quiz-option-letter {

        background: #4b2727;

        color: #efbcbc;

      }



      .tda-quiz-checking {

        margin-top: 12px;

        color: #7d848c;

        font-size: 10px;

        text-align: center;

      }



      .tda-quiz-result {

        margin-top: 15px;

        padding: 13px;

        border-radius: 12px;

      }



      .tda-quiz-result.correct {

        border: 1px solid #2d4736;

        background: #111a14;

      }



      .tda-quiz-result.wrong {

        border: 1px solid #493030;

        background: #1a1212;

      }



      .tda-quiz-result-title {

        font-size: 13px;

        font-weight: 900;

      }



      .tda-quiz-result.correct .tda-quiz-result-title { color: #78b389; }

      .tda-quiz-result.wrong .tda-quiz-result-title { color: #d98989; }



      .tda-quiz-result > p {

        margin: 8px 0 0;

        color: #cfd3d7;

        font-size: 11px;

        line-height: 1.8;

        white-space: pre-wrap;

      }



      .tda-quiz-hard-card {
        margin-top: 14px;
        padding: 16px;
        border: 1px solid #3a3026;
        border-radius: 14px;
        background: rgba(122, 78, 35, .08);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
      }

      .tda-quiz-hard-card strong {
        display: block;
        font-size: 13px;
        margin-bottom: 5px;
      }

      .tda-quiz-hard-card p {
        margin: 0;
        color: #858b94;
        font-size: 10px;
        line-height: 1.6;
      }

      .tda-quiz-hard-card button {
        flex-shrink: 0;
        border: 1px solid #4b3d2d;
        border-radius: 10px;
        background: #211a13;
        color: #e8d6bd;
        padding: 9px 13px;
        font-size: 11px;
        font-weight: 800;
        cursor: pointer;
      }

      .tda-quiz-wrong-card {
        margin-top: 10px;
        padding: 16px;
        border: 1px solid #30363d;
        border-radius: 14px;
        background: rgba(255, 255, 255, .025);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
      }

      .tda-quiz-wrong-card strong {
        display: block;
        font-size: 13px;
        margin-bottom: 5px;
      }

      .tda-quiz-wrong-card p {
        margin: 0;
        color: #858b94;
        font-size: 10px;
        line-height: 1.6;
      }

      .tda-quiz-wrong-card button {
        flex-shrink: 0;
        border: 1px solid #3b424b;
        border-radius: 10px;
        background: #191d22;
        color: #e4e7eb;
        padding: 9px 13px;
        font-size: 11px;
        font-weight: 800;
        cursor: pointer;
      }

      .tda-quiz-community-stat {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-top: 14px;
        padding: 11px 12px;
        border: 1px solid #30363d;
        border-radius: 10px;
        background: rgba(255, 255, 255, .025);
      }

      .tda-quiz-community-stat span {
        color: #8d949d;
        font-size: 11px;
        font-weight: 700;
      }

      .tda-quiz-community-stat strong {
        color: #f1f3f5;
        font-size: 17px;
      }

      .tda-quiz-community-stat small {
        margin-left: auto;
        color: #686f78;
        font-size: 10px;
      }

      .tda-quiz-rules {

        margin-top: 12px;

        padding-top: 10px;

        border-top: 1px solid rgba(255, 255, 255, .07);

      }



      .tda-quiz-rules > span {

        color: #7e858d;

        font-size: 9px;

        font-weight: 800;

      }



      .tda-quiz-next {

        margin-top: 12px;

      }



      .tda-quiz-finished {

        text-align: center;

        padding: 32px 20px;

      }



      .tda-quiz-finished-icon {

        width: 46px;

        height: 46px;

        margin: 0 auto 12px;

        display: flex;

        align-items: center;

        justify-content: center;

        border: 1px solid #34513e;

        border-radius: 50%;

        background: #111a14;

        color: #75a985;

        font-size: 20px;

        font-weight: 900;

      }



      .tda-quiz-finished-label {

        color: #6f9d7c;

        font-size: 9px;

        font-weight: 900;

        letter-spacing: 1px;

      }



      .tda-quiz-finished h3 {

        margin: 6px 0;

        font-size: 34px;

        letter-spacing: -1px;

      }



      .tda-quiz-finished p {

        margin: 0 0 18px;

        color: #838a92;

        font-size: 11px;

        line-height: 1.7;

      }



      @media (max-width: 520px) {

        .tda-quiz-select-grid {

          grid-template-columns: 1fr;

        }

      }



      .tda-placeholder {







          min-height: 350px;







          display: flex;







          flex-direction: column;







          align-items: center;







          justify-content: center;







          text-align: center;







          padding: 30px;







          border: 1px solid #20252b;







          border-radius: 16px;







          background: #101317;







        }







        .tda-placeholder-icon {







          width: 54px;







          height: 54px;







          display: flex;







          align-items: center;







          justify-content: center;







          border-radius: 16px;







          background: #171b20;







          color: #8aaa94;







          font-size: 22px;







          margin-bottom: 14px;







        }







        .tda-placeholder h2 {







          margin: 0;







          font-size: 19px;







        }







        .tda-placeholder p {







          max-width: 420px;







          margin: 9px 0 0;







          color: #7d838b;







          font-size: 11px;







          line-height: 1.8;







        }







        @media (max-width: 520px) {







          .tda-page {







            padding: 18px 12px 105px;







          }







          .tda-header {







            align-items: center;







          }







          .tda-header h1 {







            font-size: 28px;







          }







          .tda-source-badge {







            padding: 6px 8px;







            font-size: 8px;







          }







          .tda-tabs {







            margin-bottom: 23px;







          }







          .tda-tabs button {







            padding: 9px 2px;







            font-size: 8px;







          }







          .tda-tabs button strong {







            font-size: 14px;







          }







          .tda-rule-card {







            padding: 15px;







          }







          .tda-rule-card > h3 {







            font-size: 16px;







          }







        }







      `}</style>







    </main>







  )







}







function Placeholder({







  icon,







  title,







  description,







}: {







  icon: string







  title: string







  description: string







}) {







  return (







    <section className="tda-placeholder">







      <div className="tda-placeholder-icon">{icon}</div>







      <h2>{title}</h2>







      <p>{description}</p>







    </section>







  )







}







export default TDA