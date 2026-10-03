import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import Icons from 'unplugin-icons/vite'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue(), tailwindcss(), Icons({ compiler: 'vue3' })],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 0.0.0.0 so the container is reachable from Caddy. No HMR configuration
    // is needed: with no `hmr.host` or `clientPort`, Vite derives the socket
    // origin from the client script's URL, which is the page's own origin.
    host: '0.0.0.0',
    port: 5173,
    fs: {
      // Vite otherwise treats the workspace root as servable, and in the
      // container that root is the whole repository — so `/@fs/` handed out
      // the back-end source, the compose file and the lockfile to anyone who
      // could reach the dev server.
      //
      // The workspace `node_modules` has to stay in the list: pnpm symlinks
      // each package's dependencies there, so a narrower list makes Vite
      // refuse to serve its own dependencies and the page goes blank.
      allow: [
        fileURLToPath(new URL('.', import.meta.url)),
        fileURLToPath(new URL('../node_modules', import.meta.url)),
      ],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: false,
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.spec.ts'],
  },
})
