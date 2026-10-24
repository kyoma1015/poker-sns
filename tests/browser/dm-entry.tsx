import { createRoot } from 'react-dom/client'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import DirectMessageChat from '../../src/DirectMessageChat'
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={['/dm/other']}><Routes><Route path="/dm/:userId" element={<DirectMessageChat />} /></Routes></MemoryRouter>)
