import { test, expect } from '@playwright/test'

const settings = {
  confidence_threshold: 0.11,
  detection_model: 'YOLOv8n',
  segmentation_model: 'SAM3',
  defect_strategy: 'sam3_prompt',
  active_model: 'pcb-1.pt',
  qc_model: 'sam3.pt',
  qc_confidence_threshold: 0.25,
  quantity_model: 'yoloe-26l-seg-pf.pt',
  quantity_confidence_threshold: 0.5,
  quantity_nms_iou: 0.45,
  quantity_agnostic_nms: true,
  quantity_classes: '',
  input_mode_enabled: true,
  object_detection_device: '0',
  qc_device: '0',
  quantity_device: 'auto',
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    if (!path.startsWith('/api/')) {
      await route.continue()
      return
    }
    const body = path.endsWith('/settings')
      ? settings
      : path.endsWith('/cameras')
        ? []
        : path.endsWith('/defect-classes')
          ? []
          : path.endsWith('/models')
            ? { models: ['pcb-1.pt', 'sam3.pt', 'yoloe-26l-seg-pf.pt'], active: 'pcb-1.pt' }
            : path.endsWith('/system/gpus')
              ? {
                  available: true,
                  gpus: [{
                    index: 0,
                    name: 'NVIDIA GeForce RTX 4090',
                    memory_total_mb: 24564,
                    memory_used_mb: 563,
                    memory_free_mb: 24001,
                    utilization_percent: 0,
                  }],
                  error: null,
                }
              : {}
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })
})

test('GPU selectors stay inside the settings grid', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/')
  await page.locator('a[href="/settings"]').click()
  const grid = page.locator('.config-grid')
  await expect(grid).toBeVisible()

  const bounds = await grid.evaluate((element) => {
    const gridRect = element.getBoundingClientRect()
    const overflowing = [...element.querySelectorAll('.form-row')]
      .map((row) => ({
        label: row.textContent.trim().slice(0, 40),
        right: row.getBoundingClientRect().right,
      }))
      .filter((row) => row.right > gridRect.right + 1)
    return { gridRight: gridRect.right, overflowing }
  })

  expect(bounds.overflowing).toEqual([])
})
