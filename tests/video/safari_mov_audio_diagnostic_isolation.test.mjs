// Offline static isolation check for the manual Safari audio diagnostic.
// Does not execute browser APIs, touch user media, contact servers or rerun existing CI.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'
const html=readFileSync(new URL('./safari_mov_audio_diagnostic.html',import.meta.url),'utf8')
const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
assert.equal(scripts.length,1,'one self-contained diagnostic script')
new vm.Script(scripts[0][1],{filename:'safari_mov_audio_diagnostic.html'})
assert.match(html,/createMediaElementSource\(video\)/)
assert.match(html,/createAnalyser\(\)/)
assert.match(html,/createMediaStreamDestination\(\)/)
assert.match(html,/getFloatTimeDomainData\(buffer\)/)
assert.match(html,/decodeAudioData\(bytes\.slice\(0\)\)/)
assert.match(html,/video\.muted=true/)
assert.match(html,/video\.pause\(\)/)
assert.match(html,/URL\.revokeObjectURL\(url\)/)
assert.doesNotMatch(scripts[0][1],/\b(?:fetch|XMLHttpRequest|sendBeacon|WebSocket|MediaRecorder|indexedDB|localStorage|sessionStorage)\b/)
assert.doesNotMatch(html,/<script[^>]+src=|<form\b|<iframe\b/i)
console.log('PASS: Safari MOV diagnostic syntax, local PCM/graph stages, cleanup and no network/storage/recording APIs')
