<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useCameras } from '../composables/useCameras.js'
import { useToast } from '../composables/useToast.js'
import {
  captureMeasurement,
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
const knownMm = ref(50)
const taskType = ref('linear_dimension')
const viewType = ref('top')
const previewUrl = ref('')
const previewWidth = ref(1)
const previewHeight = ref(1)
const capturedSource = ref(null)
const calibrationPoints = ref([])
const calibrationMode = ref(false)
const calibrationDragging = ref(false)
const processed = ref(null)
const items = ref([])
const recentRuns = ref([])
const historyQuery = ref('')
const processing = ref(false)
const evaluated = ref(false)
const readOnly = ref(false)
const errorMessage = ref('')
const selectedCandidate = ref(-1)
const selectedHoleIndexes = ref([])
const selectedAngleIndexes = ref([])
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
const calibrationReady = computed(() => calibrationPoints.value.length === 2 && Number(knownMm.value) > 0)
const frameTransform = computed(() => `translate(${panX.value}px, ${panY.value}px) scale(${zoom.value})`)
const readiness = computed(() => processed.value?.readiness || 'idle')
const summaryStatus = computed(() => evaluated.value
  ? summarizeMeasurement(items.value, readiness.value)
  : readiness.value.toUpperCase())
const canProcess = computed(() => !processing.value && (
  source.value === 'image' || source.value === 'mobile'
    ? Boolean(selectedFile.value)
    : Boolean(capturedSource.value)
))
const taskIsHole = computed(() => taskType.value.startsWith('hole_'))
const taskNeedsEdgeCandidate = computed(() => taskType.value === 'hole_center_to_edge')
const taskRequiresProfile = computed(() => ['thickness_profile', 'bend_angle'].includes(taskType.value))
const taskViewSupported = computed(() => !taskRequiresProfile.value || ['profile', 'side'].includes(viewType.value))
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
  const points = calibrationPoints.value.length === 2
    ? calibrationPoints.value
    : [[20, 20], [120, 20]]
  return {
    mode: 'reference_line',
    point_a: points[0],
    point_b: points[1],
    known_mm: Number(knownMm.value),
  }
}

function clearPreview() {
  if (previewUrl.value?.startsWith('blob:') && typeof URL.revokeObjectURL === 'function') URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  previewWidth.value = 1
  previewHeight.value = 1
}

function resetStagedMeasurement() {
  processed.value = null
  items.value = []
  evaluated.value = false
  readOnly.value = false
  calibrationPoints.value = []
  calibrationMode.value = false
  selectedHoleIndexes.value = []
  selectedAngleIndexes.value = []
}

function startCalibration() {
  calibrationPoints.value = []
  calibrationMode.value = true
  errorMessage.value = ''
}

function previewPoint(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  const width = rect.width || 1
  const height = rect.height || 1
  return [
    Math.max(0, Math.min(previewWidth.value, ((event.clientX - rect.left) / width) * previewWidth.value)),
    Math.max(0, Math.min(previewHeight.value, ((event.clientY - rect.top) / height) * previewHeight.value)),
  ]
}

function onCalibrationPointerDown(event) {
  if (!calibrationMode.value || event.button !== 0) return
  calibrationPoints.value = [previewPoint(event)]
  calibrationDragging.value = true
}

function onCalibrationPointerMove(event) {
  if (!calibrationDragging.value) return
  calibrationPoints.value = [calibrationPoints.value[0], previewPoint(event)]
}

function onCalibrationPointerUp(event) {
  if (!calibrationDragging.value) return
  calibrationDragging.value = false
  calibrationPoints.value = [calibrationPoints.value[0], previewPoint(event)]
  calibrationMode.value = false
}

function chooseSource(value) {
  if (value !== source.value) {
    clearPreview()
    selectedFile.value = null
    capturedSource.value = null
    localFileName.value = ''
    resetStagedMeasurement()
  }
  source.value = value
  errorMessage.value = ''
  if (value === 'image') selectedCameraId.value = ''
  if (value !== 'mobile') stopMobileCamera()
}

function stageFile(file) {
  clearPreview()
  selectedFile.value = file
  capturedSource.value = null
  localFileName.value = selectedFile.value?.name || ''
  runName.value = selectedFile.value?.name?.replace(/\.[^.]+$/, '') || runName.value
  resetStagedMeasurement()
  selectedHoleIndexes.value = []
  selectedAngleIndexes.value = []
  if (selectedFile.value) {
    const objectUrl = typeof URL.createObjectURL === 'function' ? URL.createObjectURL(selectedFile.value) : ''
    previewUrl.value = objectUrl || 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=='
    previewWidth.value = 160
    previewHeight.value = 120
  }
  errorMessage.value = ''
}

function onFileChange(event) {
  stageFile(event.target.files?.[0] || null)
}

function stageCapturedFrame(capture) {
  clearPreview()
  selectedFile.value = null
  capturedSource.value = capture
  localFileName.value = capture.source_filename || ''
  runName.value = capture.source_filename?.replace(/\.[^.]+$/, '') || runName.value
  resetStagedMeasurement()
  previewUrl.value = capture.frame_url
  previewWidth.value = capture.width || 1
  previewHeight.value = capture.height || 1
  errorMessage.value = ''
}

function onPreviewLoad(event) {
  previewWidth.value = event.target.naturalWidth || event.target.width || 1
  previewHeight.value = event.target.naturalHeight || event.target.height || 1
}

async function runMeasurement(input) {
  processing.value = true
  errorMessage.value = ''
  readOnly.value = false
  try {
    processed.value = await processMeasurement({
      ...input,
      calibration: calibrationInput(),
      taskType: taskType.value,
      viewType: viewType.value,
    })
    items.value = []
    evaluated.value = false
    selectedCandidate.value = -1
    selectedHoleIndexes.value = []
    selectedAngleIndexes.value = []
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
    file: source.value === 'image' || source.value === 'mobile' ? selectedFile.value : undefined,
    sourceKey: source.value === 'live' ? capturedSource.value.source_key : undefined,
    sourceFilename: source.value === 'live' ? capturedSource.value.source_filename : undefined,
    sourceCameraId: source.value === 'live' ? capturedSource.value.source_camera_id : undefined,
    sourceType: source.value === 'mobile' ? 'mobile_camera' : source.value === 'live' ? 'live_camera' : 'image',
  })
}

async function captureCurrent() {
  if (!selectedCameraId.value || processing.value) return
  processing.value = true
  errorMessage.value = ''
  clearPreview()
  capturedSource.value = null
  resetStagedMeasurement()
  try {
    const capture = await captureMeasurement({ cameraId: selectedCameraId.value })
    stageCapturedFrame(capture)
    log('MEASUREMENT_CAPTURED', `${capture.source_type}:${capture.source_filename}`)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    processing.value = false
  }
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
    stageFile(new File([blob], 'mobile.jpg', { type: 'image/jpeg' }))
  }
}

function candidateKey(candidate, index) {
  const geometry = candidate.center ? candidate.center.join('-') : candidate.points.flat().join('-')
  return `${candidate.source}-${index}-${geometry}`
}

function selectCandidate(candidate, index) {
  if (readOnly.value || !processed.value) return
  if (taskType.value === 'bend_angle') {
    const nextIndexes = selectedAngleIndexes.value.includes(index)
      ? selectedAngleIndexes.value.filter((value) => value !== index)
      : [...selectedAngleIndexes.value, index]
    selectedAngleIndexes.value = nextIndexes.slice(-2)
    selectedCandidate.value = index
    if (selectedAngleIndexes.value.length < 2) return
    const [first, second] = selectedAngleIndexes.value.map((value) => processed.value.candidates[value])
    const shared = first.points.find((point) => second.points.some((other) => point[0] === other[0] && point[1] === other[1]))
    const otherPoint = (points) => points.find((point) => !shared || point[0] !== shared[0] || point[1] !== shared[1])
    const points = shared
      ? [shared, otherPoint(first.points), shared, otherPoint(second.points)]
      : [...first.points, ...second.points]
    const measured = measureGeometry('bend_angle', points, processed.value.calibration)
    const id = `B${items.value.length + 1}`
    items.value.push({
      id,
      type: 'bend_angle',
      task_type: 'bend_angle',
      view_type: viewType.value,
      label: `Bend ${id}`,
      points,
      measured: measured.value,
      unit: measured.unit,
      pixel_value: measured.pixel_value,
      nominal: null,
      tolerance: 0.5,
      confidence: Math.min(first.confidence, second.confidence),
      status: 'REVIEW',
      reason: 'missing_nominal_or_tolerance',
    })
    selectedAngleIndexes.value = []
    evaluated.value = false
    return
  }
  if (taskNeedsEdgeCandidate.value) {
    if (selectedHoleIndexes.value.length !== 1) return
    const hole = processed.value.holes[selectedHoleIndexes.value[0]]
    const geometry = {
      kind: 'circle_to_edge',
      center: hole.center,
      edge_a: candidate.points[0],
      edge_b: candidate.points[1],
    }
    const measured = measureGeometry(taskType.value, [], processed.value.calibration, geometry)
    const id = `H${items.value.length + 1}`
    items.value.push({
      id,
      type: taskType.value,
      task_type: taskType.value,
      view_type: viewType.value,
      label: `Hole ${id}`,
      points: [],
      geometry,
      measured: measured.value,
      unit: measured.unit,
      pixel_value: measured.pixel_value,
      nominal: null,
      tolerance: 2,
      confidence: Math.min(hole.confidence, candidate.confidence),
      status: 'REVIEW',
      reason: 'missing_nominal_or_tolerance',
    })
    selectedCandidate.value = index
    selectedHoleIndexes.value = []
    evaluated.value = false
    return
  }
  selectedCandidate.value = index
  const points = candidate.points
  if (taskType.value === 'thickness_profile') return
  const measured = measureGeometry(taskType.value, points, processed.value.calibration)
  const idPrefix = taskType.value === 'inclination' ? 'I' : 'E'
  const id = `${idPrefix}${items.value.length + 1}`
  items.value.push({
    id,
    type: taskType.value,
    task_type: taskType.value,
    view_type: viewType.value,
    label: taskType.value === 'inclination' ? `Inclination ${id}` : `Edge ${id}`,
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

function selectHole(candidate, index) {
  if (readOnly.value || !processed.value) return
  if (taskType.value === 'hole_center_distance' || taskType.value === 'hole_edge_distance') {
    const nextIndexes = selectedHoleIndexes.value.includes(index)
      ? selectedHoleIndexes.value.filter((value) => value !== index)
      : [...selectedHoleIndexes.value, index]
    selectedHoleIndexes.value = nextIndexes.slice(-2)
    selectedCandidate.value = index
    if (selectedHoleIndexes.value.length < 2) return
    const [firstIndex, secondIndex] = selectedHoleIndexes.value
    const first = processed.value.holes[firstIndex]
    const second = processed.value.holes[secondIndex]
    const pairGeometry = {
      kind: 'circle_pair',
      center_a: first.center,
      center_b: second.center,
      radius_a_px: first.radius_px,
      radius_b_px: second.radius_px,
    }
    const measuredPair = measureGeometry(taskType.value, [], processed.value.calibration, pairGeometry)
    const pairId = `H${items.value.length + 1}`
    items.value.push({
      id: pairId,
      type: taskType.value,
      task_type: taskType.value,
      view_type: viewType.value,
      label: `Hole ${pairId}`,
      points: [],
      geometry: pairGeometry,
      measured: measuredPair.value,
      unit: measuredPair.unit,
      pixel_value: measuredPair.pixel_value,
      nominal: null,
      tolerance: 2,
      confidence: Math.min(first.confidence, second.confidence),
      status: 'REVIEW',
      reason: 'missing_nominal_or_tolerance',
    })
    selectedHoleIndexes.value = []
    evaluated.value = false
    return
  }
  if (taskType.value === 'hole_center_to_edge') {
    selectedHoleIndexes.value = [index]
    selectedCandidate.value = -1
    return
  }
  selectedCandidate.value = index
  const geometry = {
    kind: 'circle',
    center: candidate.center,
    radius_px: candidate.radius_px,
  }
  const measured = measureGeometry(taskType.value, [], processed.value.calibration, geometry)
  const id = `H${items.value.length + 1}`
  items.value.push({
    id,
    type: taskType.value,
    task_type: taskType.value,
    view_type: viewType.value,
    label: `Hole ${id}`,
    points: [],
    geometry,
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
  taskType.value = run.processing?.task_type || run.items?.[0]?.task_type || run.items?.[0]?.type || 'linear_dimension'
  viewType.value = run.processing?.view_type || run.items?.[0]?.view_type || 'top'
  clearPreview()
  capturedSource.value = null
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
onBeforeUnmount(() => {
  stopMobileCamera()
  clearPreview()
})
</script>

<template>
  <main class="measurement-page measurement-shell">
    <div class="measurement-studio">
      <aside class="measurement-rail">
        <div class="measurement-rail-body scroll-region">
        <section class="rail-section">
          <div class="panel-section-title">{{ t('measurement.input') }}</div>
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

          <div class="task-grid">
            <label class="field-label" for="task-type">
              {{ t('measurement.taskType') }}
              <select id="task-type" v-model="taskType">
                <option value="linear_dimension">{{ t('measurement.taskLinear') }}</option>
                <option value="thickness_profile">{{ t('measurement.taskThickness') }}</option>
                <option value="bend_angle">{{ t('measurement.taskBend') }}</option>
                <option value="inclination">{{ t('measurement.taskInclination') }}</option>
                <option value="hole_diameter">{{ t('measurement.taskHoleDiameter') }}</option>
                <option value="hole_center_distance">{{ t('measurement.taskHolePitch') }}</option>
                <option value="hole_edge_distance">{{ t('measurement.taskHoleEdge') }}</option>
                <option value="hole_center_to_edge">{{ t('measurement.taskHoleToEdge') }}</option>
              </select>
            </label>
            <label class="field-label" for="view-type">
              {{ t('measurement.viewType') }}
              <select id="view-type" v-model="viewType">
                <option value="top">{{ t('measurement.viewTop') }}</option>
                <option value="profile">{{ t('measurement.viewProfile') }}</option>
                <option value="side">{{ t('measurement.viewSide') }}</option>
              </select>
            </label>
          </div>
          <p v-if="!taskViewSupported" class="task-warning">{{ t('measurement.profileViewRequired') }}</p>

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
            <button type="button" class="btn btn-primary trigger-capture" :disabled="!selectedCameraId || processing" @click="captureCurrent">
              {{ processing ? t('measurement.processing') : t('measurement.triggerCapture') }}
            </button>
          </template>
        </section>

        <section class="rail-section">
          <div class="panel-section-title">{{ t('measurement.calibration') }}</div>
          <p class="section-help">{{ t('measurement.calibrationHelp') }}</p>
          <button type="button" class="btn btn-secondary calibration-draw-button" :disabled="!previewUrl || readOnly" @click="startCalibration">
            {{ calibrationMode ? t('measurement.calibrationDrawing') : t('measurement.drawReference') }}
          </button>
          <label class="field-label" for="known-mm">{{ t('measurement.knownLength') }}</label>
          <div class="input-unit">
            <input id="known-mm" v-model.number="knownMm" type="number" min="0.01" step="0.01">
            <span>mm</span>
          </div>
          <p class="calibration-state" :class="{ valid: calibrationReady }">
            {{ calibrationReady ? t('measurement.calibrationReady') : t('measurement.calibrationPending') }}
          </p>
          <div class="calibration-readout">
            <span>{{ t('measurement.scale') }}</span>
            <strong>{{ processed?.calibration?.mm_per_pixel?.toFixed?.(4) || '—' }} mm/px</strong>
          </div>
        </section>
        </div>

        <section class="rail-section history-section scroll-region">
          <div class="panel-section-title">{{ t('measurement.history') }}</div>
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
        <div
          class="measurement-viewport"
          :class="{ 'is-dragging': dragging }"
          @wheel="onWheel"
          @mousedown="onMouseDown"
          @mousemove="onMouseMove"
          @mouseup="onMouseUp"
          @mouseleave="onMouseUp"
        >
          <div class="measurement-canvas-tools" @mousedown.stop>
            <div>
              <span class="toolbar-label">{{ t('measurement.currentSource') }}</span>
              <strong>{{ processed?.source_filename || localFileName || t('measurement.noInput') }}</strong>
            </div>
            <div class="measurement-canvas-actions">
              <span class="canvas-status mono" :class="`status-${summaryStatus.toLowerCase()}`">{{ summaryStatus }}</span>
              <button type="button" class="btn btn-primary process-measurement" :disabled="!canProcess" @click="processCurrent">
                {{ processing ? t('measurement.processing') : t('measurement.process') }}
              </button>
            </div>
          </div>
          <div v-if="!processed && previewUrl" class="measurement-preview">
            <div class="measurement-image-frame preview-frame">
              <img class="measurement-image" :src="previewUrl" :alt="localFileName" @load="onPreviewLoad" draggable="false">
              <svg
                class="measurement-overlay calibration-overlay"
                :viewBox="`0 0 ${previewWidth} ${previewHeight}`"
                preserveAspectRatio="none"
                :class="{ active: calibrationMode }"
                @mousedown.stop="onCalibrationPointerDown"
                @mousemove.stop="onCalibrationPointerMove"
                @mouseup.stop="onCalibrationPointerUp"
              >
                <line
                  v-if="calibrationPoints.length === 2"
                  class="calibration-drawn-line"
                  :x1="calibrationPoints[0][0]"
                  :y1="calibrationPoints[0][1]"
                  :x2="calibrationPoints[1][0]"
                  :y2="calibrationPoints[1][1]"
                ></line>
                <circle v-for="(point, index) in calibrationPoints" :key="`calibration-point-${index}`" class="calibration-drawn-point" :cx="point[0]" :cy="point[1]" r="6"></circle>
              </svg>
            </div>
            <span class="preview-guidance">{{ calibrationMode ? t('measurement.calibrationDrawHint') : t('measurement.previewHint') }}</span>
          </div>
          <div v-else-if="!processed" class="viewport-empty">
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
                :class="{ selected: selectedCandidate === index || selectedAngleIndexes.includes(index) }"
                @click="selectCandidate(candidate, index)"
              >
                <line class="measurement-line-halo" :x1="candidate.points[0][0]" :y1="candidate.points[0][1]" :x2="candidate.points[1][0]" :y2="candidate.points[1][1]"></line>
                <line class="measurement-line" :x1="candidate.points[0][0]" :y1="candidate.points[0][1]" :x2="candidate.points[1][0]" :y2="candidate.points[1][1]"></line>
                <circle class="measurement-point-halo" :cx="candidate.points[0][0]" :cy="candidate.points[0][1]" r="7"></circle>
                <circle class="measurement-point-halo" :cx="candidate.points[1][0]" :cy="candidate.points[1][1]" r="7"></circle>
                <circle class="measurement-point" :cx="candidate.points[0][0]" :cy="candidate.points[0][1]" r="4"></circle>
                <circle class="measurement-point" :cx="candidate.points[1][0]" :cy="candidate.points[1][1]" r="4"></circle>
              </g>
              <g
                v-for="(hole, index) in (processed.holes || [])"
                :key="`hole-${index}-${hole.center.join('-')}`"
                class="measurement-hole-candidate"
                :class="{ selected: selectedHoleIndexes.includes(index) }"
                @click.stop="selectHole(hole, index)"
              >
                <circle class="measurement-hole-halo" :cx="hole.center[0]" :cy="hole.center[1]" :r="hole.radius_px"></circle>
                <circle class="measurement-hole-center" :cx="hole.center[0]" :cy="hole.center[1]" r="4"></circle>
                <line class="measurement-hole-crosshair" :x1="hole.center[0] - 10" :y1="hole.center[1]" :x2="hole.center[0] + 10" :y2="hole.center[1]"></line>
                <line class="measurement-hole-crosshair" :x1="hole.center[0]" :y1="hole.center[1] - 10" :x2="hole.center[0]" :y2="hole.center[1] + 10"></line>
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
                <template v-if="item.geometry?.kind === 'circle'">
                  <circle class="measurement-line-halo" :cx="item.geometry.center[0]" :cy="item.geometry.center[1]" :r="item.geometry.radius_px"></circle>
                  <circle class="measurement-line" :cx="item.geometry.center[0]" :cy="item.geometry.center[1]" :r="item.geometry.radius_px"></circle>
                </template>
                <template v-else-if="item.geometry?.kind === 'circle_pair'">
                  <line class="measurement-line-halo" :x1="item.geometry.center_a[0]" :y1="item.geometry.center_a[1]" :x2="item.geometry.center_b[0]" :y2="item.geometry.center_b[1]"></line>
                  <line class="measurement-line" :x1="item.geometry.center_a[0]" :y1="item.geometry.center_a[1]" :x2="item.geometry.center_b[0]" :y2="item.geometry.center_b[1]"></line>
                </template>
                <template v-else-if="item.geometry?.kind === 'circle_to_edge'">
                  <circle class="measurement-point-halo" :cx="item.geometry.center[0]" :cy="item.geometry.center[1]" r="7"></circle>
                  <circle class="measurement-point" :cx="item.geometry.center[0]" :cy="item.geometry.center[1]" r="4"></circle>
                  <line class="measurement-line-halo" :x1="item.geometry.edge_a[0]" :y1="item.geometry.edge_a[1]" :x2="item.geometry.edge_b[0]" :y2="item.geometry.edge_b[1]"></line>
                  <line class="measurement-line" :x1="item.geometry.edge_a[0]" :y1="item.geometry.edge_a[1]" :x2="item.geometry.edge_b[0]" :y2="item.geometry.edge_b[1]"></line>
                </template>
                <template v-else>
                  <line class="measurement-line-halo" :x1="item.points[0][0]" :y1="item.points[0][1]" :x2="item.points[1][0]" :y2="item.points[1][1]"></line>
                  <line class="measurement-line" :x1="item.points[0][0]" :y1="item.points[0][1]" :x2="item.points[1][0]" :y2="item.points[1][1]"></line>
                </template>
                <text v-if="item.geometry?.kind === 'circle'" :x="item.geometry.center[0]" :y="item.geometry.center[1] - item.geometry.radius_px - 6">{{ item.id }} · {{ Number(item.measured).toFixed(1) }} {{ item.unit }}</text>
                <text v-else-if="item.geometry?.kind === 'circle_pair'" :x="item.geometry.center_a[0]" :y="item.geometry.center_a[1] - 6">{{ item.id }} · {{ Number(item.measured).toFixed(1) }} {{ item.unit }}</text>
                <text v-else-if="item.geometry?.kind === 'circle_to_edge'" :x="item.geometry.center[0]" :y="item.geometry.center[1] - 9">{{ item.id }} · {{ Number(item.measured).toFixed(1) }} {{ item.unit }}</text>
                <text v-else :x="item.points[0][0]" :y="item.points[0][1] - 6">{{ item.id }} · {{ Number(item.measured).toFixed(1) }} {{ item.unit }}</text>
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
            <span>{{ taskIsHole ? (processed.holes || []).length : processed.candidates.length }} {{ t('measurement.detected') }}</span>
          </div>
          <template v-if="!taskIsHole">
            <button v-for="(candidate, index) in processed.candidates" :key="candidateKey(candidate, index)" type="button" class="candidate-card" :class="{ selected: selectedCandidate === index || selectedAngleIndexes.includes(index) }" @click="selectCandidate(candidate, index)">
              <span class="candidate-line"></span>
              <strong>L{{ index + 1 }}</strong>
              <span>{{ candidate.length_px.toFixed(1) }} px</span>
              <small>{{ candidate.source }} · {{ candidate.confidence.toFixed(2) }}</small>
            </button>
          </template>
          <template v-else>
            <button v-for="(hole, index) in (processed.holes || [])" :key="candidateKey(hole, index)" type="button" class="candidate-card hole-card" :class="{ selected: selectedCandidate === index || selectedHoleIndexes.includes(index) }" @click="selectHole(hole, index)">
              <span class="candidate-hole"></span>
              <strong>H{{ index + 1 }}</strong>
              <span>Ø {{ hole.diameter_px.toFixed(1) }} px</span>
              <small>{{ hole.source }} · {{ hole.confidence.toFixed(2) }}</small>
            </button>
          </template>
          <template v-if="taskNeedsEdgeCandidate">
            <button v-for="(candidate, index) in processed.candidates" :key="`edge-${candidateKey(candidate, index)}`" type="button" class="candidate-card" :class="{ selected: selectedCandidate === index || selectedAngleIndexes.includes(index) }" @click="selectCandidate(candidate, index)">
              <span class="candidate-line"></span>
              <strong>E{{ index + 1 }}</strong>
              <span>{{ candidate.length_px.toFixed(1) }} px</span>
              <small>{{ candidate.source }} · {{ candidate.confidence.toFixed(2) }}</small>
            </button>
          </template>
          <button v-if="!taskIsHole" type="button" class="candidate-card manual-card" :disabled="readOnly" @click="addManualItem">
            <strong>＋</strong>
            <span>{{ t('measurement.addManual') }}</span>
          </button>
        </div>
      </section>

      <aside class="measurement-results">
        <section class="results-header">
          <div class="panel-section-title">{{ t('measurement.evaluate') }}</div>
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
  padding: 0;
  background: var(--color-canvas);
  color: var(--color-ink);
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
  border: 0;
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

.measurement-rail { width: var(--sidebar-left); flex-basis: var(--sidebar-left); border-right: 1px solid var(--color-hairline); }
.measurement-results { width: var(--sidebar-right); flex-basis: var(--sidebar-right); border-left: 1px solid var(--color-hairline); }

.measurement-rail-body { min-height: 0; flex: 1 1 auto; }

.rail-section,
.results-header,
.items-section,
.result-actions {
  padding: 22px;
  border-bottom: 1px solid var(--color-hairline);
}

.panel-section-title {
  margin: 0 0 14px;
  color: var(--color-ink);
  font-size: 15px;
  font-weight: 600;
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
.task-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px; }
.task-grid .field-label { margin-top: 0; }
.task-grid select { margin-top: 5px; min-height: 42px; font-size: 11px; }
.task-warning { margin: 12px 0 0; padding: 9px; border-left: 3px solid var(--color-warning); background: var(--color-surface-1); color: var(--color-warning); font-size: 11px; line-height: 1.4; }

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
.calibration-draw-button { width: 100%; margin-bottom: 4px; }
.calibration-state { margin: 10px 0 0; color: var(--color-warning); font-family: var(--font-mono); font-size: 11px; }
.calibration-state.valid { color: var(--color-success); }

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
.measurement-viewport { position: relative; display: grid; flex: 1 1 auto; min-height: 0; place-items: center; padding: 28px; overflow: hidden; cursor: grab; background: var(--color-surface-1); }
.measurement-viewport.is-dragging { cursor: grabbing; }
.measurement-preview { display: grid; max-width: 100%; max-height: 100%; place-items: center; gap: 12px; }
.preview-frame { max-width: min(100%, 920px); max-height: calc(100% - 32px); }
.preview-frame .measurement-image { max-height: calc(100vh - 260px); }
.calibration-overlay.active { cursor: crosshair; }
.calibration-drawn-line { stroke: var(--color-warning); stroke-width: 3; vector-effect: non-scaling-stroke; stroke-dasharray: 8 4; }
.calibration-drawn-point { fill: var(--color-warning); stroke: var(--color-canvas); stroke-width: 3; vector-effect: non-scaling-stroke; }
.preview-guidance { color: var(--color-ink-muted); font-size: 12px; text-align: center; }
.measurement-canvas-tools { position: absolute; top: 12px; left: 12px; z-index: 2; display: flex; align-items: center; justify-content: space-between; gap: 18px; max-width: calc(100% - 24px); padding: 9px 10px; border: 1px solid var(--color-hairline); background: var(--color-canvas); }
.measurement-canvas-tools strong { display: block; max-width: 280px; overflow: hidden; color: var(--color-ink); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.measurement-canvas-actions { display: flex; align-items: center; gap: 10px; }
.canvas-status { color: var(--color-ink-muted); font-size: 11px; font-weight: 600; }
.canvas-status.status-pass { color: var(--color-success); }
.canvas-status.status-fail { color: var(--color-error); }
.canvas-status.status-review { color: var(--color-warning); }
.measurement-image-frame { position: relative; transform-origin: center; transition: transform 0.05s linear; }
.measurement-image { display: block; max-width: 100%; max-height: 100%; object-fit: contain; pointer-events: none; }
.measurement-overlay { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: auto; }
.measurement-candidate { pointer-events: all; cursor: pointer; opacity: 0.9; }
.measurement-line-halo { stroke: var(--color-canvas); stroke-width: 6; vector-effect: non-scaling-stroke; }
.measurement-line { stroke: var(--color-info); stroke-width: 3; vector-effect: non-scaling-stroke; }
.measurement-point-halo { fill: var(--color-canvas); }
.measurement-point { fill: var(--color-info); }
.measurement-hole-candidate { cursor: pointer; opacity: 0.92; }
.measurement-hole-halo { fill: none; stroke: var(--color-canvas); stroke-width: 7; vector-effect: non-scaling-stroke; }
.measurement-hole-candidate > .measurement-hole-halo { stroke: var(--color-warning); stroke-width: 3; }
.measurement-hole-center { fill: var(--color-warning); stroke: var(--color-canvas); stroke-width: 3; vector-effect: non-scaling-stroke; }
.measurement-hole-crosshair { stroke: var(--color-warning); stroke-width: 2; vector-effect: non-scaling-stroke; }
.measurement-candidate.selected { opacity: 1; }
.measurement-candidate.selected .measurement-line { stroke: var(--color-warning); stroke-width: 4; }
.measurement-candidate.selected .measurement-point { fill: var(--color-warning); }
.selected-measurement { pointer-events: none; }
.selected-measurement .measurement-line { stroke: var(--color-success); stroke-width: 4; stroke-dasharray: 7 4; }
.selected-measurement text { fill: var(--color-success); font-family: var(--font-mono); font-size: 14px; font-weight: 600; paint-order: stroke; stroke: var(--color-surface-1); stroke-width: 5px; }
.calibration-reference { pointer-events: none; }
.calibration-reference line { stroke: var(--color-warning); stroke-width: 2.5; stroke-dasharray: 5 4; vector-effect: non-scaling-stroke; }
.calibration-reference text { fill: var(--color-warning); font-family: var(--font-mono); font-size: 13px; font-weight: 600; paint-order: stroke; stroke: var(--color-surface-1); stroke-width: 5px; }
.viewport-empty { display: grid; place-items: center; gap: 8px; color: var(--color-ink-muted); text-align: center; }
.viewport-empty span { max-width: 250px; font-size: 12px; }
.empty-crosshair { color: var(--color-primary); font-family: var(--font-mono); font-size: 42px; font-weight: 300; }

.candidate-strip { display: flex; gap: 10px; min-height: 100px; padding: 14px 18px; overflow-x: auto; border-top: 1px solid var(--color-hairline); background: var(--color-canvas); }
.strip-header { display: flex; min-width: 100px; flex-direction: column; justify-content: center; gap: 4px; color: var(--color-ink-muted); font-size: 11px; }
.strip-header span:last-child { font-family: var(--font-mono); }
.candidate-card { display: grid; min-width: 120px; grid-template-columns: 16px 1fr; align-content: center; gap: 2px 6px; padding: 8px; border: 1px solid var(--color-hairline); background: var(--color-surface-1); color: var(--color-ink); text-align: left; cursor: pointer; font-size: 11px; }
.candidate-card.selected { border-color: var(--color-warning); background: color-mix(in srgb, var(--color-warning) 12%, var(--color-canvas)); }
.candidate-card span, .candidate-card small { grid-column: 2; color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 10px; }
.candidate-line { grid-column: 1; grid-row: 1 / span 3; align-self: center; width: 14px; height: 2px; background: var(--color-info); }
.candidate-hole { grid-column: 1; grid-row: 1 / span 3; align-self: center; width: 14px; height: 14px; border: 2px solid var(--color-warning); }
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
