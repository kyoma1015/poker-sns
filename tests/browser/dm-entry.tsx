import { createRoot } from 'react-dom/client'
import { MemoryRouter, Routes, Route, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import DirectMessageChat from '../../src/DirectMessageChat'
function ChatRoute() {
  const navigate = useNavigate()
  useEffect(() => { (window as any).dmQA.navigate = navigate }, [navigate])
  return <DirectMessageChat />
}
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={['/dm/other']}><Routes><Route path="/dm/:userId" element={<ChatRoute />} /></Routes></MemoryRouter>)
