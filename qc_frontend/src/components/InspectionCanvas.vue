<script setup>
import { useInspection } from '../composables/useInspection.js'
import { defectColor } from '../utils/defect.js'

const { selected, hoveredDefectId } = useInspection()

function pointsAttr(polygon) {
  return polygon.map((p) => p.join(',')).join(' ')
}
</script>

<template>
  <section class="canvas-wrapper">
    <div
      v-if="selected"
      class="image-frame"
      :style="{ aspectRatio: `${selected.width} / ${selected.height}` }"
    >
      <img :src="selected.url" :alt="selected.filename" class="insp-img" />
      <svg
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
          @mouseenter="hoveredDefectId = d.id"
          @mouseleave="hoveredDefectId = null"
        />
      </svg>
    </div>
    <p v-else class="empty">Pilih gambar dari batch…</p>
  </section>
</template>

<style scoped>
.canvas-wrapper {
  flex: 1; background: var(--bg-canvas); overflow: hidden;
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.image-frame {
  position: relative;
  max-width: 100%; max-height: 100%;
}
.insp-img { display: block; width: 100%; height: 100%; object-fit: contain; }
.overlay { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.defect-poly {
  stroke-width: 2;
  vector-effect: non-scaling-stroke; /* garis tetap 2px walau gambar di-scale */
  pointer-events: auto; cursor: pointer;
  transition: fill-opacity 0.12s ease;
}
.empty { color: var(--text-muted); }
</style>
