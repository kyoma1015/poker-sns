import { createRoot } from 'react-dom/client'
import { MemoryRouter } from 'react-router-dom'
import GtoPreflop from '../../src/GtoPreflop'
import { handLabels, queryKey } from '../../src/gto/rangeCatalog'
import type { ReviewedCertificate } from '../../src/gto/rangeCatalog'
import '../../src/App.css'

// Isolated test entry only; no Supabase, accounts, remote data or app-catalog writes.
// Synthetic fixtures are never imported by the production app.
const query = { format: 'mtt', players: 6, seat: 2, stackBb: '100', anteBb: '0', rakePct: '0',
  rakeCapBb: null, openBb: '2.5', threeBetBb: '9', fourBetBb: '21', stage: 'rfi' }
const record = { schema: 'pokerid-verified-preflop-v1', id: 'browser-fixture-only', query,
  policyDigest: 'a'.repeat(64), configDigest: 'b'.repeat(64), certificateId: 'fixture-only',
  actions: ['Fold', 'Call', 'Raise'], coverage: { combinations: 1326, hands: 169 }, equilibriumVerified: true,
  hands: Object.fromEntries(handLabels.map(label => [label, { combinations: label.endsWith('s') ? 4 : label.endsWith('o') ? 12 : 6,
    frequencies: [.25, .5, .25], evBb: .1 }])) }
const registry: Record<string, ReviewedCertificate> = { 'fixture-only': {
  datasetId: record.id, queryKey: queryKey(query), policyDigest: record.policyDigest, configDigest: record.configDigest,
  artifactSha256: 'c'.repeat(64), scope: 'complete_target_game', continuation: 'full_native_game',
  metric: 'max_unilateral_deviation_gain', upperBoundBb: .001, acceptedToleranceBb: .01,
  reviewReference: 'UI試験用の合成fixture。実際のGTOデータではありません。',
} }
const fixture = new URLSearchParams(window.location.search).get('fixture') === '1'
createRoot(document.getElementById('root')!).render(<MemoryRouter>
  <p>隔離UIテスト専用：合成fixtureは実データではありません。</p>
  {fixture ? <GtoPreflop catalog={[record]} certificates={registry} /> : <GtoPreflop />}
</MemoryRouter>)
