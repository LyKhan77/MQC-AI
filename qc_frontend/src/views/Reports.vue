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
const reportMode = ref('defect-only')

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
    const modeLabel = reportMode.value === 'full-image'
      ? t('reports.fullImage')
      : t('reports.defectOnly')
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

    function newPage() {
      doc.addPage()
      y = margin
    }

    function getAnnotated(img) {
      return imageEls.get(img.id) || loadImage(img.url).then((imgEl) => {
        const annotated = renderAnnotated(imgEl, img, colorFor)
        imageEls.set(img.id, annotated)
        return annotated
      })
    }

    function setBodyFont(size = 10, bold = false) {
      doc.setFontSize(size)
      doc.setFont('helvetica', bold ? 'bold' : 'normal')
      doc.setTextColor(22, 22, 22)
    }

    function hexRgb(color) {
      const value = String(color || '').replace('#', '')
      if (!/^[0-9a-f]{6}$/i.test(value)) return [22, 22, 22]
      return [0, 2, 4].map((index) => parseInt(value.slice(index, index + 2), 16))
    }

    function drawDefectTable(img) {
      const columns = [
        { label: t('reports.no'), x: margin, width: 8 },
        { label: t('reports.defectType'), x: margin + 8, width: 47 },
        { label: t('reports.category'), x: margin + 55, width: 38 },
        { label: t('reports.confidence'), x: margin + 93, width: 25 },
        { label: t('reports.location'), x: margin + 118, width: 52 },
      ]
      const rowHeight = 7

      function header() {
        doc.setFillColor(22, 22, 22)
        doc.rect(margin, y - 4.5, usableWidth, rowHeight, 'F')
        doc.setTextColor(255, 255, 255)
        doc.setFontSize(8)
        doc.setFont('helvetica', 'bold')
        columns.forEach((column) => doc.text(column.label, column.x + 2, y))
        y += rowHeight
      }

      if (!img.defects.length) {
        setBodyFont(9)
        doc.text(t('reports.noDefectsOnImage'), margin, y)
        y += 7
        return
      }

      ensureSpace(rowHeight * 2)
      header()
      img.defects.forEach((defect, index) => {
        if (y + rowHeight > bottom) {
          newPage()
          header()
        }
        if (index % 2 === 0) {
          doc.setFillColor(244, 244, 244)
          doc.rect(margin, y - 4.5, usableWidth, rowHeight, 'F')
        }
        const box = defectCropBox(defect.polygon, 0, img.width, img.height)
        const location = `${Math.round(box.x)},${Math.round(box.y)} ${Math.round(box.w)}x${Math.round(box.h)}`
        const [r, g, b] = hexRgb(colorFor(defect.type))
        doc.setFillColor(r, g, b)
        doc.rect(margin + 2, y - 3.2, 2.5, 2.5, 'F')
        setBodyFont(8)
        doc.text(String(index + 1), margin + 2, y)
        doc.text(String(defect.type || '-').slice(0, 26), margin + 12, y)
        doc.text(String(defect.category || '-').slice(0, 20), margin + 57, y)
        doc.text(`${Math.round(Number(defect.confidence || 0) * 100)}%`, margin + 95, y)
        doc.text(location, margin + 120, y)
        y += rowHeight
      })
    }

    function writeReportHeader() {
      setBodyFont(18, true)
      doc.text(t('reports.reportTitle'), margin, y)
      y += 10

      setBodyFont(10)
      doc.setDrawColor(200)
      doc.line(margin, y, right, y)
      y += 10

      doc.text(`${t('batches.columnName')}: ${batch.value.batch_name}`, margin, y)
      y += 6
      doc.text(`${t('reports.date')}: ${new Date().toLocaleString('id-ID')}`, margin, y)
      y += 6
      doc.text(`${t('reports.reportMode')}: ${modeLabel}`, margin, y)
      y += 6
      if (selectedBatch.value) {
        doc.text(`${t('batches.columnCamera')}: ${selectedBatch.value.cameraName}`, margin, y)
        y += 6
        doc.text(`${t('settings.detectionModel')}: ${selectedBatch.value.modelInfo.detection}`, margin, y)
        y += 6
      }

      y += 6
      setBodyFont(10, true)
      doc.text(t('reports.summary'), margin, y)
      y += 8
      setBodyFont(10)
      const defectTotal = batch.value.images.reduce((total, img) => total + img.defects.length, 0)
      doc.text(`${t('reports.totalImages')}: ${summary.value.total}`, margin, y)
      doc.text(`${t('reports.clean')}: ${summary.value.clean}`, margin + 45, y)
      doc.text(`${t('reports.defective')}: ${summary.value.defective}`, margin + 85, y)
      doc.text(`${t('reports.defectCount')}: ${defectTotal}`, margin + 130, y)
      y += 6
      doc.text(`${t('reports.defectRate')}: ${summary.value.rate}%`, margin, y)
      y += 10
    }

    async function writeDefectOnly() {
      setBodyFont(10, true)
      doc.text(t('reports.defectDetails'), margin, y)
      y += 8
      setBodyFont(10)

      const imagesWithDefects = batch.value.images.filter((img) => img.defects.length > 0)
      if (!imagesWithDefects.length) {
        ensureSpace(8)
        doc.text(t('qc.noDefects'), margin, y)
        y += 8
      }

      for (const img of imagesWithDefects) {
        let annotated
        try {
          annotated = await getAnnotated(img)
        } catch (e) {
          console.warn('Report image skipped:', img.url, e)
          continue
        }

        ensureSpace(12)
        setBodyFont(10, true)
        doc.text(`${img.filename}  (${img.defects.length})`, margin, y, { maxWidth: usableWidth })
        y += 7
        setBodyFont(10)

        let x = margin
        let rowHeight = 0
        for (const defect of img.defects) {
          const box = defectCropBox(defect.polygon, cropPad, img.width, img.height)
          if (box.w <= 0 || box.h <= 0) continue
          const { w, h } = fitDimensions(box.w, box.h, cropColWidth, cropMaxHeight)

          if (x !== margin && x + cropColWidth > right) {
            y += rowHeight + captionHeight + cropGap
            x = margin
            rowHeight = 0
          }
          if (y + h + captionHeight > bottom) {
            newPage()
            x = margin
            rowHeight = 0
          }

          const cropCanvas = renderDefectCrop(annotated, box)
          doc.addImage(cropCanvas, 'PNG', x, y, w, h)
          setBodyFont(8)
          doc.text(`${defect.type} ${Math.round(defect.confidence * 100)}%`, x, y + h + 4, { maxWidth: cropColWidth })
          rowHeight = Math.max(rowHeight, h)
          x += cropColWidth + cropGap
        }

        y += rowHeight ? rowHeight + captionHeight + 7 : 2
        ensureSpace(4)
        doc.setDrawColor(200)
        doc.line(margin, y, right, y)
        y += 8
      }
    }

    async function writeFullImage() {
      setBodyFont(10, true)
      doc.text(t('reports.annotatedImages'), margin, y)
      y += 8

      for (const [index, img] of batch.value.images.entries()) {
        let annotated
        try {
          annotated = await getAnnotated(img)
        } catch (e) {
          console.warn('Report image skipped:', img.url, e)
          continue
        }

        ensureSpace(36)
        setBodyFont(12, true)
        doc.text(`${index + 1}. ${img.filename}`, margin, y, { maxWidth: usableWidth })
        y += 6
        setBodyFont(9)
        doc.text(`${t('reports.imageStatus')}: ${img.defects.length ? t('reports.defective') : t('reports.clean')}    ${t('reports.defectCount')}: ${img.defects.length}`, margin, y)
        y += 6

        const dimensions = fitDimensions(img.width, img.height, usableWidth, 105)
        ensureSpace(dimensions.h + 15)
        doc.addImage(annotated, 'PNG', margin, y, dimensions.w, dimensions.h)
        y += dimensions.h + 7

        setBodyFont(9, true)
        doc.text(t('reports.defectList'), margin, y)
        y += 5
        drawDefectTable(img)
        y += 6
        doc.setDrawColor(200)
        doc.line(margin, y, right, y)
        y += 9
      }
    }

    writeReportHeader()
    if (reportMode.value === 'full-image') await writeFullImage()
    else await writeDefectOnly()

    y += 7
    ensureSpace(20)
    setBodyFont(10)
    doc.text(`${t('reports.reviewedBy')}: ____________________`, margin, y)
    doc.text(`${t('reports.approvedBy')}: ____________________`, margin + 80, y)
    y += 10
    doc.text(`[  ] ${t('reports.pass')}     [  ] ${t('reports.fail')}`, margin, y)

    const pageCount = doc.getNumberOfPages()
    for (let page = 1; page <= pageCount; page += 1) {
      doc.setPage(page)
      setBodyFont(8)
      doc.setDrawColor(220)
      doc.line(margin, 284, right, 284)
      doc.text(`${batch.value.batch_name} · ${modeLabel}`, margin, 290)
      doc.text(`${page} / ${pageCount}`, right, 290, { align: 'right' })
    }

    const filename = `${batch.value.batch_name}_${reportMode.value}_report.pdf`
    doc.save(filename)
    log('REPORT_GENERATED', `Generated ${modeLabel} PDF report: ${filename}`)
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

        <fieldset class="mode-fieldset">
          <legend>{{ t('reports.modeLabel') }}</legend>
          <label class="mode-option" :class="{ active: reportMode === 'defect-only' }">
            <input v-model="reportMode" type="radio" value="defect-only" />
            <span>
              <strong>{{ t('reports.defectOnly') }}</strong>
              <small>{{ t('reports.defectOnlyHint') }}</small>
            </span>
          </label>
          <label class="mode-option" :class="{ active: reportMode === 'full-image' }">
            <input v-model="reportMode" type="radio" value="full-image" />
            <span>
              <strong>{{ t('reports.fullImage') }}</strong>
              <small>{{ t('reports.fullImageHint') }}</small>
            </span>
          </label>
        </fieldset>

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
  font-size: 15px;
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
  font-size: 15px;
  outline: none;
  margin-bottom: 24px;
  letter-spacing: 0.16px;
}
.text-input:focus {
  border-bottom-color: var(--color-primary);
}
.mode-fieldset {
  display: grid;
  gap: 8px;
  margin: 0 0 24px;
  padding: 0;
  border: 0;
}
.mode-fieldset legend {
  margin-bottom: 4px;
  color: var(--color-ink);
  font-size: 15px;
  font-weight: 600;
}
.mode-option {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
  color: var(--color-ink);
  cursor: pointer;
}
.mode-option.active {
  border-color: var(--color-primary);
  box-shadow: inset 2px 0 0 var(--color-primary);
}
.mode-option input {
  margin-top: 3px;
  accent-color: var(--color-primary);
}
.mode-option span {
  display: grid;
  gap: 3px;
}
.mode-option strong {
  font-size: 14px;
  font-weight: 600;
}
.mode-option small {
  color: var(--color-ink-muted);
  font-size: 13px;
  line-height: 1.35;
}
.report-preview {
  border: 1px solid var(--color-hairline);
  padding: 24px;
}
.report-preview h3 {
  margin: 0 0 12px;
  font-size: 15px;
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
  font-size: 13px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.stat-value {
  font-size: 16px;
  font-weight: 600;
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
  font-size: 13px;
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
  font-size: 13px;
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
  font-size: 15px;
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
  color: var(--color-ink-muted);
  font-size: 15px;
}
.mono {
  font-family: var(--font-mono);
}
</style>
