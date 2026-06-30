<script setup>
import { ref, watch } from 'vue'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()

const props = defineProps({
  show: Boolean,
  editing: { type: Object, default: null },
})

const emit = defineEmits(['cancel', 'save'])

const SWATCHES = [
  '#4589ff',
  '#08bdba',
  '#24a148',
  '#f1c21b',
  '#ff832b',
  '#fa4d56',
  '#da1e28',
  '#8a3ffc',
  '#d12771',
  '#9f1853',
  '#6f6f6f',
  '#198038',
]

const name = ref('')
const category = ref('coating')
const color = ref(SWATCHES[0])

watch(
  () => props.show,
  (open) => {
    if (!open) return
    name.value = props.editing?.name ?? ''
    category.value = props.editing?.category ?? 'coating'
    color.value = props.editing?.color ?? SWATCHES[0]
  },
  { immediate: true },
)

function save() {
  emit('save', { name: name.value.trim(), category: category.value, color: color.value })
}
</script>

<template>
  <div v-if="show" class="dialog-overlay" @click.self="emit('cancel')">
    <div class="dialog">
      <h3 class="dialog-title">{{ editing ? t('defectClasses.editTitle') : t('defectClasses.addTitle') }}</h3>
      <div class="dialog-body">
        <div class="form-row">
          <label>{{ t('defectClasses.name') }}</label>
          <input v-model="name" class="text-input" :placeholder="t('defectClasses.namePlaceholder')" />
        </div>
        <div class="form-row">
          <label>{{ t('defectClasses.category') }}</label>
          <select v-model="category" class="text-input">
            <option value="coating">{{ t('defectClasses.coating') }}</option>
            <option value="welding">{{ t('defectClasses.welding') }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>{{ t('defectClasses.color') }}</label>
          <div class="swatches">
            <button
              v-for="s in SWATCHES"
              :key="s"
              type="button"
              :class="['swatch', { active: color === s }]"
              :style="{ background: s }"
              @click="color = s"
            ></button>
          </div>
        </div>
      </div>
      <div class="dialog-actions">
        <button class="btn-ghost" @click="emit('cancel')">{{ t('common.cancel') }}</button>
        <button class="btn-primary" :disabled="!name.trim()" @click="save">{{ t('common.save') }}</button>
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
  width: 420px;
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
}
.text-input:focus {
  border-bottom-color: var(--color-primary);
}
.swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.swatch {
  width: 24px;
  height: 24px;
  border: 1px solid var(--color-hairline);
  border-radius: 0;
  cursor: pointer;
}
.swatch.active {
  outline: 2px solid var(--color-ink);
  outline-offset: 1px;
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-hairline);
}
.dialog-actions .btn-ghost {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  cursor: pointer;
  font-size: 14px;
}
.dialog-actions .btn-primary {
  padding: 8px 16px;
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  color: var(--color-on-primary);
  cursor: pointer;
  font-size: 14px;
}
.dialog-actions .btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
