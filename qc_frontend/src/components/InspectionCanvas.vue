<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useInspection } from '../composables/useInspection.js'
import { useI18n } from '../composables/useI18n.js'
import { useDefectColor } from '../composables/useDefectColor.js'
import { useDefectClasses } from '../composables/useDefectClasses.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { segmentDefect } from '../api/batches.js'
import { normalizeBox, toImageCoords } from '../utils/canvasCoords.js'
import { cursorForState } from '../utils/cursor.js'

const {
  selected,
  selectedDefectId,
  hoveredDefectId,
  toggleReviewed,
  isReviewed,
  editMode,
  toggleEditMode,
  selectDefect,
  clearDefectSelection,
  addDefect,
  removeDefect,
  currentBatchId,
} = useInspection()
const { t } = useI18n()
const { colorFor } = useDefectColor()
const { classes } = useDefectClasses()
const { log } = useAuditLog()

const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const showAnnotation = ref(true)
const dragging = ref(false)
const dragStart = ref({ x: 0, y: 0, panX: 0, panY: 0 })
const svgRef = ref(null)
const drawing = ref(false)
const pickingClass = ref(false)
const drawingPoints = ref([])
const drawMsg = ref('')
const activeTool = ref('select')
const overDefect = ref(false)
const segmenting = ref(false)
const samBoxStart = ref(null)
const samBoxCurrent = ref(null)
const pendingSource = ref('')
const segmentRun = ref(0)

const enabledClasses = computed(() => classes.value.filter((c) => c.enabled))
const frameTransform = computed(() => `translate(${panX.value}px, ${panY.value}px) scale(${zoom.value})`)
const samActive = computed(() => activeTool.value === 'sam-point' || activeTool.value === 'sam-box')
const canvasCursor = computed(() => cursorForState({
  drawing: drawing.value || samActive.value,
  dragging: dragging.value,
  editMode: editMode.value,
  overDefect: overDefect.value,
}))
const samBoxRect = computed(() => {
  if (!samBoxStart.value || !samBoxCurrent.value) return null
  const [x1, y1, x2, y2] = normalizeBox(
    samBoxStart.value.x,
    samBoxStart.value.y,
    samBoxCurrent.value.x,
    samBoxCurrent.value.y,
  )
  return { x: x1, y: y1, width: x2 - x1, height: y2 - y1 }
})

function pointsAttr(polygon) {
  return polygon.map((p) => p.join(',')).join(' ')
}

function onWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  zoom.value = Math.max(0.5, Math.min(5, zoom.value + delta))
}

function onMouseDown(e) {
  if (drawing.value || segmenting.value) return
  if (e.button !== 0) return
  if (activeTool.value === 'sam-box') {
    startSamBox(e)
    return
  }
  if (activeTool.value === 'sam-point') return
  dragging.value = true
  dragStart.value = { x: e.clientX, y: e.clientY, panX: panX.value, panY: panY.value }
}

function onMouseMove(e) {
  if (samBoxStart.value && selected.value && svgRef.value) {
    samBoxCurrent.value = toImageCoords(
      e.clientX,
      e.clientY,
      svgRef.value.getBoundingClientRect(),
      selected.value.width,
      selected.value.height,
    )
    return
  }
  if (!dragging.value) return
  panX.value = dragStart.value.panX + (e.clientX - dragStart.value.x)
  panY.value = dragStart.value.panY + (e.clientY - dragStart.value.y)
}

async function onMouseUp() {
  if (samBoxStart.value) {
    await finishSamBox()
  }
  dragging.value = false
}

function resetZoom() {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
}

function zoomIn() {
  zoom.value = Math.min(5, zoom.value + 0.2)
}

function zoomOut() {
  zoom.value = Math.max(0.5, zoom.value - 0.2)
}

function startDrawing() {
  if (!editMode.value || segmenting.value) return
  clearDefectSelection()
  activeTool.value = 'draw'
  drawing.value = true
  pickingClass.value = false
  drawingPoints.value = []
  drawMsg.value = ''
  samBoxStart.value = null
  samBoxCurrent.value = null
  pendingSource.value = ''
}

function setSelectTool() {
  if (drawing.value || pickingClass.value || samActive.value || samBoxStart.value || samBoxCurrent.value || segmenting.value) {
    cancelActive()
  } else {
    activeTool.value = 'select'
  }
}

function setSamTool(tool) {
  if (!editMode.value || segmenting.value) return
  clearDefectSelection()
  cancelDrawing()
  activeTool.value = tool
}

function setEditMode(next) {
  if (editMode.value === next) return
  if (!next) {
    clearDefectSelection()
    cancelActive()
  } else {
    activeTool.value = 'select'
  }
  toggleEditMode()
}

function cancelDrawing() {
  drawing.value = false
  pickingClass.value = false
  drawingPoints.value = []
  drawMsg.value = ''
  samBoxStart.value = null
  samBoxCurrent.value = null
  pendingSource.value = ''
  activeTool.value = 'select'
}

function cancelActive() {
  if (segmenting.value) {
    segmentRun.value += 1
    segmenting.value = false
  }
  if (pickingClass.value) {
    cancelDrawing()
  } else if (drawing.value) {
    cancelDrawing()
  } else if (samActive.value || samBoxStart.value || samBoxCurrent.value) {
    samBoxStart.value = null
    samBoxCurrent.value = null
    activeTool.value = 'select'
    drawMsg.value = ''
  } else {
    clearDefectSelection()
  }
}

function imagePointFromEvent(e) {
  return toImageCoords(e.clientX, e.clientY, svgRef.value.getBoundingClientRect(), selected.value.width, selected.value.height)
}

async function handleOverlayClick(e) {
  if (activeTool.value === 'sam-point') {
    if (!selected.value || !currentBatchId.value || !svgRef.value || segmenting.value) return
    const p = imagePointFromEvent(e)
    await requestSegment({ point: [p.x, p.y] }, 'SAM point')
    return
  }
  addPoint(e)
}

function addPoint(e) {
  if (!drawing.value || pickingClass.value || !selected.value || !svgRef.value) return
  const p = imagePointFromEvent(e)
  drawingPoints.value = [...drawingPoints.value, [p.x, p.y]]
  drawMsg.value = ''
}

function finishDrawing() {
  if (!drawing.value) return
  if (drawingPoints.value.length < 3) {
    drawMsg.value = t('qc.needThreePoints')
    return
  }
  pickingClass.value = true
}

async function requestSegment(payload, source) {
  const run = segmentRun.value + 1
  segmentRun.value = run
  segmenting.value = true
  drawMsg.value = ''
  try {
    const res = await segmentDefect(currentBatchId.value, selected.value.id, payload)
    if (run !== segmentRun.value) return
    if (!res.polygon?.length) {
      drawMsg.value = t('qc.samEmpty')
      return
    }
    drawingPoints.value = res.polygon
    pickingClass.value = true
    drawing.value = false
    pendingSource.value = source
  } catch (e) {
    if (run !== segmentRun.value) return
    drawMsg.value = e.message || t('qc.samEmpty')
  } finally {
    if (run === segmentRun.value) segmenting.value = false
  }
}

function startSamBox(e) {
  if (!selected.value || !svgRef.value || pickingClass.value) return
  const p = imagePointFromEvent(e)
  samBoxStart.value = p
  samBoxCurrent.value = p
}

async function finishSamBox() {
  const start = samBoxStart.value
  const end = samBoxCurrent.value
  samBoxStart.value = null
  samBoxCurrent.value = null
  if (!start || !end || !selected.value || !currentBatchId.value) return
  const box = normalizeBox(start.x, start.y, end.x, end.y)
  if (box[0] === box[2] || box[1] === box[3]) return
  await requestSegment({ box }, 'SAM box')
}

async function chooseClass(cls) {
  if (!selected.value) return
  await addDefect(selected.value.id, {
    type: cls.name,
    category: cls.category,
    polygon: drawingPoints.value,
    confidence: 1.0,
  })
  log('DEFECT_ADDED', `${pendingSource.value || 'Manual'}: ${cls.name}`)
  cancelDrawing()
}

function onPolygonClick(id) {
  if (drawing.value) return
  selectDefect(id)
}

async function deleteSelectedDefect() {
  if (!editMode.value || !selected.value || !selectedDefectId.value) return
  if (!confirm(t('qc.confirmDeleteDefect'))) return
  const id = selectedDefectId.value
  await removeDefect(selected.value.id, id)
  log('DEFECT_DELETED', `Deleted defect: ${id}`)
  clearDefectSelection()
}

function isTypingTarget(target) {
  return ['INPUT', 'SELECT', 'TEXTAREA'].includes(target?.tagName)
}

function onKeydown(e) {
  if (isTypingTarget(e.target)) return
  const key = e.key.toLowerCase()

  if (key === 'v') {
    e.preventDefault()
    setSelectTool()
  } else if (key === 'a' && editMode.value) {
    e.preventDefault()
    startDrawing()
  } else if (e.key === 'Delete' && editMode.value && selectedDefectId.value) {
    e.preventDefault()
    deleteSelectedDefect()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    cancelActive()
  } else if (e.key === '+' || e.key === '=') {
    e.preventDefault()
    zoomIn()
  } else if (e.key === '-') {
    e.preventDefault()
    zoomOut()
  } else if (e.key === '0') {
    e.preventDefault()
    resetZoom()
  }
}

watch(() => selected.value?.id, () => {
  clearDefectSelection()
  cancelActive()
})

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <section class="canvas-wrapper">
    <div v-if="selected && editMode" class="floating-cluster tool-dock" :aria-label="t('qc.editTools')">
      <button class="tool-btn dock-tool" :class="{ active: activeTool === 'select' && !drawing }" :disabled="segmenting" :title="t('qc.toolSelect')" :aria-label="t('qc.toolSelect')" :aria-pressed="activeTool === 'select' && !drawing" @click="setSelectTool">
        <svg class="tool-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 4l12 8-5 2-2 5-5-15z" />
        </svg>
        <span class="tool-label">{{ t('qc.toolSelect') }}</span>
      </button>
      <button class="tool-btn dock-tool" :class="{ active: activeTool === 'draw' }" :disabled="segmenting" :title="t('qc.toolAdd')" :aria-label="t('qc.toolAdd')" :aria-pressed="activeTool === 'draw'" @click="startDrawing">
        <svg class="tool-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 15l3-8 7 3 2 8-8 1-4-4z" />
          <path d="M9 7l5-3 2 6" />
        </svg>
        <span class="tool-label">{{ t('qc.toolAdd') }}</span>
      </button>
      <button class="tool-btn dock-tool" :class="{ active: activeTool === 'sam-point' }" :disabled="segmenting" :title="t('qc.toolSamPoint')" :aria-label="t('qc.toolSamPoint')" :aria-pressed="activeTool === 'sam-point'" @click="setSamTool('sam-point')">
        <svg class="tool-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8z" />
          <path d="M12 3v3M12 18v3M3 12h3M18 12h3" />
          <path class="sam-spark" d="M18 4l1 2 2 1-2 1-1 2-1-2-2-1 2-1 1-2z" />
        </svg>
        <span class="tool-label">{{ t('qc.toolSamPoint') }}</span>
      </button>
      <button class="tool-btn dock-tool" :class="{ active: activeTool === 'sam-box' }" :disabled="segmenting" :title="t('qc.toolSamBox')" :aria-label="t('qc.toolSamBox')" :aria-pressed="activeTool === 'sam-box'" @click="setSamTool('sam-box')">
        <svg class="tool-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 6h14v12H5z" stroke-dasharray="3 2" />
          <path class="sam-spark" d="M18 3l1 2 2 1-2 1-1 2-1-2-2-1 2-1 1-2z" />
        </svg>
        <span class="tool-label">{{ t('qc.toolSamBox') }}</span>
      </button>
      <button class="tool-btn dock-tool danger" :disabled="segmenting || !selectedDefectId" :title="t('qc.toolDelete')" :aria-label="t('qc.toolDelete')" @click="deleteSelectedDefect">
        <svg class="tool-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 7h14M10 11v6M14 11v6M8 7l1 12h6l1-12M10 7V5h4v2" />
        </svg>
        <span class="tool-label">{{ t('qc.toolDelete') }}</span>
      </button>
      <template v-if="drawing || samActive || pickingClass">
        <button v-if="drawing" class="tool-btn dock-action" :title="t('qc.finishDrawing')" :aria-label="t('qc.finishDrawing')" @click="finishDrawing">{{ t('qc.finishDrawing') }}</button>
        <button class="tool-btn dock-action" :title="t('common.cancel')" :aria-label="t('common.cancel')" @click="cancelActive">{{ t('common.cancel') }}</button>
      </template>
    </div>

    <div v-if="selected" class="floating-cluster top-tools">
      <button class="tool-btn" :class="{ active: showAnnotation }" :aria-pressed="showAnnotation" :aria-label="t('qc.toggleAnnotation')" :title="t('qc.toggleAnnotation')" @click="showAnnotation = !showAnnotation">
        {{ showAnnotation ? t('qc.annotationsOn') : t('qc.annotationsOff') }}
      </button>
      <button class="tool-btn" :class="{ reviewed: isReviewed(selected.id) }" :aria-label="isReviewed(selected.id) ? t('qc.markUnreviewed') : t('qc.markReviewed')" @click="toggleReviewed(selected.id)">
        {{ isReviewed(selected.id) ? t('qc.markUnreviewed') : t('qc.markReviewed') }}
      </button>
      <div class="segmented" role="group" :aria-label="t('qc.mode')">
        <button class="segment-btn" :class="{ active: !editMode }" :aria-pressed="!editMode" @click="setEditMode(false)">{{ t('qc.view') }}</button>
        <button class="segment-btn" :class="{ active: editMode }" :aria-pressed="editMode" @click="setEditMode(true)">{{ t('qc.edit') }}</button>
      </div>
    </div>

    <div v-if="selected" class="floating-cluster zoom-cluster">
      <button class="tool-btn icon-btn" :title="t('qc.zoomOut')" :aria-label="t('qc.zoomOut')" @click="zoomOut">-</button>
      <span class="zoom-display mono">{{ Math.round(zoom * 100) }}%</span>
      <button class="tool-btn icon-btn" :title="t('qc.zoomIn')" :aria-label="t('qc.zoomIn')" @click="zoomIn">+</button>
      <button class="tool-btn" :title="t('qc.zoomReset')" :aria-label="t('qc.zoomReset')" @click="resetZoom">{{ t('qc.zoomResetShort') }}</button>
    </div>

    <div v-if="selected && editMode && !pickingClass && (drawing || samActive || segmenting || drawMsg)" class="draw-hint mono">
      {{ segmenting ? t('qc.segmenting') : drawMsg || (activeTool === 'sam-point' ? t('qc.samHintPoint') : activeTool === 'sam-box' ? t('qc.samHintBox') : t('qc.drawHint')) }}
    </div>

    <div v-if="selected && editMode && pickingClass" class="floating-cluster class-picker">
      <span class="edit-label">{{ t('qc.pickClass') }}</span>
        <button
          v-for="cls in enabledClasses"
          :key="cls.id"
          class="class-chip"
          @click="chooseClass(cls)"
        >
          <span class="swatch" :style="{ background: cls.color }"></span>
          {{ cls.name }}
        </button>
        <button class="tool-btn class-cancel" :title="t('common.cancel')" :aria-label="t('common.cancel')" @click="cancelActive">{{ t('common.cancel') }}</button>
    </div>

    <div
      v-if="selected"
      class="canvas-scroll"
      @wheel="onWheel"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
      :style="{ cursor: canvasCursor }"
    >
      <div class="image-frame" :style="{ transform: frameTransform }">
        <img :src="selected.url" :alt="selected.filename" class="insp-img" draggable="false" />
        <svg
          v-if="showAnnotation"
          ref="svgRef"
          class="overlay"
          :viewBox="`0 0 ${selected.width} ${selected.height}`"
          preserveAspectRatio="none"
          @click="handleOverlayClick"
          @dblclick.stop="finishDrawing"
        >
          <polygon
            v-for="d in selected.defects"
            :key="d.id"
            :points="pointsAttr(d.polygon)"
            :stroke="colorFor(d.type)"
            :fill="colorFor(d.type)"
            :fill-opacity="hoveredDefectId === d.id || selectedDefectId === d.id ? 0.4 : 0.15"
            :stroke-width="selectedDefectId === d.id ? 4 : 2"
            :data-defect-id="d.id"
            class="defect-poly"
            :class="{ selected: selectedDefectId === d.id, 'sam-ignored': samActive }"
            @mouseenter="overDefect = true"
            @mouseleave="overDefect = false"
            @mousedown.stop
            @click.stop="onPolygonClick(d.id)"
          />
          <polyline
            v-if="drawingPoints.length"
            :points="pointsAttr(drawingPoints)"
            class="draft-poly"
          />
          <rect
            v-if="samBoxRect"
            :x="samBoxRect.x"
            :y="samBoxRect.y"
            :width="samBoxRect.width"
            :height="samBoxRect.height"
            class="sam-box-preview"
          />
          <circle
            v-for="(p, idx) in drawingPoints"
            :key="idx"
            :cx="p[0]"
            :cy="p[1]"
            r="4"
            class="draft-point"
          />
        </svg>
      </div>
    </div>
    <div v-else class="empty-state">
      <p>{{ t('qc.selectImage') }}</p>
    </div>
  </section>
</template>

<style scoped>
.canvas-wrapper {
  position: relative;
  flex: 1;
  background: var(--color-surface-1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.floating-cluster {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  z-index: 2;
  pointer-events: auto;
}
.tool-dock {
  position: absolute;
  left: 12px;
  top: 50%;
  flex-direction: column;
  padding: 4px;
  transform: translateY(-50%);
  animation: dock-enter 160ms ease-out;
}
.top-tools {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px;
}
.zoom-cluster {
  position: absolute;
  right: 12px;
  bottom: 12px;
  padding: 4px;
}
.class-picker {
  position: absolute;
  left: 64px;
  top: 50%;
  max-width: min(520px, calc(100% - 96px));
  padding: 6px;
  flex-wrap: wrap;
  transform: translateY(-50%);
  z-index: 3;
}
.draw-hint {
  position: absolute;
  left: 50%;
  bottom: 56px;
  transform: translateX(-50%);
  z-index: 2;
  padding: 6px 10px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  font-size: 12px;
  letter-spacing: 0.16px;
}
.tool-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink-muted);
  font-family: var(--font-sans);
  font-size: 12px;
  cursor: pointer;
  letter-spacing: 0.16px;
  min-height: 28px;
}
.tool-btn:hover {
  background: var(--color-surface-1);
  color: var(--color-ink);
}
.tool-btn:focus-visible,
.segment-btn:focus-visible,
.class-chip:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
.tool-btn.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-color: var(--color-primary);
}
.tool-btn.reviewed {
  background: var(--color-success);
  color: var(--color-on-primary);
  border-color: var(--color-success);
}
.tool-btn.danger {
  color: var(--color-error);
  border-color: var(--color-error);
}
.tool-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.icon-btn {
  width: 36px;
  padding: 4px;
}
.dock-tool {
  width: 128px;
  justify-content: flex-start;
}
.tool-icon {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.sam-spark {
  stroke: var(--color-primary);
}
.tool-btn.active .sam-spark {
  stroke: var(--color-on-primary);
}
.tool-label {
  color: inherit;
  white-space: nowrap;
}
.dock-action {
  width: 128px;
}
.zoom-display {
  font-size: 12px;
  color: var(--color-ink);
  min-width: 44px;
  text-align: center;
  letter-spacing: 0.16px;
}
.segmented {
  display: flex;
  align-items: center;
  border: 1px solid var(--color-hairline);
}
.segment-btn {
  min-height: 28px;
  padding: 4px 10px;
  background: transparent;
  border: 0;
  border-right: 1px solid var(--color-hairline);
  color: var(--color-ink-muted);
  font-family: var(--font-sans);
  font-size: 12px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.segment-btn:last-child {
  border-right: 0;
}
.segment-btn.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
}
.edit-label {
  font-size: 12px;
  color: var(--color-ink-muted);
}
.class-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: var(--color-canvas);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
  cursor: pointer;
  font-family: var(--font-sans);
  font-size: 12px;
}
.class-chip:hover {
  border-color: var(--color-primary);
}
.class-cancel {
  min-height: 26px;
}
.swatch {
  width: 10px;
  height: 10px;
}
.canvas-scroll {
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  user-select: none;
}
.image-frame {
  position: relative;
  transform-origin: center;
  transition: transform 0.05s linear;
}
.insp-img {
  display: block;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  pointer-events: none;
}
.overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: auto;
}
.defect-poly {
  vector-effect: non-scaling-stroke;
  pointer-events: auto;
  cursor: pointer;
  transition: fill-opacity 0.12s ease;
}
.defect-poly.selected {
  stroke-linejoin: round;
}
.defect-poly.sam-ignored {
  pointer-events: none;
}
.draft-poly {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}
.draft-point {
  fill: var(--color-primary);
  stroke: var(--color-canvas);
  stroke-width: 1;
  vector-effect: non-scaling-stroke;
}
.sam-box-preview {
  fill: transparent;
  stroke: var(--color-primary);
  stroke-dasharray: 6 4;
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-subtle);
  font-size: 14px;
  letter-spacing: 0.16px;
}
.mono {
  font-family: var(--font-mono);
}
@keyframes dock-enter {
  from {
    opacity: 0;
    transform: translate(-8px, -50%);
  }
  to {
    opacity: 1;
    transform: translate(0, -50%);
  }
}
@media (prefers-reduced-motion: reduce) {
  .tool-dock {
    animation: none;
  }
  .image-frame,
  .defect-poly {
    transition: none;
  }
}
</style>
