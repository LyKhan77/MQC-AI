<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useBatchHistory } from '../composables/useBatchHistory.js'
import { useInspection } from '../composables/useInspection.js'
import { useDefectColor } from '../composables/useDefectColor.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { defectCropBox, fitDimensions, loadImage, renderAnnotated, renderDefectCrop } from '../utils/export.js'

const { t } = useI18n()
const { batches, refresh } = useBatchHistory()
const { batch, loadBatch } = useInspection()
const { log } = useAuditLog()
const { colorFor } = useDefectColor()

const selectedBatchId = ref('')
const generating = ref(false)

onMounted(refresh)

const selectedBatch = computed(() =>
  batches.value.find((b) => b.id === selectedBatchId.value),
)

const summary = computed(() => {
  if (!batch.value) return null
  const total = batch.value.images.length
  const defective = batch.value.images.filter((i) => i.status === 'defect').length
  const clean = total - defective
  const rate = total > 0 ? Math.round((defective / total) * 100) : 0
  return { total, defective, clean, rate }
})

async function selectBatch(id) {
  selectedBatchId.value = id
  if (id) {
    await loadBatch(id)
  }
}

async function generatePDF() {
  if (!batch.value) return
  generating.value = true
  try {
    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF()

    const margin = 20
    const right = 190
    const bottom = 277
    const usableWidth = 170
    const cropPad = 40
    const cropColWidth = 40
    const cropMaxHeight = 26
    const cropGap = 5
    const captionHeight = 5
    const imageEls = new Map()
    let y = margin

    function ensureSpace(height) {
      if (y + height > bottom) {
        doc.addPage()
        y = margin
      }
    }

    doc.setFontSize(18)
    doc.setFont('helvetica', 'bold')
    doc.text(t('reports.reportTitle'), margin, y)
    y += 10

    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.setDrawColor(200)
    doc.line(margin, y, right, y)
    y += 10

    doc.text(`${t('batches.columnName')}: ${batch.value.batch_name}`, margin, y)
    y += 6
    doc.text(`${t('reports.date')}: ${new Date().toLocaleString('id-ID')}`, margin, y)
    y += 6
    if (selectedBatch.value) {
      doc.text(`${t('batches.columnCamera')}: ${selectedBatch.value.cameraName}`, margin, y)
      y += 6
      doc.text(`${t('settings.detectionModel')}: ${selectedBatch.value.modelInfo.detection}`, margin, y)
      y += 6
    }

    y += 6
    doc.setFont('helvetica', 'bold')
    doc.text(t('reports.summary'), margin, y)
    y += 8
    doc.setFont('helvetica', 'normal')

    if (summary.value) {
      doc.text(`${t('reports.totalImages')}: ${summary.value.total}`, margin, y)
      y += 6
      doc.text(`${t('reports.clean')}: ${summary.value.clean}`, margin, y)
      y += 6
      doc.text(`${t('reports.defective')}: ${summary.value.defective}`, margin, y)
      y += 6
      doc.text(`${t('reports.defectRate')}: ${summary.value.rate}%`, margin, y)
      y += 10
    }

    doc.setFont('helvetica', 'bold')
    doc.text(t('reports.defectDetails'), margin, y)
    y += 8
    doc.setFont('helvetica', 'normal')

    const imagesWithDefects = batch.value.images.filter((img) => img.defects.length > 0)
    if (!imagesWithDefects.length) {
      ensureSpace(8)
      doc.text(t('qc.noDefects'), margin, y)
      y += 8
    }

    for (const img of imagesWithDefects) {
      let imgEl = imageEls.get(img.id)
      if (!imgEl) {
        try {
          imgEl = await loadImage(img.url)
          imageEls.set(img.id, imgEl)
        } catch (e) {
          console.warn('Report image skipped:', img.url, e)
          continue
        }
      }

      const annotated = renderAnnotated(imgEl, img, colorFor)
      ensureSpace(12)
      doc.setFont('helvetica', 'bold')
      doc.text(`${img.filename}  (${img.defects.length})`, margin, y, { maxWidth: usableWidth })
      y += 7
      doc.setFont('helvetica', 'normal')

      let x = margin
      let rowHeight = 0
      for (const d of img.defects) {
        const box = defectCropBox(d.polygon, cropPad, img.width, img.height)
        if (box.w <= 0 || box.h <= 0) continue
        const { w, h } = fitDimensions(box.w, box.h, cropColWidth, cropMaxHeight)

        if (x !== margin && x + cropColWidth > right) {
          y += rowHeight + captionHeight + cropGap
          x = margin
          rowHeight = 0
        }
        if (y + h + captionHeight > bottom) {
          doc.addPage()
          y = margin
          x = margin
          rowHeight = 0
        }

        const cropCanvas = renderDefectCrop(annotated, box)
        doc.addImage(cropCanvas, 'PNG', x, y, w, h)
        doc.setFontSize(8)
        doc.text(`${d.type} ${Math.round(d.confidence * 100)}%`, x, y + h + 4, { maxWidth: cropColWidth })
        doc.setFontSize(10)
        rowHeight = Math.max(rowHeight, h)
        x += cropColWidth + cropGap
      }

      y += rowHeight ? rowHeight + captionHeight + 7 : 2
      ensureSpace(4)
      doc.line(margin, y, right, y)
      y += 8
    }

    y += 7
    ensureSpace(20)
    doc.text(`${t('reports.reviewedBy')}: ____________________`, margin, y)
    doc.text(`${t('reports.approvedBy')}: ____________________`, margin + 80, y)
    y += 10
    doc.text(`[  ] ${t('reports.pass')}     [  ] ${t('reports.fail')}`, margin, y)

    const filename = `${batch.value.batch_name}_report.pdf`
    doc.save(filename)
    log('REPORT_GENERATED', `Generated PDF report: ${filename}`)
  } catch (e) {
    console.error('Report generation failed:', e)
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p class="page-subtitle">{{ t('reports.subtitle') }}</p>
    </div>

    <div class="report-layout">
      <div class="report-config">
        <label class="field-label">{{ t('reports.selectBatch') }}</label>
        <select v-model="selectedBatchId" @change="selectBatch(selectedBatchId)" class="text-input">
          <option value="">-- {{ t('common.noResults') }} --</option>
          <option v-for="b in batches" :key="b.id" :value="b.id">{{ b.name }}</option>
        </select>

        <div v-if="batch" class="report-preview">
          <h3>{{ t('reports.summary') }}</h3>
          <div class="stat-grid">
            <div class="stat-card">
              <span class="stat-label">{{ t('reports.totalImages') }}</span>
              <span class="stat-value">{{ summary.total }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">{{ t('reports.clean') }}</span>
              <span class="stat-value success">{{ summary.clean }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">{{ t('reports.defective') }}</span>
              <span class="stat-value error">{{ summary.defective }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">{{ t('reports.defectRate') }}</span>
              <span class="stat-value">{{ summary.rate }}%</span>
            </div>
          </div>

          <h3>{{ t('reports.defectDetails') }}</h3>
          <div class="defect-list">
            <div v-for="img in batch.images" :key="img.id" class="defect-img-row">
              <span class="mono filename">{{ img.filename }}</span>
              <div class="defect-tags">
                <span v-for="d in img.defects" :key="d.id" class="defect-tag" :style="{ borderColor: colorFor(d.type) }">
                  <span class="dot" :style="{ background: colorFor(d.type) }"></span>
                  {{ d.type }} ({{ Math.round(d.confidence * 100) }}%)
                </span>
                <span v-if="!img.defects.length" class="clean-tag">{{ t('qc.noDefects') }}</span>
              </div>
            </div>
          </div>

          <button class="btn-primary" :disabled="generating" @click="generatePDF">
            {{ generating ? t('reports.generating') : t('reports.generate') }}
          </button>
        </div>

        <p v-else class="empty-hint">{{ t('reports.selectBatch') }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-layout {
  max-width: 720px;
}
.field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 6px;
  letter-spacing: 0.16px;
}
.text-input {
  width: 100%;
  padding: 8px 12px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-bottom: 2px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 14px;
  outline: none;
  margin-bottom: 24px;
  letter-spacing: 0.16px;
}
.text-input:focus {
  border-bottom-color: var(--color-primary);
}
.report-preview {
  border: 1px solid var(--color-hairline);
  padding: 24px;
}
.report-preview h3 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
  text-transform: uppercase;
}
.report-preview h3:not(:first-child) {
  margin-top: 24px;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
}
.stat-label {
  font-size: 12px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.stat-value {
  font-size: 24px;
  font-weight: 300;
  color: var(--color-ink);
  font-family: var(--font-mono);
}
.stat-value.success {
  color: var(--color-success);
}
.stat-value.error {
  color: var(--color-error);
}
.defect-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.defect-img-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-hairline);
}
.defect-img-row:last-child {
  border-bottom: none;
}
.filename {
  font-size: 13px;
  color: var(--color-ink-muted);
  min-width: 160px;
}
.defect-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
}
.defect-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 12px;
  border: 1px solid;
  border-radius: 0;
  letter-spacing: 0.16px;
  text-transform: capitalize;
}
.dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
}
.clean-tag {
  font-size: 12px;
  color: var(--color-success);
  letter-spacing: 0.16px;
}
.btn-primary {
  margin-top: 24px;
  padding: 12px 16px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  font-family: var(--font-sans);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.btn-primary:hover {
  background: var(--color-primary-hover);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: default;
}
.empty-hint {
  color: var(--color-ink-subtle);
  font-size: 14px;
}
.mono {
  font-family: var(--font-mono);
}
</style>
