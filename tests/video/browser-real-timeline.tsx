import React from 'react'
import { createRoot } from 'react-dom/client'
import { MemoryRouter } from 'react-router-dom'
import Timeline from '../../src/Timeline'

// The actual production Timeline component, mounted in isolated Chromium.
// Non-video social dependencies are stubbed by the test-only Vite transform.
createRoot(document.getElementById('root')!).render(
  <MemoryRouter><Timeline /></MemoryRouter>,
)
