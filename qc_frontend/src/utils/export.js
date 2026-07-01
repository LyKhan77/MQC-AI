import { polygonBBox } from './defect.js'

export function stripExt(filename) {
  const idx = filename.lastIndexOf('.')
  return idx > 0 ? filename.slice(0, idx) : filename
}

export function fullFilename(imageFilename) {
  return `${stripExt(imageFilename)}_full.png`
}

export function cropFilename(imageFilename, type, index) {
  return `${stripExt(imageFilename)}_${type}_${index}.png`
}

export function defectCropBox(polygon, pad, maxW, maxH) {
  const b = polygonBBox(polygon)
  const x = Math.max(0, b.x - pad)
  const y = Math.max(0, b.y - pad)
  const x2 = Math.min(maxW, b.x + b.w + pad)
  const y2 = Math.min(maxH, b.y + b.h + pad)
  return { x, y, w: x2 - x, h: y2 - y }
}

export function renderAnnotated(imgEl, image, colorFor) {
  const canvas = document.createElement('canvas')
  canvas.width = image.width
  canvas.height = image.height
  const ctx = canvas.getContext('2d')
  ctx.drawImage(imgEl, 0, 0, image.width, image.height)
  for (const d of image.defects) {
    const c = colorFor(d.type)
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

export function renderDefectCrop(annotatedCanvas, box) {
  const crop = document.createElement('canvas')
  crop.width = box.w
  crop.height = box.h
  crop.getContext('2d').drawImage(annotatedCanvas, box.x, box.y, box.w, box.h, 0, 0, box.w, box.h)
  return crop
}

export function canvasToBlob(canvas) {
  return new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))
}

export function downloadBlob(blob, filename) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

export function downloadCanvas(canvas, filename) {
  canvas.toBlob((blob) => downloadBlob(blob, filename), 'image/png')
}
