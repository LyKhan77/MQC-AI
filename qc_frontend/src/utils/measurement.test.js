import { describe, it, expect } from 'vitest'

import {
  calibrationScales,
  evaluateMeasurementItem,
  measureGeometry,
  normalizeTaskTypes,
  summarizeMeasurement,
} from './measurement.js'


describe('measurement helpers', () => {
  it('uses independent x and y calibration scales for linear geometry', () => {
    const calibration = {
      mode: 'manual_axes',
      valid: true,
      scale_x_mm_per_px: 0.5,
      scale_y_mm_per_px: 1,
    }

    expect(calibrationScales(calibration)).toEqual({ x: 0.5, y: 1 })
    expect(measureGeometry('edge_length', [[0, 0], [100, 0]], calibration).value).toBe(50)
    expect(measureGeometry('edge_length', [[0, 0], [0, 100]], calibration).value).toBe(100)
  })

  it('normalizes task types without duplicate work', () => {
    expect(normalizeTaskTypes(['linear_dimension', 'bend_angle', 'linear_dimension'])).toEqual([
      'linear_dimension',
      'bend_angle',
    ])
  })

  it('measures a circle geometry from its center and radius', () => {
    expect(measureGeometry('hole_diameter', [], { mm_per_pixel: 0.5 }, {
      kind: 'circle',
      center: [40, 30],
      radius_px: 20,
    })).toEqual({
      value: 20,
      unit: 'mm',
      pixel_value: 40,
      geometry: { kind: 'circle', center: [40, 30], radius_px: 20 },
    })
  })

  it('measures hole center and edge distances from two circles', () => {
    const geometry = {
      kind: 'circle_pair',
      center_a: [0, 0],
      center_b: [100, 0],
      radius_a_px: 10,
      radius_b_px: 10,
    }

    expect(measureGeometry('hole_center_distance', [], { mm_per_pixel: 0.5 }, geometry).value).toBe(50)
    expect(measureGeometry('hole_edge_distance', [], { mm_per_pixel: 0.5 }, geometry).value).toBe(40)
  })

  it('measures hole center to edge from circle and line geometry', () => {
    const result = measureGeometry('hole_center_to_edge', [], { mm_per_pixel: 0.5 }, {
      kind: 'circle_to_edge',
      center: [50, 20],
      edge_a: [0, 100],
      edge_b: [100, 100],
    })

    expect(result.value).toBe(40)
    expect(result.unit).toBe('mm')
  })

  it('measures canonical inclination in degrees', () => {
    expect(measureGeometry('inclination', [[0, 0], [100, 100]], { mm_per_pixel: 0.5 })).toEqual({
      value: 45,
      unit: 'deg',
      pixel_value: null,
    })
  })
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
