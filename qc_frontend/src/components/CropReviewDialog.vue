<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()
const props = defineProps({
  show: Boolean,
  crops: { type: Array, default: () => [] },
  error: { type: String, default: '' },
})
const emit = defineEmits(['cancel', 'confirm'])

const batchName = ref('')
const items = ref([])

watch(
  () => props.show,
  (open) => {
    if (!open) return
    const ts = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19)
    batchName.value = `batch_${ts}`
    items.value = props.crops.map((url) => ({ url, name: url.split('/').pop(), selected: true }))
  },
  { immediate: true },
)

watch(
  () => props.crops,
  (crops) => {
    if (props.show) {
      items.value = crops.map((url) => ({ url, name: url.split('/').pop(), selected: true }))
    }
  },
)

const selectedCount = computed(() => items.value.filter((c) => c.selected).length)

function confirm() {
  emit('confirm', {
    batchName: batchName.value,
    selectedFiles: items.value.filter((c) => c.selected).map((c) => c.name),
  })
}
</script>

<template>
  <div v-if="show" class="dialog-overlay" @click.self="emit('cancel')">
    <div class="dialog">
      <h3 class="dialog-title">{{ t('sendToQC.title') }}</h3>
      <div class="dialog-body">
        <div class="form-row">
          <label>{{ t('sendToQC.batchName') }}</label>
          <input v-model="batchName" class="text-input" :placeholder="t('sendToQC.batchNamePlaceholder')" />
        </div>
        <div class="form-row">
          <div class="crop-head">
            <label>{{ t('sendToQC.cropReview') }} ({{ selectedCount }}/{{ items.length }})</label>
            <div class="crop-head-actions">
              <button class="btn-ghost btn-sm" @click="items.forEach((c) => (c.selected = true))">
                {{ t('sendToQC.selectAll') }}
              </button>
              <button class="btn-ghost btn-sm" @click="items.forEach((c) => (c.selected = false))">
                {{ t('sendToQC.selectNone') }}
              </button>
            </div>
          </div>
          <p v-if="items.length === 0" class="form-hint">{{ t('sendToQC.noCrops') }}</p>
          <div v-else class="crop-grid">
            <label v-for="(c, i) in items" :key="i" :class="['crop-cell', { unselected: !c.selected }]">
              <input type="checkbox" v-model="c.selected" class="crop-check" />
              <img :src="c.url" class="crop-thumb" alt="crop" />
            </label>
          </div>
        </div>
        <p v-if="error" class="send-error">{{ error }}</p>
      </div>
      <div class="dialog-actions">
        <button class="btn-ghost" @click="emit('cancel')">{{ t('sendToQC.cancel') }}</button>
        <button class="btn-primary" :disabled="!batchName.trim() || selectedCount === 0" @click="confirm">
          {{ t('sendToQC.send') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  width: 480px;
  max-width: 90vw;
}
.dialog-title {
  margin: 0;
  padding: 16px 24px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
  border-bottom: 1px solid var(--color-hairline);
  letter-spacing: 0.16px;
}
.dialog-body {
  padding: 24px;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 16px;
}
.form-row label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.text-input {
  padding: 8px 12px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-bottom: 2px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 14px;
  outline: none;
  letter-spacing: 0.16px;
}
.text-input:focus {
  border-bottom-color: var(--color-primary);
}
.form-hint {
  font-size: 11px;
  color: var(--color-ink-subtle);
  letter-spacing: 0.16px;
}
.crop-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.crop-head-actions {
  display: flex;
  gap: 8px;
}
.btn-primary {
  padding: 9px 16px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  font-family: var(--font-sans);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.btn-primary:disabled {
  opacity: 0.4;
  cursor: default;
}
.btn-ghost {
  padding: 9px 16px;
  background: transparent;
  color: var(--color-ink-muted);
  border: none;
  font-family: var(--font-sans);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.btn-ghost:hover {
  background: var(--color-surface-1);
}
.btn-sm {
  font-size: 12px;
  padding: 2px 6px;
}
.crop-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}
.crop-cell {
  position: relative;
  display: block;
  cursor: pointer;
}
.crop-cell.unselected {
  opacity: 0.4;
}
.crop-check {
  position: absolute;
  top: 4px;
  left: 4px;
  z-index: 1;
}
.crop-thumb {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border: 1px solid var(--color-hairline);
  border-radius: 0px;
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-hairline);
}
.send-error {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--color-error);
  letter-spacing: 0.16px;
}
</style>
