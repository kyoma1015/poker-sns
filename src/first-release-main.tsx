import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import FirstReleaseEntry from './first-release-entry'
createRoot(document.getElementById('root')!).render(<StrictMode><FirstReleaseEntry /></StrictMode>)
