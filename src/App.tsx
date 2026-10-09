import { useEffect, useState } from 'react'
import { supabase } from './supabase'
import './App.css'
import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
  useNavigate,
  Navigate,
} from 'react-router-dom'

import Signup from './Signup'
import Login from './Login'
import ProfileEdit from './ProfileEdit'
import Profile from './Profile'
import PlayerProfile from './PlayerProfile'
import PlayerSearch from './PlayerSearch'
import FollowList from './FollowList'
import FollowerList from './FollowerList'
import StyleRating from './StyleRating'
import Timeline from './Timeline'
import PostDetail from './PostDetail'
import DirectMessages from './DirectMessages'
import DirectMessageChat from './DirectMessageChat'
import Notifications from './Notifications'
import BottomNav from './BottomNav'
import PokerResultCreate from './PokerResultCreate'
import PokerResultEdit from './PokerResultEdit'
import AmusementRingCreate from './AmusementRingCreate'
import AmusementRingEdit from './AmusementRingEdit'
import CashGameCreate from './CashGameCreate'
import CashGameEdit from './CashGameEdit'
import TDA from './TDA'
import PlayerTypeDiagnosis from './PlayerTypeDiagnosis'
import AdminReports from './AdminReports'
import Settings from './Settings'
import PokerTools from './PokerTools'
import PokerResults from './PokerResults'

function Top() {
  const navigate = useNavigate()
  const [checkingSession, setCheckingSession] = useState(true)

  useEffect(() => {
    let active = true
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (!active) return
      if (error) console.error('セッション復元エラー:', error)
      if (session) navigate('/timeline', { replace: true })
      else setCheckingSession(false)
    }).catch((error) => {
      console.error('セッション確認エラー:', error)
      if (active) setCheckingSession(false)
    })
    return () => { active = false }
  }, [navigate])

  if (checkingSession) {
    return <main className="app"><div className="card"><p className="subtitle">ログイン状態を確認中...</p></div></main>
  }

  return (
    <main className="app">
      <div className="card">
        <h1 className="logo">Poker ID</h1>

        <p className="subtitle">
          ポーカープレイヤーのためのSNS
        </p>

        <div className="buttons">
          <button
            className="login-button"
            onClick={() => navigate('/login')}
          >
            ログイン
          </button>

          <button
            className="signup-button"
            onClick={() => navigate('/signup')}
          >
            新規登録
          </button>
        </div>
      </div>
    </main>
  )
}

const menuGroups = [
  { title: 'SNS・コミュニティ', links: [
    ['⌂', 'ホーム', '/timeline'], ['⌕', 'プレイヤー検索', '/search'],
    ['♡', '通知', '/notifications'], ['✉', 'DM', '/dm'],
    ['♤', 'マイプロフィール', '/profile'], ['＋', '投稿', '/timeline?compose=1'],
  ] },
  { title: 'ポーカー学習', links: [
    ['▦', 'ポーカーツール一覧', '/tools'],
    ['♠', 'TDAクイズ', '/tda'], ['▤', 'TDA検索', '/tda'],
  ] },
  { title: '実績・診断', links: [
    ['▥', '実戦記録', '/results'], ['🏆', 'トーナメント記録', '/profile/results/new'],
    ['♣', 'リング記録', '/profile/amusement-ring/new'], ['♦', 'キャッシュ記録', '/profile/cash-game/new'],
    ['🐾', '動物タイプ診断', '/player-type'], ['✎', 'プロフィール編集', '/profile/edit'],
  ] },
  { title: 'アカウント', links: [['⚙', '設定', '/settings']] },
]

function GlobalHeader() {
  const navigate = useNavigate()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { setOpen(false); setQuery(''); setError('') }, [location.pathname, location.search])
  useEffect(() => {
    const show = () => setOpen(true)
    window.addEventListener('poker-id-open-menu', show)
    return () => window.removeEventListener('poker-id-open-menu', show)
  }, [])
  const go = (url: string) => { setOpen(false); navigate(url) }
  const logout = async () => {
    if (!window.confirm('ログアウトしますか？')) return
    setLoggingOut(true); setError('')
    const { error: signOutError } = await supabase.auth.signOut()
    setLoggingOut(false)
    if (signOutError) { setError(`ログアウトに失敗しました：${signOutError.message}`); return }
    setOpen(false); navigate('/login', { replace: true })
  }
  return (
    <>
      <header style={{ position: 'sticky', top: 0, zIndex: 70, background: 'rgba(0,0,0,.96)', borderBottom: '1px solid #242424', backdropFilter: 'blur(12px)' }}>
        <div style={{ maxWidth: 600, margin: 'auto', padding: '10px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button type="button" onClick={() => go('/timeline')} style={{ width: 'auto', background: 'transparent', color: '#fff', fontWeight: 850, fontSize: 21, padding: 0, display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ background: '#fff', color: '#000', borderRadius: 8, padding: '3px 8px' }}>♠</span> Poker ID</button>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" aria-label="DM" onClick={() => go('/dm')} style={{ width: 38, height: 38, padding: 0, borderRadius: '50%', background: '#151515', border: '1px solid #303030', color: '#fff', fontSize: 19 }}>✉</button>
            <button type="button" aria-label="全機能メニュー" aria-expanded={open} onClick={() => setOpen(!open)} style={{ width: 38, height: 38, padding: 0, borderRadius: '50%', background: '#151515', border: '1px solid #303030', color: '#fff', fontSize: 22 }}>{open ? '×' : '☰'}</button>
          </div>
        </div>
      </header>
      {open && <div role="presentation" onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 80, background: 'rgba(0,0,0,.7)' }}>
        <div role="dialog" aria-label="すべての機能" aria-modal="true" onClick={(e) => e.stopPropagation()} style={{ position: 'absolute', top: 0, right: 0, bottom: 0, width: 'min(100%, 390px)', background: '#101010', borderLeft: '1px solid #333', padding: '20px 16px 95px', overflowY: 'auto', color: '#fff', boxSizing: 'border-box' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}><strong style={{ fontSize: 20 }}>すべての機能</strong><button type="button" onClick={() => setOpen(false)} aria-label="閉じる" style={{ width: 36, background: '#222', color: '#fff' }}>×</button></div>
          <input aria-label="機能を検索" placeholder="機能を検索..." value={query} onChange={e => setQuery(e.target.value)} style={{ width: '100%', boxSizing: 'border-box', padding: 12, background: '#1c1c1c', color: '#fff', border: '1px solid #383838', borderRadius: 10, marginBottom: 16 }} />
          {menuGroups.map(group => {
            const links = group.links.filter(link => link[1].toLowerCase().includes(query.trim().toLowerCase()))
            if (!links.length) return null
            return <section key={group.title} style={{ marginBottom: 22 }}><div style={{ fontSize: 12, color: '#aaa', marginBottom: 9 }}>{group.title}</div><div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8 }}>{links.map(([icon, label, url]) => <button type="button" key={label} onClick={() => go(url)} style={{ minWidth: 0, padding: '13px 3px', borderRadius: 11, border: '1px solid #303030', background: '#1b1b1b', color: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7 }}><span style={{ fontSize: 21 }}>{icon}</span><span style={{ fontSize: 11, fontWeight: 700 }}>{label}</span></button>)}</div></section>
          })}
          {'ログアウト'.includes(query.trim()) && <button type="button" disabled={loggingOut} onClick={logout} style={{ width: '100%', padding: 13, background: '#241717', border: '1px solid #643535', color: '#ffcccc', borderRadius: 10 }}>{loggingOut ? 'ログアウト中...' : '⇥ ログアウト'}</button>}
          {error && <p role="alert" style={{ color: '#ffaaaa', fontSize: 12 }}>{error}</p>}
        </div>
      </div>}
    </>
  )
}

function AppLayout() {
  const location = useLocation()

  const hideBottomNav =
    location.pathname === '/' ||
    location.pathname === '/login' ||
    location.pathname === '/signup' ||
    location.pathname === '/player-type' ||
    location.pathname === '/admin/reports'

  return (
    <>
      {!hideBottomNav && <GlobalHeader />}
      <Routes>
        <Route path="/" element={<Top />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route path="/home" element={<Navigate to="/timeline" replace />} />

        <Route path="/timeline" element={<Timeline />} />
        <Route path="/tools" element={<PokerTools />} />
        <Route path="/results" element={<PokerResults />} />
        <Route path="/admin/reports" element={<AdminReports />} />

        <Route path="/post/:id" element={<PostDetail />} />

        <Route path="/dm" element={<DirectMessages />} />

        <Route
          path="/dm/:userId"
          element={<DirectMessageChat />}
        />

        <Route
          path="/notifications"
          element={<Notifications />}
        />

        <Route
          path="/profile/edit"
          element={<ProfileEdit />}
        />

        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />

        <Route
          path="/profile/results/new"
          element={<PokerResultCreate />}
        />

        <Route
          path="/profile/results/:id/edit"
          element={<PokerResultEdit />}
        />

        <Route
          path="/profile/amusement-ring/new"
          element={<AmusementRingCreate />}
        />

        <Route
          path="/profile/amusement-ring/:id/edit"
          element={<AmusementRingEdit />}
        />

        <Route
          path="/profile/cash-game/new"
          element={<CashGameCreate />}
        />

        <Route
          path="/profile/cash-game/:id/edit"
          element={<CashGameEdit />}
        />

        <Route
          path="/player/:id"
          element={<PlayerProfile />}
        />

        <Route
          path="/search"
          element={<PlayerSearch />}
        />

        <Route
          path="/player/:id/following"
          element={<FollowList />}
        />

        <Route
          path="/player/:id/followers"
          element={<FollowerList />}
        />

        <Route
          path="/player/:id/rate"
          element={<StyleRating />}
        />

        <Route
          path="/tda"
          element={<TDA />}
        />

        <Route
          path="/player-type"
          element={<PlayerTypeDiagnosis />}
        />
      </Routes>

      {!hideBottomNav && <BottomNav />}
    </>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}

export default App
