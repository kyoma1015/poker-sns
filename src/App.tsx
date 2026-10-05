import './App.css'
import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
  useNavigate,
} from 'react-router-dom'

import Signup from './Signup'
import Login from './Login'
import Home from './Home'
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

function Top() {
  const navigate = useNavigate()

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
    location.pathname === '/signup'

  return (
    <>
      <Routes>
        <Route path="/" element={<Top />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route
          path="/home"
          element={<Home />}
        />

        <Route
          path="/timeline"
          element={<Timeline />}
        />

        <Route
          path="/post/:id"
          element={<PostDetail />}
        />

        <Route
          path="/dm"
          element={<DirectMessages />}
        />

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

        <Route
          path="/profile"
          element={<Profile />}
        />

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