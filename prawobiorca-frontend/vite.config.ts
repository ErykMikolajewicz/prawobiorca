import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

const envDir = fileURLToPath(new URL('./', import.meta.url))
const devStorageOrigin = loadEnv('development', envDir).VITE_DEV_STORAGE_ORIGIN

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/storage': {
        target: devStorageOrigin,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/storage/, '')
      }
    }
  }
})

