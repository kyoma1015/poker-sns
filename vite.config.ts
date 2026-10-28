import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { resolve } from 'node:path'

// Keep the existing SNS entry and a separate, minimal cloud-video test entry.
export default defineConfig({
  plugins: [react()],
  build: { rollupOptions: { input: {
    main: resolve(__dirname, 'index.html'),
    cloudTest: resolve(__dirname, 'cloud-video-test.html'),
  } } },
})
