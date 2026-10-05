import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { supabase } from './supabase'

function StyleRating() {
  const { id } = useParams()
  const navigate = useNavigate()
  const areaRef = useRef<HTMLDivElement>(null)

  const [aggression, setAggression] = useState(50)
  const [looseness, setLooseness] = useState(50)
  const [hasSelected, setHasSelected] = useState(false)
  const [hasPlayedTogether, setHasPlayedTogether] = useState(false)
  const [message, setMessage] = useState('')
  const [playerName, setPlayerName] = useState('')

  useEffect(() => {
    const loadData = async () => {
      if (!id) return

      const { data: profile } = await supabase
        .from('profiles')
        .select('display_name')
        .eq('id', id)
        .maybeSingle()

      if (profile) {
        setPlayerName(profile.display_name)
      }

      const {
        data: { user },
      } = await supabase.auth.getUser()

      if (!user) return

      const { data: rating } = await supabase
        .from('player_style_ratings')
        .select('aggression, looseness')
        .eq('rater_id', user.id)
        .eq('rated_user_id', id)
        .maybeSingle()

      if (rating) {
        setAggression(rating.aggression)
        setLooseness(rating.looseness)
        setHasSelected(true)
        setHasPlayedTogether(true)
      }
    }

    loadData()
  }, [id])

  const handleSelect = (
    event: React.MouseEvent<HTMLDivElement>
  ) => {
    const area = areaRef.current
    if (!area) return

    const rect = area.getBoundingClientRect()

    const x = Math.max(
      0,
      Math.min(event.clientX - rect.left, rect.width)
    )

    const y = Math.max(
      0,
      Math.min(event.clientY - rect.top, rect.height)
    )

    setAggression(
      Math.round((x / rect.width) * 100)
    )

    setLooseness(
      Math.round((y / rect.height) * 100)
    )

    setHasSelected(true)
    setMessage('')
  }

  const handleSave = async () => {
    if (!hasPlayedTogether) {
      setMessage(
        '実際にプレイしたことがある場合のみ評価できます。'
      )
      return
    }

    if (!id || !hasSelected) {
      setMessage(
        'グラフ上でプレイスタイルを選択してください。'
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

    if (user.id === id) {
      setMessage(
        '自分自身を評価することはできません。'
      )
      return
    }

    setMessage('保存中...')

    const { error } = await supabase
      .from('player_style_ratings')
      .upsert(
        {
          rater_id: user.id,
          rated_user_id: id,
          aggression,
          looseness,
        },
        {
          onConflict: 'rater_id,rated_user_id',
        }
      )

    if (error) {
      console.error(error)
      setMessage(`エラー：${error.message}`)
      return
    }

    setMessage('評価を保存しました！')

    setTimeout(() => {
      navigate(`/player/${id}`)
    }, 800)
  }

  const quadrantStyle: React.CSSProperties = {
    position: 'absolute',
    width: '50%',
    height: '50%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    boxSizing: 'border-box',
    pointerEvents: 'none',
    padding: '8px',
  }

  const descriptionStyle: React.CSSProperties = {
    marginTop: '10px',
    padding: '7px 8px',
    border: '1px solid #3d3d3d',
    borderRadius: '8px',
    background: 'rgba(255,255,255,0.035)',
    color: '#aaa',
    fontSize: '10px',
    lineHeight: '1.45',
    width: '90%',
    boxSizing: 'border-box',
  }

  return (
    <main
      className="app"
      style={{
        alignItems: 'flex-start',
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: '500px',
          paddingTop: '32px',
          paddingBottom: '40px',
        }}
      >
        <h1
          style={{
            fontSize: '30px',
            margin: '0 0 22px',
          }}
        >
          プレイスタイルを評価
        </h1>

        {/* 説明 */}
        <div
          style={{
            border: '1px solid #3c3c3c',
            borderRadius: '14px',
            padding: '18px',
            textAlign: 'left',
            background: '#151515',
            display: 'flex',
            gap: '16px',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              width: '48px',
              height: '58px',
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg
              width="42"
              height="52"
              viewBox="0 0 42 52"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                d="M7 4L34 28H22L29 43L21 47L14 32L7 40V4Z"
                fill="#151515"
                stroke="white"
                strokeWidth="3"
                strokeLinejoin="round"
              />
              <path
                d="M5 13L1 9"
                stroke="white"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <path
                d="M13 6V1"
                stroke="white"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <path
                d="M4 21H1"
                stroke="white"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>

          <div
            style={{
              flex: 1,
              minWidth: 0,
            }}
          >
            <div
              style={{
                fontSize: '16px',
                lineHeight: '1.65',
                fontWeight: 'bold',
              }}
            >
              <div>
                あなたが感じる{' '}
                {playerName
                  ? `${playerName}さん`
                  : 'このプレイヤー'}
                の
              </div>
              <div>プレイスタイルの位置を</div>
              <div>クリックしてください。</div>
            </div>

            <div
              style={{
                color: '#999',
                fontSize: '12px',
                lineHeight: '1.7',
                marginTop: '10px',
              }}
            >
              一緒にプレイした経験をもとに、
              スターティングハンドの広さと
              ベット・レイズの頻度から総合的に
              評価してください。
            </div>
          </div>
        </div>

        {/* グラフ全体 */}
        <div style={{ marginTop: '34px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '72px 1fr',
              gridTemplateRows: 'auto auto',
              columnGap: '8px',
            }}
          >
            {/* ==================== */}
            {/* 縦軸：グラフと同じ行だけを使う */}
            {/* ==================== */}
            <div
              style={{
                gridColumn: '1',
                gridRow: '1',
                position: 'relative',
                minWidth: 0,
              }}
            >
              {/* TIGHT
                  上端がグラフ上辺 */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  textAlign: 'center',
                  fontWeight: 'bold',
                  fontSize: '12px',
                  lineHeight: '1.25',
                }}
              >
                TIGHT
                <div
                  style={{
                    fontSize: '10px',
                    marginTop: '1px',
                  }}
                >
                  （狭い）
                </div>
              </div>

              {/* 上側矢印 */}
              <div
                style={{
                  position: 'absolute',
                  top: '48px',
                  bottom: 'calc(50% + 28px)',
                  left: '50%',
                  width: '1.5px',
                  background: '#ddd',
                  transform: 'translateX(-50%)',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 0,
                    height: 0,
                    borderLeft: '5px solid transparent',
                    borderRight: '5px solid transparent',
                    borderBottom: '9px solid #ddd',
                  }}
                />
              </div>

              {/* 縦軸中央 */}
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '72px',
                  textAlign: 'center',
                  fontSize: '10px',
                  lineHeight: '1.45',
                  fontWeight: 'bold',
                  background: '#0d0d0d',
                  padding: '4px 0',
                  zIndex: 2,
                }}
              >
                スターティング
                <br />
                ハンドの広さ
              </div>

              {/* 下側矢印 */}
              <div
                style={{
                  position: 'absolute',
                  top: 'calc(50% + 28px)',
                  bottom: '48px',
                  left: '50%',
                  width: '1.5px',
                  background: '#ddd',
                  transform: 'translateX(-50%)',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: '50%',
                    transform: 'translate(-50%, 50%)',
                    width: 0,
                    height: 0,
                    borderLeft: '5px solid transparent',
                    borderRight: '5px solid transparent',
                    borderTop: '9px solid #ddd',
                  }}
                />
              </div>

              {/* LOOSE
                  下端がグラフ下辺 */}
              <div
                style={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  textAlign: 'center',
                  fontWeight: 'bold',
                  fontSize: '12px',
                  lineHeight: '1.25',
                }}
              >
                LOOSE
                <div
                  style={{
                    fontSize: '10px',
                    marginTop: '1px',
                  }}
                >
                  （広い）
                </div>
              </div>
            </div>

            {/* ==================== */}
            {/* グラフ */}
            {/* ==================== */}
            <div
              style={{
                gridColumn: '2',
                gridRow: '1',
              }}
            >
              <div
                ref={areaRef}
                onClick={handleSelect}
                style={{
                  position: 'relative',
                  width: '100%',
                  aspectRatio: '1 / 1',
                  border: '2px solid #666',
                  boxSizing: 'border-box',
                  background: '#151515',
                  cursor: 'crosshair',
                  overflow: 'hidden',
                  userSelect: 'none',
                }}
              >
                <div
                  style={{
                    ...quadrantStyle,
                    left: 0,
                    top: 0,
                  }}
                >
                  <div
                    style={{
                      color: '#4ba3ff',
                      fontSize: '31px',
                      fontWeight: 'bold',
                    }}
                  >
                    TP
                  </div>
                  <div
                    style={{
                      marginTop: '4px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                    }}
                  >
                    タイト・パッシブ
                  </div>
                  <div style={descriptionStyle}>
                    参加ハンドが狭く
                    <br />
                    ベット・レイズが少ない
                  </div>
                </div>

                <div
                  style={{
                    ...quadrantStyle,
                    right: 0,
                    top: 0,
                  }}
                >
                  <div
                    style={{
                      color: '#45dc83',
                      fontSize: '31px',
                      fontWeight: 'bold',
                    }}
                  >
                    TAG
                  </div>
                  <div
                    style={{
                      marginTop: '4px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                    }}
                  >
                    タイト・アグレッシブ
                  </div>
                  <div style={descriptionStyle}>
                    参加ハンドが狭く
                    <br />
                    ベット・レイズが多い
                  </div>
                </div>

                <div
                  style={{
                    ...quadrantStyle,
                    left: 0,
                    bottom: 0,
                  }}
                >
                  <div
                    style={{
                      color: '#ffd83d',
                      fontSize: '31px',
                      fontWeight: 'bold',
                    }}
                  >
                    LP
                  </div>
                  <div
                    style={{
                      marginTop: '4px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                    }}
                  >
                    ルース・パッシブ
                  </div>
                  <div style={descriptionStyle}>
                    参加ハンドが広く
                    <br />
                    ベット・レイズが少ない
                  </div>
                </div>

                <div
                  style={{
                    ...quadrantStyle,
                    right: 0,
                    bottom: 0,
                  }}
                >
                  <div
                    style={{
                      color: '#ff5757',
                      fontSize: '31px',
                      fontWeight: 'bold',
                    }}
                  >
                    LAG
                  </div>
                  <div
                    style={{
                      marginTop: '4px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                    }}
                  >
                    ルース・アグレッシブ
                  </div>
                  <div style={descriptionStyle}>
                    参加ハンドが広く
                    <br />
                    ベット・レイズが多い
                  </div>
                </div>

                <div
                  style={{
                    position: 'absolute',
                    left: '50%',
                    top: 0,
                    bottom: 0,
                    width: '1px',
                    background: '#666',
                    pointerEvents: 'none',
                  }}
                />

                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: 0,
                    right: 0,
                    height: '1px',
                    background: '#666',
                    pointerEvents: 'none',
                  }}
                />

                {hasSelected && (
                  <div
                    style={{
                      position: 'absolute',
                      left: `${aggression}%`,
                      top: `${looseness}%`,
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      background: '#fff',
                      border: '3px solid #111',
                      boxShadow:
                        '0 0 0 2px rgba(255,255,255,0.9)',
                      transform: 'translate(-50%, -50%)',
                      boxSizing: 'border-box',
                      pointerEvents: 'none',
                      zIndex: 10,
                    }}
                  />
                )}
              </div>
            </div>

            {/* ==================== */}
            {/* 横軸：前回の配置を維持 */}
            {/* ==================== */}
            <div
              style={{
                gridColumn: '2',
                gridRow: '2',
                position: 'relative',
                height: '64px',
                marginTop: '8px',
              }}
            >
              {/* PASSIVE */}
              <div
                style={{
                  position: 'absolute',
                  left: 0,
                  top: '4px',
                  width: '68px',
                  textAlign: 'left',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  lineHeight: '1.25',
                }}
              >
                PASSIVE
                <div
                  style={{
                    fontSize: '10px',
                    marginTop: '1px',
                    textAlign: 'center',
                  }}
                >
                  （低い）
                </div>
              </div>

              {/* 左矢印 */}
              <div
                style={{
                  position: 'absolute',
                  left: '74px',
                  right: '61%',
                  top: '12px',
                  height: '1.5px',
                  background: '#ddd',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 0,
                    height: 0,
                    borderTop: '5px solid transparent',
                    borderBottom: '5px solid transparent',
                    borderRight: '9px solid #ddd',
                  }}
                />
              </div>

              {/* 中央 */}
              <div
                style={{
                  position: 'absolute',
                  left: '50%',
                  top: '12px',
                  transform: 'translate(-50%, -50%)',
                  background: '#0d0d0d',
                  padding: '0 7px',
                  whiteSpace: 'nowrap',
                  fontSize: '10px',
                  fontWeight: 'bold',
                  zIndex: 2,
                }}
              >
                ベット・レイズの頻度
              </div>

              {/* 右矢印 */}
              <div
                style={{
                  position: 'absolute',
                  left: '61%',
                  right: '92px',
                  top: '12px',
                  height: '1.5px',
                  background: '#ddd',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: '50%',
                    transform: 'translate(50%, -50%)',
                    width: 0,
                    height: 0,
                    borderTop: '5px solid transparent',
                    borderBottom: '5px solid transparent',
                    borderLeft: '9px solid #ddd',
                  }}
                />
              </div>

              {/* AGGRESSIVE */}
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '4px',
                  width: '86px',
                  textAlign: 'right',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  lineHeight: '1.25',
                }}
              >
                AGGRESSIVE
                <div
                  style={{
                    fontSize: '10px',
                    marginTop: '1px',
                    textAlign: 'center',
                  }}
                >
                  （高い）
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* プレイ経験 */}
        <label
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
            marginTop: '10px',
            padding: '16px',
            border: '1px solid #3c3c3c',
            borderRadius: '14px',
            background: '#151515',
            textAlign: 'left',
            cursor: 'pointer',
          }}
        >
          <input
            type="checkbox"
            checked={hasPlayedTogether}
            onChange={(event) =>
              setHasPlayedTogether(event.target.checked)
            }
            style={{
              width: '22px',
              height: '22px',
              flexShrink: 0,
              marginTop: '2px',
            }}
          />

          <div>
            <div
              style={{
                fontSize: '14px',
                fontWeight: 'bold',
                lineHeight: '1.5',
              }}
            >
              このプレイヤーと実際に
              プレイしたことがあります
            </div>

            <div
              style={{
                color: '#888',
                fontSize: '11px',
                lineHeight: '1.6',
                marginTop: '6px',
              }}
            >
              実際に同じゲームでプレイした
              経験をもとに評価してください。
            </div>
          </div>
        </label>

        {/* ボタン */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1.3fr 1fr',
            gap: '10px',
            marginTop: '18px',
          }}
        >
          <button
            onClick={handleSave}
            style={{
              margin: 0,
              background: '#2388ff',
              color: '#fff',
              border: '1px solid #2388ff',
              fontSize: '15px',
            }}
          >
            この位置で評価する
          </button>

          <button
            onClick={() =>
              navigate(`/player/${id}`)
            }
            style={{
              margin: 0,
              background: '#292929',
              color: '#fff',
              border: '1px solid #555',
              fontSize: '15px',
            }}
          >
            戻る
          </button>
        </div>

        {message && (
          <p
            style={{
              marginTop: '18px',
              fontSize: '13px',
            }}
          >
            {message}
          </p>
        )}
      </div>
    </main>
  )
}

export default StyleRating