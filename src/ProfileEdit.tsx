import { useEffect, useState } from 'react'



import { useNavigate } from 'react-router-dom'



import { supabase } from './supabase'



type PokerVenue = {



  id: string



  name: string



}







function ProfileEdit() {



  const navigate = useNavigate()



  const [pokerId, setPokerId] = useState('')



  const [displayName, setDisplayName] = useState('')



  const [bio, setBio] = useState('')



  const [pokerYears, setPokerYears] = useState('')



  const [mainGame, setMainGame] = useState('')
  const [playableGames, setPlayableGames] = useState<string[]>([])
  const [gameSearch, setGameSearch] = useState('')
  const [customGame, setCustomGame] = useState('')




  const [mainPlay, setMainPlay] = useState('')



  const [playEnvironment, setPlayEnvironment] = useState('')



  const [activityAreas, setActivityAreas] = useState<string[]>([])



  const [pokerFrequency, setPokerFrequency] = useState('')



  const [avatarUrl, setAvatarUrl] = useState('')



  const [avatarFile, setAvatarFile] = useState<File | null>(null)



  const [avatarPreview, setAvatarPreview] = useState('')



  const [message, setMessage] = useState('')



  const [isSaving, setIsSaving] = useState(false)



  const [venues, setVenues] = useState<PokerVenue[]>([])



  const [selectedVenueIds, setSelectedVenueIds] = useState<string[]>([])



  const [venueSearch, setVenueSearch] = useState('')



  const [isAddingVenue, setIsAddingVenue] = useState(false)



  useEffect(() => {



    const loadProfile = async () => {



      const {



        data: { user },



      } = await supabase.auth.getUser()



      if (!user) {



        navigate('/login')



        return



      }



      const { data, error } = await supabase



        .from('profiles')



        .select('*')



        .eq('id', user.id)



        .maybeSingle()



      if (error) {



        console.error(error)



        return



      }



      if (!data) {



        return



      }



      setPokerId(data.poker_id || '')



      setDisplayName(data.display_name || '')



      setBio(data.bio || '')



      setPokerYears(data.poker_years?.toString() || '')



      setMainGame(data.main_game || '')
    setPlayableGames(Array.isArray(data.playable_games) ? data.playable_games : [])




      setMainPlay(data.main_play || '')



      setPlayEnvironment(data.play_environment || '')



      setActivityAreas(Array.isArray(data.activity_areas) ? data.activity_areas : [])



      setPokerFrequency(data.poker_frequency || '')



      setAvatarUrl(data.avatar_url || '')







      const { data: venueData, error: venueError } = await supabase



        .from('poker_venues')



        .select('id, name')



        .order('name', { ascending: true })







      if (venueError) {



        console.error('店舗一覧取得エラー:', venueError)



      } else {



        setVenues(venueData || [])



      }







      const { data: favoriteData, error: favoriteError } = await supabase



        .from('user_favorite_venues')



        .select('venue_id')



        .eq('user_id', user.id)







      if (favoriteError) {



        console.error('よく行く店舗取得エラー:', favoriteError)



      } else {



        setSelectedVenueIds((favoriteData || []).map((item) => item.venue_id))



      }



    }



    loadProfile()



  }, [navigate])



  useEffect(() => {



    return () => {



      if (avatarPreview) {



        URL.revokeObjectURL(avatarPreview)



      }



    }



  }, [avatarPreview])



  const handleAvatarChange = (



    event: React.ChangeEvent<HTMLInputElement>



  ) => {



    const file = event.target.files?.[0]



    if (!file) {



      return



    }



    const allowedTypes = [



      'image/jpeg',



      'image/png',



      'image/webp',



    ]



    if (!allowedTypes.includes(file.type)) {



      setMessage(



        'プロフィール画像はJPG・PNG・WebPを選択してください。'



      )



      event.target.value = ''



      return



    }



    if (file.size > 5 * 1024 * 1024) {



      setMessage(



        'プロフィール画像は5MB以下の画像を選択してください。'



      )



      event.target.value = ''



      return



    }



    if (avatarPreview) {



      URL.revokeObjectURL(avatarPreview)



    }



    const previewUrl = URL.createObjectURL(file)



    setAvatarFile(file)



    setAvatarPreview(previewUrl)



    setMessage('')



  }



  const getAvatarStoragePath = (



    publicUrl: string



  ) => {



    if (!publicUrl) {



      return null



    }



    const marker =



      '/storage/v1/object/public/avatars/'



    const markerIndex = publicUrl.indexOf(marker)



    if (markerIndex === -1) {



      return null



    }



    const encodedPath = publicUrl.slice(



      markerIndex + marker.length



    )



    try {



      return decodeURIComponent(encodedPath)



    } catch {



      return encodedPath



    }



  }



  const toggleVenue = (venueId: string) => {



    setSelectedVenueIds((current) =>



      current.includes(venueId)



        ? current.filter((id) => id !== venueId)



        : [...current, venueId]



    )



  }







  const handleAddVenue = async () => {



    const name = venueSearch.trim()



    if (!name || isAddingVenue) return



    const existingVenue = venues.find(



      (venue) => venue.name.trim().toLowerCase() === name.toLowerCase()



    )



    if (existingVenue) {



      if (!selectedVenueIds.includes(existingVenue.id)) {



        setSelectedVenueIds((current) => [...current, existingVenue.id])



      }



      setVenueSearch('')



      return



    }







    setIsAddingVenue(true)



    const { data, error } = await supabase



      .from('poker_venues')



      .insert({ name })



      .select('id, name')



      .single()







    if (error) {



      console.error('店舗追加エラー:', error)



      setMessage(`店舗を追加できませんでした：${error.message}`)



      setIsAddingVenue(false)



      return



    }







    setVenues((current) =>



      [...current, data].sort((a, b) => a.name.localeCompare(b.name, 'ja'))



    )



    setSelectedVenueIds((current) => [...current, data.id])



    setVenueSearch('')



    setMessage('')



    setIsAddingVenue(false)



  }







  const handleSave = async () => {



    if (isSaving) {



      return



    }



    setIsSaving(true)



    setMessage('保存中...')



    const {



      data: { user },



    } = await supabase.auth.getUser()



    if (!user) {



      setMessage(



        'ログイン情報が確認できませんでした。'



      )



      setIsSaving(false)



      return



    }



    const oldAvatarUrl = avatarUrl



    let savedAvatarUrl = avatarUrl



    let newAvatarPath: string | null = null



    if (avatarFile) {



      const extension =



        avatarFile.name



          .split('.')



          .pop()



          ?.toLowerCase() || 'jpg'



      const filePath =



        `${user.id}/avatar-${Date.now()}.${extension}`



      const { error: uploadError } =



        await supabase.storage



          .from('avatars')



          .upload(filePath, avatarFile, {



            contentType: avatarFile.type,



            cacheControl: '3600',



          })



      if (uploadError) {



        console.error(



          '画像アップロードエラー:',



          uploadError



        )



        setMessage(



          `画像のアップロードに失敗しました：${uploadError.message}`



        )



        setIsSaving(false)



        return



      }



      newAvatarPath = filePath



      const { data: publicUrlData } =



        supabase.storage



          .from('avatars')



          .getPublicUrl(filePath)



      savedAvatarUrl =



        publicUrlData.publicUrl



    }



    const { error } = await supabase



      .from('profiles')



      .upsert({



        id: user.id,



        poker_id: pokerId,



        display_name: displayName,



        bio: bio || null,



        poker_years: pokerYears



          ? Number(pokerYears)



          : null,



        main_game: mainGame || null,
      playable_games: playableGames,




        main_play: mainPlay || null,



        play_environment: playEnvironment || null,



        activity_areas: activityAreas,



        poker_frequency: pokerFrequency || null,



        avatar_url: savedAvatarUrl || null,



      })



    if (error) {



      console.error(error)



      if (newAvatarPath) {



        const { error: cleanupError } =



          await supabase.storage



            .from('avatars')



            .remove([newAvatarPath])



        if (cleanupError) {



          console.error(



            '新しい画像の後片付けエラー:',



            cleanupError



          )



        }



      }



      setMessage(`エラー：${error.message}`)



      setIsSaving(false)



      return



    }



    const { error: deleteFavoriteError } = await supabase



      .from('user_favorite_venues')



      .delete()



      .eq('user_id', user.id)







    if (deleteFavoriteError) {



      console.error('よく行く店舗更新エラー:', deleteFavoriteError)



      setMessage(`よく行く店舗を保存できませんでした：${deleteFavoriteError.message}`)



      setIsSaving(false)



      return



    }







    if (selectedVenueIds.length > 0) {



      const { error: insertFavoriteError } = await supabase



        .from('user_favorite_venues')



        .insert(



          selectedVenueIds.map((venueId) => ({



            user_id: user.id,



            venue_id: venueId,



          }))



        )







      if (insertFavoriteError) {



        console.error('よく行く店舗保存エラー:', insertFavoriteError)



        setMessage(`よく行く店舗を保存できませんでした：${insertFavoriteError.message}`)



        setIsSaving(false)



        return



      }



    }







    if (



      avatarFile &&



      oldAvatarUrl &&



      oldAvatarUrl !== savedAvatarUrl



    ) {



      const oldAvatarPath =



        getAvatarStoragePath(oldAvatarUrl)



      if (



        oldAvatarPath &&



        oldAvatarPath.startsWith(



          `${user.id}/`



        )



      ) {



        const { error: deleteError } =



          await supabase.storage



            .from('avatars')



            .remove([oldAvatarPath])



        if (deleteError) {



          console.error(



            '古いプロフィール画像の削除エラー:',



            deleteError



          )



        }



      }



    }



    setAvatarUrl(savedAvatarUrl)



    setAvatarFile(null)



    if (avatarPreview) {



      URL.revokeObjectURL(avatarPreview)



      setAvatarPreview('')



    }



    setMessage(



      'プロフィールを保存しました！'



    )



    setIsSaving(false)



    setTimeout(() => {



      navigate('/home')



    }, 1000)



  }



  const displayedAvatar =



    avatarPreview || avatarUrl







  const selectedVenues = selectedVenueIds



    .map((venueId) => venues.find((venue) => venue.id === venueId))



    .filter((venue): venue is PokerVenue => Boolean(venue))







  const normalizedVenueSearch = venueSearch.trim().toLowerCase()



  const filteredVenues = venues.filter((venue) => {



    if (!normalizedVenueSearch) return true



    return venue.name.toLowerCase().includes(normalizedVenueSearch)



  })



  const exactVenueExists = venues.some(



    (venue) => venue.name.trim().toLowerCase() === normalizedVenueSearch



  )



  const gameCategories = [
    {
      name: "Hold'em / Flop",
      games: [
        'No-Limit Hold’em (NLH)',
        'Fixed-Limit Hold’em (FLH)',
        'Pot-Limit Hold’em (PLH)',
        'Short Deck / 6+ Hold’em',
        'Pineapple',
        'Crazy Pineapple',
        'Lazy Pineapple',
        'Irish Poker',
        'Double Board Hold’em',
        'Super Hold’em',
        'Tahoe',
        'Watermelon',
      ],
    },
    {
      name: 'Omaha',
      games: [
        'Pot-Limit Omaha 4 (PLO4)',
        'Pot-Limit Omaha 5 (PLO5)',
        'Pot-Limit Omaha 6 (PLO6)',
        'Omaha Hi-Lo 8 or Better (O8)',
        'Pot-Limit Omaha Hi-Lo (PLO8)',
        'Big O',
        'Big O Hi',
        'Courchevel',
        'Courchevel Hi-Lo',
        'Double Board Omaha',
        'Omaha 5 Hi-Lo',
        'Omaha 6 Hi-Lo',
      ],
    },
    {
      name: 'Stud',
      games: [
        'Seven Card Stud',
        'Seven Card Stud Hi-Lo 8 or Better',
        'Razz',
        'Five Card Stud',
        'Six Card Stud',
        'Stud Hi-Lo Regular',
        'Super Stud',
        'Razzdugi',
        'London Lowball',
        'Mexican Stud',
      ],
    },
    {
      name: 'Draw / Lowball',
      games: [
        '2-7 Single Draw',
        '2-7 Triple Draw',
        'A-5 Single Draw',
        'A-5 Triple Draw',
        '5 Card Draw',
        'Badugi',
        'Badacey',
        'Badeucy',
        'Badugi Hi',
        '2-7 Badugi',
        'Ace-to-Five Lowball',
        'Kansas City Lowball',
        'Jacks or Better Draw',
        'California Lowball',
      ],
    },
    {
      name: 'Dramaha / Drawmaha',
      games: [
        'Dramaha',
        'Dramaha Hi',
        'Dramaha 0',
        'Dramaha 49',
        'Dramaha 2-7',
        'Dramaha A-5',
        'Dramaha Badugi',
        'Dramaha High-Dugi',
        'Double Board Dramaha',
        'Drawmaha',
      ],
    },
    {
      name: 'Mixed / Split Pot',
      games: [
        'HORSE',
        'HOSE',
        'SHOE',
        '8-Game Mix',
        '9-Game Mix',
        '10-Game Mix',
        '12-Game Mix',
        "Dealer's Choice",
        'Mixed Omaha',
        'Mixed Hold’em',
        'Mixed Triple Draw',
        'Archie',
        'Super Razzdugi',
        'Scrotum',
      ],
    },
    {
      name: 'Chinese / Open Face',
      games: [
        'Chinese Poker',
        'Open-Face Chinese (OFC)',
        'Pineapple OFC',
        'Progressive Pineapple OFC',
        'Fantasyland OFC',
        '2-7 Pineapple OFC',
        'OFC Hi-Lo',
      ],
    },
    {
      name: 'その他',
      games: [
        'Sviten Special',
        'Sökö / Scandinavian Stud',
        'Manila',
        'Cincinnati',
        'Chicago',
        'Baseball',
        'Follow the Queen',
        'Anaconda',
        'Countdown',
        'Guts',
        'Indian Poker',
        'Blind Man’s Bluff',
        'Three Card Poker',
      ],
    },
  ]

  const allPresetGames = gameCategories.flatMap((category) => category.games)

  const togglePlayableGame = (game: string) => {
    setPlayableGames((current) =>
      current.includes(game)
        ? current.filter((item) => item !== game)
        : [...current, game]
    )
  }

  const toggleGameCategory = (games: string[]) => {
    setPlayableGames((current) => {
      const allSelected = games.every((game) => current.includes(game))

      if (allSelected) {
        return current.filter((game) => !games.includes(game))
      }

      return Array.from(new Set([...current, ...games]))
    })
  }

  const addCustomGame = () => {
    const game = customGame.trim()
    if (!game || playableGames.includes(game)) return
    setPlayableGames((current) => [...current, game])
    setCustomGame('')
  }

  const normalizedGameSearch = gameSearch.trim().toLowerCase()
  const filteredGameCategories = gameCategories
    .map((category) => ({
      ...category,
      games: category.games.filter((game) =>
        game.toLowerCase().includes(normalizedGameSearch)
      ),
    }))
    .filter((category) => category.games.length > 0)

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



  const addActivityArea = (area: string) => {

    if (!area || activityAreas.includes(area)) return

    setActivityAreas((current) => [...current, area])

  }



  const removeActivityArea = (area: string) => {

    setActivityAreas((current) => current.filter((item) => item !== area))

  }



  return (



    <main className="app">



      <div className="card">



        <h1 className="logo">Poker ID</h1>



        <p className="subtitle">



          プロフィール設定



        </p>



        <div className="buttons">



          <div



            style={{



              display: 'flex',



              flexDirection: 'column',



              alignItems: 'center',



              gap: '12px',



              marginBottom: '10px',



            }}



          >



            {displayedAvatar ? (



              <img



                src={displayedAvatar}



                alt="プロフィール画像"



                style={{



                  width: '110px',



                  height: '110px',



                  borderRadius: '50%',



                  objectFit: 'cover',



                  border: '2px solid #444',



                }}



              />



            ) : (



              <div



                style={{



                  width: '110px',



                  height: '110px',



                  borderRadius: '50%',



                  background: '#292929',



                  border: '2px solid #444',



                  display: 'flex',



                  alignItems: 'center',



                  justifyContent: 'center',



                  fontSize: '40px',



                }}



              >



                ♠



              </div>



            )}



            <label



              style={{



                cursor: 'pointer',



                padding: '10px 16px',



                borderRadius: '8px',



                background: '#292929',



                border: '1px solid #444',



                fontWeight: 'bold',



              }}



            >



              プロフィール画像を選択



              <input



                type="file"



                accept="image/jpeg,image/png,image/webp"



                onChange={



                  handleAvatarChange



                }



                style={{



                  display: 'none',



                }}



              />



            </label>



            <span



              style={{



                color: '#888',



                fontSize: '12px',



              }}



            >



              JPG・PNG・WebP / 最大5MB



            </span>



          </div>



          <input



            type="text"



            placeholder="Poker ID"



            value={pokerId}



            onChange={(e) =>



              setPokerId(e.target.value)



            }



          />



          <input



            type="text"



            placeholder="表示名"



            value={displayName}



            onChange={(e) =>



              setDisplayName(e.target.value)



            }



          />



          <textarea



            placeholder="自己紹介"



            value={bio}



            onChange={(e) =>



              setBio(e.target.value)



            }



          />



          <input



            type="number"



            placeholder="ポーカー歴（年）"



            value={pokerYears}



            onChange={(e) =>



              setPokerYears(e.target.value)



            }



          />



          <select



            value={mainGame}



            onChange={(e) =>



              setMainGame(e.target.value)



            }



          >



            <option value="">



              メインゲームを選択



            </option>



            <option value="NLH">



              NLH



            </option>



            <option value="PLO">



              PLO



            </option>



            <option value="MIX">



              MIX



            </option>



            <option value="OTHER">



              その他



            </option>



          </select>



          <div style={{ padding: '14px', border: '1px solid #333', borderRadius: '12px', background: '#111' }}>

            <div style={{ fontWeight: 800, marginBottom: '5px' }}>メインプレイ</div>

            <div style={{ color: '#888', fontSize: '12px', lineHeight: 1.5, marginBottom: '12px' }}>

              普段どんなポーカーを中心にプレイしているか選択してください。

            </div>

            <select value={mainPlay} onChange={(e) => setMainPlay(e.target.value)}>

              <option value="">選択しない</option>

              <option value="tournament">トーナメント中心</option>

              <option value="ring">リング中心</option>

              <option value="cash">キャッシュ中心</option>

              <option value="balanced">バランス</option>

            </select>

        <div style={{ padding: '14px', border: '1px solid #333', borderRadius: '12px', background: '#111' }}>
          <div style={{ fontWeight: 800, marginBottom: '5px' }}>プレイ可能ゲーム</div>
          <div style={{ color: '#888', fontSize: '12px', lineHeight: 1.5, marginBottom: '12px' }}>
            プレイできるゲームをすべて選択できます。検索・複数選択・自由追加に対応しています。
          </div>

          {playableGames.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px', marginBottom: '12px' }}>
              {playableGames.map((game) => (
                <button
                  key={game}
                  type="button"
                  onClick={() => togglePlayableGame(game)}
                  style={{
                    width: 'auto',
                    padding: '7px 10px',
                    borderRadius: '999px',
                    border: '1px solid #444',
                    background: '#242424',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                >
                  {game} ×
                </button>
              ))}
            </div>
          )}

          <input
            type="text"
            placeholder="ゲーム名を検索"
            value={gameSearch}
            onChange={(e) => setGameSearch(e.target.value)}
          />

          <div
            style={{
              marginTop: '10px',
              maxHeight: '330px',
              overflowY: 'auto',
              border: '1px solid #292929',
              borderRadius: '10px',
              padding: '5px 10px',
            }}
          >
            {filteredGameCategories.map((category) => (
              <div key={category.name} style={{ padding: '8px 0 4px' }}>
                <button
                  type="button"
                  onClick={() => toggleGameCategory(category.games)}
                  style={{
                    width: '100%',
                    padding: '8px 4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'transparent',
                    border: 0,
                    borderBottom: '1px solid #333',
                    borderRadius: 0,
                    color: '#999',
                    textAlign: 'left',
                    fontSize: '10px',
                    fontWeight: 800,
                    letterSpacing: '0.8px',
                  }}
                >
                  <span>{category.name}</span>
                  <span>
                    {category.games.every((game) => playableGames.includes(game))
                      ? '✓ 全解除'
                      : '＋ 全選択'}
                  </span>
                </button>

                {category.games.map((game) => {
                  const selected = playableGames.includes(game)
                  return (
                    <button
                      key={game}
                      type="button"
                      onClick={() => togglePlayableGame(game)}
                      style={{
                        width: '100%',
                        padding: '9px 4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        background: 'transparent',
                        border: 0,
                        borderBottom: '1px solid #222',
                        borderRadius: 0,
                        color: selected ? '#fff' : '#bbb',
                        textAlign: 'left',
                        fontSize: '12px',
                      }}
                    >
                      <span>{game}</span>
                      <span style={{ fontWeight: 900 }}>{selected ? '✓' : '＋'}</span>
                    </button>
                  )
                })}
              </div>
            ))}

            {normalizedGameSearch && filteredGameCategories.length === 0 && (
              <div style={{ padding: '14px 4px', color: '#777', fontSize: '12px' }}>
                プリセットに該当するゲームがありません。
              </div>
            )}
          </div>

          <div style={{ marginTop: '12px', color: '#888', fontSize: '11px' }}>
            一覧にないゲーム
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
            <input
              type="text"
              placeholder="ゲーム名を自由入力"
              value={customGame}
              onChange={(e) => setCustomGame(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  addCustomGame()
                }
              }}
              style={{ flex: 1, minWidth: 0 }}
            />
            <button
              type="button"
              onClick={addCustomGame}
              disabled={!customGame.trim()}
              style={{
                width: 'auto',
                flexShrink: 0,
                padding: '0 14px',
                borderRadius: '8px',
              }}
            >
              追加
            </button>
          </div>

          <div style={{ marginTop: '8px', color: '#666', fontSize: '10px' }}>
            プリセット {allPresetGames.length} 種類 ＋ 自由追加
          </div>
        </div>


          </div>



          <div style={{ padding: '14px', border: '1px solid #333', borderRadius: '12px', background: '#111' }}>

            <div style={{ fontWeight: 800, marginBottom: '5px' }}>プレイ環境</div>

            <div style={{ color: '#888', fontSize: '12px', lineHeight: 1.5, marginBottom: '12px' }}>

              ライブとオンラインのどちらを中心にプレイしているか選択してください。

            </div>

            <select value={playEnvironment} onChange={(e) => setPlayEnvironment(e.target.value)}>

              <option value="">選択しない</option>

              <option value="live">ライブ中心</option>

              <option value="online">オンライン中心</option>

              <option value="both">両方</option>

            </select>

          </div>



          <div style={{ padding: '14px', border: '1px solid #333', borderRadius: '12px', background: '#111' }}>

            <div style={{ fontWeight: 800, marginBottom: '5px' }}>活動エリア</div>

            <div style={{ color: '#888', fontSize: '12px', lineHeight: 1.5, marginBottom: '12px' }}>

              普段ポーカーをプレイするエリアを複数登録できます。

            </div>



            {activityAreas.length > 0 && (

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px', marginBottom: '12px' }}>

                {activityAreas.map((area) => (

                  <button

                    key={area}

                    type="button"

                    onClick={() => removeActivityArea(area)}

                    style={{

                      width: 'auto',

                      padding: '7px 10px',

                      borderRadius: '999px',

                      border: '1px solid #444',

                      background: '#242424',

                      color: '#fff',

                      fontSize: '12px',

                    }}

                  >

                    {area} ×

                  </button>

                ))}

              </div>

            )}



            <select

              value=""

              onChange={(e) => {

                addActivityArea(e.target.value)

              }}

            >

              <option value="">活動エリアを追加</option>

              {prefectures

                .filter((area) => !activityAreas.includes(area))

                .map((area) => (

                  <option key={area} value={area}>

                    {area}

                  </option>

                ))}

            </select>

          </div>



          <div style={{ padding: '14px', border: '1px solid #333', borderRadius: '12px', background: '#111' }}>

            <div style={{ fontWeight: 800, marginBottom: '5px' }}>ポーカー頻度</div>

            <div style={{ color: '#888', fontSize: '12px', lineHeight: 1.5, marginBottom: '12px' }}>

              普段どのくらいの頻度でポーカーをプレイするか選択してください。

            </div>

            <select value={pokerFrequency} onChange={(e) => setPokerFrequency(e.target.value)}>

              <option value="">選択しない</option>

              <option value="less_than_monthly">月1回未満</option>

              <option value="monthly_1_3">月1〜3回</option>

              <option value="weekly_1">週1回程度</option>

              <option value="weekly_2_3">週2〜3回</option>

              <option value="weekly_4_plus">週4回以上</option>

            </select>

          </div>







        <div style={{ padding: '14px', border: '1px solid #333', borderRadius: '12px', background: '#111' }}>



          <div style={{ fontWeight: 800, marginBottom: '5px' }}>よく行く店舗</div>



          <div style={{ color: '#888', fontSize: '12px', lineHeight: 1.5, marginBottom: '12px' }}>



            複数選択できます。店舗名を検索して選択してください。



          </div>







          {selectedVenues.length > 0 && (



            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px', marginBottom: '12px' }}>



              {selectedVenues.map((venue) => (



                <button



                  key={venue.id}



                  type="button"



                  onClick={() => toggleVenue(venue.id)}



                  style={{ width: 'auto', padding: '7px 10px', borderRadius: '999px', border: '1px solid #444', background: '#242424', color: '#fff', fontSize: '12px' }}



                >



                  {venue.name} ×



                </button>



              ))}



            </div>



          )}







          <div style={{ display: 'flex', gap: '8px' }}>



            <input



              type="text"



              placeholder="店舗名を検索"



              value={venueSearch}



              onChange={(e) => setVenueSearch(e.target.value)}



              style={{ flex: 1, minWidth: 0 }}



            />



            {venueSearch.trim() && !exactVenueExists && (



              <button



                type="button"



                onClick={handleAddVenue}



                disabled={isAddingVenue}



                style={{ width: 'auto', flexShrink: 0, padding: '0 13px', borderRadius: '8px' }}



              >



                {isAddingVenue ? '追加中...' : '新規追加'}



              </button>



            )}



          </div>







          <div style={{ marginTop: '9px', maxHeight: '190px', overflowY: 'auto', borderTop: filteredVenues.length > 0 ? '1px solid #292929' : 'none' }}>



            {filteredVenues.map((venue) => {



              const selected = selectedVenueIds.includes(venue.id)



              return (



                <button



                  key={venue.id}



                  type="button"



                  onClick={() => toggleVenue(venue.id)}



                  style={{ width: '100%', padding: '10px 4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'transparent', border: 0, borderBottom: '1px solid #222', borderRadius: 0, color: selected ? '#fff' : '#bbb', textAlign: 'left' }}



                >



                  <span>{venue.name}</span>



                  <span style={{ fontWeight: 900 }}>{selected ? '✓' : '＋'}</span>



                </button>



              )



            })}



          </div>



        </div>



          <button



            className="login-button"



            onClick={handleSave}



            disabled={isSaving}



          >



            {isSaving



              ? '保存中...'



              : 'プロフィールを保存'}



          </button>



          {message && <p>{message}</p>}



        </div>



      </div>



    </main>



  )



}



export default ProfileEdit