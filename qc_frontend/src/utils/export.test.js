import { describe, it, expect } from 'vitest'
import { defectsBBox } from './export.js'

describe('defectsBBox', () => {
  const defects = [
    { polygon: [[100, 100], [200, 100], [200, 200], [100, 200]] },
    { polygon: [[300, 300], [400, 300], [400, 400], [300, 400]] },
  ]

  it('unions all polygons with padding', () => {
    const b = defectsBBox(defects, 10, 1000, 1000)
    expect(b).toEqual({ x: 90, y: 90, w: 320, h: 320 })
  })

  it('clamps to image bounds', () => {
    const b = defectsBBox(defects, 1000, 1000, 1000)
    expect(b).toEqual({ x: 0, y: 0, w: 1000, h: 1000 })
  })

  it('returns full image when no defects', () => {
    const b = defectsBBox([], 10, 800, 600)
    expect(b).toEqual({ x: 0, y: 0, w: 800, h: 600 })
  })
})
