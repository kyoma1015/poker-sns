import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { existsSync, renameSync } from 'node:fs'
import path from 'node:path'
// Only the new generated candidate directory is touched, never legacy source/state.
export default defineConfig({
 plugins:[react(),{name:'first-release-index',writeBundle(options){
  if(!options.dir || path.resolve(options.dir)!==path.resolve('dist-first-release'))throw new Error('Unexpected candidate output directory')
  const from=path.join(options.dir,'first-release.html')
  const to=path.join(options.dir,'index.html')
  if(!existsSync(from)||existsSync(to))throw new Error('Unexpected candidate HTML layout')
  renameSync(from,to)
 }}],
 build:{outDir:'dist-first-release',rollupOptions:{input:'first-release.html'}},
})
