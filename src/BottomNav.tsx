import { useLocation, useNavigate } from 'react-router-dom'

function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()

  const isActive = (path: string) => {
    if (path === '/timeline') {
      return (
        location.pathname === '/timeline' ||
        location.pathname.startsWith('/post/')
      )
    }

    if (path === '/search') {
      return (
        location.pathname === '/search' ||
        location.pathname.startsWith('/player/')
      )
    }

    if (path === '/notifications') {
      return location.pathname === '/notifications'
    }

    if (path === '/profile') {
      return (
        location.pathname === '/profile' ||
        location.pathname === '/profile/edit'
      )
    }

    return location.pathname === path
  }

  return (
    <nav className="bottom-nav">
      <button
        className={`bottom-nav-item ${
          isActive('/timeline') ? 'active' : ''
        }`}
        onClick={() => navigate('/timeline')}
      >
        <span className="bottom-nav-icon">⌂</span>
        <span>ホーム</span>
      </button>

      <button
        className={`bottom-nav-item ${
          isActive('/search') ? 'active' : ''
        }`}
        onClick={() => navigate('/search')}
      >
        <span className="bottom-nav-icon">⌕</span>
        <span>検索</span>
      </button>

      <button
        className="bottom-nav-item"
        onClick={() => navigate('/timeline')}
      >
        <span
          className="bottom-nav-icon"
          style={{
            width: '34px',
            height: '34px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
            background: '#fff',
            color: '#000',
            fontSize: '24px',
            fontWeight: 400,
          }}
        >
          +
        </span>
        <span>投稿</span>
      </button>

      <button
        className={`bottom-nav-item ${
          isActive('/notifications') ? 'active' : ''
        }`}
        onClick={() => navigate('/notifications')}
      >
        <span className="bottom-nav-icon">♡</span>
        <span>通知</span>
      </button>

      <button
        className={`bottom-nav-item ${
          isActive('/profile') ? 'active' : ''
        }`}
        onClick={() => navigate('/profile')}
      >
        <span className="bottom-nav-icon">♤</span>
        <span>プロフィール</span>
      </button>
    </nav>
  )
}

export default BottomNav