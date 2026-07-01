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
