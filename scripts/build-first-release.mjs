import { spawnSync } from 'node:child_process'
const gate=spawnSync(process.execPath,['scripts/first-release-gate.mjs','--check'],{stdio:'inherit'})
if(gate.status!==0)process.exit(gate.status??1)
const build=spawnSync(process.execPath,['node_modules/vite/bin/vite.js','build','--config','vite.first-release.config.ts'],{stdio:'inherit'})
process.exit(build.status??1)
