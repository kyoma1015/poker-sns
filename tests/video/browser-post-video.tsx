import React from 'react'
import { createRoot } from 'react-dom/client'
import PostVideo from '../../src/PostVideo'

declare global { interface Window { __VIDEO_QA_POST_ID?: string } }
const postId = window.__VIDEO_QA_POST_ID
if (!postId) throw new Error('isolated test post missing')
createRoot(document.getElementById('root')!).render(
  <main><h1>隔離タイムライン動画</h1><article data-testid="timeline-post"><PostVideo postId={postId} /></article></main>,
)
