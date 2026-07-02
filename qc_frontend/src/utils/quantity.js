export function perClassFromDetections(detections) {
  const counts = {}
  for (const d of detections || []) {
    counts[d.label] = (counts[d.label] || 0) + 1
  }
  return counts
}

export function addCounts(a, b) {
  const out = { ...(a || {}) }
  for (const k of Object.keys(b || {})) {
    out[k] = (out[k] || 0) + b[k]
  }
  return out
}

export function totalOf(perClass) {
  return Object.values(perClass || {}).reduce((sum, n) => sum + Number(n || 0), 0)
}

function isSet(v) {
  return v !== null && v !== undefined && v !== ''
}

export function computeVerdict({ total, perClass, expectedTotal, expectedPerClass, tolerance = 0 }) {
  const tol = Number(tolerance) || 0
  const hasTotal = isSet(expectedTotal)
  const hasPer = expectedPerClass && Object.keys(expectedPerClass).length > 0
  if (!hasTotal && !hasPer) return 'none'
  let pass = true
  if (hasTotal && Math.abs(Number(total) - Number(expectedTotal)) > tol) pass = false
  if (hasPer) {
    for (const k of Object.keys(expectedPerClass)) {
      const actual = (perClass && perClass[k]) || 0
      if (Math.abs(actual - Number(expectedPerClass[k])) > tol) pass = false
    }
  }
  return pass ? 'pass' : 'fail'
}

const CSV_COLUMNS = ['created_at', 'source_type', 'model_used', 'total_count', 'expected_total', 'verdict', 'per_class_counts']

function csvCell(value) {
  const s = typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value ?? '')
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

export function checksToCsv(checks) {
  const header = CSV_COLUMNS.join(',')
  const rows = (checks || []).map((c) => CSV_COLUMNS.map((col) => csvCell(c[col])).join(','))
  return [header, ...rows].join('\n')
}
