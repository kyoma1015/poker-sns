// Offline packaging only. This command never writes a release registry or claims GTO.
import { readFile, writeFile } from 'node:fs/promises'
import { generateReleaseCandidates, candidateDigest } from '../../src/gto/releaseCandidate.ts'
const [input, evidence, output] = process.argv.slice(2)
if (!input || !evidence || !output) throw new Error('Usage: node scripts/gto-release/build.mjs UI_SOURCE.json SOLVER_EVIDENCE.json NEW_OUTPUT.json')
const raw = await readFile(input, 'utf8')
if (Buffer.byteLength(raw) > 16 * 1024 * 1024) throw new Error('Source exceeds16MiB')
const proof = await readFile(evidence, 'utf8')
if (Buffer.byteLength(proof) > 16 * 1024 * 1024) throw new Error('Evidence exceeds16MiB')
const candidates = await generateReleaseCandidates(JSON.parse(raw), JSON.parse(proof))
const packageData = { schema: 'pokerid-preflop-candidate-package-v1', ordinaryCatalogAdded: 0,
  formalAcceptance: [0, 12], candidates,
  candidateSha256: Object.fromEntries(await Promise.all(candidates.map(async c => [c.id, await candidateDigest(c)]))) }
await writeFile(output, JSON.stringify(packageData, null, 2) + '\n', { flag: 'wx' })
console.log(`PASS ${candidates.length} candidates/${candidates.length * 169} rows; all blocked; ordinary registrations0`)
