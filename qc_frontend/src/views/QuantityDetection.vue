<script setup>
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useSettings } from '../composables/useSettings.js'
import { detectQuantityImage, createQuantityCheck } from '../api/quantity.js'
import { perClassFromDetections, addCounts, totalOf, computeVerdict } from '../utils/quantity.js'

const { t } = useI18n()
const { log } = useAuditLog()
const { settings } = useSettings()

const REVIEWER = 'inspector@gspemail.com'

const results = ref([])        // [{ name, url, total, perClass, detections, width, height }]
const running = ref(false)
const errorMsg = ref('')
const expectedTotal = ref('')
const tolerance = ref(0)
const saved = ref(false)

const hasModel = computed(() => !!settings.value.quantityModel)
const sessionPerClass = computed(() => results.value.reduce((acc, r) => addCounts(acc, r.perClass), {}))
const sessionTotal = computed(() => totalOf(sessionPerClass.value))
const verdict = computed(() => computeVerdict({
  total: sessionTotal.value,
  perClass: sessionPerClass.value,
  expectedTotal: expectedTotal.value,
  tolerance: tolerance.value,
}))

async function addFiles(files) {
  errorMsg.value = ''
  saved.value = false
  running.value = true
  try {
    for (const f of files) {
      const res = await detectQuantityImage(f)
      results.value.push({
        name: f.name,
        url: URL.createObjectURL(f),
        total: res.total,
        perClass: res.per_class || perClassFromDetections(res.detections),
        detections: res.detections || [],
        width: res.width,
        height: res.height,
      })
    }
  } catch (e) {
    errorMsg.value = e.message || t('common.error')
  } finally {
    running.value = false
  }
}

function onPick(e) {
  const files = Array.from(e.target.files || [])
  if (files.length) addFiles(files)
  e.target.value = ''
}

function removeResult(idx) {
  results.value.splice(idx, 1)
  saved.value = false
}

function resetSession() {
  results.value = []
  expectedTotal.value = ''
  tolerance.value = 0
  saved.value = false
  errorMsg.value = ''
}

async function saveCheck() {
  if (!results.value.length) return
  const payload = {
    source_type: 'image',
    count_mode: 'static',
    input_summary: `${results.value.length} ${t('quantity.imagesUnit')}`,
    model_used: settings.value.quantityModel,
    confidence_used: Number(settings.value.quantityConfidenceThreshold) || 0.5,
    total_count: sessionTotal.value,
    per_class_counts: sessionPerClass.value,
    expected_total: expectedTotal.value === '' ? null : Number(expectedTotal.value),
    expected_per_class: {},
    tolerance: Number(tolerance.value) || 0,
    verdict: verdict.value,
    reviewer: REVIEWER,
    notes: '',
  }
  await createQuantityCheck(payload)
  log('QUANTITY_CHECK', `Total ${payload.total_count}, verdict ${payload.verdict}`)
  saved.value = true
}

defineExpose({ addFiles, saveCheck, resetSession, sessionTotal, sessionPerClass, verdict })
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('quantity.title') }}</h2>
      <p class="page-subtitle">{{ t('quantity.subtitle') }}</p>
    </div>

    <p v-if="!hasModel" class="empty-state">{{ t('quantity.noModel') }}</p>

    <template v-else>
      <div class="filter-bar">
        <label class="btn-sm primary">
          {{ t('quantity.addImages') }}
          <input type="file" accept="image/*" multiple hidden @change="onPick" />
        </label>
        <input type="number" min="0" v-model="expectedTotal" class="text-input" :placeholder="t('quantity.expectedTotal')" />
        <input type="number" min="0" v-model="tolerance" class="text-input" :placeholder="t('quantity.tolerance')" />
        <button class="btn-sm" @click="resetSession">{{ t('quantity.reset') }}</button>
      </div>

      <p v-if="running" class="mono">{{ t('quantity.running') }}</p>
      <p v-if="errorMsg" class="empty-state">{{ errorMsg }}</p>

      <div class="session-summary">
        <span class="mono">{{ t('quantity.total') }}: {{ sessionTotal }}</span>
        <span v-if="verdict !== 'none'" class="status-pill" :class="verdict === 'pass' ? 'verdict-pass' : 'verdict-fail'">
          {{ verdict === 'pass' ? t('quantity.pass') : t('quantity.fail') }}
        </span>
        <button class="btn-sm primary" :disabled="!results.length" @click="saveCheck">{{ t('quantity.save') }}</button>
        <span v-if="saved" class="mono">{{ t('quantity.saved') }}</span>
      </div>

      <table class="data-table" v-if="Object.keys(sessionPerClass).length">
        <thead><tr><th>{{ t('quantity.class') }}</th><th>{{ t('quantity.count') }}</th></tr></thead>
        <tbody>
          <tr v-for="(n, label) in sessionPerClass" :key="label"><td>{{ label }}</td><td class="mono">{{ n }}</td></tr>
        </tbody>
      </table>

      <div class="result-grid">
        <div v-for="(r, idx) in results" :key="idx" class="result-card">
          <img :src="r.url" :alt="r.name" class="result-thumb" />
          <div class="mono">{{ r.name }} — {{ r.total }}</div>
          <button class="btn-sm btn-danger-sm" @click="removeResult(idx)">{{ t('quantity.removeInput') }}</button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.session-summary { display: flex; align-items: center; gap: 12px; margin: 12px 0; }
.verdict-pass { background: var(--color-success); color: var(--color-on-primary); }
.verdict-fail { background: var(--color-error); color: var(--color-on-primary); }
.result-grid { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 12px; }
.result-card { border: 1px solid var(--color-hairline); padding: 8px; }
.result-thumb { display: block; width: 160px; height: 120px; object-fit: contain; }
.mono { font-family: var(--font-mono); }
</style>
