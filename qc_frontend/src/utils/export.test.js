import { describe, it, expect } from 'vitest'
import { stripExt, fullFilename, cropFilename, defectCropBox, fitDimensions } from './export.js'

describe('stripExt', () => {
  it('removes the last extension', () => {
    expect(stripExt('img01.png')).toBe('img01')
  })
  it('keeps only the last extension when multiple dots are present', () => {
    expect(stripExt('a.b.png')).toBe('a.b')
  })
  it('returns the name unchanged when there is no extension', () => {
    expect(stripExt('no_extension')).toBe('no_extension')
  })
})

describe('fullFilename', () => {
  it('appends _full.png to the base name', () => {
    expect(fullFilename('img01.png')).toBe('img01_full.png')
  })
})

describe('cropFilename', () => {
  it('builds {base}_{type}_{index}.png', () => {
    expect(cropFilename('img01.png', 'scratch', 1)).toBe('img01_scratch_1.png')
    expect(cropFilename('img01.png', 'scratch', 2)).toBe('img01_scratch_2.png')
    expect(cropFilename('img01.png', 'porosity', 1)).toBe('img01_porosity_1.png')
  })
})

describe('defectCropBox', () => {
  const square = [[100, 100], [200, 100], [200, 200], [100, 200]]

  it('pads the polygon bbox', () => {
    const b = defectCropBox(square, 10, 1000, 1000)
    expect(b).toEqual({ x: 90, y: 90, w: 120, h: 120 })
  })

  it('clamps padding at the 0 edge', () => {
    const near0 = [[5, 5], [50, 5], [50, 50], [5, 50]]
    const b = defectCropBox(near0, 20, 1000, 1000)
    expect(b).toEqual({ x: 0, y: 0, w: 70, h: 70 })
  })

  it('clamps padding at the maxW/maxH edge', () => {
    const nearEdge = [[80, 80], [95, 80], [95, 95], [80, 95]]
    const b = defectCropBox(nearEdge, 20, 100, 100)
    expect(b).toEqual({ x: 60, y: 60, w: 40, h: 40 })
  })
})

describe('fitDimensions', () => {
  it('fits landscape boxes by width', () => {
    expect(fitDimensions(800, 400, 40, 40)).toEqual({ w: 40, h: 20 })
  })

  it('fits portrait boxes by height', () => {
    expect(fitDimensions(400, 800, 40, 40)).toEqual({ w: 20, h: 40 })
  })

  it('leaves already-small boxes unchanged', () => {
    expect(fitDimensions(20, 10, 40, 40)).toEqual({ w: 20, h: 10 })
  })

  it('preserves aspect ratio when both axes exceed the maximum', () => {
    const fitted = fitDimensions(600, 300, 50, 20)
    expect(fitted.w).toBe(40)
    expect(fitted.h).toBe(20)
    expect(fitted.w / fitted.h).toBe(2)
  })
})
