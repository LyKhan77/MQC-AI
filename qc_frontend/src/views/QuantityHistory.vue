<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useQuantityHistory } from '../composables/useQuantityHistory.js'
import { checksToCsv } from '../utils/quantity.js'
import { downloadBlob } from '../utils/export.js'

const { t } = useI18n()
const { checks, refresh, remove } = useQuantityHistory()

onMounted(refresh)

const search = ref('')
const verdictFilter = ref('')
const inspecting = ref(null)
const pendingDelete = ref(null)
const deleteError = ref('')
const showExport = ref(false)
const exportFormat = ref('csv')
const exportSel = ref({})
const inspectCrops = computed(() =>
  (inspecting.value?.inputs || []).flatMap((i) => i.crops || []),
)

const filtered = computed(() => {
  let result = checks.value
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter((c) => (c.model_used || '').toLowerCase().includes(q) || (c.id || '').toLowerCase().includes(q))
  }
  if (verdictFilter.value) {
    result = result.filter((c) => c.verdict === verdictFilter.value)
  }
  return result
})

function openExport() {
  exportSel.value = Object.fromEntries(filtered.value.map((c) => [c.id, true]))
  exportFormat.value = 'csv'
  showExport.value = true
}

function selectedChecks() {
  return filtered.value.filter((c) => exportSel.value[c.id])
}

function runExport() {
  const rows = selectedChecks()
  if (!rows.length) return
  if (exportFormat.value === 'csv') {
    downloadBlob(new Blob([checksToCsv(rows)], { type: 'text/csv' }), 'quantity_history.csv')
  } else {
    exportPdf(rows)
  }
  showExport.value = false
}

async function exportPdf(rows) {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF()
  const M = 14
  const right = 196
  let y = 16
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(15)
  doc.text(t('quantity.pdfTitle'), M, y)
  y += 7
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.text(`${t('reports.date')}: ${new Date().toLocaleString('id-ID')}`, M, y)
  y += 6
  const pass = rows.filter((r) => r.verdict === 'pass').length
  const fail = rows.filter((r) => r.verdict === 'fail').length
  doc.text(`${t('quantity.pdfChecks')}: ${rows.length}    ${t('quantity.pass')}: ${pass}    ${t('quantity.fail')}: ${fail}`, M, y)
  y += 4
  doc.setDrawColor(200)
  doc.line(M, y, right, y)
  y += 8

  for (const c of rows) {
    if (y > 250) {
      doc.addPage()
      y = 16
    }
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(11)
    doc.text(String(c.id), M, y)
    y += 6
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    for (const line of [
      `${t('quantity.colDate')}: ${formatDate(c.created_at)}`,
      `${t('quantity.colModel')}: ${c.model_used} @ ${c.confidence_used}`,
      `${t('quantity.total')}: ${c.total_count}`,
      `${t('quantity.expectedTotal')}: ${c.expected_total ?? '-'} +/- ${c.tolerance}`,
      `${t('quantity.colVerdict')}: ${c.verdict}`,
    ]) {
      doc.text(line, M, y)
      y += 5
    }

    const pc = c.per_class_counts || {}
    if (Object.keys(pc).length) {
      doc.setFont('helvetica', 'bold')
      doc.text(t('quantity.perClass'), M, y)
      y += 5
      doc.text(t('quantity.class'), M, y)
      doc.text(t('quantity.count'), M + 75, y)
      y += 2
      doc.setDrawColor(230)
      doc.line(M, y, M + 95, y)
      y += 4
      doc.setFont('helvetica', 'normal')
      for (const k of Object.keys(pc)) {
        doc.text(k, M, y)
        doc.text(String(pc[k]), M + 75, y)
        y += 5
      }
    }

    const crops = (c.inputs || []).flatMap((i) => i.crops || [])
    if (crops.length) {
      const tw = 22
      const th = 18
      let x = M
      if (y + th > 285) {
        doc.addPage()
        y = 16
      }
      for (const u of crops) {
        try {
          doc.addImage(await urlToDataUrl(u), 'PNG', x, y, tw, th)
        } catch {
          // Skip stale crop URLs; export should still finish.
        }
        x += tw + 3
        if (x + tw > right) {
          x = M
          y += th + 3
          if (y + th > 285) {
            doc.addPage()
            y = 16
          }
        }
      }
      y += th + 4
    }
    doc.setDrawColor(230)
    doc.line(M, y, right, y)
    y += 8
  }
  doc.save('quantity_history.pdf')
}

async function urlToDataUrl(url) {
  const res = await fetch(url)
  const blob = await res.blob()
  return await new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = reject
    r.readAsDataURL(blob)
  })
}

function inspect(check) {
  inspecting.value = check
}

function askDelete(check) {
  deleteError.value = ''
  pendingDelete.value = check
}

async function confirmDelete() {
  try {
    await remove(pendingDelete.value.id)
    pendingDelete.value = null
  } catch (e) {
    deleteError.value = e.message || t('common.error')
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('id-ID', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('quantity.historyTitle') }}</h2>
      <p class="page-subtitle">{{ t('quantity.historySubtitle') }}</p>
    </div>

    <div class="filter-bar">
      <input v-model="search" class="text-input" :placeholder="t('quantity.searchPlaceholder')" />
      <select v-model="verdictFilter" class="text-input">
        <option value="">{{ t('quantity.filterAll') }}</option>
        <option value="pass">{{ t('quantity.pass') }}</option>
        <option value="fail">{{ t('quantity.fail') }}</option>
      </select>
      <button class="btn-sm" @click="openExport">{{ t('quantity.export') }}</button>
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('quantity.colId') }}</th>
            <th>{{ t('quantity.colDate') }}</th>
            <th>{{ t('quantity.colModel') }}</th>
            <th>{{ t('quantity.total') }}</th>
            <th>{{ t('quantity.expectedTotal') }}</th>
            <th>{{ t('quantity.colVerdict') }}</th>
            <th>{{ t('batches.columnActions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in filtered" :key="c.id">
            <td class="mono">{{ c.id }}</td>
            <td class="mono">{{ formatDate(c.created_at) }}</td>
            <td>{{ c.model_used }}</td>
            <td class="mono">{{ c.total_count }}</td>
            <td class="mono">{{ c.expected_total ?? '-' }}</td>
            <td><span v-if="c.verdict !== 'none'" class="status-pill" :class="c.verdict === 'pass' ? 'verdict-pass' : 'verdict-fail'">{{ c.verdict === 'pass' ? t('quantity.pass') : t('quantity.fail') }}</span><span v-else>-</span></td>
            <td>
              <button class="btn-sm" @click="inspect(c)">{{ t('quantity.inspect') }}</button>
              <button class="btn-sm btn-danger-sm" @click="askDelete(c)">{{ t('common.delete') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!filtered.length" class="empty-state">{{ t('quantity.noChecks') }}</p>
    </div>

    <div v-if="inspecting" class="dialog-overlay" @click.self="inspecting = null">
      <div class="dialog">
        <h3>{{ t('quantity.inspectTitle') }}</h3>
        <div class="detail-grid mono">
          <span>{{ t('quantity.colModel') }}</span><span>{{ inspecting.model_used }}</span>
          <span>{{ t('quantity.total') }}</span><span>{{ inspecting.total_count }}</span>
          <span>{{ t('quantity.expectedTotal') }}</span><span>{{ inspecting.expected_total ?? '-' }} +/- {{ inspecting.tolerance }}</span>
          <span>{{ t('quantity.colVerdict') }}</span><span>{{ inspecting.verdict }}</span>
        </div>
        <div class="gallery" v-if="inspectCrops.length">
          <img v-for="(u, i) in inspectCrops" :key="i" :src="u" class="gallery-crop" :alt="`crop ${i + 1}`" />
        </div>
        <p v-else class="empty-state">{{ t('quantity.noCrops') }}</p>
        <div class="dialog-actions">
          <button class="btn-sm" @click="inspecting = null">{{ t('common.close') }}</button>
        </div>
      </div>
    </div>

    <div v-if="pendingDelete" class="dialog-overlay" @click.self="pendingDelete = null">
      <div class="dialog">
        <h3>{{ t('quantity.deleteTitle') }}</h3>
        <p>{{ t('quantity.confirmDelete') }} {{ pendingDelete.id }}?</p>
        <p v-if="deleteError" class="status-line error">{{ deleteError }}</p>
        <div class="dialog-actions">
          <button class="btn-sm" @click="pendingDelete = null">{{ t('common.cancel') }}</button>
          <button class="btn-sm btn-primary" @click="confirmDelete">{{ t('common.delete') }}</button>
        </div>
      </div>
    </div>

    <div v-if="showExport" class="dialog-overlay export-dialog" @click.self="showExport = false">
      <div class="dialog">
        <h3>{{ t('quantity.exportTitle') }}</h3>
        <div class="export-format">
          <label><input type="radio" value="csv" v-model="exportFormat" /> CSV</label>
          <label><input type="radio" value="pdf" v-model="exportFormat" /> PDF</label>
        </div>
        <div class="export-list">
          <label v-for="c in filtered" :key="c.id" class="export-row">
            <input type="checkbox" v-model="exportSel[c.id]" />
            <span class="mono">{{ c.id }}</span> - {{ c.total_count }} - {{ c.verdict }}
          </label>
        </div>
        <div class="dialog-actions">
          <button class="btn-sm" @click="showExport = false">{{ t('common.cancel') }}</button>
          <button class="btn-sm btn-primary" @click="runExport">{{ t('quantity.export') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.text-input {
  padding: 8px 12px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-bottom: 2px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 15px;
  outline: none;
  letter-spacing: 0.16px;
}
.text-input:focus {
  border-bottom-color: var(--color-primary);
}
.btn-sm {
  padding: 4px 12px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-primary);
  font-family: var(--font-sans);
  font-size: 13px;
  cursor: pointer;
  margin-right: 4px;
  letter-spacing: 0.16px;
}
.btn-sm:hover {
  background: var(--color-surface-1);
}
.btn-danger-sm {
  color: var(--color-error);
  border-color: var(--color-error);
}
.table-wrap {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
}
.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 13px;
  color: var(--color-ink-muted);
  letter-spacing: 0.32px;
  text-transform: uppercase;
  border-bottom: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
}
.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-hairline);
  color: var(--color-ink);
}
.data-table td.mono {
  font-size: 16px;
  font-weight: 600;
}
.data-table tbody tr:hover {
  background: var(--color-surface-1);
}
.data-table tbody tr:last-child td {
  border-bottom: none;
}
.status-pill {
  display: inline-block;
  padding: 2px 8px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.32px;
}
.empty-state {
  padding: 32px 16px;
  text-align: center;
  color: var(--color-ink-muted);
  font-size: 15px;
}
.verdict-pass { background: var(--color-success); color: var(--color-on-primary); }
.verdict-fail { background: var(--color-error); color: var(--color-on-primary); }
.dialog-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center; z-index: 50; }
.dialog { background: var(--color-canvas); border: 1px solid var(--color-hairline); padding: 20px; min-width: 360px; max-width: 520px; }
.dialog h3 { margin: 0 0 12px; font-weight: 400; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
.btn-primary { background: var(--color-primary); color: var(--color-on-primary); border-color: var(--color-primary); }
.detail-grid { display: grid; grid-template-columns: auto 1fr; gap: 6px 16px; margin-bottom: 12px; font-size: 13px; }
.gallery { display: flex; flex-wrap: wrap; gap: 8px; max-height: 320px; overflow: auto; }
.gallery-crop { width: 96px; height: 80px; object-fit: contain; border: 1px solid var(--color-hairline); background: var(--color-surface-1); }
.status-line.error { color: var(--color-error); }
.mono { font-family: var(--font-mono); }
.export-format { display: flex; gap: 16px; margin-bottom: 12px; font-size: 14px; }
.export-list { max-height: 280px; overflow: auto; display: flex; flex-direction: column; gap: 6px; }
.export-row { display: flex; align-items: center; gap: 8px; font-size: 14px; }
</style>
