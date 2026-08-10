import { test, expect } from '@playwright/test'


const processed = {
  source_key: 'tmp-browser-measurement',
  source_type: 'image',
  source_filename: 'bracket.png',
  source_camera_id: null,
  frame_url: 'data:image/png;base64,iVBORw0KGgo=',
  width: 160,
  height: 120,
  calibration: {
    valid: true,
    mm_per_pixel: 0.5,
    point_a: [0, 0],
    point_b: [100, 0],
    known_mm: 50,
  },
  readiness: 'ready',
  reason: '',
  candidates: [{
    points: [[20, 30], [140, 30]],
    length_px: 120,
    angle: 0,
    confidence: 0.95,
    source: 'lsd',
  }],
}


async function mockMeasurementApi(page) {
  await page.route('**/api/cameras', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ json: [{ id: 'cam-1', name: 'QC Top Camera', status: 'online' }] })
      return
    }
    await route.fallback()
  })
  await page.route(/\/api\/measurements(?:\/|$)/, async (route) => {
    const request = route.request()
    if (request.method() === 'GET') {
      await route.fulfill({ json: [] })
    } else if (request.method() === 'POST' && request.url().endsWith('/process')) {
      const body = request.postData() || ''
      await route.fulfill({
        json: body.includes('name="camera_id"')
          ? { ...processed, source_type: 'live_camera', source_filename: 'cam-1.jpg', source_camera_id: 'cam-1' }
          : processed,
      })
    } else if (request.method() === 'POST') {
      await route.fulfill({ status: 201, json: { id: 'measurement-1', name: 'BRKT-001' } })
    } else {
      await route.fallback()
    }
  })
  await page.route('**/api/audit', async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({ status: 201, json: { id: 'audit-1' } })
    } else {
      await route.fulfill({ json: [] })
    }
  })
}


test('processes an image, evaluates an edge, and saves the run', async ({ page }) => {
  await mockMeasurementApi(page)
  await page.goto('/measurement')

  await expect(page.getByRole('heading', { name: 'Inspect Measurement' })).toBeVisible()
  await page.locator('input[type="file"]').setInputFiles({
    name: 'bracket.png',
    mimeType: 'image/png',
    buffer: Buffer.from('not-used-by-intercept'),
  })
  await page.getByRole('button', { name: 'Process measurement' }).click()
  await expect(page.locator('.measurement-candidate')).toHaveCount(1)

  await page.locator('.measurement-candidate').click()
  await page.locator('.run-name').fill('BRKT-001')
  await page.locator('.item-nominal').fill('60')
  await page.locator('.item-tolerance').fill('2')
  await page.getByRole('button', { name: 'Evaluate dimension' }).click()
  await expect(page.locator('.measurement-summary')).toContainText('PASS')

  await page.locator('.save-measurement').click()
  await expect(page.locator('.app-toast')).toContainText(/Measurement (saved|tersimpan)/)
})


test('triggers Live Camera capture into the same measurement pipeline', async ({ page }) => {
  await mockMeasurementApi(page)
  await page.goto('/measurement')

  await page.getByRole('button', { name: 'Live Camera' }).click()
  await page.locator('.camera-select').selectOption('cam-1')
  await page.locator('.trigger-capture').click()

  await expect(page.locator('.candidate-strip')).toBeVisible()
  await expect(page.locator('.canvas-toolbar')).toContainText('cam-1.jpg')
  await expect(page.locator('.measurement-candidate')).toHaveCount(1)
})
