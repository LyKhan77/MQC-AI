import { test, expect } from '@playwright/test'

const frameUrl = `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="white"/></svg>')}`
const upload = (name) => ({
  name,
  mimeType: 'image/svg+xml',
  buffer: Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"/>'),
})

test('Direct Inspection processes a masked staged upload and a full-frame fallback', async ({ page }) => {
  const detectRequests = []
  const handoffs = []

  await page.addInitScript(() => localStorage.setItem('mqc-lang', 'en'))
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (!path.startsWith('/api/')) {
      await route.continue()
      return
    }
    if (path === '/api/inspection/detect') {
      const body = request.postData() || ''
      const mask = body.match(/name="mask_polygon"\r?\n\r?\n([^\r\n]+)/)
      const cropMode = body.match(/name="crop_mode"\r?\n\r?\n([^\r\n]+)/)
      const maskPolygon = mask ? JSON.parse(mask[1]) : null
      detectRequests.push({ cropMode: cropMode?.[1], maskPolygon })
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          key: `capture-${detectRequests.length}`,
          frame_url: frameUrl,
          width: 100,
          height: 100,
          crop_mode: cropMode?.[1] || 'full',
          mask_applied: Boolean(maskPolygon),
          mask_polygon: maskPolygon,
          defects: [{ type: 'Scratch', confidence: 0.9, polygon: [[20, 20], [40, 20], [40, 40]] }],
          verdict: 'defect',
        }),
      })
      return
    }
    if (path === '/api/inspection/to-qc') {
      handoffs.push(JSON.parse(request.postData() || '{}'))
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ batch_id: 'batch-mask' }) })
      return
    }
    const body = path.endsWith('/cameras') || path.endsWith('/defect-classes') ? [] : {}
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })

  await page.goto('/direct-inspection')
  await page.locator('input[type="file"]').setInputFiles([upload('masked.svg'), upload('full-frame.svg')])
  await page.getByText('Masking').check()

  const stagedThumbs = page.locator('.mask-stage-thumb')
  await expect(stagedThumbs).toHaveCount(2)
  await expect(page.getByTestId('mask-canvas')).toHaveCount(1)
  await stagedThumbs.nth(1).click()
  await expect(stagedThumbs.nth(1)).toHaveClass(/active/)
  await stagedThumbs.nth(0).click()

  const editor = page.getByTestId('mask-canvas')
  await editor.click({ position: { x: 20, y: 20 } })
  await editor.click({ position: { x: 80, y: 20 } })
  await editor.click({ position: { x: 50, y: 80 } })
  await expect(editor.locator('.mask-polygon')).toBeVisible()
  await page.getByTestId('mask-finish').first().click()
  await expect(page.locator('.mask-stage-heading').getByText('Mask ready')).toBeVisible()

  await page.locator('.process-qc').click()
  await expect.poll(() => detectRequests.length).toBe(2)
  expect(detectRequests.map((request) => request.cropMode)).toEqual(['full', 'full'])
  expect(detectRequests.filter((request) => request.maskPolygon)).toHaveLength(1)
  expect(detectRequests.filter((request) => !request.maskPolygon)).toHaveLength(1)
  expect(detectRequests.find((request) => request.maskPolygon).maskPolygon).toHaveLength(3)

  await page.locator('.capture-thumb').first().click()
  await expect(page.locator('.mask-result-poly')).toBeVisible()
  await expect(page.locator('.mask-result-label')).toBeVisible()

  await page.locator('.footer-actions .btn-primary').click()
  await page.locator('dialog .dialog-actions .btn-primary').click()
  await expect.poll(() => handoffs.length).toBe(1)
  expect(handoffs[0].captures).toHaveLength(2)
  expect(handoffs[0].captures.filter((capture) => capture.mask_polygon)).toHaveLength(1)
  expect(handoffs[0].captures.filter((capture) => !capture.mask_polygon)).toHaveLength(1)
})
