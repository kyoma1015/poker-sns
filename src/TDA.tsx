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

          <Placeholder

            icon="✓"

            title="TDAクイズ"

            description="実戦形式の問題でTDAルールを学べるクイズ機能を追加予定です。"

          />

        )}

        {activeTab === 'updates' && (

          <Placeholder

            icon="↻"

            title="更新情報"

            description="TDAルールの改定内容を、変更前・変更後・実戦への影響まで分かりやすく確認できる機能を追加予定です。"

          />

        )}

      </div>

      <style>{\`

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

      \`}</style>

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