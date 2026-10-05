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