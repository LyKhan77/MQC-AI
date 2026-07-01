import { describe, it, expect } from 'vitest'
import { toImageCoords } from './canvasCoords.js'

describe('toImageCoords', () => {
  const rect = { left: 100, top: 50, width: 400, height: 200 }

  it('maps client coordinates through the svg rect to image pixels', () => {
    expect(toImageCoords(300, 150, rect, 800, 600)).toEqual({ x: 400, y: 300 })
  })

  it('clamps coordinates at image edges', () => {
    expect(toImageCoords(0, 500, rect, 800, 600)).toEqual({ x: 0, y: 600 })
  })

  it('rounds mapped coordinates', () => {
    expect(toImageCoords(151, 76, rect, 1000, 1000)).toEqual({ x: 128, y: 130 })
  })
})
