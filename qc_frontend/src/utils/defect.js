const COLOR_MAP = {
  scratch: 'var(--defect-scratch)',
  porosity: 'var(--defect-porosity)',
  spatter: 'var(--defect-spatter)',
  color: 'var(--defect-color)',
}

export function defectColor(type) {
  return COLOR_MAP[type] ?? 'var(--text-muted)'
}

export function polygonBBox(points) {
  const xs = points.map((p) => p[0])
  const ys = points.map((p) => p[1])
  const x = Math.min(...xs)
  const y = Math.min(...ys)
  return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y }
}
