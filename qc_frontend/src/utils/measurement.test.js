import { describe, it, expect } from 'vitest'

import {
  evaluateMeasurementItem,
  measureGeometry,
  summarizeMeasurement,
} from './measurement.js'


describe('measurement helpers', () => {
  it('converts a linear geometry to millimeters', () => {
    const result = measureGeometry('edge_length', [[0, 0], [100, 0]], { mm_per_pixel: 0.5 })

    expect(result).toEqual({ value: 50, unit: 'mm', pixel_value: 100 })
  })

  it('calculates planar angle in degrees', () => {
    const result = measureGeometry('angle', [[0, 0], [100, 0], [0, 0], [0, 100]], {})

    expect(result.value).toBeCloseTo(90)
    expect(result.unit).toBe('deg')
  })

  it('passes at an inclusive tolerance boundary', () => {
    const result = evaluateMeasurementItem({
      measured: 142,
      unit: 'mm',
      nominal: 140,
      tolerance: 2,
      confidence: 0.95,
    }, true)

    expect(result.status).toBe('PASS')
    expect(result.min).toBe(138)
    expect(result.max).toBe(142)
  })

  it('returns review when calibration or nominal data is incomplete', () => {
    expect(evaluateMeasurementItem({ measured: 140, nominal: 140, tolerance: 2 }, false).status)
      .toBe('REVIEW')
    expect(evaluateMeasurementItem({ measured: 140, nominal: null, tolerance: null }, true).status)
      .toBe('REVIEW')
  })

  it('summarizes review before fail before pass', () => {
    expect(summarizeMeasurement([{ status: 'PASS' }], 'ready')).toBe('PASS')
    expect(summarizeMeasurement([{ status: 'FAIL' }, { status: 'PASS' }], 'ready')).toBe('FAIL')
    expect(summarizeMeasurement([{ status: 'REVIEW' }, { status: 'FAIL' }], 'ready')).toBe('REVIEW')
    expect(summarizeMeasurement([{ status: 'PASS' }], 'review')).toBe('REVIEW')
  })
})
