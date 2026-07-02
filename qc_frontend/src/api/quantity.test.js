import { describe, it, expect, vi, afterEach } from 'vitest'
import { createQuantityCheck, listQuantityChecks } from './quantity.js'

function ok(body) {
  return vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => body })
}

describe('quantity api', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('listQuantityChecks GETs the checks endpoint', async () => {
    const f = ok([{ id: 'qty-1' }])
    vi.stubGlobal('fetch', f)
    const res = await listQuantityChecks()
    expect(f).toHaveBeenCalledWith('/api/quantity/checks', expect.objectContaining({ method: 'GET' }))
    expect(res[0].id).toBe('qty-1')
  })

  it('createQuantityCheck POSTs the payload as JSON', async () => {
    const f = ok({ id: 'qty-2', verdict: 'pass' })
    vi.stubGlobal('fetch', f)
    await createQuantityCheck({ total_count: 5, verdict: 'pass' })
    expect(f).toHaveBeenCalledWith('/api/quantity/checks', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ total_count: 5, verdict: 'pass' }),
    }))
  })
})
