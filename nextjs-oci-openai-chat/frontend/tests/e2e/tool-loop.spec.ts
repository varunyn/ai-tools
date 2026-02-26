import { test, expect } from '@playwright/test'
import { startMockOpenAIBackendServer } from './servers/mock-openai-backend'
import { startMockCalculatorMcp } from './servers/mock-mcp-calculator'
import { startMockRagMcp } from './servers/mock-mcp-rag'

const stopFns: Array<() => Promise<void>> = []

test.beforeAll(async () => {
  const openai = await startMockOpenAIBackendServer(4545)
  const calc = await startMockCalculatorMcp(3020)
  const rag = await startMockRagMcp(3021)
  stopFns.push(openai.close, calc.close, rag.close)
})

test.afterAll(async () => {
  for (const stop of stopFns) {
    await stop()
  }
})

test('tool loop executes and final answer includes 3', async ({ page }) => {
  await page.goto('/')

  const input = page.locator('form input[type="text"]').first()
  await expect(input).toHaveAttribute('placeholder', 'Type your message here...', { timeout: 15000 })
  await input.fill('what is 1+2')
  await page.getByRole('button', { name: 'Send' }).click()

  await expect(page.getByText(/^calculate$/)).toBeVisible({ timeout: 30000 })
  await expect(page.locator('p').filter({ hasText: /\b3\b/ })).toBeVisible({ timeout: 30000 })
})
