<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useInspection } from '../composables/useInspection.js'
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useDefectColor } from '../composables/useDefectColor.js'
import { renderAnnotated, downloadCanvas, defectsBBox } from '../utils/export.js'

const { selected, hoveredDefectId, images, selectImage, selectedId, toggleReviewed, isReviewed } = useInspection()
const { t } = useI18n()
const { log } = useAuditLog()
const { colorFor } = useDefectColor()

const coating = computed(() => selected.value?.defects.filter((d) => d.category === 'coating') ?? [])
const welding = computed(() => selected.value?.defects.filter((d) => d.category === 'welding') ?? [])

function pct(c) {
  return `${Math.round(c * 100)}%`
}

function loadImageEl(url) {
  return new Promise((resolve, reject) => {
    const im = new Image()
    im.crossOrigin = 'anonymous'
    im.onload = () => resolve(im)
    im.onerror = reject
    im.src = url
  })
}

async function exportFull() {
  if (!selected.value) return
  try {
    const im = await loadImageEl(selected.value.url)
    const canvas = renderAnnotated(im, selected.value)
    downloadCanvas(canvas, `${selected.value.filename}_full.png`)
    log('EXPORT_FULL', `Exported full: ${selected.value.filename}`)
  } catch (e) {
    console.error('Export failed:', e)
  }
}

async function exportCrop() {
  if (!selected.value) return
  try {
    const img = selected.value
    const im = await loadImageEl(img.url)
    const full = renderAnnotated(im, img)
    const b = defectsBBox(img.defects, 40, img.width, img.height)
    const crop = document.createElement('canvas')
    crop.width = b.w
    crop.height = b.h
    crop.getContext('2d').drawImage(full, b.x, b.y, b.w, b.h, 0, 0, b.w, b.h)
    downloadCanvas(crop, `${img.filename}_crop.png`)
    log('EXPORT_CROP', `Exported crop: ${img.filename}`)
  } catch (e) {
    console.error('Export failed:', e)
  }
}

function onKeydown(e) {
  if (!images.value.length) return
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return

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
            :class="{ hot: hoveredDefectId === d.id }"
            @mouseenter="hoveredDefectId = d.id"
            @mouseleave="hoveredDefectId = null"
          >
            <span class="swatch" :style="{ background: colorFor(d.type) }"></span>
            <span class="type">{{ d.type }}</span>
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
            :class="{ hot: hoveredDefectId === d.id }"
            @mouseenter="hoveredDefectId = d.id"
            @mouseleave="hoveredDefectId = null"
          >
            <span class="swatch" :style="{ background: colorFor(d.type) }"></span>
            <span class="type">{{ d.type }}</span>
            <span class="conf mono">{{ pct(d.confidence) }}</span>
          </li>
        </ul>
      </section>
    </div>

    <p v-else class="none mono panel-body">{{ t('qc.noImageSelected') }}</p>

    <footer v-if="selected" class="panel-actions">
      <button class="btn-primary" @click="exportCrop">{{ t('qc.exportCrop') }}</button>
      <button class="btn-secondary" @click="exportFull">{{ t('qc.exportFull') }}</button>
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
  cursor: pointer;
}
.defect-row:hover,
.defect-row.hot {
  background: var(--color-surface-1);
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
.none {
  color: var(--color-ink-subtle);
  font-size: 14px;
  letter-spacing: 0.16px;
}
.panel-actions {
  padding: 12px 16px;
  border-top: 1px solid var(--color-hairline);
  display: flex;
  gap: 8px;
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
.mono {
  font-family: var(--font-mono);
}
</style>
