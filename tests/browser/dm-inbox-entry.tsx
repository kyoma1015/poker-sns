import { createRoot } from 'react-dom/client'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import DirectMessages from '../../src/DirectMessages'
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={['/dm']}><Routes><Route path="/dm" element={<DirectMessages />} /><Route path="/login" element={<p>Synthetic login</p>} /></Routes></MemoryRouter>)
