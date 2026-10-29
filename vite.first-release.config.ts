import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
// Separate candidate artifact; never changes the normal app or deployment settings.
export default defineConfig({
 plugins:[react(),{name:'first-release-index',generateBundle(_options,bundle){
  const html=bundle['first-release.html']
  if(html){delete bundle['first-release.html'];html.fileName='index.html';bundle['index.html']=html}
 }}],
 build:{outDir:'dist-first-release',rollupOptions:{input:'first-release.html'}},
})
