import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.e2e.js',
  use: {
    baseURL: 'http://127.0.0.1:5757',
    headless: true,
  },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1',
    url: 'http://127.0.0.1:5757',
    reuseExistingServer: true,
  },
})
