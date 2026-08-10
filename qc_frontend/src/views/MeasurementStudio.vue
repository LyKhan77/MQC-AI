<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useCameras } from '../composables/useCameras.js'
import { useToast } from '../composables/useToast.js'
import {
  deleteMeasurementRun,
  listMeasurementRuns,
  processMeasurement,
  saveMeasurementRun,
} from '../api/measurements.js'
import {
  evaluateMeasurementItem,
  measureGeometry,
  summarizeMeasurement,
} from '../utils/measurement.js'

const { t } = useI18n()
const { cameras } = useCameras()
const { log } = useAuditLog()
const { showToast } = useToast()

const source = ref('image')
const selectedFile = ref(null)
const localFileName = ref('')
const runName = ref('')
const selectedCameraId = ref('')
const referencePx = ref(100)
const knownMm = ref(50)
const processed = ref(null)
const items = ref([])
const recentRuns = ref([])
const historyQuery = ref('')
const processing = ref(false)
const evaluated = ref(false)
const readOnly = ref(false)
const errorMessage = ref('')
const selectedCandidate = ref(-1)
const mobileVideo = ref(null)
const mobileCameraOpen = ref(false)
const mobileResolution = ref('')
const mobileVideoAspect = ref('4 / 3')
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const dragging = ref(false)
const dragStart = ref({ x: 0, y: 0, panX: 0, panY: 0 })

let mobileStream = null

const cameraStreamUrl = computed(() => (
  selectedCameraId.value ? `/api/cameras/${selectedCameraId.value}/stream` : ''
))
const displayUrl = computed(() => processed.value?.frame_url || '')
const frameTransform = computed(() => `translate(${panX.value}px, ${panY.value}px) scale(${zoom.value})`)
const readiness = computed(() => processed.value?.readiness || 'idle')
const summaryStatus = computed(() => evaluated.value
  ? summarizeMeasurement(items.value, readiness.value)
  : readiness.value.toUpperCase())
const canProcess = computed(() => !processing.value && (
  source.value === 'image' ? Boolean(selectedFile.value) : source.value === 'live' ? Boolean(selectedCameraId.value) : false
))
const canEvaluate = computed(() => (
  !readOnly.value && Boolean(processed.value) && readiness.value === 'ready' && items.value.length > 0
))
const canSave = computed(() => Boolean(runName.value.trim()) && evaluated.value && items.value.length > 0 && !readOnly.value)
const filteredRuns = computed(() => {
  const query = historyQuery.value.trim().toLowerCase()
  if (!query) return recentRuns.value
  return recentRuns.value.filter((run) => `${run.name} ${run.source_filename}`.toLowerCase().includes(query))
})

function calibrationInput() {
  const length = Number(referencePx.value)
  return {
    point_a: [20, 20],
    point_b: [20 + length, 20],
    known_mm: Number(knownMm.value),
  }
}

function chooseSource(value) {
  source.value = value
  errorMessage.value = ''
  if (value === 'image') selectedCameraId.value = ''
  if (value !== 'mobile') stopMobileCamera()
}

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
  localFileName.value = selectedFile.value?.name || ''
  runName.value = selectedFile.value?.name?.replace(/\.[^.]+$/, '') || runName.value
  processed.value = null
  items.value = []
  evaluated.value = false
  readOnly.value = false
  errorMessage.value = ''
}

async function runMeasurement(input) {
  processing.value = true
  errorMessage.value = ''
  readOnly.value = false
  try {
    processed.value = await processMeasurement({ ...input, calibration: calibrationInput() })
    items.value = []
    evaluated.value = false
    selectedCandidate.value = -1
    resetZoom()
    log('MEASUREMENT_PROCESSED', `${processed.value.source_type}:${processed.value.source_filename}`)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    processing.value = false
  }
}

function onWheel(event) {
  event.preventDefault()
  const delta = event.deltaY > 0 ? -0.1 : 0.1
  zoom.value = Math.max(0.5, Math.min(5, Number((zoom.value + delta).toFixed(2))))
}

function onMouseDown(event) {
  if (event.button !== 0 || event.target.closest('button')) return
  dragging.value = true
  dragStart.value = { x: event.clientX, y: event.clientY, panX: panX.value, panY: panY.value }
}

function onMouseMove(event) {
  if (!dragging.value) return
  panX.value = dragStart.value.panX + event.clientX - dragStart.value.x
  panY.value = dragStart.value.panY + event.clientY - dragStart.value.y
}

function onMouseUp() {
  dragging.value = false
}

function resetZoom() {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
}

function zoomIn() {
  zoom.value = Math.min(5, Number((zoom.value + 0.2).toFixed(2)))
}

function zoomOut() {
  zoom.value = Math.max(0.5, Number((zoom.value - 0.2).toFixed(2)))
}

async function processCurrent() {
  if (!canProcess.value) return
  return runMeasurement({
    file: source.value === 'image' ? selectedFile.value : undefined,
    cameraId: source.value === 'live' ? selectedCameraId.value : undefined,
  })
}

async function openMobileCamera() {
  errorMessage.value = ''
  if (!navigator.mediaDevices?.getUserMedia) {
    errorMessage.value = t('inspection.cameraInsecure')
    return
  }
  try {
    mobileStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        frameRate: { ideal: 30 },
      },
    })
    await nextTick()
    if (!mobileVideo.value) return
    mobileVideo.value.srcObject = mobileStream
    await mobileVideo.value.play()
    const settings = mobileStream.getVideoTracks()[0]?.getSettings?.() || {}
    if (settings.width && settings.height) {
      mobileResolution.value = `${settings.width}×${settings.height}`
      mobileVideoAspect.value = `${settings.width} / ${settings.height}`
    }
    mobileCameraOpen.value = true
  } catch (error) {
    const byName = {
      NotAllowedError: t('inspection.cameraDenied'),
      NotFoundError: t('inspection.cameraNotFound'),
      NotReadableError: t('inspection.cameraInUse'),
      SecurityError: t('inspection.cameraInsecure'),
    }
    errorMessage.value = byName[error?.name] || `${t('inspection.cameraError')}: ${error?.name || error?.message || 'unknown'}`
  }
}

function stopMobileCamera() {
  if (mobileStream) mobileStream.getTracks().forEach((track) => track.stop())
  mobileStream = null
  if (mobileVideo.value) mobileVideo.value.srcObject = null
  mobileCameraOpen.value = false
  mobileResolution.value = ''
}

async function captureMobile() {
  const video = mobileVideo.value
  if (!video || !video.videoWidth || processing.value) return
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.98))
  if (blob) {
    await runMeasurement({
      file: new File([blob], 'mobile.jpg', { type: 'image/jpeg' }),
      sourceType: 'mobile_camera',
    })
  }
}

function candidateKey(candidate, index) {
  return `${candidate.source}-${index}-${candidate.points.flat().join('-')}`
}

function selectCandidate(candidate, index) {
  if (readOnly.value || !processed.value) return
  selectedCandidate.value = index
  const points = candidate.points
  const measured = measureGeometry('edge_length', points, processed.value.calibration)
  const id = `E${items.value.length + 1}`
  items.value.push({
    id,
    type: 'edge_length',
    label: `Edge ${id}`,
    points,
    measured: measured.value,
    unit: measured.unit,
    pixel_value: measured.pixel_value,
    nominal: null,
    tolerance: 2,
    confidence: candidate.confidence,
    status: 'REVIEW',
    reason: 'missing_nominal_or_tolerance',
  })
  evaluated.value = false
}

function addManualItem() {
  if (readOnly.value || !processed.value) return
  const points = [[20, 20], [120, 20]]
  const measured = measureGeometry('edge_length', points, processed.value.calibration)
  const id = `E${items.value.length + 1}`
  items.value.push({
    id,
    type: 'edge_length',
    label: `Manual ${id}`,
    points,
    measured: measured.value,
    unit: measured.unit,
    pixel_value: measured.pixel_value,
    nominal: null,
    tolerance: 2,
    confidence: 1,
    status: 'REVIEW',
    reason: 'missing_nominal_or_tolerance',
  })
  evaluated.value = false
}

function removeItem(index) {
  if (readOnly.value) return
  items.value.splice(index, 1)
  evaluated.value = false
}

function evaluate() {
  if (!canEvaluate.value) return
  items.value = items.value.map((item) => evaluateMeasurementItem(item, processed.value.calibration.valid))
  evaluated.value = true
  log('MEASUREMENT_EVALUATED', `${runName.value || processed.value.source_filename}:${summaryStatus.value}`)
}

async function save() {
  if (!canSave.value) return
  try {
    await saveMeasurementRun({
      name: runName.value.trim(),
      source_key: processed.value.source_key,
      source_filename: processed.value.source_filename,
      source_type: processed.value.source_type,
      source_camera_id: processed.value.source_camera_id,
      calibration: processed.value.calibration,
      items: items.value,
    })
    await loadHistory()
    showToast(t('measurement.saved'))
  } catch (error) {
    errorMessage.value = error.message
  }
}

async function loadHistory() {
  try {
    recentRuns.value = await listMeasurementRuns()
  } catch {
    recentRuns.value = []
  }
}

function openRun(run) {
  runName.value = run.name
  selectedFile.value = null
  localFileName.value = run.source_filename
  source.value = run.source_type === 'live_camera' ? 'live' : run.source_type === 'mobile_camera' ? 'mobile' : 'image'
  processed.value = {
    source_key: null,
    source_type: run.source_type,
    source_filename: run.source_filename,
    source_camera_id: run.source_camera_id,
    frame_url: run.source_url,
    width: run.width,
    height: run.height,
    calibration: run.calibration,
    readiness: run.summary.status === 'PASS' ? 'ready' : 'review',
    reason: '',
    candidates: [],
  }
  items.value = run.items || []
  evaluated.value = true
  readOnly.value = true
  errorMessage.value = ''
  resetZoom()
}

async function removeRun(run) {
  if (!window.confirm(t('measurement.confirmDelete'))) return
  try {
    await deleteMeasurementRun(run.id)
    await loadHistory()
    showToast(t('measurement.deleted'))
  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(loadHistory)
onBeforeUnmount(stopMobileCamera)
</script>

<template>
  <main class="measurement-page measurement-shell">
    <header class="measurement-heading">
      <div>
        <p class="eyebrow">{{ t('measurement.eyebrow') }}</p>
        <h1>{{ t('measurement.title') }}</h1>
        <p>{{ t('measurement.subtitle') }}</p>
      </div>
      <div class="heading-status" :class="`status-${summaryStatus.toLowerCase()}`">
        <span class="status-dot"></span>
        {{ summaryStatus }}
      </div>
    </header>

    <div class="measurement-studio">
      <aside class="measurement-rail">
        <div class="measurement-rail-body scroll-region">
        <section class="rail-section">
          <div class="section-kicker">01 / {{ t('measurement.input') }}</div>
          <div class="source-tabs">
            <button type="button" class="source-image" :class="{ active: source === 'image' }" @click="chooseSource('image')">
              {{ t('measurement.image') }}
            </button>
            <button type="button" class="source-live" :class="{ active: source === 'live' }" @click="chooseSource('live')">
              {{ t('measurement.liveCamera') }}
            </button>
            <button type="button" class="source-mobile" :class="{ active: source === 'mobile' }" @click="chooseSource('mobile')">
              {{ t('inspection.sourceMobileCamera') }}
            </button>
          </div>

          <template v-if="source === 'image'">
            <label class="field-label" for="measurement-file">{{ t('measurement.selectImage') }}</label>
            <input id="measurement-file" type="file" accept="image/*" @change="onFileChange">
            <div v-if="localFileName" class="file-chip">{{ localFileName }}</div>
          </template>

          <template v-else-if="source === 'mobile'">
            <div class="mobile-camera-panel">
              <p class="section-help">{{ t('inspection.mobileHint') }}</p>
              <div class="mobile-preview" :style="{ aspectRatio: mobileVideoAspect }">
                <video ref="mobileVideo" playsinline muted class="mobile-video"></video>
                <span v-if="!mobileCameraOpen">{{ t('measurement.mobileWaiting') }}</span>
              </div>
              <div class="mobile-camera-actions">
                <button type="button" class="btn btn-secondary open-mobile-camera" @click="openMobileCamera">
                  {{ t('inspection.openCamera') }}
                </button>
                <button type="button" class="btn btn-primary capture-mobile" :disabled="!mobileCameraOpen || processing" @click="captureMobile">
                  {{ processing ? t('measurement.processing') : t('inspection.capture') }}
                </button>
              </div>
              <span v-if="mobileResolution" class="camera-resolution">{{ mobileResolution }}</span>
            </div>
          </template>

          <template v-else>
            <label class="field-label" for="measurement-camera">{{ t('measurement.selectCamera') }}</label>
            <select id="measurement-camera" v-model="selectedCameraId" class="camera-select">
              <option value="">{{ t('measurement.noCamera') }}</option>
              <option v-for="camera in cameras" :key="camera.id" :value="camera.id">{{ camera.name }}</option>
            </select>
            <div class="camera-preview">
              <img v-if="cameraStreamUrl" :src="cameraStreamUrl" :alt="t('measurement.cameraPreview')">
              <span v-else>{{ t('measurement.cameraWaiting') }}</span>
            </div>
            <button type="button" class="btn btn-primary trigger-capture" :disabled="!selectedCameraId || processing" @click="processCurrent">
              {{ processing ? t('measurement.processing') : t('measurement.triggerCapture') }}
            </button>
          </template>
        </section>

        <section class="rail-section">
          <div class="section-kicker">02 / {{ t('measurement.calibration') }}</div>
          <p class="section-help">{{ t('measurement.calibrationHelp') }}</p>
          <label class="field-label" for="reference-px">{{ t('measurement.referencePx') }}</label>
          <input id="reference-px" v-model.number="referencePx" type="number" min="1" step="1">
          <label class="field-label" for="known-mm">{{ t('measurement.knownLength') }}</label>
          <div class="input-unit">
            <input id="known-mm" v-model.number="knownMm" type="number" min="0.01" step="0.01">
            <span>mm</span>
          </div>
          <div class="calibration-readout">
            <span>{{ t('measurement.scale') }}</span>
            <strong>{{ processed?.calibration?.mm_per_pixel?.toFixed?.(4) || '—' }} mm/px</strong>
          </div>
        </section>
        </div>

        <section class="rail-section history-section scroll-region">
          <div class="section-kicker">{{ t('measurement.history') }}</div>
          <input v-if="recentRuns.length" v-model="historyQuery" class="history-search" type="search" :placeholder="t('measurement.historySearch')">
          <div v-if="!filteredRuns.length" class="empty-small">{{ recentRuns.length ? t('measurement.noHistoryResults') : t('measurement.noHistory') }}</div>
          <div v-for="run in filteredRuns" :key="run.id" class="history-row">
            <button type="button" class="history-run" @click="openRun(run)">
              <strong>{{ run.name }}</strong>
              <span>{{ run.summary?.status || 'REVIEW' }} · {{ run.created_at }}</span>
            </button>
            <button type="button" class="history-delete" :aria-label="t('measurement.deleteRun')" @click="removeRun(run)">×</button>
          </div>
        </section>
      </aside>

      <section class="measurement-canvas-panel">
        <div class="canvas-toolbar">
          <div>
            <span class="toolbar-label">{{ t('measurement.currentSource') }}</span>
            <strong>{{ processed?.source_filename || t('measurement.noInput') }}</strong>
          </div>
          <button type="button" class="btn btn-primary process-measurement" :disabled="!canProcess || source === 'live'" @click="processCurrent">
            {{ processing ? t('measurement.processing') : t('measurement.process') }}
          </button>
        </div>

        <div
          class="measurement-viewport"
          :class="{ 'is-dragging': dragging }"
          @wheel="onWheel"
          @mousedown="onMouseDown"
          @mousemove="onMouseMove"
          @mouseup="onMouseUp"
          @mouseleave="onMouseUp"
        >
          <div v-if="!processed" class="viewport-empty">
            <div class="empty-crosshair">+</div>
            <strong>{{ t('measurement.viewportEmpty') }}</strong>
            <span>{{ t('measurement.viewportHint') }}</span>
          </div>
          <template v-else>
            <div class="measurement-image-frame" :style="{ transform: frameTransform }">
              <img class="measurement-image" :src="displayUrl" :alt="processed.source_filename" draggable="false">
              <svg class="measurement-overlay" :viewBox="`0 0 ${processed.width} ${processed.height}`" preserveAspectRatio="none" role="img" :aria-label="t('measurement.edgeOverlay')">
              <g
                v-for="(candidate, index) in processed.candidates"
                :key="candidateKey(candidate, index)"
                class="measurement-candidate"
                :class="{ selected: selectedCandidate === index }"
                @click="selectCandidate(candidate, index)"
              >
                <line class="measurement-line-halo" :x1="candidate.points[0][0]" :y1="candidate.points[0][1]" :x2="candidate.points[1][0]" :y2="candidate.points[1][1]"></line>
                <line class="measurement-line" :x1="candidate.points[0][0]" :y1="candidate.points[0][1]" :x2="candidate.points[1][0]" :y2="candidate.points[1][1]"></line>
                <circle class="measurement-point-halo" :cx="candidate.points[0][0]" :cy="candidate.points[0][1]" r="7"></circle>
                <circle class="measurement-point-halo" :cx="candidate.points[1][0]" :cy="candidate.points[1][1]" r="7"></circle>
                <circle class="measurement-point" :cx="candidate.points[0][0]" :cy="candidate.points[0][1]" r="4"></circle>
                <circle class="measurement-point" :cx="candidate.points[1][0]" :cy="candidate.points[1][1]" r="4"></circle>
              </g>
              <g v-if="processed.calibration.point_a && processed.calibration.point_b" class="calibration-reference">
                <line
                  :x1="processed.calibration.point_a[0]"
                  :y1="processed.calibration.point_a[1]"
                  :x2="processed.calibration.point_b[0]"
                  :y2="processed.calibration.point_b[1]"
                ></line>
                <text :x="processed.calibration.point_a[0]" :y="processed.calibration.point_a[1] + 13">REF {{ processed.calibration.known_mm }} mm</text>
              </g>
              <g v-for="item in items" :key="`item-${item.id}`" class="selected-measurement">
                <line class="measurement-line-halo" :x1="item.points[0][0]" :y1="item.points[0][1]" :x2="item.points[1][0]" :y2="item.points[1][1]"></line>
                <line class="measurement-line" :x1="item.points[0][0]" :y1="item.points[0][1]" :x2="item.points[1][0]" :y2="item.points[1][1]"></line>
                <text :x="item.points[0][0]" :y="item.points[0][1] - 6">{{ item.id }} · {{ Number(item.measured).toFixed(1) }} {{ item.unit }}</text>
              </g>
              </svg>
            </div>
            <div class="measurement-zoom-controls" :aria-label="t('measurement.zoomControls')">
              <button type="button" class="measurement-zoom-button measurement-zoom-out" :aria-label="t('measurement.zoomOut')" @click.stop="zoomOut">−</button>
              <span class="measurement-zoom-value mono">{{ Math.round(zoom * 100) }}%</span>
              <button type="button" class="measurement-zoom-button measurement-zoom-in" :aria-label="t('measurement.zoomIn')" @click.stop="zoomIn">+</button>
              <button type="button" class="measurement-zoom-reset" @click.stop="resetZoom">{{ t('measurement.zoomResetShort') }}</button>
            </div>
          </template>
        </div>

        <div v-if="processed" class="candidate-strip">
          <div class="strip-header">
            <span>{{ t('measurement.candidates') }}</span>
            <span>{{ processed.candidates.length }} {{ t('measurement.detected') }}</span>
          </div>
          <button v-for="(candidate, index) in processed.candidates" :key="candidateKey(candidate, index)" type="button" class="candidate-card" :class="{ selected: selectedCandidate === index }" @click="selectCandidate(candidate, index)">
            <span class="candidate-line"></span>
            <strong>L{{ index + 1 }}</strong>
            <span>{{ candidate.length_px.toFixed(1) }} px</span>
            <small>{{ candidate.source }} · {{ candidate.confidence.toFixed(2) }}</small>
          </button>
          <button type="button" class="candidate-card manual-card" :disabled="readOnly" @click="addManualItem">
            <strong>＋</strong>
            <span>{{ t('measurement.addManual') }}</span>
          </button>
        </div>
      </section>

      <aside class="measurement-results">
        <section class="results-header">
          <div class="section-kicker">03 / {{ t('measurement.evaluate') }}</div>
          <label class="field-label" for="run-name">{{ t('measurement.runName') }}</label>
          <input id="run-name" v-model="runName" class="run-name" type="text" :placeholder="t('measurement.runNamePlaceholder')">
        </section>

        <section class="items-section scroll-region">
          <div class="section-title-row">
            <h2>{{ t('measurement.items') }}</h2>
            <span>{{ items.length }}</span>
          </div>
          <div v-if="!items.length" class="empty-items">{{ t('measurement.noItems') }}</div>
          <article v-for="(item, index) in items" :key="item.id" class="measurement-item">
            <div class="item-topline">
              <div><strong>{{ item.id }}</strong><span>{{ item.label }}</span></div>
              <button type="button" class="item-remove" :disabled="readOnly" @click="removeItem(index)">×</button>
            </div>
            <div class="item-measured">
              <strong>{{ Number(item.measured).toFixed(2) }}</strong>
              <span>{{ item.unit }}</span>
              <span class="measurement-status" :class="`item-${(item.status || 'review').toLowerCase()}`">{{ item.status || 'REVIEW' }}</span>
            </div>
            <div class="item-fields">
              <label>{{ t('measurement.nominal') }}<input v-model.number="item.nominal" class="item-nominal" type="number" step="0.01" :disabled="readOnly"></label>
              <label>{{ t('measurement.tolerance') }}<input v-model.number="item.tolerance" class="item-tolerance" type="number" min="0" step="0.01" :disabled="readOnly"></label>
            </div>
            <div class="item-limits">
              <span>{{ t('measurement.range') }}</span>
              <strong>{{ item.min ?? '—' }} – {{ item.max ?? '—' }} {{ item.unit }}</strong>
              <span>{{ t('measurement.deviation') }} {{ item.deviation == null ? '—' : Number(item.deviation).toFixed(2) }}</span>
            </div>
            <div v-if="item.reason" class="item-reason">{{ item.reason }}</div>
          </article>
        </section>

        <section class="result-actions">
          <div class="measurement-summary" :class="`summary-${summaryStatus.toLowerCase()}`">
            <span>{{ t('measurement.summary') }}</span>
            <strong>{{ summaryStatus }}</strong>
          </div>
          <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
          <button type="button" class="btn btn-secondary evaluate-measurement" :disabled="!canEvaluate" @click="evaluate">{{ t('measurement.evaluateDimension') }}</button>
          <button type="button" class="btn btn-primary save-measurement" :disabled="!canSave" @click="save">{{ t('measurement.save') }}</button>
        </section>
      </aside>
    </div>
  </main>
</template>

<style scoped>
.measurement-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px 24px 24px;
  background: var(--color-surface-1);
  color: var(--color-ink);
}

.measurement-heading {
  flex: 0 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 22px;
}

.eyebrow,
.section-kicker,
.toolbar-label {
  margin: 0 0 6px;
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.measurement-heading h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.measurement-heading p:not(.eyebrow) {
  margin: 6px 0 0;
  color: var(--color-ink-muted);
  font-size: 14px;
}

.heading-status,
.measurement-summary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border: 1px solid var(--color-hairline);
  background: var(--color-canvas);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: var(--color-ink-subtle);
}

.status-pass .status-dot,
.summary-pass strong,
.item-pass { color: var(--color-success); }
.status-pass .status-dot { background: var(--color-success); }
.status-fail .status-dot { background: var(--color-error); }
.status-review .status-dot { background: var(--color-warning); }

.measurement-studio {
  flex: 1 1 auto;
  display: flex;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--color-hairline);
  background: var(--color-canvas);
}

.measurement-rail,
.measurement-results {
  flex-shrink: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-canvas);
}

.measurement-rail { width: 340px; flex-basis: 340px; border-right: 1px solid var(--color-hairline); }
.measurement-results { width: 380px; flex-basis: 380px; border-left: 1px solid var(--color-hairline); }

.measurement-rail-body { min-height: 0; flex: 1 1 auto; }

.rail-section,
.results-header,
.items-section,
.result-actions {
  padding: 22px;
  border-bottom: 1px solid var(--color-hairline);
}

.section-help,
.empty-small,
.empty-items {
  margin: 0 0 12px;
  color: var(--color-ink-muted);
  font-size: 12px;
  line-height: 1.45;
}

.source-tabs { display: grid; grid-template-columns: repeat(3, 1fr); margin-bottom: 16px; }
.source-tabs button {
  padding: 9px 6px;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
  color: var(--color-ink-muted);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
}
.source-tabs button + button { border-left: 0; }
.source-tabs button.active { background: var(--color-primary); border-color: var(--color-primary); color: var(--color-on-primary); }

.field-label,
.item-fields label {
  display: block;
  margin: 12px 0 5px;
  color: var(--color-ink-muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

input,
select {
  box-sizing: border-box;
  width: 100%;
  min-height: 34px;
  border: 1px solid var(--color-hairline-strong);
  border-radius: 0;
  padding: 7px 9px;
  background: var(--color-canvas);
  color: var(--color-ink);
  font: inherit;
  font-size: 13px;
}

input:focus-visible,
select:focus-visible,
button:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 1px; }
.file-chip { margin-top: 10px; padding: 8px; overflow: hidden; background: var(--color-surface-1); color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.input-unit { display: flex; align-items: center; gap: 7px; }
.input-unit input { flex: 1; }
.input-unit span { color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 12px; }
.calibration-readout { display: flex; justify-content: space-between; gap: 8px; margin-top: 12px; color: var(--color-ink-muted); font-size: 11px; }
.calibration-readout strong { color: var(--color-primary); font-family: var(--font-mono); font-weight: 400; }

.camera-preview { display: grid; place-items: center; min-height: 120px; margin: 12px 0; overflow: hidden; background: var(--color-inverse-canvas); color: var(--color-inverse-ink-muted); font-size: 11px; }
.camera-preview img { display: block; width: 100%; height: 120px; object-fit: cover; }

.mobile-camera-panel { display: grid; gap: 10px; }
.mobile-preview { position: relative; display: grid; min-height: 150px; place-items: center; overflow: hidden; background: var(--color-inverse-canvas); color: var(--color-inverse-ink-muted); font-size: 11px; }
.mobile-video { display: block; width: 100%; height: 100%; min-height: 150px; object-fit: cover; }
.mobile-camera-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.camera-resolution { color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 10px; }

.btn { min-height: 36px; border: 1px solid transparent; border-radius: 0; padding: 8px 12px; cursor: pointer; font: inherit; font-size: 12px; font-weight: 600; }
.btn:disabled { cursor: not-allowed; opacity: 0.45; }
.btn-primary { background: var(--color-primary); color: var(--color-on-primary); }
.btn-secondary { border-color: var(--color-hairline-strong); background: var(--color-canvas); color: var(--color-ink); }
.trigger-capture { width: 100%; }

.history-section { border-bottom: 0; }
.scroll-region { min-height: 0; overflow-y: auto; overscroll-behavior: contain; }
.measurement-rail .history-section { flex: 0 1 280px; min-height: 180px; }
.measurement-results .results-header { flex: 0 0 auto; }
.history-search { min-height: 30px; margin: 8px 0; font-size: 11px; }
.history-row { display: flex; align-items: stretch; border-top: 1px solid var(--color-hairline); }
.history-run { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 3px; padding: 9px 0; border: 0; background: transparent; color: var(--color-ink); text-align: left; cursor: pointer; }
.history-run span { overflow: hidden; color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.history-delete,
.item-remove { border: 0; background: transparent; color: var(--color-ink-muted); cursor: pointer; font-size: 18px; }

.measurement-canvas-panel { display: flex; flex: 1 1 auto; min-width: 0; min-height: 0; flex-direction: column; overflow: hidden; background: var(--color-surface-1); }
.canvas-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 64px; padding: 12px 16px; border-bottom: 1px solid var(--color-hairline); background: var(--color-canvas); }
.canvas-toolbar strong { display: block; max-width: 420px; overflow: hidden; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.measurement-viewport { position: relative; display: grid; flex: 1 1 auto; min-height: 0; place-items: center; padding: 28px; overflow: hidden; cursor: grab; background: var(--color-inverse-canvas); }
.measurement-viewport.is-dragging { cursor: grabbing; }
.measurement-image-frame { position: relative; transform-origin: center; transition: transform 0.05s linear; }
.measurement-image { display: block; max-width: 100%; max-height: 100%; object-fit: contain; pointer-events: none; }
.measurement-overlay { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: auto; }
.measurement-candidate { pointer-events: all; cursor: pointer; opacity: 0.9; }
.measurement-line-halo { stroke: var(--color-canvas); stroke-width: 6; vector-effect: non-scaling-stroke; }
.measurement-line { stroke: var(--color-info); stroke-width: 3; vector-effect: non-scaling-stroke; }
.measurement-point-halo { fill: var(--color-canvas); }
.measurement-point { fill: var(--color-info); }
.measurement-candidate.selected { opacity: 1; }
.measurement-candidate.selected .measurement-line { stroke: var(--color-warning); stroke-width: 4; }
.measurement-candidate.selected .measurement-point { fill: var(--color-warning); }
.selected-measurement { pointer-events: none; }
.selected-measurement .measurement-line { stroke: var(--color-success); stroke-width: 4; stroke-dasharray: 7 4; }
.selected-measurement text { fill: var(--color-success); font-family: var(--font-mono); font-size: 14px; font-weight: 600; paint-order: stroke; stroke: var(--color-inverse-canvas); stroke-width: 5px; }
.calibration-reference { pointer-events: none; }
.calibration-reference line { stroke: var(--color-warning); stroke-width: 2.5; stroke-dasharray: 5 4; vector-effect: non-scaling-stroke; }
.calibration-reference text { fill: var(--color-warning); font-family: var(--font-mono); font-size: 13px; font-weight: 600; paint-order: stroke; stroke: var(--color-inverse-canvas); stroke-width: 5px; }
.viewport-empty { display: grid; place-items: center; gap: 8px; color: var(--color-inverse-ink-muted); text-align: center; }
.viewport-empty span { max-width: 250px; font-size: 12px; }
.empty-crosshair { color: var(--color-primary); font-family: var(--font-mono); font-size: 42px; font-weight: 300; }

.candidate-strip { display: flex; gap: 10px; min-height: 100px; padding: 14px 18px; overflow-x: auto; border-top: 1px solid var(--color-hairline); background: var(--color-canvas); }
.strip-header { display: flex; min-width: 100px; flex-direction: column; justify-content: center; gap: 4px; color: var(--color-ink-muted); font-size: 11px; }
.strip-header span:last-child { font-family: var(--font-mono); }
.candidate-card { display: grid; min-width: 120px; grid-template-columns: 16px 1fr; align-content: center; gap: 2px 6px; padding: 8px; border: 1px solid var(--color-hairline); background: var(--color-surface-1); color: var(--color-ink); text-align: left; cursor: pointer; font-size: 11px; }
.candidate-card.selected { border-color: var(--color-warning); background: color-mix(in srgb, var(--color-warning) 12%, var(--color-canvas)); }
.candidate-card span, .candidate-card small { grid-column: 2; color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 10px; }
.candidate-line { grid-column: 1; grid-row: 1 / span 3; align-self: center; width: 14px; height: 2px; background: var(--color-info); }
.manual-card { display: flex; align-items: center; justify-content: center; gap: 6px; }

.results-header { padding-bottom: 14px; }
.items-section { flex: 1 1 auto; }
.section-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-title-row h2 { margin: 0; font-size: 15px; }
.section-title-row span { color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 12px; }
.measurement-item { margin-top: 14px; padding: 16px; border: 1px solid var(--color-hairline); background: var(--color-surface-1); }
.item-topline { display: flex; justify-content: space-between; }
.item-topline div { display: flex; gap: 7px; align-items: baseline; }
.item-topline strong { color: var(--color-primary); font-family: var(--font-mono); font-size: 12px; }
.item-topline span { color: var(--color-ink-muted); font-size: 12px; }
.item-measured { display: flex; align-items: baseline; gap: 6px; margin: 12px 0 4px; }
.item-measured strong { font-family: var(--font-mono); font-size: 30px; font-weight: 400; }
.item-measured > span:not(.measurement-status) { color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 11px; }
.measurement-status { margin-left: auto; font-family: var(--font-mono); font-size: 11px; font-weight: 600; }
.item-fail { color: var(--color-error); }
.item-review { color: var(--color-warning); }
.item-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.item-fields label { margin: 0; }
.item-limits { display: grid; grid-template-columns: 1fr auto; gap: 4px; margin-top: 10px; color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 10px; }
.item-limits strong { color: var(--color-ink); font-weight: 400; text-align: right; }
.item-limits span:last-child { grid-column: 1 / -1; }
.item-reason { margin-top: 8px; color: var(--color-warning); font-size: 11px; }
.result-actions { flex: 0 0 auto; display: grid; gap: 9px; border-bottom: 0; }
.measurement-summary { justify-content: space-between; }
.measurement-summary strong { color: var(--color-ink); }
.summary-pass strong { color: var(--color-success); }
.summary-fail strong { color: var(--color-error); }
.summary-review strong { color: var(--color-warning); }
.error-message { margin: 0; color: var(--color-error); font-size: 12px; }
.measurement-zoom-controls { position: absolute; right: 18px; bottom: 18px; z-index: 2; display: flex; align-items: center; gap: 4px; padding: 5px; border: 1px solid var(--color-hairline); background: var(--color-canvas); }
.measurement-zoom-button,
.measurement-zoom-reset { min-height: 34px; border: 1px solid var(--color-hairline); background: transparent; color: var(--color-ink); cursor: pointer; font: inherit; }
.measurement-zoom-button { width: 34px; font-size: 20px; line-height: 1; }
.measurement-zoom-button:hover,
.measurement-zoom-reset:hover { background: var(--color-surface-1); }
.measurement-zoom-reset { padding: 0 10px; font-size: 11px; }
.measurement-zoom-value { min-width: 48px; color: var(--color-ink); font-size: 12px; text-align: center; }

@media (max-width: 1180px) {
  .measurement-rail { width: 300px; flex-basis: 300px; }
  .measurement-results { width: 340px; flex-basis: 340px; }
  .measurement-page { padding: 20px; }
}

@media (max-width: 900px) {
  .measurement-page { overflow-y: auto; }
  .measurement-studio { flex-direction: column; flex: 0 0 auto; min-height: 880px; overflow: visible; }
  .measurement-rail, .measurement-results { width: auto; flex-basis: auto; border: 0; }
  .measurement-rail, .measurement-results, .scroll-region { overflow: visible; }
  .measurement-rail { border-bottom: 1px solid var(--color-hairline); }
  .measurement-results { border-top: 1px solid var(--color-hairline); }
  .measurement-viewport { min-height: 360px; }
}
</style>
