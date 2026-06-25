<script setup>
import { computed } from 'vue'
import { useInspection } from '../composables/useInspection.js'
import { defectColor } from '../utils/defect.js'

const { selected, hoveredDefectId } = useInspection()

const coating = computed(() => selected.value?.defects.filter((d) => d.category === 'coating') ?? [])
const welding = computed(() => selected.value?.defects.filter((d) => d.category === 'welding') ?? [])

function pct(c) {
  return `${Math.round(c * 100)}%`
}
</script>

<template>
  <aside class="defect-panel">
    <header class="panel-head">
      <h3>Defect Details</h3>
      <span v-if="selected" class="mono fname">{{ selected.filename }}</span>
    </header>

    <div v-if="selected" class="panel-body">
      <section class="group">
        <h4>Coating Defects <span class="grp-count mono">{{ coating.length }}</span></h4>
        <p v-if="!coating.length" class="none mono">—</p>
        <ul>
          <li
            v-for="d in coating"
            :key="d.id"
            class="defect-row"
            :class="{ hot: hoveredDefectId === d.id }"
            @mouseenter="hoveredDefectId = d.id"
            @mouseleave="hoveredDefectId = null"
          >
            <span class="swatch" :style="{ background: defectColor(d.type) }"></span>
            <span class="type">{{ d.type }}</span>
            <span class="conf mono">{{ pct(d.confidence) }}</span>
          </li>
        </ul>
      </section>

      <section class="group">
        <h4>Welding Defects <span class="grp-count mono">{{ welding.length }}</span></h4>
        <p v-if="!welding.length" class="none mono">—</p>
        <ul>
          <li
            v-for="d in welding"
            :key="d.id"
            class="defect-row"
            :class="{ hot: hoveredDefectId === d.id }"
            @mouseenter="hoveredDefectId = d.id"
            @mouseleave="hoveredDefectId = null"
          >
            <span class="swatch" :style="{ background: defectColor(d.type) }"></span>
            <span class="type">{{ d.type }}</span>
            <span class="conf mono">{{ pct(d.confidence) }}</span>
          </li>
        </ul>
      </section>
    </div>

    <p v-else class="none mono">Tidak ada gambar terpilih.</p>
  </aside>
</template>

<style scoped>
.defect-panel {
  width: var(--sidebar-right); flex-shrink: 0;
  background: var(--bg-panel); border-left: 1px solid var(--border-subtle);
  display: flex; flex-direction: column; overflow: hidden;
}
.panel-head { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-subtle); }
.panel-head h3 { margin: 0 0 0.25rem; font-size: 0.95rem; }
.panel-head .fname { font-size: 0.7rem; color: var(--text-muted); }
.panel-body { padding: 1rem; overflow-y: auto; flex: 1; }
.group { margin-bottom: 1.25rem; }
.group h4 {
  margin: 0 0 0.5rem; font-size: 0.8rem; color: var(--text-secondary);
  display: flex; align-items: center; gap: 0.5rem;
}
.grp-count { background: var(--bg-hover); padding: 0 0.4rem; border-radius: 8px; font-size: 0.7rem; }
.group ul { list-style: none; margin: 0; padding: 0; }
.defect-row {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.4rem 0.5rem; border-radius: var(--radius-btn); cursor: pointer;
}
.defect-row:hover, .defect-row.hot { background: var(--bg-hover); }
.swatch { width: 12px; height: 12px; border-radius: 2px; flex-shrink: 0; }
.type { flex: 1; font-size: 0.8rem; text-transform: capitalize; }
.conf { font-size: 0.75rem; color: var(--text-secondary); }
.none { color: var(--text-muted); font-size: 0.8rem; }
</style>
