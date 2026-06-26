import { describe, it, expect, vi, afterEach } from 'vitest'
import { postAudit, listAudit } from './audit.js'

describe('audit api', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('postAudit posts snake_case body', async () => {
    const f = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ id: 'log-1' }) })
    vi.stubGlobal('fetch', f)
    await postAudit({ user: 'u', action: 'A', detail: 'd' })
    expect(f).toHaveBeenCalledWith('/api/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: 'u', action: 'A', detail: 'd' }),
    })
  })

  it('listAudit GETs /audit', async () => {
    const f = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [{ id: 'log-1' }] })
    vi.stubGlobal('fetch', f)
    const data = await listAudit()
    expect(f).toHaveBeenCalledWith('/api/audit', { method: 'GET', headers: {} })
    expect(data).toEqual([{ id: 'log-1' }])
  })
})
