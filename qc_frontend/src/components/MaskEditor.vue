<script setup>
import { computed, ref, watch } from 'vue'

import { toImageCoords } from '../utils/canvasCoords.js'

const props = defineProps({
  src: { type: String, required: true },
  width: { type: Number, required: true },
  height: { type: Number, required: true },
  modelValue: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'finish', 'clear'])
const points = ref(props.modelValue.map(([x, y]) => [x, y]))

watch(() => props.modelValue, (value) => {
  points.value = value.map(([x, y]) => [x, y])
}, { deep: true })

const polygonPoints = computed(() => points.value.map(([x, y]) => `${x},${y}`).join(' '))

function updatePoints(nextPoints) {
  points.value = nextPoints
  emit('update:modelValue', nextPoints)
}

function pointAt(event) {
  const svg = event.currentTarget
  const { x, y } = toImageCoords(event.clientX, event.clientY, svg.getBoundingClientRect(), props.width, props.height)
  return [x, y]
}

function addPoint(event) {
  if (props.disabled) return
  updatePoints([...points.value, pointAt(event)])
}

function finish() {
  if (!props.disabled && points.value.length >= 3) emit('finish', points.value.map(([x, y]) => [x, y]))
}

function finishOnDoubleClick(event) {
  if (props.disabled) return
  const point = pointAt(event)
  let next = points.value
  while (next.length > 1 && next.at(-1)?.[0] === point[0] && next.at(-1)?.[1] === point[1]) {
    next = next.slice(0, -1)
  }
  if (next.at(-1)?.[0] !== point[0] || next.at(-1)?.[1] !== point[1]) next = [...next, point]
  if (next !== points.value) updatePoints(next)
  if (next.length >= 3) emit('finish', next.map(([x, y]) => [x, y]))
}

function undo() {
  if (!props.disabled && points.value.length) updatePoints(points.value.slice(0, -1))
}

function clear() {
  if (props.disabled) return
  updatePoints([])
  emit('clear')
}
</script>

<template>
  <div class="mask-editor" :class="{ 'is-disabled': disabled }">
    <svg
      data-testid="mask-canvas"
      class="mask-canvas"
      :viewBox="`0 0 ${width} ${height}`"
      :aria-disabled="disabled"
      role="img"
      @click="addPoint"
      @dblclick="finishOnDoubleClick"
    >
      <image :href="src" :width="width" :height="height" preserveAspectRatio="none" pointer-events="none" />
      <polygon v-if="points.length >= 3" class="mask-polygon" :points="polygonPoints" />
      <polyline v-else-if="points.length > 1" class="mask-line" :points="polygonPoints" />
      <circle
        v-for="([x, y], index) in points"
        :key="`${index}-${x}-${y}`"
        class="mask-handle"
        :cx="x"
        :cy="y"
        r="3"
        pointer-events="none"
      />
    </svg>

    <div class="mask-actions" aria-label="Mask controls">
      <button type="button" data-testid="mask-finish" :disabled="disabled || points.length < 3" @click="finish">Finish</button>
      <button type="button" data-testid="mask-undo" :disabled="disabled || !points.length" @click="undo">Undo</button>
      <button type="button" data-testid="mask-clear" :disabled="disabled || !points.length" @click="clear">Clear</button>
    </div>
  </div>
</template>

<style scoped>
.mask-editor {
  width: min(100%, 960px);
}

.mask-canvas {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  background: var(--color-surface-1);
  cursor: crosshair;
  outline: 1px solid var(--color-hairline);
}

.mask-editor.is-disabled .mask-canvas {
  cursor: not-allowed;
  opacity: 0.65;
}

.mask-line,
.mask-polygon {
  fill: var(--color-primary);
  fill-opacity: 0.12;
  stroke: var(--color-primary);
  stroke-width: 1.5;
  vector-effect: non-scaling-stroke;
}

.mask-line {
  fill: none;
}

.mask-handle {
  fill: var(--color-canvas);
  stroke: var(--color-primary);
  stroke-width: 1.5;
  vector-effect: non-scaling-stroke;
}

.mask-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.mask-actions button {
  min-height: 32px;
  padding: 0 16px;
  border: 0;
  border-radius: 0;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font: inherit;
  cursor: pointer;
}

.mask-actions button:disabled {
  background: var(--color-surface-2);
  color: var(--color-ink-subtle);
  cursor: not-allowed;
}
</style>
