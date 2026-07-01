<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useDefectClasses } from '../composables/useDefectClasses.js'
import { useSettings } from '../composables/useSettings.js'

const { t } = useI18n()
const { classes, refresh: refreshClasses } = useDefectClasses()
const { settings } = useSettings()

const props = defineProps({ show: Boolean })
const emit = defineEmits(['cancel', 'confirm'])

const confidence = ref(0.5)

const activeClasses = computed(() => classes.value.filter((c) => c.enabled))
const strategyLabel = computed(() =>
  settings.value.defectStrategy === 'sam3_prompt'
    ? t('settings.strategySam3')
    : t('settings.strategyMock'),
)

watch(
  () => props.show,
  (open) => {
    if (!open) return
    refreshClasses()
    confidence.value = Number(settings.value.qcConfidenceThreshold ?? 0.5)
  },
  { immediate: true },
)

function confirm() {
  emit('confirm', { confidenceThreshold: Number(confidence.value) })
}
</script>

<template>
  <div v-if="show" class="dialog-overlay" @click.self="emit('cancel')">
    <div class="dialog">
      <h3 class="dialog-title">{{ t('qc.runTitle') }}</h3>
      <div class="dialog-body">
        <div class="summary-row">
          <span class="summary-label">{{ t('qc.strategy') }}</span>
          <span class="summary-value mono">{{ strategyLabel }}</span>
        </div>

        <div class="form-row">
          <label>{{ t('qc.confidence') }}</label>
          <input
            type="number"
            min="0"
            max="1"
            step="0.05"
            v-model="confidence"
            class="text-input"
          />
        </div>

        <div class="form-row">
          <label>{{ t('qc.activeClasses') }} ({{ activeClasses.length }})</label>
          <div v-if="activeClasses.length" class="class-chips">
            <span v-for="c in activeClasses" :key="c.id" class="class-chip">
              <span class="chip-swatch" :style="{ background: c.color }"></span>
              {{ c.name }}
            </span>
          </div>
          <p v-else class="warn-text">{{ t('qc.noActiveClasses') }}</p>
        </div>
      </div>
      <div class="dialog-actions">
        <button class="btn-ghost" @click="emit('cancel')">{{ t('common.cancel') }}</button>
        <button class="btn-primary" :disabled="!activeClasses.length" @click="confirm">
          {{ t('qc.runConfirm') }}
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
  width: 460px;
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
.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-bottom: 12px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--color-hairline);
}
.summary-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.summary-value {
  font-size: 13px;
  color: var(--color-ink);
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
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
  width: 120px;
}
.text-input:focus {
  border-bottom-color: var(--color-primary);
}
.class-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.class-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  font-size: 12px;
  letter-spacing: 0.16px;
}
.chip-swatch {
  width: 10px;
  height: 10px;
  flex-shrink: 0;
}
.warn-text {
  font-size: 12px;
  color: var(--color-error);
  margin: 0;
  letter-spacing: 0.16px;
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
.mono {
  font-family: var(--font-mono);
}
</style>
