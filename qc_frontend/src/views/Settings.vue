<script setup>
import { computed, ref, onMounted } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useCameras } from '../composables/useCameras.js'
import { useSettings } from '../composables/useSettings.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useToast } from '../composables/useToast.js'
import { useDefectClasses } from '../composables/useDefectClasses.js'
import DefectClassModal from '../components/DefectClassModal.vue'
import { listModels } from '../api/models.js'

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
const expandedGroups = ref({ coating: true, welding: true })
function toggleGroup(key) {
  expandedGroups.value[key] = !expandedGroups.value[key]
}

const showClassModal = ref(false)
const editingClass = ref(null)
const pendingDeleteClass = ref(null)

const coating = computed(() => classes.value.filter((c) => c.category === 'coating'))
const welding = computed(() => classes.value.filter((c) => c.category === 'welding'))
const coatingOn = computed(() => coating.value.filter((c) => c.enabled).length)
const weldingOn = computed(() => welding.value.filter((c) => c.enabled).length)
const classGroups = computed(() => [
  { key: 'coating', items: coating.value, on: coatingOn.value },
  { key: 'welding', items: welding.value, on: weldingOn.value },
])

const cameraTypes = [
  { value: 'rpi', label: 'Raspberry Pi Cam (CSI)' },
  { value: 'rtsp', label: 'RTSP Stream' },
  { value: 'usb', label: 'USB Camera' },
]

onMounted(async () => {
  refreshCameras()
  refreshSettings()
  refreshClasses()
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
    qcConfidenceThreshold: Number(settings.value.qcConfidenceThreshold),
    defectStrategy: settings.value.defectStrategy,
    activeModel: settings.value.activeModel,
    qcModel: settings.value.qcModel,
    quantityModel: settings.value.quantityModel,
    quantityConfidenceThreshold: Number(settings.value.quantityConfidenceThreshold),
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
        </div>
        <div class="config-grid">
          <div class="form-row">
            <label>{{ t('settings.activeModel') }}</label>
            <select v-if="availableModels.length" v-model="settings.activeModel" class="text-input">
              <option value="">{{ t('settings.noModelSelected') }}</option>
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
            <p v-else class="form-hint">{{ t('settings.noModels') }}</p>
          </div>
          <div class="form-row">
            <label>{{ t('settings.objectDetectionConfidence') }}</label>
            <input type="number" min="0" max="1" step="0.05" v-model="settings.confidenceThreshold" class="text-input" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.qcModel') }}</label>
            <select v-if="availableModels.length" v-model="settings.qcModel" class="text-input">
              <option value="">{{ t('settings.noModelSelected') }}</option>
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
            <p v-else class="form-hint">{{ t('settings.noModels') }}</p>
          </div>
          <div class="form-row">
            <label>{{ t('settings.qcConfidence') }}</label>
            <input type="number" min="0" max="1" step="0.05" v-model="settings.qcConfidenceThreshold" class="text-input" />
          </div>
          <div class="form-row">
            <label>{{ t('settings.defectStrategy') }}</label>
            <select v-model="settings.defectStrategy" class="text-input">
              <option value="mock">{{ t('settings.strategyMock') }}</option>
              <option value="sam3_prompt">{{ t('settings.strategySam3') }}</option>
            </select>
          </div>
          <div class="form-row">
            <label>{{ t('settings.quantityModel') }}</label>
            <select v-if="availableModels.length" v-model="settings.quantityModel" class="text-input">
              <option value="">{{ t('settings.noModelSelected') }}</option>
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
            <p v-else class="form-hint">{{ t('settings.noModels') }}</p>
          </div>
          <div class="form-row">
            <label>{{ t('settings.quantityConfidence') }}</label>
            <input type="number" min="0" max="1" step="0.05" v-model="settings.quantityConfidenceThreshold" class="text-input" />
          </div>
          <div class="form-actions">
            <button class="btn-sm primary" @click="saveSettings">{{ t('settings.save') }}</button>
          </div>
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
                <span class="dc-chevron">{{ expandedGroups[grp.key] ? '▾' : '▸' }}</span>
                {{ t('defectClasses.' + grp.key) }}
              </span>
              <span class="mono">{{ grp.on }} / {{ grp.items.length }} {{ t('defectClasses.on') }}</span>
            </button>
            <template v-if="expandedGroups[grp.key]">
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

    <DefectClassModal :show="showClassModal" :editing="editingClass" @cancel="showClassModal = false" @save="saveClass" />

    <div v-if="pendingDeleteClass" class="dialog-overlay" @click.self="pendingDeleteClass = null">
      <div class="dialog">
        <h3 class="dialog-title">{{ t('defectClasses.deleteTitle') }}</h3>
        <div class="dialog-body">
          <p>{{ t('defectClasses.confirmDelete') }} <span class="mono">{{ pendingDeleteClass.name }}</span>?</p>
        </div>
        <div class="dialog-actions">
          <button class="btn-ghost" @click="pendingDeleteClass = null">{{ t('common.cancel') }}</button>
          <button class="btn-primary" @click="confirmDeleteClass">{{ t('common.delete') }}</button>
        </div>
      </div>
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
  font-size: 12px;
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
  font-size: 14px;
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
  font-size: 12px;
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
  color: var(--color-ink);
  font-size: 14px;
}
.dialog-body p {
  margin: 0;
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
</style>
