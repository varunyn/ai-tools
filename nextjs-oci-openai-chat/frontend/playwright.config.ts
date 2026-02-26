import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 90_000,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: 'http://localhost:4000',
    trace: 'retain-on-failure'
  },
  webServer: {
    command: 'pnpm exec next dev -p 4000',
    url: 'http://localhost:4000',
    reuseExistingServer: !process.env.CI,
    env: {
      PORT: '4000',
      NODE_ENV: 'development',
      MODEL_ID: 'mock-model',
      FASTAPI_BACKEND_URL: 'http://localhost:4545',
      MCP_CALCULATOR_URL: 'http://localhost:3020/mcp',
      MCP_ORACLE_RAG_URL: 'http://localhost:3021/mcp'
    }
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ]
})
