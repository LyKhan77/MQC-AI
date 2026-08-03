import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.route('**/api/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    if (!path.startsWith('/api/')) {
      await route.continue()
      return
    }
    let body = {}
    if (path.endsWith('/batches')) body = [{ id: 'batch-1', name: 'Batch 1' }]
    else if (path.endsWith('/settings')) body = {}
    else if (path.endsWith('/cameras') || path.endsWith('/defect-classes')) body = []
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })
})

test('reports exposes per-run defect-only and full-image formats', async ({ page }) => {
  await page.goto('/')
  await page.goto('/reports')
  await expect(page.locator('.mode-fieldset')).toBeVisible()
  await expect(page.locator('input[value="defect-only"]')).toBeChecked()
  await page.locator('input[value="full-image"]').check()
  await expect(page.locator('input[value="full-image"]')).toBeChecked()
})
