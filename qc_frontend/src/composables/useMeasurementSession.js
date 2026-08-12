import { computed, ref } from 'vue'

import {
  createMeasurementSession,
  deleteMeasurementSession,
  deleteMeasurementView,
  getMeasurementSession,
  listMeasurementSessions,
  listMeasurementProfiles,
  saveMeasurementView,
  updateMeasurementSession,
} from '../api/measurements.js'

const session = ref(null)
const views = ref([])
const selectedViewId = ref(null)
const profiles = ref([])
const sessions = ref([])
let sequence = 0

function nextViewId() {
  sequence += 1
  return `view-${Date.now()}-${sequence}`
}

function revokePreview(url) {
  if (url?.startsWith('blob:') && typeof URL.revokeObjectURL === 'function') {
    URL.revokeObjectURL(url)
  }
}

function previewFor(file) {
  return typeof URL.createObjectURL === 'function'
    ? URL.createObjectURL(file)
    : 'data:image/gif;base64,R0lGODlhAQABAAAAACw='
}

function createView(fields = {}) {
  return {
    id: nextViewId(),
    sourceType: 'image',
    sourceKey: null,
    sourceFilename: '',
    sourceCameraId: null,
    file: null,
    previewUrl: '',
    width: 0,
    height: 0,
    viewLabel: '',
    poseType: 'TOP_FACE',
    taskType: 'linear_dimension',
    taskTypes: ['linear_dimension'],
    viewType: 'top',
    scaleProfileId: null,
    status: 'captured',
    processed: null,
    calibrationPoints: [],
    calibrationAxes: { x: [], y: [] },
    knownMm: '',
    knownMmY: '',
    ...fields,
  }
}

function appendView(view) {
  views.value.push(view)
  selectedViewId.value = view.id
  return view
}

function stageImage(input, sourceType = 'image') {
  const files = input instanceof File ? [input] : Array.from(input || [])
  return files.map((file) => appendView(createView({
    sourceType,
    sourceFilename: file.name || 'capture.jpg',
    file,
    previewUrl: previewFor(file),
  })))
}

function stageServerCapture(capture) {
  return appendView(createView({
    sourceType: capture.source_type || 'server_camera',
    sourceKey: capture.source_key || null,
    sourceFilename: capture.source_filename || 'camera-capture.jpg',
    sourceCameraId: capture.source_camera_id || null,
    previewUrl: capture.frame_url || '',
    width: capture.width || 0,
    height: capture.height || 0,
  }))
}

function stageMobileCapture(file) {
  return stageImage(file, 'mobile_camera')[0] || null
}

function selectView(id) {
  if (views.value.some((view) => view.id === id)) selectedViewId.value = id
}

function removeStagedView(id) {
  const view = views.value.find((item) => item.id === id)
  if (!view) return
  revokePreview(view.previewUrl)
  views.value = views.value.filter((item) => item.id !== id)
  if (selectedViewId.value === id) selectedViewId.value = views.value.at(-1)?.id || null
}

function updateViewMetadata(id, patch) {
  const view = views.value.find((item) => item.id === id)
  if (view) Object.assign(view, patch)
  return view || null
}

function clearSession() {
  views.value.forEach((view) => revokePreview(view.previewUrl))
  session.value = null
  views.value = []
  selectedViewId.value = null
}

async function startSession(name) {
  session.value = await createMeasurementSession(name)
  return session.value
}

async function loadProfiles() {
  if (typeof listMeasurementProfiles !== 'function') return profiles.value
  profiles.value = await listMeasurementProfiles()
  return profiles.value
}

async function loadSession(id) {
  session.value = await getMeasurementSession(id)
  views.value = (session.value.views || []).map((view) => createView({
    ...view,
    id: view.id,
    sourceType: view.source_type || view.sourceType || 'image',
    sourceKey: view.source_key || view.sourceKey || null,
    sourceFilename: view.source_filename || view.sourceFilename || '',
    sourceCameraId: view.source_camera_id || view.sourceCameraId || null,
    previewUrl: view.frame_url || view.source_url || view.preview_url || view.previewUrl || '',
    width: view.width || 1,
    height: view.height || 1,
    viewLabel: view.view_label || view.viewLabel || '',
    poseType: view.pose_type || view.poseType || 'TOP_FACE',
    scaleProfileId: view.scale_profile_id || view.scaleProfileId || null,
    taskType: view.processing?.task_type || view.task_type || 'linear_dimension',
    taskTypes: view.processing?.task_types || view.task_types || [view.processing?.task_type || view.task_type || 'linear_dimension'],
    viewType: view.processing?.view_type || view.view_type || 'top',
    calibrationPoints: view.calibration?.point_a && view.calibration?.point_b
      ? [view.calibration.point_a, view.calibration.point_b]
      : [],
    calibrationAxes: view.calibration?.mode === 'manual_axes'
      ? {
          x: view.calibration.x?.point_a ? [view.calibration.x.point_a, view.calibration.x.point_b] : [],
          y: view.calibration.y?.point_a ? [view.calibration.y.point_a, view.calibration.y.point_b] : [],
        }
      : { x: view.calibration?.point_a && view.calibration?.point_b ? [view.calibration.point_a, view.calibration.point_b] : [], y: [] },
    knownMm: view.calibration?.known_mm || 50,
    knownMmY: view.calibration?.y?.known_mm || view.calibration?.known_mm || 50,
    processed: {
      source_key: view.source_key || null,
      source_type: view.source_type || 'image',
      source_filename: view.source_filename || '',
      source_camera_id: view.source_camera_id || null,
      frame_url: view.source_url || '',
      width: view.width || 1,
      height: view.height || 1,
      calibration: view.calibration || {},
      task_type: view.processing?.task_type || 'linear_dimension',
      view_type: view.processing?.view_type || 'top',
      pose_type: view.pose_type || 'TOP_FACE',
      readiness: 'ready',
      reason: '',
      candidates: [],
      holes: [],
    },
    status: view.view_status || view.status || 'saved',
  }))
  selectedViewId.value = views.value[0]?.id || null
  return session.value
}

async function loadSessions() {
  if (typeof listMeasurementSessions !== 'function') return sessions.value
  sessions.value = await listMeasurementSessions()
  return sessions.value
}

async function saveSelectedView(payload = {}) {
  if (!session.value?.id || !selectedViewId.value) return null
  const view = views.value.find((item) => item.id === selectedViewId.value)
  const saved = await saveMeasurementView(session.value.id, {
    ...payload,
    view_label: payload.view_label ?? view?.viewLabel,
    pose_type: payload.pose_type ?? view?.poseType,
    scale_profile_id: payload.scale_profile_id ?? view?.scaleProfileId,
  })
  updateViewMetadata(selectedViewId.value, {
    ...saved,
    status: saved.status || 'saved',
  })
  return saved
}

async function completeSession() {
  if (!session.value?.id) return null
  session.value = await updateMeasurementSession(session.value.id, { status: 'complete' })
  return session.value
}

async function deleteSavedView(id) {
  if (session.value?.id && typeof deleteMeasurementView === 'function') {
    await deleteMeasurementView(session.value.id, id)
  }
  const wasSelected = selectedViewId.value === id
  const view = views.value.find((item) => item.id === id)
  if (view) revokePreview(view.previewUrl)
  views.value = views.value.filter((view) => view.id !== id)
  if (wasSelected) selectedViewId.value = views.value.at(-1)?.id || null
}

async function deleteSession(id) {
  if (typeof deleteMeasurementSession === 'function') await deleteMeasurementSession(id)
  sessions.value = sessions.value.filter((item) => item.id !== id)
  if (session.value?.id === id) clearSession()
}

const selectedView = computed(() => views.value.find((view) => view.id === selectedViewId.value) || null)

export function useMeasurementSession() {
  return {
    session,
    views,
    selectedView,
    selectedViewId,
    profiles,
    sessions,
    stageImage,
    stageServerCapture,
    stageMobileCapture,
    selectView,
    removeStagedView,
    updateViewMetadata,
    clearSession,
    startSession,
    loadProfiles,
    loadSessions,
    loadSession,
    saveSelectedView,
    completeSession,
    deleteSavedView,
    deleteSession,
  }
}
