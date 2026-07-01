import { describe, it, expect } from 'vitest'
import { normalizeBox, toImageCoords } from './canvasCoords.js'

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

describe('normalizeBox', () => {
  it('orders left-top to right-bottom regardless of drag direction', () => {
    expect(normalizeBox(10, 20, 30, 40)).toEqual([10, 20, 30, 40])
    expect(normalizeBox(30, 40, 10, 20)).toEqual([10, 20, 30, 40])
    expect(normalizeBox(30, 20, 10, 40)).toEqual([10, 20, 30, 40])
    expect(normalizeBox(10, 40, 30, 20)).toEqual([10, 20, 30, 40])
  })
})
