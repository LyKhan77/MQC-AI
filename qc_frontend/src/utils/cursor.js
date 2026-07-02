export function cursorForState({ drawing, dragging, overDefect, overHandle, reshaping }) {
  if (reshaping) return 'grabbing'
  if (drawing) return 'crosshair'
  if (dragging) return 'grabbing'
  if (overHandle) return 'grab'
  if (overDefect) return 'pointer'
  return 'grab'
}
