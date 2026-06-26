import { ref } from 'vue'
import { MOCK } from '../utils/mockData.js'

const STORAGE_KEY = 'mqc-audit-log'
const logs = ref([])

function load() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      logs.value = JSON.parse(saved)
      return
    } catch {
      // fallthrough
    }
  }
  logs.value = [...MOCK.auditLogs]
  persist()
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(logs.value.slice(0, 500)))
}

load()

function log(action, detail, user = 'inspector@gspemail.com') {
  const id = `log-${String(Date.now()).slice(-8)}`
  logs.value.unshift({
    id,
    timestamp: new Date().toISOString(),
    user,
    action,
    detail,
  })
  persist()
}

export function useAuditLog() {
  return { logs, log }
}
