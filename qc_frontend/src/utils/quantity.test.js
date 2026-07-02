import { describe, it, expect } from 'vitest'
import { perClassFromDetections, addCounts, totalOf, computeVerdict, checksToCsv } from './quantity.js'

describe('quantity utils', () => {
  it('counts detections per label', () => {
    expect(perClassFromDetections([{ label: 'a' }, { label: 'a' }, { label: 'b' }]))
      .toEqual({ a: 2, b: 1 })
  })

  it('adds two per-class maps', () => {
    expect(addCounts({ a: 2 }, { a: 1, b: 3 })).toEqual({ a: 3, b: 3 })
  })

  it('totals a per-class map', () => {
    expect(totalOf({ a: 2, b: 3 })).toBe(5)
  })

  it('returns none when no expectation set', () => {
    expect(computeVerdict({ total: 5, perClass: { a: 5 } })).toBe('none')
  })

  it('passes/fails on expected total within tolerance', () => {
    expect(computeVerdict({ total: 10, perClass: {}, expectedTotal: 12, tolerance: 2 })).toBe('pass')
    expect(computeVerdict({ total: 8, perClass: {}, expectedTotal: 12, tolerance: 2 })).toBe('fail')
  })

  it('passes only when every expected per-class is within tolerance', () => {
    expect(computeVerdict({ total: 5, perClass: { a: 3, b: 2 }, expectedPerClass: { a: 3, b: 2 } })).toBe('pass')
    expect(computeVerdict({ total: 5, perClass: { a: 3, b: 1 }, expectedPerClass: { a: 3, b: 2 } })).toBe('fail')
  })

  it('builds CSV with a header and a row per check', () => {
    const csv = checksToCsv([
      { created_at: '2026-07-02T10:00:00', source_type: 'image', model_used: 'm.pt', total_count: 5, expected_total: 5, verdict: 'pass', per_class_counts: { a: 5 } },
    ])
    const lines = csv.trim().split('\n')
    expect(lines[0]).toContain('created_at')
    expect(lines[1]).toContain('pass')
    expect(lines[1]).toContain('5')
  })
})
