import { createRoot } from 'react-dom/client'
import { MemoryRouter } from 'react-router-dom'
import TDA from '../../src/TDA'
createRoot(document.getElementById('root')!).render(<MemoryRouter><TDA /></MemoryRouter>)
