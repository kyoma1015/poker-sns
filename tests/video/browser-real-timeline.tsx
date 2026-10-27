import React from 'react'
import { createRoot } from 'react-dom/client'
import { MemoryRouter } from 'react-router-dom'
import Timeline from '../../src/Timeline'

// The actual production Timeline component, mounted in isolated Chromium.
// Non-video social dependencies are stubbed by the test-only Vite transform.
const root = createRoot(document.getElementById('root')!)
Object.assign(window, { __VIDEO_QA_UNMOUNT: () => root.unmount() })
root.render(
  <MemoryRouter><Timeline /></MemoryRouter>,
)
