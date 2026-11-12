import { readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
const root = fileURLToPath(new URL('../../', import.meta.url))
const hash = x => createHash('sha256').update(x).digest('base64')
export function validate(source, precision) {
  if (source.full_game_gto_verified !== false || precision.full_game_gto_verified !== false || precision.confidence !== .99 || precision.real_game_approximation_error !== null) throw Error('Research scope required')
  const ranks = 'AKQJT98765432'.split('')
  const grid = ranks.map((a, i) => ranks.map((b, j) => i === j ? a + b : i < j ? a + b + 's' : b + a + 'o'))
  for (const mode of ['checkdown', 'flop_controller']) {
    const model = source.models[mode]
    if (model.policy_digest !== precision.fixed_policy_digests[mode]) throw Error('Frozen policy identity differs')
    for (const stage of ['rfi', 'vs_open', 'vs_3bet', 'vs_4bet']) {
      const c = model.contexts[stage], p = precision.models[mode].contexts[stage]
      if (c.actor !== p.actor || JSON.stringify(c.actions) !== JSON.stringify(p.actions) || Object.keys(c.hands).length !== 169 || Object.keys(p.hands).length !== 169) throw Error('Complete matched context required')
      for (const hand of grid.flat()) {
        const row = c.hands[hand], ev = p.hands[hand]
        if (!row || !ev || row.frequencies.length !== c.actions.length || row.frequencies.some(x => !Number.isFinite(x) || x < 0 || x > 1) || Math.abs(row.frequencies.reduce((a, b) => a + b, 0) - 1) > 1e-9 || !Number.isFinite(ev.ev_bb) || ev.action_ev_bb.length !== c.actions.length || ev.action_ev_bb.some(x => !Number.isFinite(x)) || !Number.isFinite(ev.radius_bb) || ev.radius_bb < 0 || ev.interval_bb.length !== 2 || ev.interval_bb.some(x => !Number.isFinite(x)) || ev.interval_bb[0] > ev.ev_bb || ev.interval_bb[1] < ev.ev_bb || ev.action_intervals_bb.length !== c.actions.length || ev.action_intervals_bb.some((ci, i) => ci.length !== 2 || ci.some(x => !Number.isFinite(x)) || ci[0] > ev.action_ev_bb[i] || ci[1] < ev.action_ev_bb[i]) || Math.abs(ev.ev_bb - row.frequencies.reduce((v, f, i) => v + f * ev.action_ev_bb[i], 0)) > 1e-8) throw Error('Invalid hand frequencies or EV')
      }
    }
  }
  return grid
}
export function build() {
  const sourceText = readFileSync(path.join(root, 'src/gto/abstractResearchData.json'), 'utf8')
  const precisionText = readFileSync(path.join(root, 'src/gto/precisionResearchData.json'), 'utf8')
  const source = JSON.parse(sourceText), precision = JSON.parse(precisionText)
  const grid = validate(source, precision)
  const data = { grid, models: source.models, precision, sourceHashes: { frequencies: hash(sourceText), precision: hash(precisionText) } }
  const json = JSON.stringify(data).replace(/</g, '\\u003c').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029')
  const js = `const DATA=${json};\n` + readFileSync(path.join(root, 'scripts/gto-demo/view.js'), 'utf8')
  const css = readFileSync(path.join(root, 'scripts/gto-demo/style.css'), 'utf8')
  const template = readFileSync(path.join(root, 'scripts/gto-demo/template.html'), 'utf8')
  const csp = `default-src 'none'; script-src 'sha256-${hash(js)}'; style-src 'sha256-${hash(css)}'; connect-src 'none'; img-src 'none'; font-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'`
  return template.replace('%%CSP%%', csp).replace('%%STYLE%%', css).replace('%%SCRIPT%%', js)
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const html = build(), target = path.resolve(root, process.argv[2] ?? 'public/gto-demo/index.html')
  mkdirSync(path.dirname(target), { recursive: true });writeFileSync(target, html)
  console.log(`Built standalone research demo: ${target} (${Buffer.byteLength(html)} bytes); no runtime dependencies`)
}
