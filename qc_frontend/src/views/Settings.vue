<script setup>
import { computed, ref, onMounted } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useCameras } from '../composables/useCameras.js'
import { useSettings } from '../composables/useSettings.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useToast } from '../composables/useToast.js'
import { useDefectClasses } from '../composables/useDefectClasses.js'
import DefectClassModal from '../components/DefectClassModal.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { listModels } from '../api/models.js'
import { listGpus } from '../api/system.js'

const { t, locale, setLocale } = useI18n()
const { cameras, refresh: refreshCameras, addCamera, updateCamera, deleteCamera } = useCameras()
const { settings, refresh: refreshSettings, update } = useSettings()
const { log } = useAuditLog()
const { showToast } = useToast()
const { classes, refresh: refreshClasses, add, update: updateClass, toggle, remove } = useDefectClasses()

const editingId = ref(null)
const showForm = ref(false)
const form = ref({ name: '', type: 'rpi', source: '', location: '', status: 'offline' })
const availableModels = ref([])
const availableGpus = ref([])
const gpuError = ref('')
const expandedGroups = ref({ coating: true, welding: true })
function toggleGroup(key) {
  expandedGroups.value[key] = !expandedGroups.value[key]
}
function isGroupExpanded(key) {
  return expandedGroups.value[key] !== false
}

function gpuLabel(gpu) {
  const free = (gpu.memory_free_mb / 1024).toFixed(1)
  return `GPU ${gpu.index} — ${gpu.name} — ${free} GB free — ${gpu.utilization_percent}% util`
}

async function refreshGpus() {
  try {
    const result = await listGpus()
    availableGpus.value = result.gpus || []
    gpuError.value = result.error || ''
  } catch {
    availableGpus.value = []
    gpuError.value = t('settings.gpuUnavailable')
  }
}

const showClassModal = ref(false)
const editingClass = ref(null)
const pendingDeleteClass = ref(null)
const pendingDeleteCamera = ref(null)

const categoryOptions = computed(() => [...new Set(classes.value.map((c) => c.category).filter(Boolean))])
const classGroups = computed(() =>
  categoryOptions.value.map((key) => {
    const items = classes.value.filter((c) => c.category === key)
    return { key, label: categoryLabel(key), items, on: items.filter((c) => c.enabled).length }
  }),
)

function categoryLabel(key) {
  const i18nKey = `defectClasses.${key}`
  const translated = t(i18nKey)
  return translated === i18nKey ? key : translated
}

const cameraTypes = [
  { value: 'rpi', label: 'Raspberry Pi Cam (CSI)' },
  { value: 'rtsp', label: 'RTSP Stream' },
  { value: 'usb', label: 'USB Camera' },
]

onMounted(async () => {
  refreshCameras()
  refreshSettings()
  refreshClasses()
  refreshGpus()
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

function removeCamera(cam) {
  pendingDeleteCamera.value = cam
}

async function confirmDeleteCamera() {
  const cam = pendingDeleteCamera.value
  if (!cam) return
  await deleteCamera(cam.id)
  log('CAMERA_DELETED', `Deleted camera: ${cam.name} (${cam.id})`)
  pendingDeleteCamera.value = null
}

async function saveSettings() {
  await update({
    confidenceThreshold: Number(settings.value.confidenceThreshold),
    qcConfidenceThreshold: Number(settings.value.qcConfidenceThreshold),
    defectStrategy: settings.value.defectStrategy,
    activeModel: settings.value.activeModel,
    qcModel: settings.value.qcModel,
    quantityModel: settings.value.quantityModel,
    quantityConfidenceThreshold: Number(settings.value.quantityConfidenceThreshold),
    quantityNmsIou: Number(settings.value.quantityNmsIou),
    quantityAgnosticNms: settings.value.quantityAgnosticNms,
    quantityClasses: settings.value.quantityClasses,
    objectDetectionDevice: settings.value.objectDetectionDevice,
    qcDevice: settings.value.qcDevice,
    quantityDevice: settings.value.quantityDevice,
  })
  log('SETTINGS_CHANGED', 'Updated model configuration')
  showToast(t('settings.saved'))
}

function changeLanguage(lang) {
  setLocale(lang)
  log('SETTINGS_CHANGED', `Changed language to ${lang === 'id' ? 'Indonesia' : 'English'}`)
}

function openAddClass() {
  editingClass.value = null
  showClassModal.value = true
}

function openEditClass(cls) {
  editingClass.value = cls
  showClassModal.value = true
}

async function saveClass(payload) {
  if (editingClass.value) {
    await updateClass(editingClass.value.id, payload)
  } else {
    await add(payload)
  }
  showClassModal.value = false
  showToast(t('defectClasses.saved'))
}

async function confirmDeleteClass() {
  await remove(pendingDeleteClass.value.id)
  pendingDeleteClass.value = null
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
            <h3>{{ t('settings.models') }}</h3>
            <p class="section-desc">{{ t('settings.modelConfigDesc') }}</p>
          </div>
          <button class="btn-sm" type="button" @click="refreshGpus">{{ t('settings.refreshGpu') }}</button>
        </div>
        <div class="config-grid">
          <h4 class="model-block-title">{{ t('settings.objectDetection') }}</h4>
          <div class="form-row">
            <label>{{ t('settings.activeModel') }}<span class="info-i" :title="t('settings.tip.activeModel')">i</span></label>
            <select v-if="availableModels.length" v-model="settings.activeModel" class="text-input">
              <option value="">{{ t('settings.noModelSelected') }}</option>
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
            <p v-else class="form-hint">{{ t('settings.noModels') }}</p>
          </div>
          <div class="form-row">
            <label>{{ t('settings.objectDetectionConfidence') }}<span class="info-i" :title="t('settings.tip.objectDetectionConfidence')">i</span></label>
            <input type="number" min="0" max="1" step="0.05" v-model="settings.confidenceThreshold" class="text-input" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.device') }}</label>
            <select v-model="settings.objectDetectionDevice" class="text-input">
              <option value="auto">{{ t('settings.deviceAuto') }}</option>
              <option value="cpu">CPU</option>
              <option v-for="gpu in availableGpus" :key="`od-${gpu.index}`" :value="String(gpu.index)">{{ gpuLabel(gpu) }}</option>
            </select>
          </div>
          <h4 class="model-block-title">{{ t('settings.qcSegmentation') }}</h4>
          <div class="form-row">
            <label>{{ t('settings.qcModel') }}<span class="info-i" :title="t('settings.tip.qcModel')">i</span></label>
            <select v-if="availableModels.length" v-model="settings.qcModel" class="text-input">
              <option value="">{{ t('settings.noModelSelected') }}</option>
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
            <p v-else class="form-hint">{{ t('settings.noModels') }}</p>
          </div>
          <div class="form-row">
            <label>{{ t('settings.qcConfidence') }}<span class="info-i" :title="t('settings.tip.qcConfidence')">i</span></label>
            <input type="number" min="0" max="1" step="0.05" v-model="settings.qcConfidenceThreshold" class="text-input" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.device') }}</label>
            <select v-model="settings.qcDevice" class="text-input">
              <option value="auto">{{ t('settings.deviceAuto') }}</option>
              <option value="cpu">CPU</option>
              <option v-for="gpu in availableGpus" :key="`qc-${gpu.index}`" :value="String(gpu.index)">{{ gpuLabel(gpu) }}</option>
            </select>
          </div>
          <div class="form-row">
            <label>{{ t('settings.defectStrategy') }}<span class="info-i" :title="t('settings.tip.defectStrategy')">i</span></label>
            <select v-model="settings.defectStrategy" class="text-input">
              <option value="mock">{{ t('settings.strategyMock') }}</option>
              <option value="sam3_prompt">{{ t('settings.strategySam3') }}</option>
            </select>
          </div>
          <h4 class="model-block-title">{{ t('settings.quantity') }}</h4>
          <div class="form-row">
            <label>{{ t('settings.quantityModel') }}<span class="info-i" :title="t('settings.tip.quantityModel')">i</span></label>
            <select v-if="availableModels.length" v-model="settings.quantityModel" class="text-input">
              <option value="">{{ t('settings.noModelSelected') }}</option>
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
            <p v-else class="form-hint">{{ t('settings.noModels') }}</p>
          </div>
          <div class="form-row">
            <label>{{ t('settings.device') }}</label>
            <select v-model="settings.quantityDevice" class="text-input">
              <option value="auto">{{ t('settings.deviceAuto') }}</option>
              <option value="cpu">CPU</option>
              <option v-for="gpu in availableGpus" :key="`qty-${gpu.index}`" :value="String(gpu.index)">{{ gpuLabel(gpu) }}</option>
            </select>
          </div>
          <div class="form-row">
            <label>{{ t('settings.quantityClasses') }}<span class="info-i" :title="t('settings.tip.quantityClasses')">i</span></label>
            <input v-model="settings.quantityClasses" class="text-input" :aria-label="t('settings.quantityClasses')" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.quantityConfidence') }}<span class="info-i" :title="t('settings.tip.quantityConfidence')">i</span></label>
            <input type="number" min="0" max="1" step="0.05" v-model="settings.quantityConfidenceThreshold" class="text-input" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.quantityNmsIou') }}<span class="info-i" :title="t('settings.tip.quantityNmsIou')">i</span></label>
            <input type="number" min="0" max="1" step="0.05" v-model="settings.quantityNmsIou" class="text-input" />
          </div>
          <div class="form-row">
            <label class="check-label">
              <input type="checkbox" v-model="settings.quantityAgnosticNms" />
              {{ t('settings.quantityMergeOverlap') }}
              <span class="info-i" :title="t('settings.tip.quantityMergeOverlap')">i</span>
            </label>
            <p class="form-hint">{{ t('settings.quantityNmsFreeNote') }}</p>
          </div>
          <div class="form-actions">
            <button class="btn-sm primary" @click="saveSettings">{{ t('settings.save') }}</button>
          </div>
          <p v-if="gpuError" class="form-hint grid-note">{{ gpuError }}</p>
        </div>
      </section>

      <section class="settings-section">
        <div class="section-header">
          <div>
            <h3>{{ t('defectClasses.title') }}</h3>
            <p class="section-desc">{{ t('defectClasses.desc') }}</p>
          </div>
          <button class="btn-sm" @click="openAddClass">+ {{ t('defectClasses.add') }}</button>
        </div>

        <div class="dc-list">
          <template v-for="grp in classGroups" :key="grp.key">
            <button type="button" class="dc-group-head" @click="toggleGroup(grp.key)">
              <span class="dc-group-label">
                <span class="dc-chevron">{{ isGroupExpanded(grp.key) ? '▾' : '▸' }}</span>
                {{ grp.label }}
              </span>
              <span class="mono">{{ grp.on }} / {{ grp.items.length }} {{ t('defectClasses.on') }}</span>
            </button>
            <template v-if="isGroupExpanded(grp.key)">
              <p v-if="grp.items.length === 0" class="form-hint">{{ t('defectClasses.empty') }}</p>
              <div v-for="c in grp.items" :key="c.id" class="dc-row">
                <label class="dc-check">
                  <input type="checkbox" :checked="c.enabled" @change="toggle(c)" />
                  <span class="dc-swatch" :style="{ background: c.color }"></span>
                  <span class="dc-name">{{ c.name }}</span>
                </label>
                <div class="dc-actions">
                  <button class="dc-icon" :title="t('common.edit')" @click="openEditClass(c)">{{ t('common.edit') }}</button>
                  <button class="dc-icon danger" :title="t('common.delete')" @click="pendingDeleteClass = c">{{ t('common.delete') }}</button>
                </div>
              </div>
            </template>
          </template>
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

    <DefectClassModal
      :show="showClassModal"
      :editing="editingClass"
      :categories="categoryOptions"
      @cancel="showClassModal = false"
      @save="saveClass"
    />

    <ConfirmDialog
      :show="Boolean(pendingDeleteClass)"
      :title="t('defectClasses.deleteTitle')"
      :message="pendingDeleteClass ? `${t('defectClasses.confirmDelete')} ${pendingDeleteClass.name}?` : ''"
      :confirm-label="t('common.delete')"
      :cancel-label="t('common.cancel')"
      danger
      @cancel="pendingDeleteClass = null"
      @confirm="confirmDeleteClass"
    />

    <ConfirmDialog
      :show="Boolean(pendingDeleteCamera)"
      :title="t('settings.confirmDelete')"
      :message="pendingDeleteCamera ? `${t('settings.confirmDelete')} ${pendingDeleteCamera.name}?` : ''"
      :confirm-label="t('common.delete')"
      :cancel-label="t('common.cancel')"
      danger
      @cancel="pendingDeleteCamera = null"
      @confirm="confirmDeleteCamera"
    />
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
  min-width: 0;
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
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: 0.16px;
}
.section-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
}
.data-table th {
  text-align: left;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 13px;
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
  min-width: 0;
}
.form-row label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.check-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-ink);
}
.form-hint {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.text-input {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  padding: 8px 12px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-bottom: 2px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 15px;
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
.grid-note {
  grid-column: 1 / -1;
}
.config-grid {
  padding: 24px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
}
.model-block-title {
  grid-column: 1 / -1;
  margin: 8px 0 4px;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.32px;
  color: var(--color-ink-muted);
}
.info-i {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 15px;
  height: 15px;
  margin-left: 6px;
  border: 1px solid var(--color-hairline);
  border-radius: 50%;
  font-size: 10px;
  font-style: italic;
  color: var(--color-ink-muted);
  cursor: help;
  vertical-align: middle;
}
.dc-list {
  padding: 12px 24px 20px;
}
.dc-group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin: 16px 0 4px;
  padding: 6px 8px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.32px;
  text-transform: uppercase;
  color: var(--color-ink-muted);
  background: var(--color-surface-1);
  border: none;
  border-bottom: 1px solid var(--color-hairline);
  cursor: pointer;
  font-family: var(--font-sans);
}
.dc-group-head:hover { color: var(--color-ink); }
.dc-group-label { display: flex; align-items: center; gap: 8px; }
.dc-chevron { font-size: 10px; width: 10px; }
.dc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-bottom: 1px solid var(--color-hairline);
}
.dc-row:hover {
  background: var(--color-surface-1);
}
.dc-check {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 15px;
  color: var(--color-ink);
}
.dc-swatch {
  width: 14px;
  height: 14px;
  border: 1px solid var(--color-hairline);
}
.dc-name {
  letter-spacing: 0.16px;
}
.dc-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
}
.dc-row:hover .dc-actions,
.dc-actions:focus-within {
  opacity: 1;
}
.dc-icon {
  padding: 2px 6px;
  background: transparent;
  border: none;
  color: var(--color-ink-muted);
  font-family: var(--font-sans);
  font-size: 13px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.dc-icon:hover {
  color: var(--color-primary);
}
.dc-icon.danger:hover {
  color: var(--color-error);
}
.btn-sm {
  padding: 6px 16px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 13px;
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
  font-size: 13px;
  cursor: pointer;
  margin-right: 4px;
  letter-spacing: 0.16px;
}
.btn-xs.danger {
  color: var(--color-error);
}
.status-pill {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 6px;
  letter-spacing: 0.32px;
}
.status-pill.on {
  color: var(--color-success);
}
.status-pill.off {
  color: var(--color-ink-muted);
}
.mono {
  font-family: var(--font-mono);
  font-size: 13px;
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
  font-size: 15px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.lang-toggle button.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-weight: 600;
}
</style>
