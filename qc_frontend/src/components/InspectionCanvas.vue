<script setup>
import { ref, computed } from 'vue'
import { useInspection } from '../composables/useInspection.js'
import { useI18n } from '../composables/useI18n.js'
import { defectColor } from '../utils/defect.js'

const { selected, hoveredDefectId, toggleReviewed, isReviewed } = useInspection()
const { t } = useI18n()

const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const showAnnotation = ref(true)
const dragging = ref(false)
const dragStart = ref({ x: 0, y: 0, panX: 0, panY: 0 })

function pointsAttr(polygon) {
  return polygon.map((p) => p.join(',')).join(' ')
}

function onWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  zoom.value = Math.max(0.5, Math.min(5, zoom.value + delta))
}

function onMouseDown(e) {
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

const frameTransform = computed(() => `translate(${panX.value}px, ${panY.value}px) scale(${zoom.value})`)
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
          class="overlay"
          :viewBox="`0 0 ${selected.width} ${selected.height}`"
          preserveAspectRatio="none"
        >
          <polygon
            v-for="d in selected.defects"
            :key="d.id"
            :points="pointsAttr(d.polygon)"
            :stroke="defectColor(d.type)"
            :fill="defectColor(d.type)"
            :fill-opacity="hoveredDefectId === d.id ? 0.4 : 0.15"
            :data-defect-id="d.id"
            class="defect-poly"
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
.defect-poly {
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
  pointer-events: auto;
  cursor: pointer;
  transition: fill-opacity 0.12s ease;
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
