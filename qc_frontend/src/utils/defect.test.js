import { describe, it, expect } from 'vitest'
import { polygonBBox } from './defect.js'

describe('polygonBBox', () => {
  it('computes bounding box from points', () => {
    const bbox = polygonBBox([[10, 20], [50, 20], [50, 80], [10, 80]])
    expect(bbox).toEqual({ x: 10, y: 20, w: 40, h: 60 })
  })
})
