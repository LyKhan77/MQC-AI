<script setup>
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useToast } from '../composables/useToast.js'
import { useSettings } from '../composables/useSettings.js'
import { detectQuantityImage, createQuantityCheck } from '../api/quantity.js'
import { perClassFromDetections, addCounts, totalOf, computeVerdict } from '../utils/quantity.js'

const { t } = useI18n()
const { log } = useAuditLog()
const { showToast } = useToast()
const { settings } = useSettings()

const REVIEWER = 'inspector@gspemail.com'

const source = ref('image')
const results = ref([]) // [{ name, url, total, perClass, detections, width, height, cropKey, crops }]
const selectedIdx = ref(0)
const running = ref(false)
const errorMsg = ref('')
const expectedTotal = ref('')
const tolerance = ref(0)

const hasModel = computed(() => !!settings.value.quantityModel)
const selectedResult = computed(() => results.value[selectedIdx.value] || null)
const sessionPerClass = computed(() => results.value.reduce((acc, r) => addCounts(acc, r.perClass), {}))
const sessionTotal = computed(() => totalOf(sessionPerClass.value))
const hasTarget = computed(() => expectedTotal.value !== '' && expectedTotal.value !== null)
const totalDelta = computed(() => (hasTarget.value ? sessionTotal.value - Number(expectedTotal.value) : null))
const verdict = computed(() => computeVerdict({
  total: sessionTotal.value,
  perClass: sessionPerClass.value,
  expectedTotal: expectedTotal.value,
  tolerance: tolerance.value,
}))

async function addFiles(files) {
  errorMsg.value = ''
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
        width: res.width || 1,
        height: res.height || 1,
        cropKey: res.crop_key || '',
        crops: res.crops || [],
      })
      selectedIdx.value = results.value.length - 1
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

function revokeResult(item) {
  if (item.url) URL.revokeObjectURL(item.url)
}

function removeResult(idx) {
  const [removed] = results.value.splice(idx, 1)
  if (removed) revokeResult(removed)
  if (selectedIdx.value >= results.value.length) {
    selectedIdx.value = Math.max(0, results.value.length - 1)
  }
}

function resetSession() {
  results.value.forEach(revokeResult)
  results.value = []
  selectedIdx.value = 0
  expectedTotal.value = ''
  tolerance.value = 0
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
    expected_total: hasTarget.value ? Number(expectedTotal.value) : null,
    expected_per_class: {},
    tolerance: Number(tolerance.value) || 0,
    verdict: verdict.value,
    reviewer: REVIEWER,
    notes: '',
    inputs: results.value.map((r) => ({
      name: r.name,
      total: r.total,
      per_class: r.perClass,
      crop_key: r.cropKey,
      crops: r.crops.map((c) => c.file),
    })),
  }
  await createQuantityCheck(payload)
  log('QUANTITY_CHECK', `Total ${payload.total_count}, verdict ${payload.verdict}`)
  showToast(t('quantity.saved'))
}

defineExpose({ addFiles, saveCheck, resetSession, sessionTotal, sessionPerClass, verdict })
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('quantity.title') }}</h2>
      <p class="page-subtitle">{{ t('quantity.subtitle') }}</p>
    </div>

    <div v-if="!hasModel" class="empty-state">
      <p>{{ t('quantity.noModel') }}</p>
      <router-link :to="{ name: 'settings' }" class="btn-sm primary">{{ t('quantity.goSettings') }}</router-link>
    </div>

    <template v-else>
      <div class="segmented" role="group" :aria-label="t('quantity.source')">
        <button class="segment-btn" :class="{ active: source === 'image' }" :aria-pressed="source === 'image'" @click="source = 'image'">{{ t('quantity.sourceImage') }}</button>
        <button class="segment-btn" disabled :title="t('quantity.comingSoon')">{{ t('quantity.sourceVideo') }}</button>
        <button class="segment-btn" disabled :title="t('quantity.comingSoon')">{{ t('quantity.sourceCamera') }}</button>
        <span class="ctx mono">{{ settings.quantityModel }} - {{ Number(settings.quantityConfidenceThreshold).toFixed(2) }}</span>
      </div>

      <div class="result-band">
        <div class="total-block">
          <div class="total-num mono">{{ sessionTotal }}</div>
          <div class="total-label">{{ t('quantity.total') }}</div>
        </div>
        <div class="verdict-block">
          <span v-if="verdict !== 'none'" class="status-pill" :class="verdict === 'pass' ? 'verdict-pass' : 'verdict-fail'">
            {{ verdict === 'pass' ? t('quantity.pass') : t('quantity.fail') }}
          </span>
          <div v-if="hasTarget" class="target-readout mono">
            {{ t('quantity.expectedTotal') }} {{ expectedTotal }} +/- {{ tolerance }} - Delta {{ totalDelta > 0 ? '+' : '' }}{{ totalDelta }}
          </div>
        </div>
        <div class="target-inputs">
          <label class="field">
            <span class="field-label">{{ t('quantity.expectedTotal') }}</span>
            <input type="number" min="0" v-model="expectedTotal" class="text-input" />
          </label>
          <label class="field">
            <span class="field-label">{{ t('quantity.tolerance') }}</span>
            <input type="number" min="0" v-model="tolerance" class="text-input" />
          </label>
        </div>
        <div class="band-actions">
          <button class="btn-sm primary" :disabled="!results.length" @click="saveCheck">{{ t('quantity.save') }}</button>
          <button class="btn-sm" :disabled="!results.length" @click="resetSession">{{ t('quantity.reset') }}</button>
        </div>
      </div>

      <p v-if="running" class="mono status-line">{{ t('quantity.running') }}</p>
      <p v-if="errorMsg" class="status-line error">{{ errorMsg }}</p>

      <table class="data-table" v-if="Object.keys(sessionPerClass).length">
        <thead><tr><th>{{ t('quantity.class') }}</th><th>{{ t('quantity.count') }}</th></tr></thead>
        <tbody>
          <tr v-for="(n, label) in sessionPerClass" :key="label"><td>{{ label }}</td><td class="mono">{{ n }}</td></tr>
        </tbody>
      </table>

      <div v-if="results.length" class="inference">
        <div class="anno-wrap" v-if="selectedResult">
          <img :src="selectedResult.url" :alt="selectedResult.name" class="anno-img" draggable="false" />
          <svg class="anno-overlay" :viewBox="`0 0 ${selectedResult.width} ${selectedResult.height}`" preserveAspectRatio="none">
            <rect
              v-for="(d, i) in selectedResult.detections"
              :key="i"
              class="det-box"
              :x="d.box[0]"
              :y="d.box[1]"
              :width="d.box[2] - d.box[0]"
              :height="d.box[3] - d.box[1]"
            />
          </svg>
          <span class="count-badge mono">{{ selectedResult.total }}</span>
        </div>

        <div class="filmstrip">
          <button
            v-for="(r, idx) in results"
            :key="idx"
            class="film-thumb"
            :class="{ active: idx === selectedIdx }"
            :aria-pressed="idx === selectedIdx"
            @click="selectedIdx = idx"
          >
            <img :src="r.url" :alt="r.name" />
            <span class="film-count mono">{{ r.total }}</span>
            <span class="film-remove" @click.stop="removeResult(idx)" :title="t('quantity.removeInput')">x</span>
          </button>
          <label class="film-add btn-sm primary">
            {{ t('quantity.addImages') }}
            <input type="file" accept="image/*" multiple hidden @change="onPick" />
          </label>
        </div>

        <div class="evidence-head">
          <span class="evidence-title">{{ t('quantity.evidence') }} - {{ selectedResult ? selectedResult.crops.length : 0 }}</span>
        </div>
        <div class="evi-grid">
          <figure v-for="(c, i) in (selectedResult ? selectedResult.crops : [])" :key="i" class="evi-card">
            <img :src="c.url" :alt="c.label" class="evi-crop" />
            <figcaption class="mono">{{ c.label }}</figcaption>
          </figure>
        </div>
      </div>

      <div v-else class="evidence-head">
        <label class="btn-sm primary">
          {{ t('quantity.addImages') }}
          <input type="file" accept="image/*" multiple hidden @change="onPick" />
        </label>
        <p class="empty-state">{{ t('quantity.emptyEvidence') }}</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.segmented { display: inline-flex; align-items: center; border: 1px solid var(--color-hairline); margin-bottom: 16px; }
.segment-btn { min-height: 32px; padding: 6px 14px; background: transparent; border: 0; border-right: 1px solid var(--color-hairline); color: var(--color-ink-muted); font-family: var(--font-sans); font-size: 13px; cursor: pointer; }
.segment-btn.active { background: var(--color-primary); color: var(--color-on-primary); }
.segment-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ctx { padding: 0 12px; color: var(--color-ink-subtle); font-size: 12px; }

.result-band { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; padding: 20px; border: 1px solid var(--color-hairline); background: var(--color-surface-1); margin-bottom: 16px; }
.total-block { display: flex; flex-direction: column; }
.total-num { font-size: 48px; line-height: 1; color: var(--color-ink); }
.total-label { font-size: 12px; letter-spacing: 0.32px; text-transform: uppercase; color: var(--color-ink-muted); margin-top: 4px; }
.verdict-block { display: flex; flex-direction: column; gap: 6px; }
.target-readout { font-size: 12px; color: var(--color-ink-muted); }
.target-inputs { display: flex; gap: 16px; margin-left: auto; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field-label { font-size: 12px; color: var(--color-ink-muted); letter-spacing: 0.16px; }
.band-actions { display: flex; gap: 8px; }

.status-pill { display: inline-block; padding: 3px 10px; font-size: 12px; font-weight: 600; letter-spacing: 0.32px; }
.verdict-pass { background: var(--color-success); color: var(--color-on-primary); }
.verdict-fail { background: var(--color-error); color: var(--color-on-primary); }
.status-line { margin: 8px 0; font-size: 13px; }
.status-line.error { color: var(--color-error); }

.text-input { padding: 8px 12px; background: var(--color-canvas); border: 1px solid var(--color-hairline); border-bottom: 2px solid var(--color-hairline); color: var(--color-ink); font-family: var(--font-sans); font-size: 14px; outline: none; width: 96px; }
.text-input:focus { border-bottom-color: var(--color-primary); }

.data-table { width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 16px; }
.data-table th { text-align: left; padding: 10px 16px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.32px; color: var(--color-ink-muted); border-bottom: 1px solid var(--color-hairline); background: var(--color-surface-1); }
.data-table td { padding: 8px 16px; border-bottom: 1px solid var(--color-hairline); color: var(--color-ink); }

.evidence-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.evidence-title { font-size: 12px; letter-spacing: 0.32px; text-transform: uppercase; color: var(--color-ink-muted); }
.inference { display: flex; flex-direction: column; gap: 12px; }
.anno-wrap { position: relative; width: 100%; max-width: 640px; background: var(--color-surface-1); border: 1px solid var(--color-hairline); }
.anno-img { display: block; width: 100%; max-height: 480px; object-fit: contain; }
.anno-overlay { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.det-box { fill: none; stroke: var(--color-primary); stroke-width: 2; vector-effect: non-scaling-stroke; }
.count-badge { position: absolute; top: 8px; right: 8px; padding: 2px 8px; background: var(--color-primary); color: var(--color-on-primary); font-size: 12px; font-weight: 600; }
.filmstrip { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.film-thumb { position: relative; width: 84px; height: 64px; padding: 0; border: 1px solid var(--color-hairline); background: var(--color-surface-1); cursor: pointer; }
.film-thumb:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.film-thumb.active { border-color: var(--color-primary); box-shadow: inset 0 0 0 1px var(--color-primary); }
.film-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.film-count { position: absolute; bottom: 2px; left: 2px; padding: 0 5px; background: var(--color-primary); color: var(--color-on-primary); font-size: 11px; }
.film-remove { position: absolute; top: 0; right: 0; width: 18px; height: 18px; line-height: 18px; text-align: center; background: var(--color-error); color: var(--color-on-primary); font-size: 13px; }
.film-add { display: inline-flex; align-items: center; height: 64px; }
.evi-grid { display: flex; flex-wrap: wrap; gap: 10px; }
.evi-card { margin: 0; border: 1px solid var(--color-hairline); width: 110px; }
.evi-crop { display: block; width: 100%; height: 90px; object-fit: contain; background: var(--color-surface-1); }
.evi-card figcaption { padding: 3px 6px; font-size: 11px; color: var(--color-ink-muted); text-align: center; }

.btn-sm { padding: 5px 12px; background: transparent; border: 1px solid var(--color-hairline); color: var(--color-primary); font-family: var(--font-sans); font-size: 12px; cursor: pointer; letter-spacing: 0.16px; }
.btn-sm:hover { background: var(--color-surface-1); }
.btn-sm.primary { background: var(--color-primary); color: var(--color-on-primary); border-color: var(--color-primary); }
.btn-sm:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-danger-sm { color: var(--color-error); border-color: var(--color-error); }
.empty-state { padding: 24px 16px; text-align: center; color: var(--color-ink-subtle); font-size: 14px; }
.mono { font-family: var(--font-mono); }
</style>
