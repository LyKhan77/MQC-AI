const MIN_CONFIDENCE = 0.5

export function calibrationScales(calibration = {}) {
  const legacy = Number(calibration.mm_per_pixel)
  const x = Number(calibration.scale_x_mm_per_px ?? legacy)
  const y = Number(calibration.scale_y_mm_per_px ?? legacy)
  if (!(x > 0) || !(y > 0)) throw new Error('invalid calibration')
  return { x, y }
}

function scalarCalibrationScale(calibration) {
  const { x, y } = calibrationScales(calibration)
  return (x + y) / 2
}

export function normalizeTaskTypes(taskTypes, fallback = 'linear_dimension') {
  const values = Array.isArray(taskTypes) && taskTypes.length ? taskTypes : [fallback]
  return [...new Set(values)]
}

export function buildBendGeometry(firstEdge, secondEdge) {
  const first = firstEdge?.support_points || firstEdge?.points || []
  const second = secondEdge?.support_points || secondEdge?.points || []
  if (first.length < 2 || second.length < 2) throw new Error('bend edges require two support points')
  if (firstEdge.id && firstEdge.id === secondEdge.id) throw new Error('bend edges must be different')
  const firstA = first[0]
  const firstB = first.at(-1)
  const secondA = second[0]
  const secondB = second.at(-1)
  const firstDirection = [Number(firstB[0]) - Number(firstA[0]), Number(firstB[1]) - Number(firstA[1])]
  const secondDirection = [Number(secondB[0]) - Number(secondA[0]), Number(secondB[1]) - Number(secondA[1])]
  const determinant = firstDirection[0] * secondDirection[1] - firstDirection[1] * secondDirection[0]
  if (Math.abs(determinant) < 1e-6) throw new Error('bend support lines are parallel')
  const offset = [Number(secondA[0]) - Number(firstA[0]), Number(secondA[1]) - Number(firstA[1])]
  const parameter = (offset[0] * secondDirection[1] - offset[1] * secondDirection[0]) / determinant
  const vertex = [Number(firstA[0]) + parameter * firstDirection[0], Number(firstA[1]) + parameter * firstDirection[1]]
  const rayA = [(Number(firstA[0]) + Number(firstB[0])) / 2, (Number(firstA[1]) + Number(firstB[1])) / 2]
  const rayB = [(Number(secondA[0]) + Number(secondB[0])) / 2, (Number(secondA[1]) + Number(secondB[1])) / 2]
  const firstRay = [rayA[0] - vertex[0], rayA[1] - vertex[1]]
  const secondRay = [rayB[0] - vertex[0], rayB[1] - vertex[1]]
  const firstLength = Math.hypot(...firstRay)
  const secondLength = Math.hypot(...secondRay)
  if (!firstLength || !secondLength) throw new Error('bend support rays are too short')
  const cosine = Math.max(-1, Math.min(1, (firstRay[0] * secondRay[0] + firstRay[1] * secondRay[1]) / (firstLength * secondLength)))
  return {
    kind: 'bend_angle',
    vertex,
    ray_a: rayA,
    ray_b: rayB,
    logical_edge_ids: [firstEdge.id, secondEdge.id],
    angle_deg: Math.acos(cosine) * 180 / Math.PI,
  }
}

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
  if (type === 'corner_radius' && geometry?.kind === 'corner_arc') {
    const value = Number(geometry.radius_mm)
    if (!(value > 0)) throw new Error('corner radius must be positive')
    return { value, unit: 'mm', pixel_value: null, geometry }
  }
  if (type === 'bend_angle' && geometry?.kind === 'bend_angle') {
    const value = Number(geometry.angle_deg)
    if (!(value >= 0 && value <= 180)) throw new Error('bend angle must be between 0 and 180 degrees')
    return { value, unit: 'deg', pixel_value: null, geometry }
  }
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
    const scale = scalarCalibrationScale(calibration)
    const edgeDistance = centerDistance - Number(geometry.radius_a_px) - Number(geometry.radius_b_px)
    const pixelValue = type === 'hole_edge_distance' ? edgeDistance : centerDistance
    if (type !== 'hole_center_distance' && type !== 'hole_edge_distance') throw new Error('unsupported circle pair measurement type')
    if (pixelValue < 0) throw new Error('hole edge distance cannot be negative')
    return { value: pixelValue * scale, unit: 'mm', pixel_value: pixelValue, geometry }
  }
  if (type === 'hole_center_to_edge' && geometry?.kind === 'circle_to_edge') {
    const scale = scalarCalibrationScale(calibration)
    const pixelValue = distanceToSegment(geometry.center, geometry.edge_a, geometry.edge_b)
    return { value: pixelValue * scale, unit: 'mm', pixel_value: pixelValue, geometry }
  }
  if (type === 'hole_diameter' && geometry?.kind === 'circle') {
      const radius = Number(geometry.radius_px)
      if (!(radius > 0)) throw new Error('circle radius must be positive')
      const center = [Number(geometry.center[0]), Number(geometry.center[1])]
      const scale = scalarCalibrationScale(calibration)
      return {
        value: radius * 2 * scale,
        unit: 'mm',
        pixel_value: radius * 2,
        geometry: { kind: 'circle', center, radius_px: radius },
      }
  }
  if (points.length !== 2) throw new Error('linear measurement requires two points')
  const [first, second] = points
  const { x, y } = calibrationScales(calibration)
  const dx = (Number(second[0]) - Number(first[0])) * x
  const dy = (Number(second[1]) - Number(first[1])) * y
  const pixelValue = distance(first, second)
  const multiplier = type === 'hole_diameter' ? 2 : 1
  return { value: Math.hypot(dx, dy) * multiplier, unit: 'mm', pixel_value: pixelValue }
}

export function evaluateMeasurementItem(item, calibrationValid, calibrationReason = 'invalid_calibration') {
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
  if (item.quality_reason) return { ...base, min, max, deviation: measured - nominal, status: 'REVIEW', reason: item.quality_reason }
  if (!calibrationValid) return { ...base, min, max, deviation: measured - nominal, status: 'REVIEW', reason: calibrationReason }
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
