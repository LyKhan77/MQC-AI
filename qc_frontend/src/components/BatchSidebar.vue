<script setup>
import { useInspection } from '../composables/useInspection.js'

const { batch, images, selectedId, loadBatch, selectImage } = useInspection()

async function onLoad() {
  try {
    await loadBatch()
  } catch (e) {
    console.error(e)
  }
}
</script>

<template>
  <aside class="batch-sidebar">
    <div class="batch-head">
      <button class="btn-load" @click="onLoad">Load Batch</button>
      <p v-if="batch" class="batch-meta mono">{{ batch.batch_name }}</p>
      <p v-if="batch" class="batch-path mono">{{ batch.source_path }}</p>
    </div>

    <ul class="batch-list">
      <li
        v-for="img in images"
        :key="img.id"
        class="batch-item"
        :class="{ active: img.id === selectedId }"
        @click="selectImage(img.id)"
      >
        <span class="dot" :class="img.status === 'defect' ? 'bad' : 'ok'"></span>
        <span class="fname mono">{{ img.filename }}</span>
        <span v-if="img.defects.length" class="count mono">{{ img.defects.length }}</span>
      </li>
    </ul>

    <p v-if="!images.length" class="empty">Belum ada batch dimuat.</p>
  </aside>
</template>

<style scoped>
.batch-sidebar {
  width: var(--sidebar-left); flex-shrink: 0;
  background: var(--bg-panel); border-right: 1px solid var(--border-subtle);
  display: flex; flex-direction: column; overflow: hidden;
}
.batch-head { padding: 0.75rem; border-bottom: 1px solid var(--border-subtle); }
.btn-load {
  width: 100%; padding: 0.5rem; cursor: pointer;
  background: var(--accent-primary); color: var(--text-primary);
  border: none; border-radius: var(--radius-btn); font-weight: 600;
}
.btn-load:hover { background: #2b7bff; }
.batch-meta { font-size: 0.75rem; color: var(--text-secondary); margin: 0.5rem 0 0.15rem; }
.batch-path { font-size: 0.7rem; color: var(--text-muted); margin: 0; word-break: break-all; }

.batch-list { list-style: none; margin: 0; padding: 0.25rem; overflow-y: auto; flex: 1; }
.batch-item {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.4rem 0.5rem; cursor: pointer; border-radius: var(--radius-btn);
  border-left: 3px solid transparent; color: var(--text-secondary);
}
.batch-item:hover { background: var(--bg-hover); }
.batch-item.active {
  background: var(--bg-hover); border-left-color: var(--accent-primary);
  color: var(--text-primary);
}
.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot.bad { background: var(--status-error); }
.dot.ok { background: var(--status-success); }
.fname { font-size: 0.75rem; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.count {
  font-size: 0.7rem; background: var(--status-error); color: #fff;
  padding: 0 0.35rem; border-radius: 8px;
}
.empty { color: var(--text-muted); font-size: 0.8rem; padding: 1rem; }
</style>
