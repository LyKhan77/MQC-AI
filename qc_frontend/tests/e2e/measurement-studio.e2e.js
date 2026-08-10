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
  await page.route('**/api/measurements/files/**', async (route) => {
    await route.fulfill({
      contentType: 'image/png',
      body: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64'),
    })
  })
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


test('uses the QC Studio full-height shell and application top bar', async ({ page }) => {
  await mockMeasurementApi(page)
  await page.goto('/measurement')

  await expect(page.locator('.top-bar .page-title')).toHaveText('Inspect Measurement')
  await expect(page.locator('.measurement-heading')).toHaveCount(0)

  const shell = await page.evaluate(() => {
    const page = document.querySelector('.measurement-page')
    const studio = document.querySelector('.measurement-studio')
    return {
      pagePadding: getComputedStyle(page).padding,
      studioDisplay: getComputedStyle(studio).display,
      studioBorder: getComputedStyle(studio).borderTopWidth,
      leftRailWidth: getComputedStyle(document.querySelector('.measurement-rail')).width,
      rightRailWidth: getComputedStyle(document.querySelector('.measurement-results')).width,
    }
  })

  expect(shell).toEqual({
    pagePadding: '0px',
    studioDisplay: 'flex',
    studioBorder: '0px',
    leftRailWidth: '280px',
    rightRailWidth: '320px',
  })
})


test('triggers Live Camera capture into the same measurement pipeline', async ({ page }) => {
  await mockMeasurementApi(page)
  await page.goto('/measurement')

  await page.getByRole('button', { name: 'Live Camera' }).click()
  await page.locator('.camera-select').selectOption('cam-1')
  await page.locator('.trigger-capture').click()

  await expect(page.locator('.candidate-strip')).toBeVisible()
  await expect(page.locator('.measurement-canvas-tools')).toContainText('cam-1.jpg')
  await expect(page.locator('.measurement-candidate')).toHaveCount(1)
})


test('keeps Studio scrolling inside History and measurement items', async ({ page }) => {
  await mockMeasurementApi(page)
  await page.goto('/measurement')

  const overflow = await page.evaluate(() => Object.fromEntries([
    ['page', '.measurement-page'],
    ['railBody', '.measurement-rail-body'],
    ['history', '.history-section'],
    ['items', '.items-section'],
    ['canvas', '.measurement-canvas-panel'],
  ].map(([key, selector]) => [key, getComputedStyle(document.querySelector(selector)).overflowY])))

  expect(overflow).toEqual({ page: 'hidden', railBody: 'auto', history: 'auto', items: 'auto', canvas: 'hidden' })
})


test('keeps measurement overlay aligned while zooming the canvas', async ({ page }) => {
  await mockMeasurementApi(page)
  await page.goto('/measurement')

  await page.locator('input[type="file"]').setInputFiles({
    name: 'bracket.png',
    mimeType: 'image/png',
    buffer: Buffer.from('not-used-by-intercept'),
  })
  await page.getByRole('button', { name: 'Process measurement' }).click()

  const frame = page.locator('.measurement-image-frame')
  await expect(frame.locator('.measurement-image')).toBeVisible()
  await expect(frame.locator('.measurement-overlay')).toBeVisible()
  const bounds = await frame.evaluate((element) => {
    const image = element.querySelector('.measurement-image').getBoundingClientRect()
    const overlay = element.querySelector('.measurement-overlay').getBoundingClientRect()
    return { image, overlay }
  })
  expect(bounds.overlay.width).toBeCloseTo(bounds.image.width, 0)
  expect(bounds.overlay.height).toBeCloseTo(bounds.image.height, 0)
  await expect(frame.locator('.measurement-line').first()).toHaveCSS('stroke-width', '3px')
  await expect(page.locator('.measurement-zoom-value')).toHaveText('100%')

  await page.locator('.measurement-zoom-in').click()
  await expect(page.locator('.measurement-zoom-value')).toHaveText('120%')
})


test('shows Mobile Camera client capture controls', async ({ page }) => {
  await mockMeasurementApi(page)
  await page.goto('/measurement')

  await page.locator('.source-mobile').click()

  await expect(page.locator('.mobile-camera-panel')).toBeVisible()
  await expect(page.locator('.open-mobile-camera')).toBeVisible()
  await expect(page.locator('.capture-mobile')).toBeDisabled()
  await expect(page.locator('.mobile-camera-panel')).toContainText(/HTTPS|kamera|camera/i)
})
