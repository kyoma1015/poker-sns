import { useLocation, useNavigate } from 'react-router-dom'

function HomeButton() {
  const navigate = useNavigate()
  const location = useLocation()

  const hiddenPaths = ['/', '/login', '/signup', '/home']

  if (hiddenPaths.includes(location.pathname)) {
    return null
  }

  return (
    <button
      onClick={() => navigate('/home')}
      title="ホームへ戻る"
      style={{
        position: 'fixed',
        top: '16px',
        right: '16px',
        width: '46px',
        height: '46px',
        padding: 0,
        borderRadius: '50%',
        border: '1px solid #444',
        background: '#292929',
        color: '#ffffff',
        fontSize: '21px',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      🏠
    </button>
  )
}

export default HomeButton