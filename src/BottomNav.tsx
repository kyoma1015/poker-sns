import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { supabase } from './supabase'

function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    let active = true
    let busy = false
    const refreshUnread = async () => {
      if (busy) return
      busy = true
      try {
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (!active) return
        if (authError || !user) { setUnreadCount(0); return }
        const { count, error } = await supabase
          .from('notifications')
          .select('id', { count: 'exact', head: true })
          .eq('user_id', user.id)
          .is('read_at', null)
        if (error) { console.error('通知未読件数取得エラー:', error); return }
        if (active) setUnreadCount(count ?? 0)
      } catch (error) {
        console.error('通知未読件数取得エラー:', error)
      } finally {
        busy = false
      }
    }
    const onFocus = () => { void refreshUnread() }
    const onVisible = () => { if (document.visibilityState === 'visible') void refreshUnread() }
    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onVisible)
    window.addEventListener('poker-id-notifications-updated', onFocus)
    const interval = window.setInterval(() => { if (document.visibilityState === 'visible') void refreshUnread() }, 30000)
    void refreshUnread()
    return () => {
      active = false
      window.clearInterval(interval)
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onVisible)
      window.removeEventListener('poker-id-notifications-updated', onFocus)
    }
  }, [location.pathname])

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

    if (path === '/tda') {
      return location.pathname.startsWith('/tda')
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
    <nav className="bottom-nav" style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(5, minmax(0, 1fr))',
      width: '100%',
      maxWidth: '100vw',
      boxSizing: 'border-box',
      paddingLeft: 'max(9px, env(safe-area-inset-left))',
      paddingRight: 'max(9px, env(safe-area-inset-right))',
    }}>
      <button
        style={{ minWidth: 0, paddingLeft: 1, paddingRight: 1 }}
        className={`bottom-nav-item ${
          isActive('/timeline') ? 'active' : ''
        }`}
        onClick={() => navigate('/timeline')}
      >
        <span className="bottom-nav-icon">⌂</span>
        <span>ホーム</span>
      </button>

      <button
        style={{ minWidth: 0, paddingLeft: 1, paddingRight: 1 }}
        className={`bottom-nav-item ${
          isActive('/search') ? 'active' : ''
        }`}
        onClick={() => navigate('/search')}
      >
        <span className="bottom-nav-icon">⌕</span>
        <span>検索</span>
      </button>

      <button
        style={{ minWidth: 0, paddingLeft: 1, paddingRight: 1 }}
        className="bottom-nav-item"
        onClick={() => { if (location.pathname === '/timeline') window.dispatchEvent(new Event('poker-id-open-compose')); else navigate('/timeline?compose=1') }}
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
        style={{ minWidth: 0, paddingLeft: 1, paddingRight: 1 }}
        className={`bottom-nav-item ${
          isActive('/notifications') ? 'active' : ''
        }`}
        onClick={() => navigate('/notifications')}
      >
        <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
          <span className="bottom-nav-icon">♡</span>
          {unreadCount > 0 && (
            <span aria-label={`未読通知${unreadCount}件`} style={{
              position: 'absolute', top: -7, right: -16, minWidth: 17, height: 17,
              padding: '0 4px', boxSizing: 'border-box', borderRadius: 999,
              background: '#ef4444', color: '#fff', border: '1px solid #111',
              fontSize: 10, fontWeight: 800, lineHeight: '15px', textAlign: 'center',
            }}>{unreadCount > 99 ? '99+' : unreadCount}</span>
          )}
        </span>
        <span>通知</span>
      </button>

      <button
        style={{ minWidth: 0, paddingLeft: 1, paddingRight: 1 }}
        className={`bottom-nav-item ${
          isActive('/profile') ? 'active' : ''
        }`}
        onClick={() => navigate('/profile')}
      >
        <span className="bottom-nav-icon">♤</span>
        <span style={{ fontSize: 10, letterSpacing: '-0.5px', whiteSpace: 'nowrap' }}>プロフィール</span>
      </button>
    </nav>
  )
}

export default BottomNav