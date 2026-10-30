import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createIsolatedSupabaseVideoAdapters } from '../api/video-isolated-supabase-adapters.ts'

test('isolated real Supabase adapter refuses remote and production endpoints', () => {
  for (const url of ['https://project.supabase.co', 'http://localhost:56321',
    'http://127.0.0.1:56322', 'http://127.0.0.1:56321.evil.test',
    'http://127.0.0.1:56321@evil.test']) {
    assert.throws(() => createIsolatedSupabaseVideoAdapters(url, 'anon', 'service', 'jwt'),
      /isolated Supabase/)
  }
})
test('isolated adapter rejects invalid owner path before any Storage request', async () => {
  const adapter = createIsolatedSupabaseVideoAdapters(
    'http://127.0.0.1:56321', 'anon', 'service', 'jwt')
  await assert.rejects(adapter.snapshot('10000000-0000-0000-0000-000000000001',
    '../foreign.mp4'), /unauthorized|owner/)
})
