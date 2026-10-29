import { lazy, Suspense } from 'react'
import { BrowserRouter, Link, useLocation } from 'react-router-dom'
import { FIRST_RELEASE_ENABLED, firstReleaseRoute } from './firstReleasePolicy'
const pages = {
 entry:lazy(()=>import('./Login')),login:lazy(()=>import('./Login')),signup:lazy(()=>import('./Signup')),
 timeline:lazy(()=>import('./Timeline')),post:lazy(()=>import('./PostDetail')),
 dm:lazy(()=>import('./DirectMessages')),conversation:lazy(()=>import('./DirectMessageChat')),
 notifications:lazy(()=>import('./Notifications')),profile:lazy(()=>import('./Profile')),
 profileEdit:lazy(()=>import('./ProfileEdit')),search:lazy(()=>import('./PlayerSearch')),
 player:lazy(()=>import('./PlayerProfile')),following:lazy(()=>import('./FollowList')),
 followers:lazy(()=>import('./FollowerList')),settings:lazy(()=>import('./Settings')),
}
function CandidateRoute() {
 const location=useLocation()
 const route=firstReleaseRoute(location.pathname)
 const Page=route ? pages[route as keyof typeof pages] : undefined
 return <>
  <nav aria-label="初回公開候補"><Link to="/timeline">ホーム</Link>{' '}
   <Link to="/search">検索</Link>{' '}<Link to="/notifications">通知</Link>{' '}
   <Link to="/dm">DM</Link>{' '}<Link to="/profile">プロフィール</Link></nav>
  {!Page ? <main className="app"><h1>初回公開対象外</h1><p>この機能は準備中です。既存データは削除していません。</p></main> :
   !FIRST_RELEASE_ENABLED ? <main className="app"><h1>初回公開準備中</h1><p>認証・所有者認可・プライバシーの確認が完了するまで公開しません。</p></main> :
   <Suspense fallback={<p role="status">読み込み中...</p>}><Page /></Suspense>}
 </>
}
export default function FirstReleaseApp() {
 return <BrowserRouter><CandidateRoute /></BrowserRouter>
}
