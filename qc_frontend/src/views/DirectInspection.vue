<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { detectInspection, inspectionToQc } from '../api/inspection.js'
import { useCameras } from '../composables/useCameras.js'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()
const router = useRouter()
const { cameras, refresh } = useCameras()

const source = ref('upload')
const cropMode = ref('full')
const selectedCameraId = ref('')
const stack = ref([])
const busy = ref(false)
const errorMsg = ref('')
const videoEl = ref(null)

let mediaStream = null

const selectedCamera = computed(() => cameras.value.find((c) => c.id === selectedCameraId.value))
const rawStreamUrl = computed(() =>
  selectedCameraId.value ? `/api/cameras/${selectedCameraId.value}/stream` : '',
)

let statusTimer = null
onMounted(() => {
  refresh()
  statusTimer = setInterval(refresh, 10000)
})
onBeforeUnmount(() => {
  if (statusTimer) clearInterval(statusTimer)
  stopCamera()
})

async function pushDetect(opts) {
  busy.value = true
  errorMsg.value = ''
  try {
    stack.value.push(await detectInspection({ ...opts, cropMode: cropMode.value }))
  } catch (err) {
    errorMsg.value = err?.message || 'error'
  } finally {
    busy.value = false
  }
}

async function onFiles(event) {
  const files = Array.from(event.target.files || [])
  for (const file of files) await pushDetect({ file })
  event.target.value = ''
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
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    if (videoEl.value) {
      videoEl.value.srcObject = mediaStream
      await videoEl.value.play()
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
  if (!mediaStream) return
  mediaStream.getTracks().forEach((track) => track.stop())
  mediaStream = null
}

async function captureMobile() {
  const video = videoEl.value
  if (!video || !video.videoWidth) return
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92))
  if (blob) await pushDetect({ file: new File([blob], 'mobile.jpg', { type: 'image/jpeg' }) })
}

function removeCapture(index) {
  stack.value.splice(index, 1)
}

async function sendToStudio() {
  if (!stack.value.length) return
  busy.value = true
  errorMsg.value = ''
  try {
    const { batch_id } = await inspectionToQc(stack.value.map((item) => ({ key: item.key, defects: item.defects })))
    stopCamera()
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
        <button class="seg-btn" :class="{ active: cropMode === 'full' }" @click="cropMode = 'full'">
          {{ t('inspection.cropFull') }}
        </button>
        <button class="seg-btn" :class="{ active: cropMode === 'auto' }" @click="cropMode = 'auto'">
          {{ t('inspection.cropAuto') }}
        </button>
      </div>
    </div>

    <div class="source-panel">
      <div v-if="source === 'upload'">
        <input type="file" accept="image/*" multiple :disabled="busy" @change="onFiles" />
      </div>
      <div v-else-if="source === 'server'" class="server-cam">
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
        <video ref="videoEl" playsinline muted class="cam-video"></video>
        <div class="row">
          <button class="btn-sm" @click="openCamera">{{ t('inspection.openCamera') }}</button>
          <button class="btn-sm" :disabled="busy" @click="captureMobile">
            {{ t('inspection.capture') }}
          </button>
        </div>
      </div>
    </div>

    <p v-if="errorMsg" class="status-line error">{{ errorMsg }}</p>

    <h3 class="stack-title">{{ t('inspection.reviewStack') }} ({{ stack.length }})</h3>
    <div v-if="stack.length" class="stack">
      <div v-for="(item, index) in stack" :key="item.key" class="stack-card">
        <div class="canvas-wrap">
          <img :src="item.frame_url" class="frame-img" :alt="`capture ${index + 1}`" />
          <svg class="overlay" :viewBox="`0 0 ${item.width} ${item.height}`" preserveAspectRatio="none">
            <polygon
              v-for="(defect, defectIndex) in item.defects"
              :key="defectIndex"
              :points="polyPoints(defect.polygon)"
              class="poly"
            />
          </svg>
        </div>
        <div class="stack-meta">
          <span class="status-pill" :class="item.verdict === 'defect' ? 'verdict-fail' : 'verdict-pass'">
            {{ item.verdict === 'defect' ? t('inspection.defect') : t('inspection.clean') }}
          </span>
          <button class="btn-sm btn-danger-sm" @click="removeCapture(index)">
            {{ t('inspection.removeCapture') }}
          </button>
        </div>
      </div>
    </div>
    <p v-else class="empty-state">{{ t('inspection.empty') }}</p>

    <div class="footer-actions">
      <button class="btn-primary" :disabled="busy || !stack.length" @click="sendToStudio">
        {{ t('inspection.sendToStudio') }}
      </button>
    </div>
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
  max-width: 480px;
  aspect-ratio: 4 / 3;
  background: var(--color-ink);
  object-fit: contain;
}

.stack-title {
  margin: 8px 0;
  font-weight: 400;
}

.stack {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.stack-card {
  width: 240px;
  border: 1px solid var(--color-hairline);
  background: var(--color-canvas);
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

.stack-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px;
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
  .stack-card {
    width: 100%;
  }

  .controls {
    gap: 10px;
  }

  .footer-actions,
  .btn-primary {
    width: 100%;
  }
}
</style>
