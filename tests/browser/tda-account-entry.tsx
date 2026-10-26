import { createRoot } from 'react-dom/client'
import { MemoryRouter } from 'react-router-dom'
import TDA from '../../src/TDA'
const root = createRoot(document.getElementById('root')!)
Object.assign(window, { unmountTda: () => root.unmount() })
root.render(<MemoryRouter><TDA /></MemoryRouter>)
