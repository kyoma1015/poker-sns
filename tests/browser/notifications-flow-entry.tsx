import { createRoot } from 'react-dom/client'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import Notifications from '../../src/Notifications'
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={['/notifications']}><Routes><Route path="/notifications" element={<Notifications />} /><Route path="/login" element={<p>Synthetic login</p>} /><Route path="/post/:id" element={<p>Synthetic post</p>} /><Route path="/player/:id" element={<p>Synthetic profile</p>} /></Routes></MemoryRouter>)
