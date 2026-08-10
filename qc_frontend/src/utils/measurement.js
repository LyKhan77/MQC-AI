const MIN_CONFIDENCE = 0.5

function distance(a, b) {
  return Math.hypot(Number(b[0]) - Number(a[0]), Number(b[1]) - Number(a[1]))
}

function distanceToSegment(point, a, b) {
  const dx = Number(b[0]) - Number(a[0])
  const dy = Number(b[1]) - Number(a[1])
  const lengthSquared = dx * dx + dy * dy
  if (!lengthSquared) throw new Error('edge points must be different')
  const ratio = Math.max(0, Math.min(1, ((Number(point[0]) - Number(a[0])) * dx + (Number(point[1]) - Number(a[1])) * dy) / lengthSquared))
  return distance(point, [Number(a[0]) + ratio * dx, Number(a[1]) + ratio * dy])
}

function angle(points) {
  const first = [Number(points[1][0]) - Number(points[0][0]), Number(points[1][1]) - Number(points[0][1])]
  const second = [Number(points[3][0]) - Number(points[2][0]), Number(points[3][1]) - Number(points[2][1])]
  const firstLength = Math.hypot(...first)
  const secondLength = Math.hypot(...second)
  if (!firstLength || !secondLength) throw new Error('angle lines must have length')
  const cosine = Math.max(-1, Math.min(1, (first[0] * second[0] + first[1] * second[1]) / (firstLength * secondLength)))
  return Math.acos(cosine) * 180 / Math.PI
}

export function measureGeometry(type, points, calibration = {}, geometry = null) {
  if (type === 'angle' || type === 'bend_angle') {
    if (points.length !== 4) throw new Error('angle requires four points')
    return { value: angle(points), unit: 'deg', pixel_value: null }
  }
  if (type === 'inclination') {
    if (points.length !== 2) throw new Error('inclination requires two points')
    const radians = Math.atan2(Number(points[1][1]) - Number(points[0][1]), Number(points[1][0]) - Number(points[0][0]))
    const raw = Math.abs(radians * 180 / Math.PI)
    return { value: raw <= 90 ? raw : 180 - raw, unit: 'deg', pixel_value: null }
  }
  if (geometry?.kind === 'circle_pair') {
    const centerDistance = distance(geometry.center_a, geometry.center_b)
    const scale = Number(calibration.mm_per_pixel)
    if (!(scale > 0)) throw new Error('invalid calibration')
    const edgeDistance = centerDistance - Number(geometry.radius_a_px) - Number(geometry.radius_b_px)
    const pixelValue = type === 'hole_edge_distance' ? edgeDistance : centerDistance
    if (type !== 'hole_center_distance' && type !== 'hole_edge_distance') throw new Error('unsupported circle pair measurement type')
    if (pixelValue < 0) throw new Error('hole edge distance cannot be negative')
    return { value: pixelValue * scale, unit: 'mm', pixel_value: pixelValue, geometry }
  }
  if (type === 'hole_center_to_edge' && geometry?.kind === 'circle_to_edge') {
    const scale = Number(calibration.mm_per_pixel)
    if (!(scale > 0)) throw new Error('invalid calibration')
    const pixelValue = distanceToSegment(geometry.center, geometry.edge_a, geometry.edge_b)
    return { value: pixelValue * scale, unit: 'mm', pixel_value: pixelValue, geometry }
  }
  if (type === 'hole_diameter' && geometry?.kind === 'circle') {
      const radius = Number(geometry.radius_px)
      if (!(radius > 0)) throw new Error('circle radius must be positive')
      const center = [Number(geometry.center[0]), Number(geometry.center[1])]
      const scale = Number(calibration.mm_per_pixel)
      if (!(scale > 0)) throw new Error('invalid calibration')
      return {
        value: radius * 2 * scale,
        unit: 'mm',
        pixel_value: radius * 2,
        geometry: { kind: 'circle', center, radius_px: radius },
      }
  }
  if (points.length !== 2) throw new Error('linear measurement requires two points')
  const pixelValue = distance(points[0], points[1])
  const scale = Number(calibration.mm_per_pixel)
  if (!(scale > 0)) throw new Error('invalid calibration')
  const multiplier = type === 'hole_diameter' ? 2 : 1
  return { value: pixelValue * scale * multiplier, unit: 'mm', pixel_value: pixelValue }
}

export function evaluateMeasurementItem(item, calibrationValid) {
  const measured = Number(item.measured)
  const nominal = item.nominal === null || item.nominal === undefined || item.nominal === '' ? null : Number(item.nominal)
  const tolerance = item.tolerance === null || item.tolerance === undefined || item.tolerance === '' ? null : Number(item.tolerance)
  const base = { ...item, measured, nominal, tolerance }
  if (nominal === null || tolerance === null) {
    return { ...base, min: null, max: null, deviation: null, status: 'REVIEW', reason: 'missing_nominal_or_tolerance' }
  }
  if (tolerance < 0) throw new Error('tolerance must be non-negative')
  const min = nominal - tolerance
  const max = nominal + tolerance
  if (!calibrationValid) return { ...base, min, max, deviation: measured - nominal, status: 'REVIEW', reason: 'invalid_calibration' }
  if (Number(item.confidence ?? 0) < MIN_CONFIDENCE) return { ...base, min, max, deviation: measured - nominal, status: 'REVIEW', reason: 'low_confidence' }
  const status = measured >= min && measured <= max ? 'PASS' : 'FAIL'
  return { ...base, min, max, deviation: measured - nominal, status, reason: status === 'PASS' ? '' : 'outside_tolerance' }
}

export function summarizeMeasurement(items, readiness) {
  if (readiness !== 'ready') return 'REVIEW'
  const statuses = (items || []).map((item) => item.status)
  if (!statuses.length || statuses.includes('REVIEW')) return 'REVIEW'
  if (statuses.includes('FAIL')) return 'FAIL'
  return statuses.every((status) => status === 'PASS') ? 'PASS' : 'REVIEW'
}
