<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../composables/useI18n.js'
import { useCameras } from '../composables/useCameras.js'
import { useSettings } from '../composables/useSettings.js'
import { submitBatch } from '../api/batches.js'
import { useAuditLog } from '../composables/useAuditLog.js'

const { t } = useI18n()
const router = useRouter()
const { cameras, refresh: refreshCameras } = useCameras()
const { settings } = useSettings()
const { log } = useAuditLog()

const selectedCameraId = ref('')
const detecting = ref(false)
const connecting = ref(false)
const objectCount = ref(0)
const fps = ref(0)
const tempC = ref(0)
const showSendDialog = ref(false)
const batchNameInput = ref('')
const sourcePathInput = ref('')
const sendError = ref('')

const selectedCamera = computed(() =>
  cameras.value.find((c) => c.id === selectedCameraId.value),
)

const onlineCameras = computed(() => cameras.value.filter((c) => c.status === 'online'))
const detectStreamUrl = computed(() =>
  selectedCameraId.value ? `/api/cameras/${selectedCameraId.value}/detect-stream` : '',
)

let statusTimer = null
let countTimer = null
onMounted(() => {
  refreshCameras()
  statusTimer = setInterval(refreshCameras, 10000)
})
onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
  if (countTimer) clearInterval(countTimer)
})

async function pollCount() {
  if (!selectedCameraId.value) return
  try {
    const res = await fetch(`/api/cameras/${selectedCameraId.value}/count`)
    if (res.ok) objectCount.value = (await res.json()).count
  } catch {
    // best-effort metric
  }
}

async function startDetection() {
  if (!selectedCamera.value) return
  connecting.value = true
  await new Promise((r) => setTimeout(r, 800))
  connecting.value = false
  detecting.value = true

  fps.value = selectedCamera.value.fps
  objectCount.value = 0
  countTimer = setInterval(pollCount, 1000)

  log('CAMERA_STARTED', `Started ${selectedCamera.value.name} (${selectedCameraId.value})`)
}

function stopDetection() {
  if (countTimer) {
    clearInterval(countTimer)
    countTimer = null
  }
  detecting.value = false
  objectCount.value = 0
  if (selectedCamera.value) {
    log('CAMERA_STOPPED', `Stopped ${selectedCamera.value.name} (${selectedCameraId.value})`)
  }
}

function openSendDialog() {
  const now = new Date()
  const ts = now.toISOString().replace(/[:T]/g, '-').slice(0, 19)
  batchNameInput.value = `batch_${ts}`
  showSendDialog.value = true
}

async function sendToQC() {
  const cam = selectedCamera.value
  sendError.value = ''
  try {
    const { batch_id } = await submitBatch({
      batchName: batchNameInput.value,
      sourcePath: sourcePathInput.value,
      cameraId: cam?.id ?? null,
    })
    log('BATCH_SENT', `Sent batch ${batchNameInput.value} to QC`)
    showSendDialog.value = false
    stopDetection()
    objectCount.value = 0
    router.push({ name: 'qc', query: { batch: batch_id } })
  } catch (e) {
    sendError.value = e.message || t('sendToQC.sendFailed')
  }
}

function onCameraChange() {
  if (detecting.value) stopDetection()
  objectCount.value = 0
}
</script>

<template>
  <div class="live-page">
    <div class="control-bar">
      <div class="camera-select-group">
        <label class="control-label">{{ t('live.selectCamera') }}</label>
        <select v-model="selectedCameraId" @change="onCameraChange" class="text-input" :disabled="detecting">
          <option value="">-- {{ t('live.noCameraSelected') }} --</option>
          <option v-for="cam in cameras" :key="cam.id" :value="cam.id">
            {{ cam.name }} ({{ t(`live.cameraType.${cam.type}`) }}) - {{ cam.location }}
          </option>
        </select>
      </div>

      <div class="action-buttons">
        <button
          v-if="!detecting"
          class="btn-primary"
          :disabled="!selectedCameraId || connecting"
          @click="startDetection"
        >
          {{ connecting ? t('live.connecting') : t('live.startDetection') }}
        </button>
        <button v-else class="btn-danger" @click="stopDetection">
          {{ t('live.stopDetection') }}
        </button>

        <button
          v-if="detecting"
          class="btn-secondary"
          @click="openSendDialog"
        >
          {{ t('live.sendToQC') }} ({{ objectCount }})
        </button>
      </div>
    </div>

    <div class="status-strip">
      <div class="status-item">
        <span class="status-led" :class="selectedCamera?.status === 'online' ? 'on' : 'off'"></span>
        <span class="status-text">
          {{ selectedCamera ? t(`live.${selectedCamera.status}`) : t('live.noCameraSelected') }}
        </span>
      </div>
      <div class="status-item">
        <span class="metric-label">{{ t('live.objectCount') }}</span>
        <span class="metric-value mono">{{ objectCount }}</span>
      </div>
      <div class="status-item">
        <span class="metric-label">{{ t('live.fps') }}</span>
        <span class="metric-value mono">{{ fps }}</span>
      </div>
      <div class="status-item">
        <span class="metric-label">{{ t('live.temp') }}</span>
        <span class="metric-value mono">{{ tempC }}C</span>
      </div>
    </div>

    <div class="video-stage">
      <div v-if="detecting" class="video-feed">
        <img
          v-if="selectedCamera?.status === 'online' && settings.activeModel"
          :src="detectStreamUrl"
          class="stream-img"
          :alt="selectedCamera?.name"
        />
        <div v-else class="placeholder-content">
          <p>{{ selectedCamera?.status !== 'online' ? t('live.offlineNoSignal') : t('live.modelNotConfigured') }}</p>
          <p class="mono endpoint">{{ selectedCamera?.source }}</p>
        </div>
      </div>
      <div v-else class="video-placeholder">
        <div v-if="selectedCamera" class="placeholder-content">
          <p>{{ t('live.waitingStream') }}</p>
          <p class="mono endpoint">{{ selectedCamera.source }}</p>
          <p class="hint">{{ selectedCamera.resolution }} | {{ selectedCamera.fps }}fps max</p>
        </div>
        <div v-else class="placeholder-content">
          <p>{{ onlineCameras.length === 0 ? t('live.noCameraAvailable') : t('live.noCameraSelected') }}</p>
        </div>
      </div>
    </div>

    <div v-if="showSendDialog" class="dialog-overlay" @click.self="showSendDialog = false">
      <div class="dialog">
        <h3 class="dialog-title">{{ t('sendToQC.title') }}</h3>

        <div class="dialog-body">
          <div class="form-row">
            <label>{{ t('sendToQC.batchName') }}</label>
            <input v-model="batchNameInput" class="text-input" :placeholder="t('sendToQC.batchNamePlaceholder')" />
            <span class="form-hint">{{ t('sendToQC.autoTimestamp') }}</span>
          </div>

          <div class="form-row">
            <label>{{ t('sendToQC.sourcePath') }}</label>
            <input v-model="sourcePathInput" class="text-input" :placeholder="t('sendToQC.sourcePathPlaceholder')" />
          </div>

          <p v-if="sendError" class="send-error">{{ sendError }}</p>

          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">{{ t('sendToQC.sourceCamera') }}</span>
              <span class="info-value">{{ selectedCamera?.name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('sendToQC.imagesCaptured') }}</span>
              <span class="info-value mono">{{ objectCount }} frames</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('sendToQC.detectionModel') }}</span>
              <span class="info-value">{{ settings.detectionModel }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('sendToQC.confidence') }}</span>
              <span class="info-value">{{ Math.round(settings.confidenceThreshold * 100) }}%</span>
            </div>
          </div>
        </div>

        <div class="dialog-actions">
          <button class="btn-ghost" @click="showSendDialog = false">{{ t('sendToQC.cancel') }}</button>
          <button class="btn-primary" @click="sendToQC" :disabled="!batchNameInput.trim() || !sourcePathInput.trim()">{{ t('sendToQC.send') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.live-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 12px;
  background: var(--color-canvas);
  overflow: hidden;
}
.control-bar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-shrink: 0;
}
.camera-select-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  max-width: 400px;
}
.control-label {
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
.text-input:disabled {
  opacity: 0.6;
}
.action-buttons {
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
  font-weight: 400;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.btn-primary:hover {
  background: var(--color-primary-hover);
}
.btn-primary:disabled {
  opacity: 0.4;
  cursor: default;
}
.btn-danger {
  padding: 9px 16px;
  background: var(--color-error);
  color: var(--color-on-primary);
  border: none;
  font-family: var(--font-sans);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.btn-secondary {
  padding: 9px 16px;
  background: transparent;
  color: var(--color-ink);
  border: 1px solid var(--color-ink);
  font-family: var(--font-sans);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.btn-secondary:hover {
  background: var(--color-surface-1);
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
.status-strip {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 8px 16px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  flex-shrink: 0;
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
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.metric-label {
  font-size: 12px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: 0.16px;
}
.video-stage {
  flex: 1;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-placeholder,
.video-feed {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.placeholder-content {
  text-align: center;
  color: var(--color-ink-subtle);
}
.placeholder-content p {
  margin: 0 0 8px;
  font-size: 14px;
  letter-spacing: 0.16px;
}
.endpoint {
  font-size: 12px;
  color: var(--color-ink-muted);
}
.hint {
  font-size: 12px;
  color: var(--color-ink-subtle);
}
.stream-img {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  background: black;
}

/* Dialog */
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
.form-hint {
  font-size: 11px;
  color: var(--color-ink-subtle);
  letter-spacing: 0.16px;
}
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 16px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.info-label {
  font-size: 11px;
  color: var(--color-ink-subtle);
  letter-spacing: 0.32px;
  text-transform: uppercase;
}
.info-value {
  font-size: 14px;
  color: var(--color-ink);
  letter-spacing: 0.16px;
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
.mono {
  font-family: var(--font-mono);
}
</style>
