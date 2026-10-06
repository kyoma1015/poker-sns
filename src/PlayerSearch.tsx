import { useState } from 'react'

import { useNavigate } from 'react-router-dom'

import { supabase } from './supabase'



type Player = {
  id: string
  display_name: string
  poker_id: string
  avatar_url: string | null
  main_game: string | null
  main_play: string | null
  play_environment: string | null
  activity_areas: string[] | null
  poker_frequency: string | null
}



function PlayerSearch() {

  const navigate = useNavigate()



  const [keyword, setKeyword] = useState('')

  const [players, setPlayers] = useState<Player[]>([])

  const [hasSearched, setHasSearched] = useState(false)

  const [isSearching, setIsSearching] = useState(false)

  const [message, setMessage] = useState('')
  const [mainGame, setMainGame] = useState('')
  const [mainPlay, setMainPlay] = useState('')
  const [playEnvironment, setPlayEnvironment] = useState('')
  const [activityArea, setActivityArea] = useState('')




  const handleSearch = async () => {
    const trimmedKeyword = keyword.trim()
    const hasFilter = mainGame || mainPlay || playEnvironment || activityArea

    if (!trimmedKeyword && !hasFilter) {
      setPlayers([])
      setHasSearched(false)
      setMessage('')
      return
    }

    setIsSearching(true)
    setMessage('')

    let query = supabase
      .from('profiles')
      .select(
        'id, display_name, poker_id, avatar_url, main_game, main_play, play_environment, activity_areas, poker_frequency'
      )

    if (trimmedKeyword) {
      query = query.or(
        `poker_id.ilike.%${trimmedKeyword}%,display_name.ilike.%${trimmedKeyword}%`
      )
    }

    if (mainGame) query = query.eq('main_game', mainGame)
    if (mainPlay) query = query.eq('main_play', mainPlay)
    if (playEnvironment) query = query.eq('play_environment', playEnvironment)
    if (activityArea) query = query.contains('activity_areas', [activityArea])

    const { data, error } = await query.limit(50)

    setIsSearching(false)
    setHasSearched(true)

    if (error) {
      console.error(error)
      setPlayers([])
      setMessage('検索に失敗しました。もう一度お試しください。')
      return
    }

    setPlayers(data || [])
  }

  const handleKeyDown = (

    e: React.KeyboardEvent<HTMLInputElement>

  ) => {

    if (e.key === 'Enter') {

      handleSearch()

    }

  }



  const prefectures = [
    '北海道', '青森', '岩手', '宮城', '秋田', '山形', '福島',
    '茨城', '栃木', '群馬', '埼玉', '千葉', '東京', '神奈川',
    '新潟', '富山', '石川', '福井', '山梨', '長野',
    '岐阜', '静岡', '愛知', '三重',
    '滋賀', '京都', '大阪', '兵庫', '奈良', '和歌山',
    '鳥取', '島根', '岡山', '広島', '山口',
    '徳島', '香川', '愛媛', '高知',
    '福岡', '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島', '沖縄',
    '海外',
  ]

  const mainPlayLabels: Record<string, string> = {
    tournament: 'トーナメント中心',
    ring: 'リング中心',
    cash: 'キャッシュ中心',
    balanced: 'バランス',
  }

  const environmentLabels: Record<string, string> = {
    live: 'ライブ中心',
    online: 'オンライン中心',
    both: 'ライブ・オンライン',
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

            padding: '15px 20px 13px',

            background:

              'rgba(0, 0, 0, 0.94)',

            borderBottom:

              '1px solid #242424',

            backdropFilter: 'blur(14px)',

            WebkitBackdropFilter:

              'blur(14px)',

          }}

        >

          <div

            style={{

              fontSize: '20px',

              fontWeight: 800,

              letterSpacing: '-0.4px',

            }}

          >

            検索

          </div>



          {/* 検索ボックス */}

          <div

            style={{

              display: 'flex',

              alignItems: 'center',

              gap: '9px',

              marginTop: '13px',

            }}

          >

            <div

              style={{

                flex: 1,

                position: 'relative',

              }}

            >

              <span

                style={{

                  position: 'absolute',

                  left: '14px',

                  top: '50%',

                  transform:

                    'translateY(-50%)',

                  color: '#777',

                  fontSize: '18px',

                  pointerEvents: 'none',

                }}

              >

                ⌕

              </span>



              <input

                type="text"

                placeholder="Poker ID または表示名"

                value={keyword}

                onChange={(e) =>

                  setKeyword(e.target.value)

                }

                onKeyDown={handleKeyDown}

                style={{

                  height: '44px',

                  padding:

                    '0 42px 0 42px',

                  background: '#151515',

                  border:

                    '1px solid #292929',

                  borderRadius: '999px',

                  fontSize: '14px',

                }}

              />



              {keyword && (

                <button

                  onClick={() => {

                    setKeyword('')

                    setPlayers([])

                    setHasSearched(false)

                    setMessage('')

                  }}

                  aria-label="検索文字を消す"

                  style={{

                    position: 'absolute',

                    right: '12px',

                    top: '50%',

                    transform:

                      'translateY(-50%)',

                    width: '24px',

                    height: '24px',

                    padding: 0,

                    display: 'flex',

                    alignItems: 'center',

                    justifyContent: 'center',

                    background: '#333',

                    color: '#aaa',

                    borderRadius: '50%',

                    fontSize: '13px',

                  }}

                >

                  ×

                </button>

              )}

            </div>



            <button

              onClick={handleSearch}

              disabled={isSearching || (!keyword.trim() && !mainGame && !mainPlay && !playEnvironment && !activityArea)}

              style={{

                width: 'auto',

                padding: '10px 15px',

                flexShrink: 0,

                background: '#fff',

                color: '#000',

                borderRadius: '999px',

                fontSize: '13px',

                fontWeight: 800,

              }}

            >

              {isSearching

                ? '検索中'

                : '検索'}

            </button>

          </div>

        </header>

      {/* 絞り込み */}
      <section style={{ padding: '14px 0 4px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '8px' }}>
          <select value={mainGame} onChange={(e) => setMainGame(e.target.value)} style={{ background: '#151515', border: '1px solid #292929', borderRadius: '12px', padding: '11px', color: '#fff', fontSize: '12px' }}>
            <option value="">メインゲーム：すべて</option>
            <option value="NLH">NLH</option>
            <option value="PLO">PLO</option>
            <option value="MIX">MIX</option>
            <option value="その他">その他</option>
          </select>

          <select value={mainPlay} onChange={(e) => setMainPlay(e.target.value)} style={{ background: '#151515', border: '1px solid #292929', borderRadius: '12px', padding: '11px', color: '#fff', fontSize: '12px' }}>
            <option value="">メインプレイ：すべて</option>
            <option value="tournament">トーナメント中心</option>
            <option value="ring">リング中心</option>
            <option value="cash">キャッシュ中心</option>
            <option value="balanced">バランス</option>
          </select>

          <select value={playEnvironment} onChange={(e) => setPlayEnvironment(e.target.value)} style={{ background: '#151515', border: '1px solid #292929', borderRadius: '12px', padding: '11px', color: '#fff', fontSize: '12px' }}>
            <option value="">プレイ環境：すべて</option>
            <option value="live">ライブ中心</option>
            <option value="online">オンライン中心</option>
            <option value="both">ライブ・オンライン</option>
          </select>

          <select value={activityArea} onChange={(e) => setActivityArea(e.target.value)} style={{ background: '#151515', border: '1px solid #292929', borderRadius: '12px', padding: '11px', color: '#fff', fontSize: '12px' }}>
            <option value="">活動エリア：すべて</option>
            {prefectures.map((area) => <option key={area} value={area}>{area}</option>)}
          </select>
        </div>

        {(mainGame || mainPlay || playEnvironment || activityArea) && (
          <button
            onClick={() => {
              setMainGame('')
              setMainPlay('')
              setPlayEnvironment('')
              setActivityArea('')
              setPlayers([])
              setHasSearched(false)
              setMessage('')
            }}
            style={{ marginTop: '9px', width: 'auto', padding: '7px 11px', background: 'transparent', border: '1px solid #292929', borderRadius: '999px', color: '#888', fontSize: '11px' }}
          >
            絞り込みをクリア
          </button>
        )}
      </section>




        {/* エラー */}

        {message && (

          <div

            style={{

              margin: '15px 0',

              padding: '12px 14px',

              background: '#111',

              border:

                '1px solid #292929',

              borderRadius: '12px',

              color: '#aaa',

              fontSize: '13px',

            }}

          >

            {message}

          </div>

        )}



        {/* 検索前 */}

        {!hasSearched &&

          !isSearching &&

          !message && (

            <div

              style={{

                padding: '75px 25px',

                textAlign: 'center',

              }}

            >

              <div

                style={{

                  width: '62px',

                  height: '62px',

                  margin: '0 auto 17px',

                  display: 'flex',

                  alignItems: 'center',

                  justifyContent: 'center',

                  background: '#111',

                  border:

                    '1px solid #292929',

                  borderRadius: '50%',

                  fontSize: '28px',

                }}

              >

                ⌕

              </div>



              <div

                style={{

                  fontSize: '17px',

                  fontWeight: 800,

                }}

              >

                プレイヤーを探す

              </div>



              <div

                style={{

                  marginTop: '8px',

                  color: '#666',

                  fontSize: '13px',

                  lineHeight: 1.6,

                }}

              >

                Poker ID または表示名から

                <br />

                プレイヤーを検索できます

              </div>

            </div>

          )}



        {/* 検索中 */}

        {isSearching && (

          <div

            style={{

              padding: '65px 20px',

              color: '#777',

              fontSize: '13px',

              textAlign: 'center',

            }}

          >

            プレイヤーを検索中...

          </div>

        )}



        {/* 0件 */}

        {hasSearched &&

          !isSearching &&

          !message &&

          players.length === 0 && (

            <div

              style={{

                padding: '70px 25px',

                textAlign: 'center',

              }}

            >

              <div

                style={{

                  fontSize: '32px',

                  marginBottom: '14px',

                }}

              >

                ♠

              </div>



              <div

                style={{

                  fontSize: '15px',

                  fontWeight: 700,

                }}

              >

                プレイヤーが見つかりません

              </div>



              <div

                style={{

                  marginTop: '7px',

                  color: '#666',

                  fontSize: '12px',

                }}

              >

                Poker ID や表示名を確認して

                もう一度検索してください

              </div>

            </div>

          )}



        {/* 検索結果 */}

        {hasSearched &&

          !isSearching &&

          players.length > 0 && (

            <section

              style={{

                margin: '0 -20px',

              }}

            >

              <div

                style={{

                  padding: '17px 20px 10px',

                  color: '#777',

                  fontSize: '12px',

                  fontWeight: 600,

                }}

              >

                検索結果

                <span

                  style={{

                    marginLeft: '7px',

                    color: '#555',

                  }}

                >

                  {players.length}人

                </span>

              </div>



              {players.map(

                (player) => (

                  <button

                    key={player.id}

                    onClick={() =>

                      navigate(

                        `/player/${player.id}`

                      )

                    }

                    style={{

                      width: '100%',

                      padding: '13px 20px',

                      display: 'flex',

                      alignItems: 'center',

                      gap: '12px',

                      background:

                        'transparent',

                      color: '#fff',

                      borderRadius: 0,

                      borderTop:

                        '1px solid #1d1d1d',

                      textAlign: 'left',

                    }}

                  >

                    {player.avatar_url ? (

                      <img

                        src={

                          player.avatar_url

                        }

                        alt={`${player.display_name}のプロフィール画像`}

                        style={{

                          width: '50px',

                          height: '50px',

                          borderRadius:

                            '50%',

                          objectFit:

                            'cover',

                          border:

                            '1px solid #333',

                          flexShrink: 0,

                        }}

                      />

                    ) : (

                      <div

                        style={{

                          width: '50px',

                          height: '50px',

                          borderRadius:

                            '50%',

                          background:

                            '#171717',

                          border:

                            '1px solid #333',

                          display: 'flex',

                          alignItems:

                            'center',

                          justifyContent:

                            'center',

                          fontSize:

                            '21px',

                          flexShrink: 0,

                        }}

                      >

                        ♠

                      </div>

                    )}



                    <div

                      style={{

                        minWidth: 0,

                        flex: 1,

                      }}

                    >

                      <div

                        style={{

                          overflow:

                            'hidden',

                          textOverflow:

                            'ellipsis',

                          whiteSpace:

                            'nowrap',

                          fontSize:

                            '15px',

                          fontWeight: 700,

                        }}

                      >

                        {player.display_name}

                      </div>



                      <div

                        style={{

                          marginTop: '3px',

                          overflow:

                            'hidden',

                          textOverflow:

                            'ellipsis',

                          whiteSpace:

                            'nowrap',

                          color: '#777',

                          fontSize:

                            '13px',

                        }}

                      >

                        @{player.poker_id}

                      </div>

                    {(player.main_game || player.main_play || player.play_environment || (player.activity_areas && player.activity_areas.length > 0)) && (
                      <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {player.main_game && <span style={{ color: '#aaa', fontSize: '10px' }}>{player.main_game}</span>}
                        {player.main_play && <span style={{ color: '#777', fontSize: '10px' }}>・{mainPlayLabels[player.main_play]}</span>}
                        {player.play_environment && <span style={{ color: '#777', fontSize: '10px' }}>・{environmentLabels[player.play_environment]}</span>}
                        {player.activity_areas && player.activity_areas.length > 0 && (
                          <span style={{ color: '#777', fontSize: '10px' }}>・{player.activity_areas.slice(0, 2).join('・')}</span>
                        )}
                      </div>
                    )}

                    </div>



                    <span

                      style={{

                        flexShrink: 0,

                        color: '#555',

                        fontSize: '23px',

                        fontWeight: 300,

                      }}

                    >

                      ›

                    </span>

                  </button>

                )

              )}

            </section>

          )}

      </div>

    </main>

  )

}



export default PlayerSearch