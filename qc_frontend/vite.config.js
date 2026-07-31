import fs from 'node:fs'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const tlsKey = process.env.MQC_TLS_KEY
const tlsCert = process.env.MQC_TLS_CERT

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5757,
    strictPort: true,
    host: true,
    ...(tlsKey && tlsCert
      ? {
          https: {
            key: fs.readFileSync(tlsKey),
            cert: fs.readFileSync(tlsCert),
          },
        }
      : {}),
    proxy: {
      '/api': {
        target: 'http://localhost:8787',
        changeOrigin: true,
      },
    },
  },
})
