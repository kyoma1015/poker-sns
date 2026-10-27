import React, { useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom'
import Timeline from '../../src/Timeline'

// Actual production Timeline; test-only navigation tears it down through Router.
function Surface() {
  const navigate=useNavigate()
  useEffect(()=>{Object.assign(window,{__VIDEO_QA_NAVIGATE:navigate})},[navigate])
  return <Routes><Route path="/away" element={<main>隔離別画面</main>}/><Route path="*" element={<Timeline/>}/></Routes>
}
const root=createRoot(document.getElementById('root')!)
Object.assign(window,{__VIDEO_QA_UNMOUNT:()=>root.unmount()})
const surface=<MemoryRouter><Surface/></MemoryRouter>
root.render((window as Window & {__VIDEO_QA_STRICT?:boolean}).__VIDEO_QA_STRICT ? <React.StrictMode>{surface}</React.StrictMode> : surface)
