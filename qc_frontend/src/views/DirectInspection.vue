<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { detectInspection, inspectionToQc, previewAutocrop } from '../api/inspection.js'
import { useCameras } from '../composables/useCameras.js'
import { useI18n } from '../composables/useI18n.js'
import { useSettings } from '../composables/useSettings.js'
import BaseModal from '../components/BaseModal.vue'
import MaskEditor from '../components/MaskEditor.vue'

const { t } = useI18n()
const router = useRouter()
const { cameras, refresh } = useCameras()
const { settings } = useSettings()

const source = ref('upload')
const cropMode = ref('full')
const debugCrop = ref(false)
const selectedCameraId = ref('')
const stack = ref([])
const staged = ref([])
const masking = ref(false)
const busy = ref(false)
const errorMsg = ref('')
const videoEl = ref(null)
const selectedIdx = ref(0)
const showSendDialog = ref(false)
const liveOverlayEnabled = ref(true)
const liveOverlayBox = ref(null)
const liveOverlaySize = ref({ width: 4, height: 3 })
const livePreviewQuality = ref(null)
const liveResolution = ref('')
const liveVideoAspect = ref('4 / 3')

let mediaStream = null
let previewTimer = null
let previewInFlight = false

const selectedCamera = computed(() => cameras.value.find((c) => c.id === selectedCameraId.value))
const rawStreamUrl = computed(() =>
  selectedCameraId.value ? `/api/cameras/${selectedCameraId.value}/stream` : '',
)
const selectedCapture = computed(() => stack.value[selectedIdx.value] || null)
const defectCaptureCount = computed(() => stack.value.filter((item) => item.verdict === 'defect').length)
const cleanCaptureCount = computed(() => stack.value.filter((item) => item.verdict !== 'defect').length)
const defectTotal = computed(() =>
  stack.value.reduce((total, item) => total + (item.defects?.length || 0), 0),
)
const modelContext = computed(() => ({
  model: settings.value.qcModel || '-',
  confidence: Number(settings.value.qcConfidenceThreshold || 0).toFixed(2),
  strategy: settings.value.defectStrategy || '-',
}))
const allCropsReady = computed(() => stack.value.every((item) => (
  item.crop_mode !== 'auto' || item.crop_quality?.status === 'ok' || item.cropConfirmed
)))
const liveOverlayActive = computed(() => liveOverlayEnabled.value && cropMode.value === 'auto')
const stagedPending = computed(() => staged.value.some((item) => item.status !== 'done'))

let statusTimer = null
onMounted(() => {
  refresh()
  statusTimer = setInterval(refresh, 10000)
})
onBeforeUnmount(() => {
  if (statusTimer) clearInterval(statusTimer)
  stopCamera()
  staged.value.forEach((item) => URL.revokeObjectURL(item.previewUrl))
})

async function pushDetect(opts) {
  busy.value = true
  errorMsg.value = ''
  try {
    const result = await detectInspection({ ...opts, cropMode: cropMode.value, debugCrop: debugCrop.value })
    result.cropConfirmed = result.crop_mode !== 'auto' || result.crop_quality?.status === 'ok'
    stack.value.push(result)
    selectedIdx.value = stack.value.length - 1
  } catch (err) {
    errorMsg.value = err?.message || 'error'
  } finally {
    busy.value = false
  }
}

async function onFiles(event) {
  const files = Array.from(event.target.files || [])
  staged.value.push(...files.map((file, index) => ({
    id: `${Date.now()}-${index}-${file.name}`,
    file,
    previewUrl: URL.createObjectURL(file),
    width: 0,
    height: 0,
    maskPolygon: [],
    maskStatus: masking.value ? 'editing' : 'none',
    status: 'staged',
    error: '',
  })))
  event.target.value = ''
}

function setStageSize(item, event) {
  item.width = event.target.naturalWidth
  item.height = event.target.naturalHeight
}

function toggleMasking() {
  staged.value.forEach((item) => {
    item.maskStatus = masking.value ? 'editing' : 'none'
    if (!masking.value) item.maskPolygon = []
  })
}

function finishMask(item, polygon) {
  if (polygon.length < 3) {
    item.error = t('inspection.maskValidation')
    return
  }
  item.maskPolygon = polygon
  item.maskStatus = 'ready'
  item.error = ''
}

function clearMask(item) {
  item.maskPolygon = []
  item.maskStatus = masking.value ? 'editing' : 'none'
}

function removeStage(index) {
  URL.revokeObjectURL(staged.value[index].previewUrl)
  staged.value.splice(index, 1)
}

async function processStaged() {
  busy.value = true
  errorMsg.value = ''
  for (const item of staged.value.filter((stage) => stage.status !== 'done')) {
    item.status = 'processing'
    item.error = ''
    const opts = {
      file: item.file,
      cropMode: masking.value ? 'full' : cropMode.value,
      debugCrop: masking.value ? false : debugCrop.value,
    }
    if (item.maskStatus === 'ready' && item.maskPolygon.length) opts.maskPolygon = item.maskPolygon
    try {
      const result = await detectInspection(opts)
      result.cropConfirmed = result.crop_mode !== 'auto' || result.crop_quality?.status === 'ok'
      stack.value.push(result)
      selectedIdx.value = stack.value.length - 1
      item.status = 'done'
    } catch (err) {
      item.status = 'error'
      item.error = err?.message || t('inspection.processingError')
    }
  }
  busy.value = false
}

function captureServer() {
  if (!selectedCameraId.value) return
  return pushDetect({ cameraId: selectedCameraId.value })
}

async function openCamera() {
  errorMsg.value = ''
  // getUserMedia is undefined on a non-secure context (plain http over LAN IP).
  if (!navigator.mediaDevices?.getUserMedia) {
    errorMsg.value = t('inspection.cameraInsecure')
    return
  }
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        frameRate: { ideal: 30 },
      },
    })
    if (videoEl.value) {
      videoEl.value.srcObject = mediaStream
      await videoEl.value.play()
      const trackSettings = mediaStream.getVideoTracks()[0]?.getSettings?.() || {}
      if (trackSettings.width && trackSettings.height) {
        liveResolution.value = `${trackSettings.width}×${trackSettings.height}`
        liveVideoAspect.value = `${trackSettings.width} / ${trackSettings.height}`
      }
      startLivePreview()
    }
  } catch (err) {
    const byName = {
      NotAllowedError: t('inspection.cameraDenied'),
      NotFoundError: t('inspection.cameraNotFound'),
      NotReadableError: t('inspection.cameraInUse'),
      SecurityError: t('inspection.cameraInsecure'),
    }
    errorMsg.value = byName[err?.name] || `${t('inspection.cameraError')}: ${err?.name || err?.message || 'unknown'}`
  }
}

function stopCamera() {
  stopLivePreview()
  if (!mediaStream) return
  mediaStream.getTracks().forEach((track) => track.stop())
  mediaStream = null
  liveResolution.value = ''
  liveOverlayBox.value = null
  livePreviewQuality.value = null
}

function stopLivePreview() {
  if (previewTimer) clearInterval(previewTimer)
  previewTimer = null
  previewInFlight = false
}

function startLivePreview() {
  stopLivePreview()
  if (!liveOverlayActive.value) return
  previewLiveFrame()
  previewTimer = setInterval(previewLiveFrame, 400)
}

async function previewLiveFrame() {
  const video = videoEl.value
  if (!liveOverlayActive.value || previewInFlight || !video?.videoWidth) return
  previewInFlight = true
  try {
    const scale = Math.min(1, 480 / video.videoWidth)
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale))
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale))
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height)
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.7))
    if (!blob) return
    const result = await previewAutocrop(new File([blob], 'preview.jpg', { type: 'image/jpeg' }))
    liveOverlayBox.value = result.box
    liveOverlaySize.value = { width: result.width, height: result.height }
    livePreviewQuality.value = result.quality
  } catch {
    liveOverlayBox.value = null
    livePreviewQuality.value = null
  } finally {
    previewInFlight = false
  }
}

function onLiveOverlayToggle() {
  if (liveOverlayEnabled.value) startLivePreview()
  else {
    stopLivePreview()
    liveOverlayBox.value = null
    livePreviewQuality.value = null
  }
}

function setCropMode(next) {
  cropMode.value = next
  if (next === 'auto') startLivePreview()
  else {
    stopLivePreview()
    liveOverlayBox.value = null
    livePreviewQuality.value = null
  }
}

async function captureMobile() {
  const video = videoEl.value
  if (!video || !video.videoWidth) return
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.98))
  if (blob) await pushDetect({ file: new File([blob], 'mobile.jpg', { type: 'image/jpeg' }) })
}

function confirmCrop(index) {
  const item = stack.value[index]
  if (item?.crop_quality?.status === 'review') item.cropConfirmed = true
}

function retakeFullFrame(index) {
  removeCapture(index)
  cropMode.value = 'full'
}

function removeCapture(index) {
  stack.value.splice(index, 1)
  if (selectedIdx.value >= stack.value.length) {
    selectedIdx.value = Math.max(0, stack.value.length - 1)
  }
}

function openSendReview() {
  if (!stack.value.length) return
  showSendDialog.value = true
}

function closeSendReview() {
  showSendDialog.value = false
}

async function sendToStudio() {
  if (!stack.value.length || !allCropsReady.value) {
    errorMsg.value = t('inspection.cropReviewRequired')
    return
  }
  busy.value = true
  errorMsg.value = ''
  try {
    const { batch_id } = await inspectionToQc(stack.value.map((item) => ({
      key: item.key,
      defects: item.defects,
      ...(item.mask_polygon?.length ? { mask_polygon: item.mask_polygon } : {}),
    })))
    closeSendReview()
    router.push({ name: 'qc', query: { batch: batch_id } })
  } catch (err) {
    errorMsg.value = err?.message || 'error'
  } finally {
    busy.value = false
  }
}

function setSource(next) {
  source.value = next
  if (next !== 'mobile') stopCamera()
}

function polyPoints(poly) {
  return (poly || []).map((point) => point.join(',')).join(' ')
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('inspection.title') }}</h2>
      <p class="page-subtitle">{{ t('inspection.subtitle') }}</p>
    </div>

    <div class="context-strip" aria-label="Direct inspection context">
      <div class="context-item">
        <span class="context-label">{{ t('inspection.qcModel') }}</span>
        <span class="context-value mono">{{ modelContext.model }}</span>
      </div>
      <div class="context-item">
        <span class="context-label">{{ t('inspection.confidence') }}</span>
        <span class="context-value mono">{{ modelContext.confidence }}</span>
      </div>
      <div class="context-item">
        <span class="context-label">{{ t('inspection.strategy') }}</span>
        <span class="context-value mono">{{ modelContext.strategy }}</span>
      </div>
      <div class="context-item">
        <span class="context-label">{{ t('inspection.cropMode') }}</span>
        <span class="context-value">{{ cropMode === 'auto' ? t('inspection.cropAuto') : t('inspection.cropFull') }}</span>
      </div>
    </div>

    <div class="controls">
      <div class="seg">
        <button class="seg-btn" :class="{ active: source === 'upload' }" @click="setSource('upload')">
          {{ t('inspection.sourceUpload') }}
        </button>
        <button class="seg-btn" :class="{ active: source === 'server' }" @click="setSource('server')">
          {{ t('inspection.sourceServerCamera') }}
        </button>
        <button class="seg-btn" :class="{ active: source === 'mobile' }" @click="setSource('mobile')">
          {{ t('inspection.sourceMobileCamera') }}
        </button>
      </div>
      <div class="seg">
        <span class="seg-label">{{ t('inspection.cropMode') }}</span>
        <button class="seg-btn" :class="{ active: cropMode === 'full' }" @click="setCropMode('full')">
          {{ t('inspection.cropFull') }}
        </button>
        <button class="seg-btn" :class="{ active: cropMode === 'auto' }" :disabled="source === 'upload' && masking" @click="setCropMode('auto')">
          {{ t('inspection.cropAuto') }}
        </button>
        <label class="debug-toggle">
          <input v-model="debugCrop" type="checkbox" :disabled="cropMode !== 'auto' || (source === 'upload' && masking)" />
          <span>{{ t('inspection.debugCrop') }}</span>
        </label>
      </div>
    </div>

    <div class="source-panel">
      <div v-if="source === 'upload'">
        <p class="source-hint">{{ t('inspection.uploadHint') }}</p>
        <input type="file" accept="image/*" multiple :disabled="busy" @change="onFiles" />
        <label class="debug-toggle masking-toggle">
          <input v-model="masking" type="checkbox" :disabled="busy" @change="toggleMasking" />
          <span>{{ t('inspection.masking') }}</span>
        </label>
        <div v-if="staged.length" class="mask-stage-list">
          <section v-for="(item, index) in staged" :key="item.id" class="mask-stage-item">
            <div class="mask-stage-heading">
              <strong>{{ item.file.name }}</strong>
              <span class="mono">{{ item.status === 'processing' ? t('inspection.processing') : item.status === 'done' ? t('inspection.processed') : item.maskStatus === 'ready' ? t('inspection.maskReady') : t('inspection.fullFrame') }}</span>
              <button class="btn-sm btn-danger-sm" :disabled="item.status === 'processing'" @click="removeStage(index)">{{ t('inspection.removeCapture') }}</button>
            </div>
            <img class="mask-stage-preview" :src="item.previewUrl" :alt="item.file.name" @load="setStageSize(item, $event)" />
            <MaskEditor
              v-if="masking && item.width && item.height"
              :src="item.previewUrl"
              :width="item.width"
              :height="item.height"
              :model-value="item.maskPolygon"
              :disabled="item.status === 'processing' || item.status === 'done'"
              @update:model-value="item.maskPolygon = $event"
              @finish="finishMask(item, $event)"
              @clear="clearMask(item)"
            />
            <p v-if="masking && item.maskStatus !== 'ready'" class="mask-stage-status">{{ t('inspection.maskValidation') }}</p>
            <p v-if="item.error" class="mask-stage-error">{{ item.error }}</p>
          </section>
          <button class="btn-primary process-qc" :disabled="busy || !stagedPending" @click="processStaged">{{ t('inspection.processQc') }}</button>
        </div>
      </div>
      <div v-else-if="source === 'server'" class="server-cam">
        <p class="source-hint">{{ t('inspection.serverHint') }}</p>
        <div class="row">
          <select v-model="selectedCameraId" class="text-input">
            <option value="">{{ t('inspection.selectCamera') }}</option>
            <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
              {{ camera.name }}
            </option>
          </select>
          <button class="btn-sm" :disabled="busy || !selectedCameraId" @click="captureServer">
            {{ t('inspection.capture') }}
          </button>
        </div>

        <div class="status-strip">
          <div class="status-item">
            <span class="status-led" :class="selectedCamera?.status === 'online' ? 'on' : 'off'"></span>
            <span class="status-text">
              {{ selectedCamera ? t(`live.${selectedCamera.status}`) : t('live.noCameraSelected') }}
            </span>
          </div>
          <div v-if="selectedCamera" class="status-item">
            <span class="metric-label">{{ t('live.fps') }}</span>
            <span class="metric-value mono">{{ selectedCamera.fps }}</span>
          </div>
          <div v-if="selectedCamera?.resolution" class="status-item">
            <span class="metric-value mono">{{ selectedCamera.resolution }}</span>
          </div>
        </div>

        <div class="video-stage">
          <img
            v-if="selectedCamera && selectedCamera.status === 'online'"
            :src="rawStreamUrl"
            class="stream-img"
            :alt="selectedCamera.name"
          />
          <div v-else class="placeholder-content">
            <p>{{ selectedCamera ? t('live.offlineNoSignal') : t('live.noCameraSelected') }}</p>
            <p v-if="selectedCamera" class="mono endpoint">{{ selectedCamera.source }}</p>
          </div>
        </div>
      </div>
      <div v-else class="mobile-cam">
        <p class="source-hint">{{ t('inspection.mobileHint') }}</p>
        <div class="live-camera-wrap" :style="{ aspectRatio: liveVideoAspect }">
          <video ref="videoEl" playsinline muted class="cam-video"></video>
          <svg
            v-if="liveOverlayActive && liveOverlayBox"
            class="live-overlay"
            :viewBox="`0 0 ${liveOverlaySize.width} ${liveOverlaySize.height}`"
            preserveAspectRatio="none"
          >
            <rect
              :x="liveOverlayBox[0]"
              :y="liveOverlayBox[1]"
              :width="liveOverlayBox[2] - liveOverlayBox[0]"
              :height="liveOverlayBox[3] - liveOverlayBox[1]"
              class="live-box"
            />
          </svg>
          <span
            v-if="liveOverlayActive"
            class="live-overlay-label"
            :class="livePreviewQuality?.status || 'waiting'"
          >
            {{ livePreviewQuality?.status === 'ok' ? t('inspection.cropOk') : livePreviewQuality?.status === 'review' ? t('inspection.cropReview') : livePreviewQuality?.status === 'reject' ? t('inspection.cropRetake') : t('inspection.cropWaiting') }}
          </span>
        </div>
        <div class="row">
          <button class="btn-sm" @click="openCamera">{{ t('inspection.openCamera') }}</button>
          <button class="btn-sm" :disabled="busy" @click="captureMobile">
            {{ t('inspection.capture') }}
          </button>
          <label class="debug-toggle live-toggle">
            <input v-model="liveOverlayEnabled" type="checkbox" @change="onLiveOverlayToggle" />
            <span>{{ t('inspection.liveOverlay') }}</span>
          </label>
          <span v-if="liveResolution" class="mono camera-resolution">{{ liveResolution }}</span>
        </div>
      </div>
    </div>

    <p v-if="errorMsg" class="status-line error">{{ errorMsg }}</p>

    <div class="review-summary">
      <div class="summary-item">
        <span class="summary-number mono">{{ stack.length }}</span>
        <span class="summary-label">{{ t('inspection.captures') }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-number mono">{{ defectCaptureCount }}</span>
        <span class="summary-label">{{ t('inspection.defects') }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-number mono">{{ cleanCaptureCount }}</span>
        <span class="summary-label">{{ t('inspection.cleanCaptures') }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-number mono">{{ defectTotal }}</span>
        <span class="summary-label">{{ t('inspection.defectPolygons') }}</span>
      </div>
    </div>

    <h3 class="stack-title">{{ t('inspection.reviewStack') }} ({{ stack.length }})</h3>
    <div v-if="stack.length" class="inspection-workbench">
      <section v-if="selectedCapture" class="selected-capture">
        <div class="canvas-wrap large">
          <img :src="selectedCapture.frame_url" class="frame-img" :alt="`capture ${selectedIdx + 1}`" />
          <svg class="overlay" :viewBox="`0 0 ${selectedCapture.width} ${selectedCapture.height}`" preserveAspectRatio="none">
            <polygon
              v-if="selectedCapture.mask_applied && selectedCapture.mask_polygon?.length"
              :points="polyPoints(selectedCapture.mask_polygon)"
              class="mask-result-poly"
            />
            <polygon
              v-for="(defect, defectIndex) in selectedCapture.defects"
              :key="defectIndex"
              :points="polyPoints(defect.polygon)"
              class="poly"
            />
          </svg>
          <span v-if="selectedCapture.mask_applied && selectedCapture.mask_polygon?.length" class="mask-result-label">{{ t('inspection.maskApplied') }}</span>
        </div>
        <div v-if="selectedCapture.debug_frame_url" class="auto-crop-debug">
          <div class="debug-title">{{ t('inspection.debugCrop') }}</div>
          <img :src="selectedCapture.debug_frame_url" class="frame-img" :alt="t('inspection.debugCrop')" />
        </div>
        <div class="selected-meta">
          <span class="status-pill" :class="selectedCapture.verdict === 'defect' ? 'verdict-fail' : 'verdict-pass'">
            {{ selectedCapture.verdict === 'defect' ? t('inspection.defect') : t('inspection.clean') }}
          </span>
          <span class="mono">{{ selectedCapture.defects?.length || 0 }} {{ t('inspection.defectPolygons') }}</span>
          <span v-if="selectedCapture.crop_quality && selectedCapture.crop_mode === 'auto'" class="crop-quality" :class="selectedCapture.cropConfirmed || selectedCapture.crop_quality.status === 'ok' ? 'ok' : selectedCapture.crop_quality.status">
            {{ selectedCapture.crop_quality.status === 'ok' ? t('inspection.cropOk') : selectedCapture.crop_quality.status === 'review' ? t('inspection.cropReview') : t('inspection.cropRetake') }}
            · {{ Math.round((selectedCapture.crop_quality.coverage || 0) * 100) }}%
          </span>
          <button
            v-if="selectedCapture.crop_mode === 'auto' && selectedCapture.crop_quality?.status === 'review' && !selectedCapture.cropConfirmed"
            class="btn-sm"
            @click="confirmCrop(selectedIdx)"
          >
            {{ t('inspection.confirmCrop') }}
          </button>
          <button
            v-if="selectedCapture.crop_mode === 'auto' && selectedCapture.crop_quality?.status === 'reject'"
            class="btn-sm btn-danger-sm"
            @click="retakeFullFrame(selectedIdx)"
          >
            {{ t('inspection.retakeFull') }}
          </button>
          <button class="btn-sm btn-danger-sm" @click="removeCapture(selectedIdx)">
            {{ t('inspection.removeCapture') }}
          </button>
        </div>
      </section>

      <div class="capture-strip">
        <button
          v-for="(item, index) in stack"
          :key="item.key"
          class="capture-thumb"
          :class="{ active: selectedIdx === index }"
          :aria-pressed="selectedIdx === index"
          @click="selectedIdx = index"
        >
          <img :src="item.frame_url" :alt="`capture ${index + 1}`" />
          <span class="thumb-count mono">{{ item.defects?.length || 0 }}</span>
        </button>
      </div>
    </div>
    <p v-else class="empty-state">{{ t('inspection.empty') }}</p>

    <div class="footer-actions">
      <button class="btn-primary" :disabled="busy || !stack.length || !allCropsReady" @click="openSendReview">
        {{ t('inspection.sendToStudio') }}
      </button>
    </div>

    <BaseModal :show="showSendDialog" :title="t('inspection.sendReviewTitle')" @close="closeSendReview">
      <div class="review-summary compact">
        <div class="summary-item">
          <span class="summary-number mono">{{ stack.length }}</span>
          <span class="summary-label">{{ t('inspection.captures') }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-number mono">{{ defectCaptureCount }}</span>
          <span class="summary-label">{{ t('inspection.defects') }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-number mono">{{ defectTotal }}</span>
          <span class="summary-label">{{ t('inspection.defectPolygons') }}</span>
        </div>
      </div>
      <p class="send-note">{{ t('inspection.sendReviewNote') }}</p>
      <template #actions>
        <button class="btn-sm" @click="closeSendReview">{{ t('common.cancel') }}</button>
        <button class="btn-primary" :disabled="busy" @click="sendToStudio">
          {{ t('inspection.sendToStudio') }}
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<style scoped>
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
}

.seg {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.seg-label {
  margin-right: 4px;
  color: var(--color-ink-muted);
  font-size: 13px;
}

.debug-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink-muted);
  font-size: 13px;
}

.debug-toggle input:disabled {
  cursor: default;
}

.seg-btn,
.btn-sm,
.btn-primary {
  border: 1px solid var(--color-hairline);
  font-family: var(--font-sans);
  cursor: pointer;
}

.seg-btn {
  padding: 6px 14px;
  background: transparent;
  color: var(--color-ink);
  font-size: 14px;
}

.seg-btn.active,
.btn-primary {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.source-panel {
  margin-bottom: 16px;
}

.context-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
  margin-bottom: 16px;
}

.context-item {
  min-width: 160px;
  padding: 10px 14px;
  border-right: 1px solid var(--color-hairline);
}

.context-label {
  display: block;
  font-size: 12px;
  color: var(--color-ink-muted);
}

.context-value {
  display: block;
  margin-top: 2px;
  color: var(--color-ink);
  font-size: 14px;
}

.source-hint {
  margin: 0 0 8px;
  color: var(--color-ink-muted);
  font-size: 14px;
}

.mask-stage-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.mask-stage-item {
  padding: 12px;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
}

.mask-stage-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.mask-stage-heading .btn-sm {
  margin-left: auto;
}

.mask-stage-preview {
  display: block;
  width: 100%;
  max-width: 960px;
  margin-bottom: 12px;
}

.mask-stage-status,
.mask-stage-error {
  margin: 8px 0 0;
  color: var(--color-ink-muted);
}

.mask-stage-error {
  color: var(--color-error);
}

.row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.text-input {
  padding: 8px 12px;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 15px;
}

.btn-sm {
  padding: 6px 14px;
  background: transparent;
  color: var(--color-primary);
  font-size: 14px;
}

.btn-sm:disabled,
.btn-primary:disabled {
  cursor: default;
  opacity: 0.5;
}

.btn-danger-sm {
  border-color: var(--color-error);
  color: var(--color-error);
}

.server-cam,
.mobile-cam {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.status-strip {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 8px 16px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
}
.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-led {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-led.on {
  background: var(--color-success);
  box-shadow: 0 0 6px var(--color-success);
}
.status-led.off {
  background: var(--color-ink-subtle);
}
.status-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.metric-label {
  font-size: 13px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: 0.16px;
}
.video-stage {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  max-height: 60vh;
}
.stream-img {
  max-width: 100%;
  max-height: 60vh;
  width: auto;
  height: auto;
  background: #000;
}
.placeholder-content {
  text-align: center;
  color: var(--color-ink-muted);
  padding: 24px;
}
.placeholder-content p {
  margin: 0 0 8px;
  font-size: 15px;
}
.endpoint {
  font-size: 13px;
  color: var(--color-ink-muted);
}
.mono {
  font-family: var(--font-mono);
}

.cam-video {
  width: 100%;
  height: 100%;
  background: var(--color-ink);
  object-fit: fill;
}

.live-camera-wrap {
  position: relative;
  width: 100%;
  max-width: 640px;
  min-height: 220px;
  background: var(--color-ink);
  overflow: hidden;
}

.live-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.live-box {
  fill: color-mix(in srgb, var(--color-warning) 12%, transparent);
  stroke: var(--color-warning);
  stroke-width: 3;
  vector-effect: non-scaling-stroke;
}

.live-overlay-label {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 8px;
  color: var(--color-on-primary);
  background: var(--color-ink);
  font-family: var(--font-mono);
  font-size: 12px;
}

.live-overlay-label.ok,
.crop-quality.ok {
  background: var(--color-success);
  color: var(--color-on-primary);
}

.live-overlay-label.review,
.crop-quality.review {
  background: var(--color-warning);
  color: var(--color-ink);
}

.live-overlay-label.reject,
.crop-quality.reject {
  background: var(--color-error);
  color: var(--color-on-primary);
}

.camera-resolution {
  color: var(--color-ink-muted);
  font-size: 12px;
}

.crop-quality {
  padding: 2px 8px;
  font-size: 12px;
  font-family: var(--font-mono);
}

.stack-title {
  margin: 8px 0;
  font-weight: 400;
}

.canvas-wrap {
  position: relative;
  width: 100%;
}

.frame-img {
  display: block;
  width: 100%;
}

.overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.poly {
  fill: color-mix(in srgb, var(--color-error) 25%, transparent);
  stroke: var(--color-error);
  stroke-width: 2;
}

.mask-result-poly {
  fill: color-mix(in srgb, var(--color-primary) 20%, transparent);
  stroke: var(--color-primary);
  stroke-width: 2;
}

.mask-result-label {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 8px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-family: var(--font-mono);
  font-size: 12px;
}

.selected-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

.review-summary {
  display: flex;
  flex-wrap: wrap;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
  margin: 16px 0;
}

.summary-item {
  min-width: 140px;
  padding: 12px 16px;
  border-right: 1px solid var(--color-hairline);
}

.summary-number {
  display: block;
  font-size: 24px;
  color: var(--color-ink);
}

.summary-label {
  display: block;
  font-size: 13px;
  color: var(--color-ink-muted);
}

.inspection-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
}

.canvas-wrap.large {
  max-width: 760px;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
}

.auto-crop-debug {
  max-width: 760px;
  margin-top: 12px;
  border: 1px solid var(--color-warning);
  background: var(--color-surface-1);
}

.debug-title {
  padding: 6px 10px;
  color: var(--color-warning);
  font-size: 12px;
  font-family: var(--font-mono);
}

.capture-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.capture-thumb {
  position: relative;
  width: 88px;
  height: 64px;
  padding: 0;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
  cursor: pointer;
}

.capture-thumb.active {
  border-color: var(--color-primary);
  box-shadow: inset 0 0 0 1px var(--color-primary);
}

.capture-thumb img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-count {
  position: absolute;
  bottom: 2px;
  left: 2px;
  padding: 0 5px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: 13px;
}

.review-summary.compact {
  margin: 0;
}

.send-note {
  margin: 12px 0 0;
  color: var(--color-ink-muted);
}

.status-pill {
  display: inline-block;
  padding: 2px 8px;
  font-size: 13px;
  font-weight: 600;
}

.verdict-pass {
  background: var(--color-success);
  color: var(--color-on-primary);
}

.verdict-fail {
  background: var(--color-error);
  color: var(--color-on-primary);
}

.empty-state {
  padding: 24px;
  color: var(--color-ink-muted);
  text-align: center;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-primary {
  padding: 10px 20px;
  font-size: 15px;
}

.status-line.error {
  color: var(--color-error);
}

@media (max-width: 640px) {
  .controls {
    gap: 10px;
  }

  .footer-actions,
  .btn-primary {
    width: 100%;
  }
}
</style>
