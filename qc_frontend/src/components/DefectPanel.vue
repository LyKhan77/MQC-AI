<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useInspection } from '../composables/useInspection.js'
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useDefectColor } from '../composables/useDefectColor.js'
import { useDefectClasses } from '../composables/useDefectClasses.js'
import JSZip from 'jszip'
import {
  renderAnnotated,
  renderDefectCrop,
  canvasToBlob,
  downloadBlob,
  fullFilename,
  cropFilename,
  defectCropBox,
  loadImage,
} from '../utils/export.js'

const {
  selected,
  selectedDefectId,
  hoveredDefectId,
  images,
  batch,
  selectImage,
  selectedId,
  toggleReviewed,
  isReviewed,
  editMode,
  selectDefect,
  updateDefect,
  removeDefect,
} = useInspection()
const { t } = useI18n()
const { log } = useAuditLog()
const { colorFor } = useDefectColor()
const { classes } = useDefectClasses()

const CROP_PAD = 40

const exporting = ref(false)
const exportMsg = ref('')

const coating = computed(() => selected.value?.defects.filter((d) => d.category === 'coating') ?? [])
const welding = computed(() => selected.value?.defects.filter((d) => d.category === 'welding') ?? [])
const enabledClasses = computed(() => classes.value.filter((c) => c.enabled))

function pct(c) {
  return `${Math.round(c * 100)}%`
}

async function zipAndDownload(files, zipName) {
  if (files.length === 1) {
    downloadBlob(files[0].blob, files[0].name)
    return
  }
  const zip = new JSZip()
  for (const f of files) zip.file(f.name, f.blob)
  const zipBlob = await zip.generateAsync({ type: 'blob' })
  downloadBlob(zipBlob, zipName)
}

async function exportFull() {
  if (!images.value.length) return
  exporting.value = true
  try {
    const files = []
    for (const img of images.value) {
      const im = await loadImage(img.url)
      const canvas = renderAnnotated(im, img, colorFor)
      const blob = await canvasToBlob(canvas)
      files.push({ name: fullFilename(img.filename), blob })
    }
    if (!files.length) return
    await zipAndDownload(files, `${batch.value.batch_name}_full.zip`)
    log('EXPORT_FULL', `Exported full: ${files.length} image(s)`)
  } catch (e) {
    console.error('Export failed:', e)
  } finally {
    exporting.value = false
  }
}

async function exportCrop() {
  exporting.value = true
  try {
    const files = []
    for (const img of images.value) {
      if (!img.defects.length) continue
      const im = await loadImage(img.url)
      const annotated = renderAnnotated(im, img, colorFor)
      const typeCounters = {}
      for (const d of img.defects) {
        const idx = (typeCounters[d.type] = (typeCounters[d.type] ?? 0) + 1)
        const box = defectCropBox(d.polygon, CROP_PAD, img.width, img.height)
        const cropCanvas = renderDefectCrop(annotated, box)
        const blob = await canvasToBlob(cropCanvas)
        files.push({ name: cropFilename(img.filename, d.type, idx), blob })
      }
    }
    if (!files.length) {
      exportMsg.value = t('qc.exportNoDefects')
      setTimeout(() => { exportMsg.value = '' }, 3000)
      return
    }
    await zipAndDownload(files, `${batch.value.batch_name}_crops.zip`)
    log('EXPORT_CROP', `Exported crop: ${files.length} defect(s)`)
  } catch (e) {
    console.error('Export failed:', e)
  } finally {
    exporting.value = false
  }
}

async function deletePanelDefect(defect) {
  if (!selected.value) return
  if (!confirm(t('qc.confirmDeleteDefect'))) return
  await removeDefect(selected.value.id, defect.id)
  log('DEFECT_DELETED', `Deleted defect: ${defect.id}`)
}

async function relabelDefect(defect, classId) {
  if (!selected.value) return
  const cls = enabledClasses.value.find((c) => c.id === classId)
  if (!cls) return
  await updateDefect(selected.value.id, defect.id, { type: cls.name, category: cls.category })
  log('DEFECT_RELABELED', `Relabeled defect: ${defect.id} -> ${cls.name}`)
}

function selectPanelDefect(defect) {
  selectDefect(defect.id)
}

function onKeydown(e) {
  if (!images.value.length) return
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return

  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
    e.preventDefault()
    const idx = images.value.findIndex((i) => i.id === selectedId.value)
    const next = images.value[Math.min(idx + 1, images.value.length - 1)]
    if (next) selectImage(next.id)
  } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
    e.preventDefault()
    const idx = images.value.findIndex((i) => i.id === selectedId.value)
    const prev = images.value[Math.max(idx - 1, 0)]
    if (prev) selectImage(prev.id)
  } else if (e.key === ' ') {
    e.preventDefault()
    if (selectedId.value) toggleReviewed(selectedId.value)
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <aside class="defect-panel">
    <header class="panel-head">
      <h3>{{ t('qc.defectDetails') }}</h3>
      <span v-if="selected" class="mono fname">{{ selected.filename }}</span>
    </header>

    <div v-if="selected" class="panel-body">
      <section class="group">
        <h4>{{ t('qc.coatingDefects') }} <span class="grp-count mono">{{ coating.length }}</span></h4>
        <p v-if="!coating.length" class="none mono">{{ t('qc.noDefects') }}</p>
        <ul>
          <li
            v-for="d in coating"
            :key="d.id"
            class="defect-row"
            :class="{ hot: hoveredDefectId === d.id, active: selectedDefectId === d.id }"
            role="button"
            tabindex="0"
            @mouseenter="hoveredDefectId = d.id"
            @mouseleave="hoveredDefectId = null"
            @click="selectPanelDefect(d)"
            @keydown.enter.prevent="selectPanelDefect(d)"
            @keydown.space.prevent="selectPanelDefect(d)"
          >
            <span class="swatch" :style="{ background: colorFor(d.type) }"></span>
            <span class="type">{{ d.type }}</span>
            <select
              v-if="editMode"
              class="class-select"
              :aria-label="t('qc.relabel')"
              @click.stop
              @change="relabelDefect(d, $event.target.value)"
            >
              <option value="">{{ t('qc.relabel') }}</option>
              <option v-for="cls in enabledClasses" :key="cls.id" :value="cls.id">
                {{ cls.name }}
              </option>
            </select>
            <button v-if="editMode" class="row-delete" :title="t('qc.deleteDefect')" :aria-label="t('qc.deleteDefect')" @click.stop="deletePanelDefect(d)">x</button>
            <span class="conf mono">{{ pct(d.confidence) }}</span>
          </li>
        </ul>
      </section>

      <section class="group">
        <h4>{{ t('qc.weldingDefects') }} <span class="grp-count mono">{{ welding.length }}</span></h4>
        <p v-if="!welding.length" class="none mono">{{ t('qc.noDefects') }}</p>
        <ul>
          <li
            v-for="d in welding"
            :key="d.id"
            class="defect-row"
            :class="{ hot: hoveredDefectId === d.id, active: selectedDefectId === d.id }"
            role="button"
            tabindex="0"
            @mouseenter="hoveredDefectId = d.id"
            @mouseleave="hoveredDefectId = null"
            @click="selectPanelDefect(d)"
            @keydown.enter.prevent="selectPanelDefect(d)"
            @keydown.space.prevent="selectPanelDefect(d)"
          >
            <span class="swatch" :style="{ background: colorFor(d.type) }"></span>
            <span class="type">{{ d.type }}</span>
            <select
              v-if="editMode"
              class="class-select"
              :aria-label="t('qc.relabel')"
              @click.stop
              @change="relabelDefect(d, $event.target.value)"
            >
              <option value="">{{ t('qc.relabel') }}</option>
              <option v-for="cls in enabledClasses" :key="cls.id" :value="cls.id">
                {{ cls.name }}
              </option>
            </select>
            <button v-if="editMode" class="row-delete" :title="t('qc.deleteDefect')" :aria-label="t('qc.deleteDefect')" @click.stop="deletePanelDefect(d)">x</button>
            <span class="conf mono">{{ pct(d.confidence) }}</span>
          </li>
        </ul>
      </section>
    </div>

    <p v-else class="none mono panel-body">{{ t('qc.noImageSelected') }}</p>

    <footer v-if="selected" class="panel-actions">
      <p v-if="exportMsg" class="export-msg mono">{{ exportMsg }}</p>
      <div class="panel-actions-row">
        <button class="btn-primary" :disabled="exporting" @click="exportCrop">
          {{ exporting ? t('qc.exporting') : t('qc.exportCrop') }}
        </button>
        <button class="btn-secondary" :disabled="exporting" @click="exportFull">
          {{ exporting ? t('qc.exporting') : t('qc.exportFull') }}
        </button>
      </div>
    </footer>
  </aside>
</template>

<style scoped>
.defect-panel {
  width: var(--sidebar-right);
  flex-shrink: 0;
  background: var(--color-canvas);
  border-left: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel-head {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-hairline);
}
.panel-head h3 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 400;
  color: var(--color-ink);
  letter-spacing: 0.16px;
}
.panel-head .fname {
  font-size: 12px;
  color: var(--color-ink-subtle);
  letter-spacing: 0.16px;
}
.panel-body {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}
.group {
  margin-bottom: 20px;
}
.group h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink-muted);
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 0.16px;
}
.grp-count {
  background: var(--color-surface-1);
  padding: 0 6px;
  font-size: 12px;
  letter-spacing: 0.32px;
}
.group ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.defect-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid transparent;
  cursor: pointer;
}
.defect-row:hover,
.defect-row.hot {
  background: var(--color-surface-1);
}
.defect-row.active {
  background: var(--color-surface-1);
  border-color: var(--color-primary);
}
.defect-row:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
.swatch {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
}
.type {
  flex: 1;
  font-size: 14px;
  text-transform: capitalize;
  color: var(--color-ink);
  letter-spacing: 0.16px;
}
.conf {
  font-size: 12px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.class-select {
  min-width: 84px;
  max-width: 120px;
  background: var(--color-canvas);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
  font-family: var(--font-sans);
  font-size: 12px;
  padding: 4px;
}
.class-select:focus-visible,
.row-delete:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
.row-delete {
  width: 24px;
  height: 24px;
  background: transparent;
  color: var(--color-error);
  border: 1px solid var(--color-hairline);
  cursor: pointer;
  font-family: var(--font-sans);
}
.row-delete:hover {
  border-color: var(--color-error);
}
.none {
  color: var(--color-ink-subtle);
  font-size: 14px;
  letter-spacing: 0.16px;
}
.panel-actions {
  padding: 12px 16px;
  border-top: 1px solid var(--color-hairline);
}
.panel-actions-row {
  display: flex;
  gap: 8px;
}
.export-msg {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--color-ink-subtle);
  letter-spacing: 0.16px;
}
.btn-primary {
  flex: 1;
  padding: 9px 16px;
  cursor: pointer;
  font-weight: 400;
  font-family: var(--font-sans);
  font-size: 14px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  letter-spacing: 0.16px;
}
.btn-secondary {
  flex: 1;
  padding: 9px 16px;
  cursor: pointer;
  font-weight: 400;
  font-family: var(--font-sans);
  font-size: 14px;
  background: transparent;
  color: var(--color-ink);
  border: 1px solid var(--color-ink);
  letter-spacing: 0.16px;
}
.btn-primary:hover {
  background: var(--color-primary-hover);
}
.btn-secondary:hover {
  background: var(--color-surface-1);
}
.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: default;
}
.mono {
  font-family: var(--font-mono);
}
</style>
