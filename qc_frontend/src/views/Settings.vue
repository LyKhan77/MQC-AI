<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useCameras } from '../composables/useCameras.js'
import { useSettings } from '../composables/useSettings.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { listModels } from '../api/models.js'

const { t, locale, setLocale } = useI18n()
const { cameras, refresh: refreshCameras, addCamera, updateCamera, deleteCamera } = useCameras()
const { settings, refresh: refreshSettings, update } = useSettings()
const { log } = useAuditLog()

const editingId = ref(null)
const showForm = ref(false)
const form = ref({ name: '', type: 'rpi', source: '', location: '', status: 'offline' })
const availableModels = ref([])

const cameraTypes = [
  { value: 'rpi', label: 'Raspberry Pi Cam (CSI)' },
  { value: 'rtsp', label: 'RTSP Stream' },
  { value: 'usb', label: 'USB Camera' },
]

onMounted(async () => {
  refreshCameras()
  refreshSettings()
  try {
    availableModels.value = (await listModels()).models
  } catch {
    availableModels.value = []
  }
})

function startAdd() {
  editingId.value = null
  form.value = { name: '', type: 'rpi', source: '', location: '', status: 'offline' }
  showForm.value = true
}

function startEdit(cam) {
  editingId.value = cam.id
  form.value = { ...cam }
  showForm.value = true
}

async function saveCamera() {
  if (editingId.value) {
    await updateCamera(editingId.value, form.value)
    log('CAMERA_EDITED', `Edited camera: ${form.value.name}`)
  } else {
    const id = await addCamera(form.value)
    log('CAMERA_ADDED', `Added camera: ${form.value.name} (${id})`)
  }
  showForm.value = false
}

async function removeCamera(cam) {
  if (confirm(t('settings.confirmDelete'))) {
    await deleteCamera(cam.id)
    log('CAMERA_DELETED', `Deleted camera: ${cam.name} (${cam.id})`)
  }
}

async function saveSettings() {
  await update({
    confidenceThreshold: Number(settings.value.confidenceThreshold),
    detectionModel: settings.value.detectionModel,
    segmentationModel: settings.value.segmentationModel,
    defectStrategy: settings.value.defectStrategy,
    activeModel: settings.value.activeModel,
  })
  log('SETTINGS_CHANGED', 'Updated model configuration')
}

function changeLanguage(lang) {
  setLocale(lang)
  log('SETTINGS_CHANGED', `Changed language to ${lang === 'id' ? 'Indonesia' : 'English'}`)
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('settings.title') }}</h2>
      <p class="page-subtitle">{{ t('settings.subtitle') }}</p>
    </div>

    <div class="settings-sections">
      <section class="settings-section">
        <div class="section-header">
          <div>
            <h3>{{ t('settings.cameras') }}</h3>
            <p class="section-desc">{{ t('settings.camerasDesc') }}</p>
          </div>
          <button class="btn-sm" @click="startAdd">+ {{ t('settings.addCamera') }}</button>
        </div>

        <div v-if="showForm" class="camera-form">
          <div class="form-row">
            <label>{{ t('settings.cameraName') }}</label>
            <input v-model="form.name" class="text-input" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.cameraType') }}</label>
            <select v-model="form.type" class="text-input">
              <option v-for="ct in cameraTypes" :key="ct.value" :value="ct.value">{{ ct.label }}</option>
            </select>
          </div>
          <div class="form-row">
            <label>{{ t('settings.cameraSource') }}</label>
            <input v-model="form.source" class="text-input" placeholder="csi://0 or rtsp://..." />
          </div>
          <div class="form-row">
            <label>{{ t('settings.cameraLocation') }}</label>
            <input v-model="form.location" class="text-input" />
          </div>
          <div class="form-actions">
            <button class="btn-sm" @click="showForm = false">{{ t('common.cancel') }}</button>
            <button class="btn-sm primary" @click="saveCamera">{{ t('common.save') }}</button>
          </div>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('settings.cameraName') }}</th>
              <th>{{ t('settings.cameraType') }}</th>
              <th>{{ t('settings.cameraSource') }}</th>
              <th>{{ t('settings.cameraLocation') }}</th>
              <th>{{ t('settings.cameraStatus') }}</th>
              <th>{{ t('settings.cameraActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cam in cameras" :key="cam.id">
              <td>{{ cam.name }}</td>
              <td>{{ t(`live.cameraType.${cam.type}`) }}</td>
              <td class="mono">{{ cam.source }}</td>
              <td>{{ cam.location }}</td>
              <td>
                <span class="status-pill" :class="cam.status === 'online' ? 'on' : 'off'">
                  {{ cam.status === 'online' ? t('common.online') : t('common.offline') }}
                </span>
              </td>
              <td>
                <button class="btn-xs" @click="startEdit(cam)">{{ t('common.edit') }}</button>
                <button class="btn-xs danger" @click="removeCamera(cam)">{{ t('common.delete') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="settings-section">
        <div class="section-header">
          <div>
            <h3>{{ t('settings.modelConfig') }}</h3>
            <p class="section-desc">{{ t('settings.modelConfigDesc') }}</p>
          </div>
        </div>
        <div class="config-grid">
          <div class="form-row">
            <label>{{ t('settings.detectionModel') }}</label>
            <input v-model="settings.detectionModel" class="text-input" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.segmentationModel') }}</label>
            <input v-model="settings.segmentationModel" class="text-input" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.confidenceThreshold') }}: {{ Math.round(settings.confidenceThreshold * 100) }}%</label>
            <input type="range" min="0" max="1" step="0.05" v-model="settings.confidenceThreshold" class="slider" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.defectStrategy') }}</label>
            <select v-model="settings.defectStrategy" class="text-input">
              <option value="mock">{{ t('settings.strategyMock') }}</option>
              <option value="sam3_prompt">{{ t('settings.strategySam3') }}</option>
            </select>
          </div>
          <div class="form-row">
            <label>{{ t('settings.activeModel') }}</label>
            <select v-if="availableModels.length" v-model="settings.activeModel" class="text-input">
              <option value="">{{ t('settings.noModelSelected') }}</option>
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
            <p v-else class="form-hint">{{ t('settings.noModels') }}</p>
          </div>
          <div class="form-actions">
            <button class="btn-sm primary" @click="saveSettings">{{ t('settings.save') }}</button>
          </div>
        </div>
      </section>

      <section class="settings-section">
        <div class="section-header">
          <div>
            <h3>{{ t('settings.preferences') }}</h3>
            <p class="section-desc">{{ t('settings.preferencesDesc') }}</p>
          </div>
        </div>
        <div class="form-row">
          <label>{{ t('settings.language') }}</label>
          <div class="lang-toggle">
            <button :class="{ active: locale === 'id' }" @click="changeLanguage('id')">{{ t('settings.languageId') }}</button>
            <button :class="{ active: locale === 'en' }" @click="changeLanguage('en')">{{ t('settings.languageEn') }}</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 900px;
}
.settings-section {
  border: 1px solid var(--color-hairline);
  background: var(--color-canvas);
}
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
}
.section-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: 0.16px;
}
.section-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.data-table th {
  text-align: left;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 12px;
  color: var(--color-ink-muted);
  letter-spacing: 0.32px;
  text-transform: uppercase;
  border-bottom: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
}
.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-hairline);
  color: var(--color-ink);
}
.data-table tbody tr:hover {
  background: var(--color-surface-1);
}
.camera-form {
  padding: 16px 24px;
  background: var(--color-surface-1);
  border-bottom: 1px solid var(--color-hairline);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-row label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.form-hint {
  margin: 0;
  font-size: 12px;
  color: var(--color-ink-subtle);
  letter-spacing: 0.16px;
}
.text-input {
  padding: 8px 12px;
  background: var(--color-canvas);
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
.form-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.config-grid {
  padding: 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.slider {
  width: 100%;
  accent-color: var(--color-primary);
}
.btn-sm {
  padding: 6px 16px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 12px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.btn-sm:hover {
  background: var(--color-surface-1);
}
.btn-sm.primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-color: var(--color-primary);
}
.btn-xs {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-primary);
  font-family: var(--font-sans);
  font-size: 11px;
  cursor: pointer;
  margin-right: 4px;
  letter-spacing: 0.16px;
}
.btn-xs.danger {
  color: var(--color-error);
}
.status-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  letter-spacing: 0.32px;
}
.status-pill.on {
  color: var(--color-success);
}
.status-pill.off {
  color: var(--color-ink-subtle);
}
.mono {
  font-family: var(--font-mono);
  font-size: 12px;
}
.lang-toggle {
  display: flex;
  border: 1px solid var(--color-hairline);
}
.lang-toggle button {
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: var(--color-ink-muted);
  font-family: var(--font-sans);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.lang-toggle button.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-weight: 600;
}
</style>
