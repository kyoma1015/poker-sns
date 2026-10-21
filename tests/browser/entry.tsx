import React from 'react'
import { createRoot } from 'react-dom/client'
import { MemoryRouter } from 'react-router-dom'
import Timeline from '../../src/Timeline'
import { InteractiveCard, InteractiveComposer } from '../../src/TimelineInteractive'

const kind = new URLSearchParams(location.search).get('case')
const item = { post_id: 'qa-poll', kind: 'poll' as const, options: ['A', 'B'], is_anonymous: kind === 'anonymous', closes_at: '2099-01-01T00:00:00Z' }
const result = { post_id: item.post_id, total_votes: 1, vote_counts: { 0: 1 }, my_option_index: 0, has_responded: true,
  voters: [{ option_index: 0, poker_id: 'qa-identity-secret', display_name: 'QA Named User' }], answers: [] }
const updated = async () => {}
createRoot(document.getElementById('root')!).render(<MemoryRouter>
  {kind === 'anonymous' || kind === 'named' || kind === 'question'
    ? <InteractiveCard item={kind === 'question' ? { ...item, kind: 'question' } : item} result={result} onUpdated={updated} isOwner />
    : kind === 'standalone' ? <InteractiveComposer onCreated={updated} /> : <Timeline />}
</MemoryRouter>)
