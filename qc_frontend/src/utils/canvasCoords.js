function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

export function toImageCoords(clientX, clientY, rect, imageW, imageH) {
  const x = ((clientX - rect.left) / rect.width) * imageW
  const y = ((clientY - rect.top) / rect.height) * imageH
  return {
    x: Math.round(clamp(x, 0, imageW)),
    y: Math.round(clamp(y, 0, imageH)),
  }
}

export function normalizeBox(x1, y1, x2, y2) {
  return [Math.min(x1, x2), Math.min(y1, y2), Math.max(x1, x2), Math.max(y1, y2)]
}
