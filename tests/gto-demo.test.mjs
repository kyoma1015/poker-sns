import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { build, validate } from '../scripts/gto-demo/build.mjs'
const source = JSON.parse(readFileSync(new URL('../src/gto/abstractResearchData.json', import.meta.url)))
const precision = JSON.parse(readFileSync(new URL('../src/gto/precisionResearchData.json', import.meta.url)))
test('standalone artifact is deterministic, complete and byte-identical to generated output', () => {
  assert.equal(validate(source, precision).flat().length, 169)
  assert.equal(build(), readFileSync(new URL('../public/gto-demo/index.html', import.meta.url), 'utf8'))
})
test('CSP pins script/style and forbids runtime connections, forms and external dependencies', () => {
  const html = build()
  const js = html.match(/<script>([\s\S]*?)<\/script>/)[1]
  const css = html.match(/<style>([\s\S]*?)<\/style>/)[1]
  for (const text of [js, css]) assert.ok(html.includes(`sha256-${createHash('sha256').update(text).digest('base64')}`))
  assert.ok(html.includes("connect-src 'none'"));assert.ok(html.includes("form-action 'none'"))
  assert.doesNotMatch(html, /<script[^>]+src=|<link|<iframe|<form|fetch\(|XMLHttpRequest|localStorage|sessionStorage|supabase|import\s*\(/i)
  assert.ok(html.includes('研究版／実戦GTO精度未検証'))
})
test('missing rows, policy drift and invalid EV never silently become a complete range', () => {
  for (const mutate of [p => delete p.models.checkdown.contexts.rfi.hands.AA, p => {p.fixed_policy_digests.checkdown = 'bad'}, p => {p.models.checkdown.contexts.rfi.hands.AA.ev_bb = NaN}]) {
    const copy = structuredClone(precision);mutate(copy);assert.throws(() => validate(source, copy))
  }
})
