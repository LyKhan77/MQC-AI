import { describe, it, expect, vi, afterEach } from 'vitest'
import { apiGet, apiPost, apiPut, apiDelete } from './client.js'

function mockFetch(status, body) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
}

describe('api client', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('apiGet hits /api + path and returns json', async () => {
    const f = mockFetch(200, { hello: 'world' })
    vi.stubGlobal('fetch', f)
    const data = await apiGet('/batches')
    expect(f).toHaveBeenCalledWith('/api/batches', { method: 'GET', headers: {} })
    expect(data).toEqual({ hello: 'world' })
  })

  it('apiPost sends a JSON body', async () => {
    const f = mockFetch(201, { batch_id: 'b1' })
    vi.stubGlobal('fetch', f)
    const data = await apiPost('/batches', { batch_name: 'x' })
    expect(f).toHaveBeenCalledWith('/api/batches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_name: 'x' }),
    })
    expect(data).toEqual({ batch_id: 'b1' })
  })

  it('apiPut sends a JSON body', async () => {
    const f = mockFetch(200, { ok: true })
    vi.stubGlobal('fetch', f)
    await apiPut('/settings', { confidence_threshold: 0.7 })
    expect(f).toHaveBeenCalledWith('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confidence_threshold: 0.7 }),
    })
  })

  it('apiDelete issues a DELETE', async () => {
    const f = mockFetch(200, { deleted: 'cam-1' })
    vi.stubGlobal('fetch', f)
    const data = await apiDelete('/cameras/cam-1')
    expect(f).toHaveBeenCalledWith('/api/cameras/cam-1', { method: 'DELETE', headers: {} })
    expect(data).toEqual({ deleted: 'cam-1' })
  })

  it('throws on non-2xx', async () => {
    vi.stubGlobal('fetch', mockFetch(404, {}))
    await expect(apiGet('/nope')).rejects.toThrow('HTTP 404')
  })
})
