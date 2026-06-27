import { describe, it, expect, vi, afterEach } from 'vitest'
import { createCamera, deleteCamera } from './cameras.js'

describe('cameras api', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('createCamera posts the camera as-is', async () => {
    const f = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ id: 'cam-1' }) })
    vi.stubGlobal('fetch', f)
    await createCamera({ id: 'cam-1', name: 'X', type: 'usb', source: '/dev/video0' })
    expect(f).toHaveBeenCalledWith('/api/cameras', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: 'cam-1', name: 'X', type: 'usb', source: '/dev/video0' }),
    })
  })

  it('deleteCamera issues DELETE', async () => {
    const f = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ deleted: 'cam-1' }) })
    vi.stubGlobal('fetch', f)
    await deleteCamera('cam-1')
    expect(f).toHaveBeenCalledWith('/api/cameras/cam-1', { method: 'DELETE', headers: {} })
  })
})
