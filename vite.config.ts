import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { fileURLToPath } from 'node:url'

// Separate mobile cloud-test entry; no production feature flag is changed.
export default defineConfig({
  plugins: [react()],
  build: { rollupOptions: { input: {
    main: fileURLToPath(new URL('./index.html', import.meta.url)),
    cloudTest: fileURLToPath(new URL('./cloud-video-test.html', import.meta.url)),
  } } },
})
