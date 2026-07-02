import { describe, expect, it } from 'vitest'
import { cursorForState } from './cursor.js'

describe('cursorForState', () => {
  it('uses crosshair while drawing', () => {
    expect(cursorForState({ drawing: true, dragging: true, editMode: true, overDefect: true })).toBe('crosshair')
  })

  it('uses grabbing while dragging outside drawing', () => {
    expect(cursorForState({ drawing: false, dragging: true, editMode: false, overDefect: true })).toBe('grabbing')
  })

  it('uses pointer over selectable polygons', () => {
    expect(cursorForState({ drawing: false, dragging: false, editMode: false, overDefect: true })).toBe('pointer')
  })

  it('uses grab as the default pannable state', () => {
    expect(cursorForState({ drawing: false, dragging: false, editMode: true, overDefect: false })).toBe('grab')
  })

  it('uses grabbing while reshaping a vertex', () => {
    expect(cursorForState({ reshaping: true, overHandle: true })).toBe('grabbing')
  })

  it('uses grab when hovering a reshape handle', () => {
    expect(cursorForState({ overHandle: true })).toBe('grab')
  })
})
