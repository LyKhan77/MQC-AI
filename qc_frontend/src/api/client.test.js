import { describe, it, expect, vi, afterEach } from 'vitest'
import { apiGet, apiPost } from './client.js'

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

  it('throws on non-2xx', async () => {
    vi.stubGlobal('fetch', mockFetch(404, {}))
    await expect(apiGet('/nope')).rejects.toThrow('HTTP 404')
  })
})
