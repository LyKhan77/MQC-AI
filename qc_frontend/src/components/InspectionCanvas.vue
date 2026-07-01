<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useInspection } from '../composables/useInspection.js'
import { useI18n } from '../composables/useI18n.js'
import { useDefectColor } from '../composables/useDefectColor.js'
import { useDefectClasses } from '../composables/useDefectClasses.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { toImageCoords } from '../utils/canvasCoords.js'

const {
  selected,
  hoveredDefectId,
  toggleReviewed,
  isReviewed,
  editMode,
  toggleEditMode,
  addDefect,
  removeDefect,
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
const selectedDefectId = ref(null)
const drawMsg = ref('')

const enabledClasses = computed(() => classes.value.filter((c) => c.enabled))

function pointsAttr(polygon) {
  return polygon.map((p) => p.join(',')).join(' ')
}

function onWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  zoom.value = Math.max(0.5, Math.min(5, zoom.value + delta))
}

function onMouseDown(e) {
  if (drawing.value) return
  if (e.button !== 0) return
  dragging.value = true
  dragStart.value = { x: e.clientX, y: e.clientY, panX: panX.value, panY: panY.value }
}

function onMouseMove(e) {
  if (!dragging.value) return
  panX.value = dragStart.value.panX + (e.clientX - dragStart.value.x)
  panY.value = dragStart.value.panY + (e.clientY - dragStart.value.y)
}

function onMouseUp() {
  dragging.value = false
}

function resetZoom() {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
}

function startDrawing() {
  selectedDefectId.value = null
  drawing.value = true
  pickingClass.value = false
  drawingPoints.value = []
  drawMsg.value = ''
}

function toggleMode() {
  const leavingEdit = editMode.value
  toggleEditMode()
  if (leavingEdit) {
    selectedDefectId.value = null
    cancelDrawing()
  }
}

function cancelDrawing() {
  drawing.value = false
  pickingClass.value = false
  drawingPoints.value = []
  drawMsg.value = ''
}

function addPoint(e) {
  if (!drawing.value || pickingClass.value || !selected.value || !svgRef.value) return
  const p = toImageCoords(e.clientX, e.clientY, svgRef.value.getBoundingClientRect(), selected.value.width, selected.value.height)
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

async function chooseClass(cls) {
  if (!selected.value) return
  await addDefect(selected.value.id, {
    type: cls.name,
    category: cls.category,
    polygon: drawingPoints.value,
    confidence: 1.0,
  })
  log('DEFECT_ADDED', `Added defect: ${cls.name}`)
  cancelDrawing()
}

function onPolygonClick(id) {
  if (!editMode.value) return
  selectedDefectId.value = id
}

async function deleteSelectedDefect() {
  if (!editMode.value || !selected.value || !selectedDefectId.value) return
  const id = selectedDefectId.value
  await removeDefect(selected.value.id, id)
  log('DEFECT_DELETED', `Deleted defect: ${id}`)
  selectedDefectId.value = null
}

function onKeydown(e) {
  if (e.key === 'Escape' && drawing.value) cancelDrawing()
  if (e.key === 'Delete' && editMode.value && selectedDefectId.value) deleteSelectedDefect()
}

const frameTransform = computed(() => `translate(${panX.value}px, ${panY.value}px) scale(${zoom.value})`)

watch(() => selected.value?.id, () => {
  selectedDefectId.value = null
  cancelDrawing()
})

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <section class="canvas-wrapper">
    <div v-if="selected" class="canvas-toolbar">
      <button class="tool-btn" @click="zoom = Math.max(0.5, zoom - 0.2)" :title="t('qc.zoomOut')">-</button>
      <span class="zoom-display mono">{{ Math.round(zoom * 100) }}%</span>
      <button class="tool-btn" @click="zoom = Math.min(5, zoom + 0.2)" :title="t('qc.zoomIn')">+</button>
      <button class="tool-btn" @click="resetZoom" :title="t('qc.zoomReset')">{{ t('qc.zoomReset') }}</button>
      <span class="tool-sep"></span>
      <button class="tool-btn" :class="{ active: showAnnotation }" @click="showAnnotation = !showAnnotation" :title="t('qc.toggleAnnotation')">
        {{ showAnnotation ? t('qc.toggleAnnotation') : 'OFF' }}
      </button>
      <span class="tool-sep"></span>
      <button class="tool-btn" @click="toggleReviewed(selected.id)" :class="{ reviewed: isReviewed(selected.id) }">
        {{ isReviewed(selected.id) ? '&#10003; ' + t('qc.markUnreviewed') : t('qc.markReviewed') }}
      </button>
      <span class="tool-sep"></span>
      <button class="tool-btn" :class="{ active: editMode }" @click="toggleMode">
        {{ editMode ? t('qc.editMode') : t('qc.viewOnly') }}
      </button>
      <template v-if="editMode">
        <button class="tool-btn" :class="{ active: drawing }" @click="startDrawing">{{ t('qc.addDefect') }}</button>
        <button v-if="drawing" class="tool-btn" @click="finishDrawing">{{ t('qc.finishDrawing') }}</button>
        <button v-if="drawing" class="tool-btn" @click="cancelDrawing">{{ t('common.cancel') }}</button>
        <button v-if="selectedDefectId" class="tool-btn danger" @click="deleteSelectedDefect">{{ t('qc.deleteDefect') }}</button>
      </template>
    </div>
    <div v-if="selected && editMode && (drawMsg || pickingClass)" class="edit-strip">
      <span v-if="drawMsg" class="edit-msg mono">{{ drawMsg }}</span>
      <template v-if="pickingClass">
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
      </template>
    </div>

    <div
      v-if="selected"
      class="canvas-scroll"
      @wheel="onWheel"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
      :class="{ grabbing: dragging }"
    >
      <div class="image-frame" :style="{ transform: frameTransform }">
        <img :src="selected.url" :alt="selected.filename" class="insp-img" draggable="false" />
        <svg
          v-if="showAnnotation"
          ref="svgRef"
          class="overlay"
          :class="{ editing: editMode }"
          :viewBox="`0 0 ${selected.width} ${selected.height}`"
          preserveAspectRatio="none"
          @click="addPoint"
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
            @click.stop="onPolygonClick(d.id)"
          />
          <polyline
            v-if="drawingPoints.length"
            :points="pointsAttr(drawingPoints)"
            class="draft-poly"
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
  flex: 1;
  background: var(--color-surface-1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--color-canvas);
  border-bottom: 1px solid var(--color-hairline);
  flex-shrink: 0;
}
.tool-btn {
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink-muted);
  font-family: var(--font-sans);
  font-size: 12px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.tool-btn:hover {
  background: var(--color-surface-1);
  color: var(--color-ink);
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
.zoom-display {
  font-size: 12px;
  color: var(--color-ink);
  min-width: 44px;
  text-align: center;
  letter-spacing: 0.16px;
}
.tool-sep {
  width: 1px;
  height: 20px;
  background: var(--color-hairline);
  margin: 0 4px;
}
.edit-strip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: var(--color-surface-1);
  border-bottom: 1px solid var(--color-hairline);
  flex-wrap: wrap;
}
.edit-msg,
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
  cursor: grab;
  user-select: none;
}
.canvas-scroll.grabbing {
  cursor: grabbing;
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
  pointer-events: none;
}
.overlay.editing {
  pointer-events: auto;
}
.defect-poly {
  vector-effect: non-scaling-stroke;
  pointer-events: auto;
  cursor: pointer;
  transition: fill-opacity 0.12s ease;
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
</style>
