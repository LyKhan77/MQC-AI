import { describe, it, expect } from 'vitest'
import { defectColor, polygonBBox } from './defect.js'

describe('defectColor', () => {
  it('maps known defect types to CSS vars', () => {
    expect(defectColor('scratch')).toBe('var(--defect-scratch)')
    expect(defectColor('porosity')).toBe('var(--defect-porosity)')
    expect(defectColor('spatter')).toBe('var(--defect-spatter)')
    expect(defectColor('color')).toBe('var(--defect-color)')
  })
  it('falls back for unknown types', () => {
    expect(defectColor('weird')).toBe('var(--text-muted)')
  })
})

describe('polygonBBox', () => {
  it('computes bounding box from points', () => {
    const bbox = polygonBBox([[10, 20], [50, 20], [50, 80], [10, 80]])
    expect(bbox).toEqual({ x: 10, y: 20, w: 40, h: 60 })
  })
})
