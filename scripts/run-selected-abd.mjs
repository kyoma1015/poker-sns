import {readFileSync} from 'node:fs'
import {execFileSync} from 'node:child_process'
const m=JSON.parse(readFileSync('docs/qa/selected-abd-20261026/source-manifest.json','utf8'))
for(const suite of m.unit_suites)execFileSync(process.execPath,[suite],{stdio:'inherit'})
execFileSync(process.execPath,['tests/selected-browser.test.mjs'],{stdio:'inherit'})
