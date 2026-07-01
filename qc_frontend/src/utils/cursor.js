export function cursorForState({ drawing, dragging, overDefect }) {
  if (drawing) return 'crosshair'
  if (dragging) return 'grabbing'
  if (overDefect) return 'pointer'
  return 'grab'
}
