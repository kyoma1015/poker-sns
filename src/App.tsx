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
      <Routes>
        <Route path="/" element={<Top />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route path="/home" element={<Navigate to="/timeline" replace />} />

        <Route path="/timeline" element={<Timeline />} />
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
