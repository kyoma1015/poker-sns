import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { createClient } from '@supabase/supabase-js'
import PostVideo from '../../src/PostVideo'

// This is an isolated real PostgREST feed fixture, not the full Timeline.tsx.
declare global {
  interface Window {
    __VIDEO_QA_POST_ID?: string
    __VIDEO_QA_JWT?: string
    __VIDEO_QA_ANON?: string
  }
}
const postId = window.__VIDEO_QA_POST_ID
if (!postId || !window.__VIDEO_QA_JWT || !window.__VIDEO_QA_ANON) {
  throw new Error('isolated browser test credentials missing')
}
function Feed() {
  const [posts, setPosts] = useState<Array<{id:string;content:string;video_path:string|null}>>([])
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)
  useEffect(() => {
    const supabase = createClient('http://127.0.0.1:56321', window.__VIDEO_QA_ANON!, {
      global: {headers: {Authorization: 'Bearer ' + window.__VIDEO_QA_JWT}},
      auth: {persistSession:false, autoRefreshToken:false},
    })
    void supabase.from('posts').select('id,content,video_path').order('created_at',{ascending:false})
      .then(({data,error}) => {
        if(error) setError(error.message)
        else setPosts(data || [])
        setLoaded(true)
      })
  },[])
  return <main data-feed-loaded={loaded ? 'true' : 'false'}><h1>隔離タイムライン動画</h1>
    {error && <p role="alert">{error}</p>}
    {posts.map(post => <article key={post.id} data-testid="timeline-post" data-post-id={post.id}>
      <p>{post.content}</p>
      {post.video_path && <PostVideo postId={post.id}/>}
    </article>)}
  </main>
}
createRoot(document.getElementById('root')!).render(<Feed />)
