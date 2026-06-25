import { polygonBBox } from './defect.js'

// Resolusi CSS var warna defect ke nilai nyata untuk dipakai di <canvas>.
const FALLBACK = '#557799'
function resolveColor(type) {
  const map = {
    scratch: '#FFD700', porosity: '#FF24BD', spatter: '#00E5FF', color: '#FFA500',
  }
  return map[type] ?? FALLBACK
}

export function defectsBBox(defects, pad, maxW, maxH) {
  if (!defects.length) return { x: 0, y: 0, w: maxW, h: maxH }
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const d of defects) {
    const b = polygonBBox(d.polygon)
    minX = Math.min(minX, b.x)
    minY = Math.min(minY, b.y)
    maxX = Math.max(maxX, b.x + b.w)
    maxY = Math.max(maxY, b.y + b.h)
  }
  const x = Math.max(0, minX - pad)
  const y = Math.max(0, minY - pad)
  const x2 = Math.min(maxW, maxX + pad)
  const y2 = Math.min(maxH, maxY + pad)
  return { x, y, w: x2 - x, h: y2 - y }
}

// Gambar full-res + overlay poligon. `imgEl` = HTMLImageElement yang sudah load.
export function renderAnnotated(imgEl, image) {
  const canvas = document.createElement('canvas')
  canvas.width = image.width
  canvas.height = image.height
  const ctx = canvas.getContext('2d')
  ctx.drawImage(imgEl, 0, 0, image.width, image.height)
  for (const d of image.defects) {
    const c = resolveColor(d.type)
    ctx.beginPath()
    d.polygon.forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)))
    ctx.closePath()
    ctx.lineWidth = 2
    ctx.strokeStyle = c
    ctx.globalAlpha = 0.15
    ctx.fillStyle = c
    ctx.fill()
    ctx.globalAlpha = 1
    ctx.stroke()
  }
  return canvas
}

export function downloadCanvas(canvas, filename) {
  canvas.toBlob((blob) => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    a.click()
    URL.revokeObjectURL(a.href)
  }, 'image/png')
}
