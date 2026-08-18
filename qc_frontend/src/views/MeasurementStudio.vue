<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { useCameras } from '../composables/useCameras.js'
import { useMeasurementSession } from '../composables/useMeasurementSession.js'
import { useToast } from '../composables/useToast.js'
import {
  captureMeasurement,
  detectMeasurementJig,
  deleteMeasurementRun,
  listMeasurementRuns,
  processMeasurement,
  saveMeasurementRun,
} from '../api/measurements.js'
import {
  evaluateMeasurementItem,
  measureGeometry,
  summarizeMeasurement,
  validateManualCalibration,
} from '../utils/measurement.js'

const { t } = useI18n()
const { cameras } = useCameras()
const { log } = useAuditLog()
const { showToast } = useToast()
const measurementSession = useMeasurementSession()
const {
  session,
  views: stagedViews,
  selectedView,
  selectedViewId,
  profiles,
  sessions,
  startSession,
  stageImage,
  stageServerCapture,
  stageMobileCapture,
  selectView,
  updateViewMetadata,
  removeStagedView,
  saveSelectedView,
  completeSession,
  deleteSavedView,
  deleteSession,
  clearSession,
  loadProfiles,
  loadSessions,
} = measurementSession

const source = ref('image')
const selectedFile = ref(null)
const localFileName = ref('')
const runName = ref('')
const sessionNameError = ref('')
const sessionStarting = ref(false)
const selectedCameraId = ref('')
const knownMm = ref(50)
const knownMmY = ref(50)
const calibrationSource = ref('component_demo')
const taskType = ref('linear_dimension')
const selectedTaskTypes = ref(['linear_dimension'])
const viewType = ref('top')
const viewLabel = ref('')
const poseType = ref('TOP_FACE')
const scaleProfileId = ref('')
const previewUrl = ref('')
const previewWidth = ref(1)
const previewHeight = ref(1)
const capturedSource = ref(null)
const calibrationAxes = ref({ x: [], y: [] })
const calibrationAxis = ref('x')
const calibrationMode = ref(false)
const calibrationDragging = ref(false)
const calibrationCursor = ref(null)
const showCalibrationReference = ref(true)
const showDetectedEdges = ref(true)
const showEvaluatedMeasurements = ref(true)
const jigDetecting = ref(false)
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
const calibrationPoints = computed({
  get: () => calibrationAxes.value.x,
  set: (value) => { calibrationAxes.value = { ...calibrationAxes.value, x: value } },
})
const activeCalibrationPoints = computed(() => calibrationAxes.value[calibrationAxis.value] || [])
const calibrationValidation = computed(() => validateManualCalibration({
  axes: calibrationAxes.value,
  knownX: knownMm.value,
  knownY: knownMmY.value,
}))
const calibrationReady = computed(() => calibrationValidation.value.valid)
const frameTransform = computed(() => `translate(${panX.value}px, ${panY.value}px) scale(${zoom.value})`)
const readiness = computed(() => processed.value?.readiness || 'idle')
const summaryStatus = computed(() => evaluated.value
  ? summarizeMeasurement(items.value, readiness.value)
  : readiness.value.toUpperCase())
const canProcess = computed(() => !processing.value && taskSelectionSupported.value && (
  calibrationReady.value
  && (
  source.value === 'image' || source.value === 'mobile'
    ? Boolean(selectedFile.value)
    : Boolean(capturedSource.value)
  )
))
const taskIsHole = computed(() => taskType.value.startsWith('hole_'))
const taskTypesForProcess = computed(() => selectedTaskTypes.value.length ? selectedTaskTypes.value : ['linear_dimension'])
const cornerTaskSelected = computed(() => taskTypesForProcess.value.includes('corner_radius'))
const bendTaskSelected = computed(() => taskTypesForProcess.value.includes('bend_angle'))
const taskSelectionRequiresProfile = computed(() => taskTypesForProcess.value.some((type) => ['thickness_profile', 'bend_angle'].includes(type)))
const taskSelectionSupported = computed(() => !taskSelectionRequiresProfile.value || (viewType.value !== 'top' && poseType.value === 'PROFILE_FACE'))
const taskNeedsEdgeCandidate = computed(() => taskType.value === 'hole_center_to_edge')
const taskRequiresProfile = computed(() => ['thickness_profile', 'bend_angle'].includes(taskType.value))
const poseSupported = computed(() => !taskRequiresProfile.value || poseType.value === 'PROFILE_FACE')
const taskViewSupported = computed(() => poseSupported.value && (!taskRequiresProfile.value || ['profile', 'side'].includes(viewType.value)))
const selectedProfile = computed(() => profiles.value.find((profile) => profile.id === scaleProfileId.value) || null)
const canEvaluate = computed(() => (
  !readOnly.value && Boolean(processed.value) && readiness.value === 'ready' && items.value.length > 0
))
const canSave = computed(() => Boolean(runName.value.trim()) && evaluated.value && items.value.length > 0 && !readOnly.value)
const canSaveView = computed(() => Boolean(session.value?.id) && canSave.value)
const canCompleteSession = computed(() => Boolean(session.value?.id) && stagedViews.value.length > 0 && stagedViews.value.every((view) => view.status === 'saved'))
const filteredRuns = computed(() => {
  const query = historyQuery.value.trim().toLowerCase()
  if (!query) return recentRuns.value
  return recentRuns.value.filter((run) => `${run.name} ${run.source_filename}`.toLowerCase().includes(query))
})
const filteredSessions = computed(() => {
  const query = historyQuery.value.trim().toLowerCase()
  if (!query) return sessions.value
  return sessions.value.filter((item) => `${item.name} ${item.status}`.toLowerCase().includes(query))
})
const logicalEdges = computed(() => processed.value?.logical_edges || [])
const visibleCandidates = computed(() => logicalEdges.value.length ? logicalEdges.value : (processed.value?.candidates || []))
const cornerCandidates = computed(() => processed.value?.corner_arcs || [])
const bendCandidates = computed(() => processed.value?.bend_candidates || [])
const evaluatedOverlayItems = computed(() => {
  const width = Number(processed.value?.width) || 0
  const height = Number(processed.value?.height) || 0
  const labels = []
  return items.value.map((item, index) => {
    const anchor = measurementAnchor(item)
    const side = anchor[0] > width / 2 ? -1 : 1
    const x = Math.max(8, Math.min(width - 8, anchor[0] + side * 24))
    let y = Math.max(12, Math.min(height - 8, anchor[1] + (index % 2 ? 16 : -16)))
    const conflict = labels.find((label) => label.side === side && Math.abs(label.x - x) < 84 && Math.abs(label.y - y) < 18)
    if (conflict) y = Math.max(12, Math.min(height - 8, conflict.y + 18))
    const overlay = { item, anchor, side, x, y, textAnchor: side > 0 ? 'start' : 'end' }
    labels.push(overlay)
    return overlay
  })
})
const selectionGuidance = computed(() => [
  taskTypesForProcess.value.includes('linear_dimension') ? t('measurement.selectEdgeHint') : '',
  taskTypesForProcess.value.includes('corner_radius') ? t('measurement.selectCornerHint') : '',
  taskTypesForProcess.value.includes('bend_angle') ? t('measurement.selectBendHint') : '',
].filter(Boolean).join(' · '))

const calibrationReferences = computed(() => {
  const calibration = processed.value?.calibration || {}
  if (calibration.mode === 'manual_axes') {
    return ['x', 'y'].filter((axis) => calibration[axis]?.point_a && calibration[axis]?.point_b).map((axis) => ({
      axis: axis.toUpperCase(),
      point_a: calibration[axis].point_a,
      point_b: calibration[axis].point_b,
      known_mm: calibration[axis].known_mm,
    }))
  }
  return calibration.point_a && calibration.point_b
    ? [{ axis: 'REF', point_a: calibration.point_a, point_b: calibration.point_b, known_mm: calibration.known_mm }]
    : []
})

const selectedSourceName = computed(() => selectedView.value?.sourceFilename || localFileName.value || t('measurement.noInput'))

function calibrationInput() {
  const xPoints = calibrationAxes.value.x.length === 2 ? calibrationAxes.value.x : [[20, 20], [120, 20]]
  const yPoints = calibrationAxes.value.y.length === 2 ? calibrationAxes.value.y : [[20, 20], [20, 120]]
  return {
    mode: 'manual_axes',
    source: calibrationSource.value,
    coordinate_width: previewWidth.value,
    coordinate_height: previewHeight.value,
    x: { point_a: xPoints[0], point_b: xPoints[1], known_mm: Number(knownMm.value) },
    y: { point_a: yPoints[0], point_b: yPoints[1], known_mm: Number(knownMmY.value) },
  }
}

const calibrationStateLabel = computed(() => {
  if (calibrationReady.value) return t('measurement.calibrationReady')
  return t(`measurement.calibration_${calibrationValidation.value.reason}`)
})

function clearPreview() {
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
  calibrationAxes.value = { x: [], y: [] }
  calibrationMode.value = false
  calibrationCursor.value = null
  calibrationAxis.value = 'x'
  calibrationSource.value = 'component_demo'
  showCalibrationReference.value = true
  showDetectedEdges.value = true
  showEvaluatedMeasurements.value = true
  selectedHoleIndexes.value = []
  selectedAngleIndexes.value = []
  selectedTaskTypes.value = ['linear_dimension']
}

function syncActiveView() {
  if (!selectedViewId.value) return
  updateViewMetadata(selectedViewId.value, {
    sourceKey: processed.value?.source_key || selectedView.value?.sourceKey || null,
    sourceFilename: processed.value?.source_filename || selectedView.value?.sourceFilename || localFileName.value,
    sourceType: processed.value?.source_type || selectedView.value?.sourceType || source.value,
    sourceCameraId: processed.value?.source_camera_id || selectedView.value?.sourceCameraId || null,
    taskType: taskType.value,
    taskTypes: taskTypesForProcess.value,
    viewType: viewType.value,
    viewLabel: viewLabel.value,
    poseType: poseType.value,
    scaleProfileId: scaleProfileId.value || null,
    knownMm: knownMm.value,
    calibrationSource: calibrationSource.value,
    calibrationPoints: calibrationPoints.value,
    knownMmY: knownMmY.value,
    calibrationAxes: calibrationAxes.value,
    processed: processed.value,
    items: items.value,
    status: processed.value ? (evaluated.value ? 'evaluated' : 'processed') : 'captured',
  })
}

function loadActiveView(view = selectedView.value) {
  if (!view) {
    clearPreview()
    selectedFile.value = null
    capturedSource.value = null
    localFileName.value = ''
    resetStagedMeasurement()
    return
  }
  source.value = view.sourceType === 'live_camera' || view.sourceType === 'server_camera'
    ? 'live'
    : view.sourceType === 'mobile_camera' ? 'mobile' : 'image'
  selectedFile.value = view.file || null
  capturedSource.value = view.sourceKey
    ? {
        source_key: view.sourceKey,
        source_type: view.sourceType,
        source_filename: view.sourceFilename,
        source_camera_id: view.sourceCameraId,
        frame_url: view.previewUrl,
        width: view.width,
        height: view.height,
      }
    : null
  localFileName.value = view.sourceFilename || ''
  previewUrl.value = view.previewUrl || ''
  previewWidth.value = view.width || 1
  previewHeight.value = view.height || 1
  taskType.value = view.taskType || 'linear_dimension'
  selectedTaskTypes.value = view.taskTypes?.length
    ? [...view.taskTypes]
    : view.processed?.task_types?.length ? [...view.processed.task_types] : [taskType.value]
  viewType.value = view.viewType || 'top'
  viewLabel.value = view.viewLabel || ''
  poseType.value = view.poseType || 'TOP_FACE'
  scaleProfileId.value = view.scaleProfileId || ''
  knownMm.value = view.knownMm || 50
  knownMmY.value = view.knownMmY || 50
  calibrationSource.value = view.calibrationSource || view.processed?.calibration?.source || 'component_demo'
  const persistedAxes = view.calibrationAxes || (view.processed?.calibration?.mode === 'manual_axes'
    ? { x: view.processed.calibration.x?.point_a ? [view.processed.calibration.x.point_a, view.processed.calibration.x.point_b] : [], y: view.processed.calibration.y?.point_a ? [view.processed.calibration.y.point_a, view.processed.calibration.y.point_b] : [] }
    : { x: view.calibrationPoints || [], y: [] })
  calibrationAxes.value = { x: persistedAxes.x || [], y: persistedAxes.y || [] }
  processed.value = view.processed || null
  items.value = view.items || []
  evaluated.value = Boolean(view.status === 'evaluated' || view.status === 'saved')
  readOnly.value = false
  selectedHoleIndexes.value = []
  selectedAngleIndexes.value = []
  resetZoom()
}

function selectStagedView(id) {
  if (id === selectedViewId.value) return
  syncActiveView()
  selectView(id)
  loadActiveView()
}

async function removeView(id) {
  const view = stagedViews.value.find((item) => item.id === id)
  if (!view) return
  if (view.status === 'saved' && !window.confirm(t('measurement.confirmDeleteView'))) return
  const wasSelected = id === selectedViewId.value
  if (view.status === 'saved') await deleteSavedView(id)
  else removeStagedView(id)
  if (wasSelected) loadActiveView()
}

async function startMeasurementSession() {
  sessionNameError.value = ''
  if (!runName.value.trim()) {
    sessionNameError.value = t('measurement.sessionNameRequired')
    return
  }
  sessionStarting.value = true
  try {
    await startSession(runName.value.trim())
    showToast(t('measurement.sessionStarted'))
  } catch (error) {
    sessionNameError.value = error.message
  } finally {
    sessionStarting.value = false
  }
}

async function saveCurrentView() {
  if (!canSaveView.value) return
  syncActiveView()
  const view = selectedView.value
  try {
    await saveSelectedView({
      name: runName.value.trim(),
      source_key: view.sourceKey,
      source_filename: view.sourceFilename,
      source_type: view.sourceType,
      source_camera_id: view.sourceCameraId,
      task_type: view.taskType,
      task_types: view.taskTypes || [view.taskType],
      view_type: view.viewType,
      view_label: view.viewLabel,
      pose_type: view.poseType,
      scale_profile_id: view.scaleProfileId,
      calibration: view.processed?.calibration || calibrationInput(),
      processing: {
        task_readiness: view.processed?.task_readiness || {},
        calibration_quality: view.processed?.calibration_quality || {},
      },
      items: view.items || items.value,
    })
    showToast(t('measurement.viewSaved'))
  } catch (error) {
    errorMessage.value = error.message
  }
}

async function completeMeasurementSession() {
  if (!canCompleteSession.value) return
  try {
    await completeSession()
    showToast(t('measurement.sessionCompleted'))
  } catch (error) {
    errorMessage.value = error.message
  }
}

function startCalibration(axis = 'x') {
  if (calibrationMode.value && calibrationAxis.value === axis) {
    calibrationMode.value = false
    calibrationDragging.value = false
    calibrationCursor.value = null
    return
  }
  calibrationAxis.value = axis
  calibrationMode.value = true
  errorMessage.value = ''
}

async function autoDetectJig() {
  if (!previewUrl.value || readOnly.value || jigDetecting.value) return
  jigDetecting.value = true
  errorMessage.value = ''
  try {
    const result = await detectMeasurementJig({
      file: source.value === 'image' || source.value === 'mobile' ? selectedFile.value : undefined,
      sourceKey: source.value === 'live' ? capturedSource.value?.source_key : undefined,
    })
    calibrationAxes.value = {
      x: [result.x.point_a, result.x.point_b],
      y: [result.y.point_a, result.y.point_b],
    }
    calibrationMode.value = false
    calibrationCursor.value = null
    showToast(t('measurement.jigDetected'))
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    jigDetecting.value = false
  }
}

function onTaskTypeChange() {
  selectedTaskTypes.value = [taskType.value]
}

function toggleTaskType(type, checked) {
  const next = selectedTaskTypes.value.filter((value) => value !== type)
  if (checked) next.push(type)
  if (!next.length) next.push('linear_dimension')
  selectedTaskTypes.value = [...new Set(next)]
  if (!selectedTaskTypes.value.includes(taskType.value)) taskType.value = selectedTaskTypes.value[0]
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
  const point = previewPoint(event)
  calibrationAxes.value = { ...calibrationAxes.value, [calibrationAxis.value]: [point] }
  calibrationCursor.value = point
  calibrationDragging.value = true
}

function onCalibrationPointerMove(event) {
  if (!calibrationDragging.value) return
  calibrationCursor.value = previewPoint(event)
  const points = activeCalibrationPoints.value
  calibrationAxes.value = { ...calibrationAxes.value, [calibrationAxis.value]: [points[0], calibrationCursor.value] }
}

function onCalibrationPointerUp(event) {
  if (!calibrationDragging.value) return
  calibrationDragging.value = false
  const points = activeCalibrationPoints.value
  calibrationAxes.value = { ...calibrationAxes.value, [calibrationAxis.value]: [points[0], previewPoint(event)] }
  calibrationMode.value = false
  calibrationCursor.value = null
}

function resetMeasurementWorkspace() {
  const hasWorkspace = stagedViews.value.length || processed.value || items.value.length || runName.value
  if (hasWorkspace && !window.confirm(t('measurement.confirmResetWorkspace'))) return
  stopMobileCamera()
  clearSession()
  clearPreview()
  selectedFile.value = null
  capturedSource.value = null
  localFileName.value = ''
  runName.value = ''
  sessionNameError.value = ''
  knownMm.value = 50
  knownMmY.value = 50
  source.value = 'image'
  resetStagedMeasurement()
  resetZoom()
  showToast(t('measurement.workspaceReset'))
}

function chooseSource(value) {
  source.value = value
  errorMessage.value = ''
  if (value === 'image') selectedCameraId.value = ''
  if (value !== 'mobile') stopMobileCamera()
}

function stageFile(fileInput) {
  const files = fileInput instanceof File ? [fileInput] : Array.from(fileInput || [])
  if (!files.length) return
  const staged = stageImage(files)
  if (!runName.value.trim()) runName.value = files[0].name?.replace(/\.[^.]+$/, '') || ''
  loadActiveView(staged.at(-1))
  errorMessage.value = ''
}

function onFileChange(event) {
  stageFile(event.target.files)
}

function downloadStagedOriginal(view) {
  if (!view?.previewUrl) return
  const anchor = document.createElement('a')
  anchor.href = view.previewUrl
  anchor.download = view.sourceFilename || 'measurement-capture.jpg'
  document.body.append(anchor)
  anchor.click()
  anchor.remove()
}

function stageCapturedFrame(capture) {
  const staged = stageServerCapture(capture)
  if (!runName.value.trim()) runName.value = capture.source_filename?.replace(/\.[^.]+$/, '') || ''
  loadActiveView(staged)
  errorMessage.value = ''
}

function onPreviewLoad(event) {
  previewWidth.value = event.target.naturalWidth || event.target.width || 1
  previewHeight.value = event.target.naturalHeight || event.target.height || 1
}

async function runMeasurement(input) {
  if (!taskSelectionSupported.value) return
  processing.value = true
  errorMessage.value = ''
  readOnly.value = false
  try {
    processed.value = await processMeasurement({
      ...input,
      calibration: calibrationInput(),
      taskType: taskType.value,
      taskTypes: taskTypesForProcess.value,
      viewType: viewType.value,
      viewLabel: viewLabel.value,
      poseType: poseType.value,
      scaleProfileId: scaleProfileId.value || undefined,
    })
    items.value = []
    evaluated.value = false
    showDetectedEdges.value = true
    showEvaluatedMeasurements.value = true
    selectedCandidate.value = -1
    selectedHoleIndexes.value = []
    selectedAngleIndexes.value = []
    resetZoom()
    syncActiveView()
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
  if (!canProcess.value || !selectedView.value) return
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
    const staged = stageMobileCapture(new File([blob], 'mobile.jpg', { type: 'image/jpeg' }))
    loadActiveView(staged)
  }
}

function candidateKey(candidate, index) {
  const geometry = candidate.center ? candidate.center.join('-') : (candidate.points || []).flat().join('-')
  return `${candidate.id || candidate.source || 'candidate'}-${index}-${geometry}`
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
    const [first, second] = selectedAngleIndexes.value.map((value) => visibleCandidates.value[value])
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

function addMeasurementItem({ id, type, label, measured, geometry, points, confidence, unit = 'mm', tolerance = 2, qualityReason = '' }) {
  items.value.push({
    id: `${id}${items.value.length + 1}`,
    type,
    task_type: type,
    view_type: viewType.value,
    label,
    points: points || [],
    geometry,
    measured,
    unit,
    pixel_value: null,
    nominal: null,
    tolerance,
    confidence,
    quality_reason: qualityReason,
    status: 'REVIEW',
    reason: 'missing_nominal_or_tolerance',
  })
  evaluated.value = false
}

function selectCorner(candidate) {
  if (readOnly.value || !processed.value) return
  const geometry = candidate.geometry || {
    kind: 'corner_arc',
    center: candidate.center,
    radius_mm: candidate.radius_mm,
    points: candidate.points || [],
  }
  const measured = measureGeometry('corner_radius', [], processed.value.calibration, geometry)
  addMeasurementItem({
    id: 'C',
    type: 'corner_radius',
    label: `Corner ${candidate.id || 'C'}`,
    measured: measured.value,
    geometry: measured.geometry,
    points: candidate.points,
    confidence: candidate.confidence,
    qualityReason: candidate.review_reason || '',
  })
}

function selectBend(candidate) {
  if (readOnly.value || !processed.value) return
  const measured = measureGeometry('bend_angle', [], processed.value.calibration, candidate.geometry)
  addMeasurementItem({
    id: 'B',
    type: 'bend_angle',
    label: `Bend ${candidate.id || 'B'}`,
    measured: measured.value,
    geometry: measured.geometry,
    points: [candidate.geometry.vertex, candidate.geometry.ray_a, candidate.geometry.vertex, candidate.geometry.ray_b],
    confidence: candidate.confidence,
    unit: 'deg',
    tolerance: 0.5,
    qualityReason: candidate.review_reason || '',
  })
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

function removeItem(index) {
  if (readOnly.value) return
  items.value.splice(index, 1)
  evaluated.value = false
}

function evaluate() {
  if (!canEvaluate.value) return
  const calibrationValid = processed.value.calibration_quality?.verdict_eligible ?? processed.value.calibration?.valid
  const calibrationReason = processed.value.calibration?.source === 'component_demo'
    ? 'reference_not_independent'
    : 'invalid_calibration'
  items.value = items.value.map((item) => evaluateMeasurementItem(item, calibrationValid, calibrationReason))
  evaluated.value = true
  showDetectedEdges.value = false
  showEvaluatedMeasurements.value = true
  log('MEASUREMENT_EVALUATED', `${runName.value || processed.value.source_filename}:${summaryStatus.value}`)
}

function measurementAnchor(item) {
  if (item.geometry?.kind === 'circle') return item.geometry.center
  if (item.geometry?.kind === 'circle_pair') {
    return [
      (item.geometry.center_a[0] + item.geometry.center_b[0]) / 2,
      (item.geometry.center_a[1] + item.geometry.center_b[1]) / 2,
    ]
  }
  if (item.geometry?.kind === 'circle_to_edge') return item.geometry.center
  if (item.geometry?.kind === 'corner_arc') return item.geometry.center
  if (item.geometry?.kind === 'bend_angle') return item.geometry.vertex
  return [
    (item.points[0][0] + item.points[1][0]) / 2,
    (item.points[0][1] + item.points[1][1]) / 2,
  ]
}

function measurementLabel(item) {
  const value = Number(item.measured).toFixed(1)
  const unit = item.geometry?.kind === 'corner_arc' ? `R ${value} ${item.unit}` : item.geometry?.kind === 'bend_angle' ? `${value}°` : `${value} ${item.unit}`
  return `${item.id} · ${unit} · ${item.status || 'REVIEW'}`
}

function reasonLabel(reason) {
  const known = new Set(['reference_not_independent', 'arc_coverage_low', 'arc_residual_high', 'no_usable_corner', 'no_usable_bend'])
  return known.has(reason) ? t(`measurement.reason_${reason}`) : reason
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
      task_type: taskType.value,
      task_types: [taskType.value],
      processing: {
        task_readiness: processed.value.task_readiness || {},
        calibration_quality: processed.value.calibration_quality || {},
      },
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

async function loadSessionHistory() {
  try {
    await loadSessions()
  } catch {
    sessions.value = []
  }
}

async function openSession(item) {
  try {
    await measurementSession.loadSession(item.id)
    runName.value = session.value?.name || item.name || ''
    loadActiveView(selectedView.value)
    errorMessage.value = ''
  } catch (error) {
    errorMessage.value = error.message
  }
}

function openRun(run) {
  runName.value = run.name
  taskType.value = run.processing?.task_type || run.items?.[0]?.task_type || run.items?.[0]?.type || 'linear_dimension'
  selectedTaskTypes.value = run.processing?.task_types?.length
    ? [...run.processing.task_types]
    : [taskType.value]
  viewType.value = run.processing?.view_type || run.items?.[0]?.view_type || 'top'
  viewLabel.value = run.view_label || ''
  poseType.value = run.pose_type || 'TOP_FACE'
  scaleProfileId.value = run.scale_profile_id || ''
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
    logical_edges: [],
    corner_arcs: [],
    bend_candidates: [],
    task_types: selectedTaskTypes.value,
    task_readiness: {},
    calibration_quality: {},
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

async function removeSession(item) {
  if (!window.confirm(t('measurement.confirmDeleteSession'))) return
  try {
    await deleteSession(item.id)
    showToast(t('measurement.sessionDeleted'))
  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(async () => {
  clearSession()
  await loadHistory()
  await loadSessionHistory()
  try {
    await loadProfiles()
  } catch {
    // Manual calibration remains available when profile API is offline.
  }
})
onBeforeUnmount(() => {
  stopMobileCamera()
  clearPreview()
  clearSession()
})
</script>

<template>
  <main class="measurement-page measurement-shell">
    <div class="measurement-studio">
      <aside class="measurement-rail">
        <div class="measurement-rail-body scroll-region">
        <section class="rail-section session-section">
          <div class="panel-section-title">{{ t('measurement.session') }}</div>
          <label class="field-label" for="session-name">{{ t('measurement.sessionName') }}</label>
          <input id="session-name" v-model="runName" type="text" :placeholder="t('measurement.runNamePlaceholder')">
          <button id="start-session" type="button" class="btn btn-secondary session-start" :disabled="sessionStarting || Boolean(session)" @click="startMeasurementSession">
            {{ session ? t('measurement.sessionStarted') : t('measurement.startSession') }}
          </button>
          <button type="button" class="btn btn-secondary reset-measurement-workspace" @click="resetMeasurementWorkspace">{{ t('measurement.resetWorkspace') }}</button>
          <p v-if="sessionNameError" class="session-name-error error-message">{{ sessionNameError }}</p>
        </section>
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
            <label class="field-label" for="view-type">
              {{ t('measurement.viewType') }}
              <select id="view-type" v-model="viewType">
                <option value="top">{{ t('measurement.viewTop') }}</option>
                <option value="profile">{{ t('measurement.viewProfile') }}</option>
                <option value="side">{{ t('measurement.viewSide') }}</option>
              </select>
            </label>
          </div>
          <div class="task-checklist" aria-label="Measurement checks">
            <span class="field-label">{{ t('measurement.checksInProcess') }}</span>
            <label class="task-check"><input id="task-linear" type="checkbox" :checked="taskTypesForProcess.includes('linear_dimension')" @change="toggleTaskType('linear_dimension', $event.target.checked)"> <span>{{ t('measurement.taskLinear') }}</span></label>
            <label class="task-check"><input id="task-corner" type="checkbox" :checked="taskTypesForProcess.includes('corner_radius')" @change="toggleTaskType('corner_radius', $event.target.checked)"> <span>{{ t('measurement.taskCorner') }}</span></label>
            <label class="task-check"><input id="task-bend" type="checkbox" :checked="taskTypesForProcess.includes('bend_angle')" @change="toggleTaskType('bend_angle', $event.target.checked)"> <span>{{ t('measurement.taskBend') }}</span></label>
          </div>
          <details class="measurement-advanced">
            <summary>{{ t('measurement.advancedTasks') }}</summary>
            <label class="field-label" for="task-type">
              {{ t('measurement.taskType') }}
              <select id="task-type" v-model="taskType" @change="onTaskTypeChange">
                <option value="linear_dimension">{{ t('measurement.taskLinear') }}</option>
                <option value="corner_radius">{{ t('measurement.taskCorner') }}</option>
                <option value="thickness_profile">{{ t('measurement.taskThickness') }}</option>
                <option value="bend_angle">{{ t('measurement.taskBend') }}</option>
                <option value="inclination">{{ t('measurement.taskInclination') }}</option>
                <option value="hole_diameter">{{ t('measurement.taskHoleDiameter') }}</option>
                <option value="hole_center_distance">{{ t('measurement.taskHolePitch') }}</option>
                <option value="hole_edge_distance">{{ t('measurement.taskHoleEdge') }}</option>
                <option value="hole_center_to_edge">{{ t('measurement.taskHoleToEdge') }}</option>
              </select>
            </label>
          </details>
          <div class="task-grid pose-grid">
            <label class="field-label" for="pose-type">
              {{ t('measurement.poseType') }}
              <select id="pose-type" v-model="poseType">
                <option value="TOP_FACE">{{ t('measurement.poseTop') }}</option>
                <option value="REVERSE_FACE">{{ t('measurement.poseReverse') }}</option>
                <option value="PROFILE_FACE">{{ t('measurement.poseProfile') }}</option>
                <option value="CUSTOM_FACE">{{ t('measurement.poseCustom') }}</option>
              </select>
            </label>
            <label class="field-label" for="scale-profile">
              {{ t('measurement.scaleProfile') }}
              <select id="scale-profile" v-model="scaleProfileId">
                <option value="">{{ t('measurement.manualCalibration') }}</option>
                <option v-for="profile in profiles" :key="profile.id" :value="profile.id">{{ profile.name }} · {{ profile.scale_type }}</option>
              </select>
            </label>
          </div>
          <label class="field-label" for="view-label">
            {{ t('measurement.viewLabel') }}
            <input id="view-label" v-model="viewLabel" type="text" :placeholder="t('measurement.viewLabelPlaceholder')">
          </label>
          <p v-if="selectedProfile" class="profile-capability">
            {{ selectedProfile.status }} · {{ selectedProfile.revision || t('measurement.unversionedProfile') }}
          </p>
          <p v-if="!poseSupported" class="task-warning pose-warning">{{ t('measurement.poseProfileRequired') }}</p>
          <p v-if="!taskViewSupported" class="task-warning">{{ t('measurement.profileViewRequired') }}</p>
          <p v-if="!taskSelectionSupported && taskViewSupported" class="task-warning">{{ t('measurement.profileViewRequired') }}</p>

          <template v-if="source === 'image'">
            <label class="field-label" for="measurement-file">{{ t('measurement.selectImage') }}</label>
            <input id="measurement-file" type="file" accept="image/*" multiple @change="onFileChange">
            <div v-if="localFileName" class="file-chip">{{ localFileName }}</div>
          </template>

          <template v-else-if="source === 'mobile'">
            <div class="mobile-camera-panel">
              <p class="section-help">{{ t('inspection.mobileHint') }}</p>
              <div class="mobile-preview" :style="{ aspectRatio: mobileVideoAspect }">
                <video ref="mobileVideo" playsinline muted class="mobile-video"></video>
                <span class="mobile-camera-guide" aria-hidden="true"></span>
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

          <div v-if="stagedViews.length" class="measurement-view-list">
            <div class="panel-section-title">{{ t('measurement.stagedViews') }}</div>
            <div
              v-for="view in stagedViews"
              :key="view.id"
              class="measurement-view-card"
              :class="{ active: view.id === selectedViewId }"
              role="button"
              tabindex="0"
              @click="selectStagedView(view.id)"
              @keydown.enter="selectStagedView(view.id)"
            >
              <span class="view-card-name">{{ view.sourceFilename }}</span>
              <span class="view-card-meta">{{ view.sourceType }} · {{ view.status }}</span>
              <span class="view-card-pose">{{ view.poseType }}</span>
              <button type="button" class="view-card-download" :aria-label="t('measurement.downloadOriginal')" :title="t('measurement.downloadOriginal')" @click.stop="downloadStagedOriginal(view)">↓</button>
              <button type="button" class="view-card-remove" :aria-label="t('measurement.deleteView')" @click.stop="removeView(view.id)">×</button>
            </div>
          </div>
        </section>

        <section class="rail-section">
          <div class="panel-section-title">{{ t('measurement.calibration') }}</div>
          <p class="section-help">{{ t('measurement.calibrationHelp') }}</p>
          <label class="field-label" for="calibration-source">{{ t('measurement.calibrationSource') }}
            <select id="calibration-source" v-model="calibrationSource" class="camera-select">
              <option value="component_demo">{{ t('measurement.calibrationSourceComponent') }}</option>
              <option value="independent_artifact">{{ t('measurement.calibrationSourceArtifact') }}</option>
            </select>
          </label>
          <div class="calibration-axis-actions">
            <button type="button" class="btn btn-secondary calibration-draw-button" :class="{ active: calibrationAxis === 'x' && calibrationMode }" :disabled="!previewUrl || readOnly || Boolean(processed)" @click="startCalibration('x')">
              {{ calibrationMode && calibrationAxis === 'x' ? t('measurement.calibrationDrawing') : t('measurement.drawHorizontal') }}
            </button>
            <button type="button" class="btn btn-secondary calibration-draw-button-y" :class="{ active: calibrationAxis === 'y' && calibrationMode }" :disabled="!previewUrl || readOnly || Boolean(processed)" @click="startCalibration('y')">
              {{ calibrationMode && calibrationAxis === 'y' ? t('measurement.calibrationDrawing') : t('measurement.drawVertical') }}
            </button>
            <button type="button" class="btn btn-secondary auto-detect-jig" :disabled="!previewUrl || readOnly || jigDetecting || Boolean(processed)" @click="autoDetectJig">{{ jigDetecting ? t('measurement.detectingJig') : t('measurement.detectJig') }}</button>
          </div>
          <p class="section-help">{{ t('measurement.autoJigHelp') }}</p>
          <div class="calibration-axis-fields">
            <label class="field-label" for="known-mm">{{ t('measurement.horizontalLength') }}<div class="input-unit">
              <input id="known-mm" v-model.number="knownMm" type="number" min="0.01" step="0.01">
              <span>mm</span>
            </div></label>
            <label class="field-label" for="known-mm-y">{{ t('measurement.verticalLength') }}<div class="input-unit">
              <input id="known-mm-y" v-model.number="knownMmY" type="number" min="0.01" step="0.01">
              <span>mm</span>
            </div></label>
          </div>
          <p class="calibration-state" :class="{ valid: calibrationReady }">
            {{ calibrationStateLabel }}
          </p>
          <div class="calibration-readout">
            <span>{{ t('measurement.scale') }}</span>
            <strong>
              X {{ processed?.calibration?.scale_x_mm_per_px?.toFixed?.(4) || processed?.calibration?.mm_per_pixel?.toFixed?.(4) || '—' }} ·
              Y {{ processed?.calibration?.scale_y_mm_per_px?.toFixed?.(4) || processed?.calibration?.mm_per_pixel?.toFixed?.(4) || '—' }} mm/px
            </strong>
          </div>
          <button v-if="processed" type="button" class="btn btn-secondary calibration-reference-toggle" @click="showCalibrationReference = !showCalibrationReference">
            {{ showCalibrationReference ? t('measurement.hideReference') : t('measurement.showReference') }}
          </button>
        </section>
        </div>

        <section class="rail-section history-section scroll-region">
          <div class="panel-section-title">{{ t('measurement.history') }}</div>
          <input v-if="recentRuns.length || sessions.length" v-model="historyQuery" class="history-search" type="search" :placeholder="t('measurement.historySearch')">
          <div v-if="!filteredRuns.length && !filteredSessions.length" class="empty-small">{{ recentRuns.length || sessions.length ? t('measurement.noHistoryResults') : t('measurement.noHistory') }}</div>
          <div v-for="item in filteredSessions" :key="item.id" class="history-row history-session">
            <button type="button" class="history-run" @click="openSession(item)">
              <strong>{{ item.name }}</strong>
              <span>{{ item.summary?.status || item.status }} · {{ item.summary?.view_count || 0 }} {{ t('measurement.stagedViews') }} · {{ item.created_at }}</span>
            </button>
            <button type="button" class="history-delete" :aria-label="t('measurement.deleteSession')" @click.stop="removeSession(item)">×</button>
          </div>
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
              <strong>{{ selectedSourceName }}</strong>
            </div>
            <div class="measurement-canvas-actions">
              <div v-if="processed" class="measurement-overlay-toggles" role="group" :aria-label="t('measurement.overlayControls')">
                <button type="button" class="overlay-toggle-detected" :class="{ active: showDetectedEdges }" :aria-pressed="showDetectedEdges" @click.stop="showDetectedEdges = !showDetectedEdges">{{ t('measurement.showDetectedEdges') }}</button>
                <button type="button" class="overlay-toggle-evaluated" :class="{ active: showEvaluatedMeasurements }" :aria-pressed="showEvaluatedMeasurements" @click.stop="showEvaluatedMeasurements = !showEvaluatedMeasurements">{{ t('measurement.showEvaluatedMeasurements') }}</button>
                <button type="button" class="overlay-toggle-calibration" :class="{ active: showCalibrationReference }" :aria-pressed="showCalibrationReference" @click.stop="showCalibrationReference = !showCalibrationReference">{{ t('measurement.showCalibrationReference') }}</button>
              </div>
              <span class="canvas-status mono" :class="`status-${summaryStatus.toLowerCase()}`">{{ summaryStatus }}</span>
              <button type="button" class="btn btn-primary process-measurement" :disabled="!canProcess" @click="processCurrent">
                {{ processing ? t('measurement.processing') : t('measurement.process') }}
              </button>
            </div>
          </div>
          <div v-if="!processed && previewUrl" class="measurement-preview">
            <div class="measurement-image-frame preview-frame" :style="{ transform: frameTransform }">
              <img class="measurement-image" :src="previewUrl" :alt="localFileName" @load="onPreviewLoad" draggable="false">
              <svg
                class="measurement-overlay calibration-overlay"
                :viewBox="`0 0 ${previewWidth} ${previewHeight}`"
                preserveAspectRatio="xMidYMid meet"
                :class="{ active: calibrationMode }"
                @mousedown.stop="onCalibrationPointerDown"
                @mousemove.stop="onCalibrationPointerMove"
                @mouseup.stop="onCalibrationPointerUp"
              >
                <g v-if="calibrationMode && calibrationCursor" class="calibration-guide">
                  <line :x1="calibrationCursor[0]" y1="0" :x2="calibrationCursor[0]" :y2="previewHeight"></line>
                  <line x1="0" :y1="calibrationCursor[1]" :x2="previewWidth" :y2="calibrationCursor[1]"></line>
                </g>
                <g v-for="axis in ['x', 'y']" :key="`calibration-axis-${axis}`">
                  <line
                    v-if="calibrationAxes[axis].length === 2"
                    class="calibration-drawn-line"
                    :class="`calibration-axis-${axis}`"
                    :x1="calibrationAxes[axis][0][0]"
                    :y1="calibrationAxes[axis][0][1]"
                    :x2="calibrationAxes[axis][1][0]"
                    :y2="calibrationAxes[axis][1][1]"
                  ></line>
                  <circle v-for="(point, index) in calibrationAxes[axis]" :key="`calibration-point-${axis}-${index}`" class="calibration-drawn-point" :cx="point[0]" :cy="point[1]" r="6"></circle>
                </g>
              </svg>
            </div>
            <div class="measurement-zoom-controls" :aria-label="t('measurement.zoomControls')">
              <button type="button" class="measurement-zoom-button measurement-zoom-out" :aria-label="t('measurement.zoomOut')" @click.stop="zoomOut">−</button>
              <span class="measurement-zoom-value mono">{{ Math.round(zoom * 100) }}%</span>
              <button type="button" class="measurement-zoom-button measurement-zoom-in" :aria-label="t('measurement.zoomIn')" @click.stop="zoomIn">+</button>
              <button type="button" class="measurement-zoom-reset" @click.stop="resetZoom">{{ t('measurement.zoomResetShort') }}</button>
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
                v-if="showDetectedEdges"
                v-for="(candidate, index) in visibleCandidates"
                :key="candidateKey(candidate, index)"
                class="measurement-candidate"
                :class="{ selected: selectedCandidate === index || selectedAngleIndexes.includes(index), 'measurement-logical-edge': logicalEdges.length > 0 }"
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
                v-for="(corner, index) in cornerCandidates"
                v-if="showDetectedEdges && cornerTaskSelected"
                :key="`corner-${candidateKey(corner, index)}`"
                class="measurement-corner-candidate"
                @click.stop="selectCorner(corner)"
              >
                <polyline class="measurement-corner-halo" :points="corner.points.map((point) => point.join(',')).join(' ')"></polyline>
                <polyline class="measurement-corner-line" :points="corner.points.map((point) => point.join(',')).join(' ')"></polyline>
                <circle class="measurement-corner-center" :cx="corner.center[0]" :cy="corner.center[1]" r="4"></circle>
              </g>
              <g
                v-for="(bend, index) in bendCandidates"
                v-if="showDetectedEdges && bendTaskSelected"
                :key="`bend-${candidateKey(bend, index)}`"
                class="measurement-bend-candidate"
                @click.stop="selectBend(bend)"
              >
                <line class="measurement-bend-halo" :x1="bend.geometry.vertex[0]" :y1="bend.geometry.vertex[1]" :x2="bend.geometry.ray_a[0]" :y2="bend.geometry.ray_a[1]"></line>
                <line class="measurement-bend-line" :x1="bend.geometry.vertex[0]" :y1="bend.geometry.vertex[1]" :x2="bend.geometry.ray_a[0]" :y2="bend.geometry.ray_a[1]"></line>
                <line class="measurement-bend-halo" :x1="bend.geometry.vertex[0]" :y1="bend.geometry.vertex[1]" :x2="bend.geometry.ray_b[0]" :y2="bend.geometry.ray_b[1]"></line>
                <line class="measurement-bend-line" :x1="bend.geometry.vertex[0]" :y1="bend.geometry.vertex[1]" :x2="bend.geometry.ray_b[0]" :y2="bend.geometry.ray_b[1]"></line>
                <circle class="measurement-bend-vertex" :cx="bend.geometry.vertex[0]" :cy="bend.geometry.vertex[1]" r="5"></circle>
              </g>
              <g
                v-if="showDetectedEdges"
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
              <g v-if="showCalibrationReference" class="calibration-reference">
                <line
                  v-for="reference in calibrationReferences"
                  :key="`reference-${reference.axis}`"
                  :x1="reference.point_a[0]"
                  :y1="reference.point_a[1]"
                  :x2="reference.point_b[0]"
                  :y2="reference.point_b[1]"
                ></line>
                <text
                  v-for="reference in calibrationReferences"
                  :key="`reference-label-${reference.axis}`"
                  :x="reference.point_a[0]"
                  :y="reference.point_a[1] + 13"
                >REF {{ reference.axis }} {{ reference.known_mm }} mm</text>
              </g>
              <g v-if="showEvaluatedMeasurements" v-for="item in items" :key="`item-${item.id}`" class="selected-measurement" :class="`status-${(item.status || 'review').toLowerCase()}`">
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
                <template v-else-if="item.geometry?.kind === 'corner_arc'">
                  <polyline class="measurement-corner-halo" :points="item.geometry.points.map((point) => point.join(',')).join(' ')"></polyline>
                  <polyline class="measurement-corner-line" :points="item.geometry.points.map((point) => point.join(',')).join(' ')"></polyline>
                  <circle class="measurement-corner-center" :cx="item.geometry.center[0]" :cy="item.geometry.center[1]" r="4"></circle>
                </template>
                <template v-else-if="item.geometry?.kind === 'bend_angle'">
                  <line class="measurement-bend-halo" :x1="item.geometry.vertex[0]" :y1="item.geometry.vertex[1]" :x2="item.geometry.ray_a[0]" :y2="item.geometry.ray_a[1]"></line>
                  <line class="measurement-bend-line" :x1="item.geometry.vertex[0]" :y1="item.geometry.vertex[1]" :x2="item.geometry.ray_a[0]" :y2="item.geometry.ray_a[1]"></line>
                  <line class="measurement-bend-halo" :x1="item.geometry.vertex[0]" :y1="item.geometry.vertex[1]" :x2="item.geometry.ray_b[0]" :y2="item.geometry.ray_b[1]"></line>
                  <line class="measurement-bend-line" :x1="item.geometry.vertex[0]" :y1="item.geometry.vertex[1]" :x2="item.geometry.ray_b[0]" :y2="item.geometry.ray_b[1]"></line>
                  <circle class="measurement-bend-vertex" :cx="item.geometry.vertex[0]" :cy="item.geometry.vertex[1]" r="5"></circle>
                </template>
                <template v-else>
                  <line class="measurement-line-halo" :x1="item.points[0][0]" :y1="item.points[0][1]" :x2="item.points[1][0]" :y2="item.points[1][1]"></line>
                  <line class="measurement-line" :x1="item.points[0][0]" :y1="item.points[0][1]" :x2="item.points[1][0]" :y2="item.points[1][1]"></line>
                </template>
              </g>
              <g v-if="showEvaluatedMeasurements && evaluated" v-for="overlay in evaluatedOverlayItems" :key="`label-${overlay.item.id}`" class="measurement-label" :class="`status-${(overlay.item.status || 'review').toLowerCase()}`">
                <line class="measurement-label-leader" :x1="overlay.anchor[0]" :y1="overlay.anchor[1]" :x2="overlay.x" :y2="overlay.y - 5"></line>
                <text :x="overlay.x" :y="overlay.y" :text-anchor="overlay.textAnchor">{{ measurementLabel(overlay.item) }}</text>
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

        <p v-if="processed" class="selection-guidance">{{ selectionGuidance }}</p>
        <div v-if="processed" class="candidate-strip">
          <div class="strip-header">
            <span>{{ t('measurement.candidates') }}</span>
            <span>{{ taskIsHole ? (processed.holes || []).length : visibleCandidates.length }} {{ t('measurement.detected') }}</span>
          </div>
          <template v-if="!taskIsHole">
            <button v-for="(candidate, index) in visibleCandidates" :key="candidateKey(candidate, index)" type="button" class="candidate-card" :class="{ selected: selectedCandidate === index || selectedAngleIndexes.includes(index) }" @click="selectCandidate(candidate, index)">
              <span class="candidate-line"></span>
              <strong>{{ candidate.id || `L${index + 1}` }}</strong>
              <span>{{ candidate.length_px.toFixed(1) }} px</span>
              <small>{{ candidate.source || 'logical-edge' }} · {{ candidate.confidence.toFixed(2) }}</small>
            </button>
            <button v-if="cornerTaskSelected" v-for="(corner, index) in cornerCandidates" :key="`corner-card-${candidateKey(corner, index)}`" type="button" class="candidate-card corner-card measurement-corner-candidate" @click="selectCorner(corner)">
              <span class="candidate-corner"></span>
              <strong>{{ corner.id || `C${index + 1}` }}</strong>
              <span>R {{ Number(corner.radius_mm).toFixed(2) }} mm</span>
              <small>{{ corner.coverage_deg?.toFixed?.(1) || '—' }}° · {{ corner.confidence.toFixed(2) }}</small>
            </button>
            <button v-if="bendTaskSelected" v-for="(bend, index) in bendCandidates" :key="`bend-card-${candidateKey(bend, index)}`" type="button" class="candidate-card bend-card measurement-bend-candidate" @click="selectBend(bend)">
              <span class="candidate-bend"></span>
              <strong>{{ bend.id || `B${index + 1}` }}</strong>
              <span>{{ Number(bend.angle_deg).toFixed(2) }}°</span>
              <small>{{ bend.confidence.toFixed(2) }}</small>
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
            <button v-for="(candidate, index) in visibleCandidates" :key="`edge-${candidateKey(candidate, index)}`" type="button" class="candidate-card" :class="{ selected: selectedCandidate === index || selectedAngleIndexes.includes(index) }" @click="selectCandidate(candidate, index)">
              <span class="candidate-line"></span>
              <strong>E{{ index + 1 }}</strong>
              <span>{{ candidate.length_px.toFixed(1) }} px</span>
              <small>{{ candidate.source }} · {{ candidate.confidence.toFixed(2) }}</small>
            </button>
          </template>
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
            <div v-if="item.reason" class="item-reason">{{ reasonLabel(item.reason) }}</div>
          </article>
        </section>

        <section class="result-actions">
          <div class="measurement-summary" :class="`summary-${summaryStatus.toLowerCase()}`">
            <span>{{ t('measurement.summary') }}</span>
            <strong>{{ summaryStatus }}</strong>
          </div>
          <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
          <button type="button" class="btn btn-secondary evaluate-measurement" :disabled="!canEvaluate" @click="evaluate">{{ t('measurement.evaluateDimension') }}</button>
          <button type="button" class="btn btn-secondary save-view" :disabled="!canSaveView" @click="saveCurrentView">{{ t('measurement.saveView') }}</button>
          <button type="button" class="btn btn-secondary complete-session" :disabled="!canCompleteSession" @click="completeMeasurementSession">{{ t('measurement.completeSession') }}</button>
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

.session-section { background: var(--color-surface-1); }
.session-start { width: 100%; margin-top: 10px; }
.measurement-view-list { display: grid; gap: 6px; margin-top: 16px; }
.measurement-view-list .panel-section-title { margin-bottom: 4px; }
.measurement-view-card { position: relative; display: grid; gap: 3px; width: 100%; padding: 10px 52px 10px 10px; border: 1px solid var(--color-hairline); background: var(--color-surface-1); color: var(--color-ink); text-align: left; cursor: pointer; font: inherit; }
.measurement-view-card.active { border-color: var(--color-primary); background: color-mix(in srgb, var(--color-primary) 8%, var(--color-canvas)); }
.view-card-name { overflow: hidden; font-size: 12px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.view-card-meta, .view-card-pose, .profile-capability { color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 10px; }
.view-card-remove { position: absolute; top: 7px; right: 9px; border: 0; padding: 0; background: transparent; color: var(--color-ink-muted); cursor: pointer; font: inherit; font-size: 17px; line-height: 1; }
.view-card-download { position: absolute; top: 7px; right: 29px; border: 0; padding: 0; background: transparent; color: var(--color-ink-muted); cursor: pointer; font: var(--font-mono); font-size: 16px; line-height: 1; }

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
.task-checklist { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: 12px; }
.task-checklist .field-label { grid-column: 1 / -1; margin: 0; }
.task-check { display: flex; align-items: center; gap: 5px; min-width: 0; padding: 7px; border: 1px solid var(--color-hairline); color: var(--color-ink-muted); font-size: 10px; line-height: 1.2; }
.task-check input { width: auto; min-height: 0; accent-color: var(--color-primary); }
.measurement-advanced { margin-top: 12px; border-top: 1px solid var(--color-hairline); color: var(--color-ink-muted); font-size: 11px; }
.measurement-advanced summary { padding: 10px 0 4px; cursor: pointer; font-weight: 600; }
.task-warning { margin: 12px 0 0; padding: 9px; border-left: 3px solid var(--color-warning); background: var(--color-surface-1); color: var(--color-warning); font-size: 11px; line-height: 1.4; }
.profile-capability { margin: 10px 0 0; }

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
.calibration-axis-actions,
.calibration-axis-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.calibration-axis-actions { margin-bottom: 8px; }
.calibration-axis-actions .btn.active { border-color: var(--color-primary); color: var(--color-primary); }
.calibration-axis-fields .field-label { margin-top: 0; }

.camera-preview { display: grid; place-items: center; min-height: 120px; margin: 12px 0; overflow: hidden; background: var(--color-inverse-canvas); color: var(--color-inverse-ink-muted); font-size: 11px; }
.camera-preview img { display: block; width: 100%; height: 120px; object-fit: cover; }

.mobile-camera-panel { display: grid; gap: 10px; }
.mobile-preview { position: relative; display: grid; min-height: 150px; place-items: center; overflow: hidden; background: var(--color-inverse-canvas); color: var(--color-inverse-ink-muted); font-size: 11px; }
.mobile-video { display: block; width: 100%; height: 100%; min-height: 150px; object-fit: cover; }
.mobile-camera-guide { position: absolute; top: 50%; left: 50%; width: 26px; height: 26px; transform: translate(-50%, -50%); border: 1px solid var(--color-warning); border-radius: 50%; pointer-events: none; }
.mobile-camera-guide::before, .mobile-camera-guide::after { position: absolute; top: 50%; left: 50%; width: 38px; height: 1px; transform: translate(-50%, -50%); background: var(--color-warning); content: ''; }
.mobile-camera-guide::after { width: 1px; height: 38px; }
.mobile-camera-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.camera-resolution { color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 10px; }

.btn { min-height: 36px; border: 1px solid transparent; border-radius: 0; padding: 8px 12px; cursor: pointer; font: inherit; font-size: 12px; font-weight: 600; }
.btn:disabled { cursor: not-allowed; opacity: 0.45; }
.btn-primary { background: var(--color-primary); color: var(--color-on-primary); }
.btn-secondary { border-color: var(--color-hairline-strong); background: var(--color-canvas); color: var(--color-ink); }
.trigger-capture { width: 100%; }
.calibration-draw-button,
.calibration-draw-button-y,
.calibration-reference-toggle { width: 100%; margin-bottom: 4px; }
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
.calibration-guide line { stroke: var(--color-warning); stroke-width: 1; stroke-dasharray: 5 5; opacity: 0.3; vector-effect: non-scaling-stroke; }
.preview-guidance { color: var(--color-ink-muted); font-size: 12px; text-align: center; }
.measurement-canvas-tools { position: absolute; top: 12px; left: 12px; z-index: 2; display: flex; align-items: center; justify-content: space-between; gap: 18px; max-width: calc(100% - 24px); padding: 9px 10px; border: 1px solid var(--color-hairline); background: var(--color-canvas); }
.measurement-canvas-tools strong { display: block; max-width: 280px; overflow: hidden; color: var(--color-ink); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.measurement-canvas-actions { display: flex; align-items: center; gap: 10px; }
.measurement-overlay-toggles { display: flex; border: 1px solid var(--color-hairline); }
.measurement-overlay-toggles button { min-height: 28px; padding: 0 8px; border: 0; border-right: 1px solid var(--color-hairline); background: var(--color-canvas); color: var(--color-ink-muted); font: 600 11px/1 var(--font-sans); cursor: pointer; }
.measurement-overlay-toggles button:last-child { border-right: 0; }
.measurement-overlay-toggles button.active { background: var(--color-primary); color: var(--color-on-primary); }
.measurement-overlay-toggles button:focus-visible { outline: 2px solid var(--color-primary); outline-offset: -2px; }
.canvas-status { color: var(--color-ink-muted); font-size: 11px; font-weight: 600; }
.canvas-status.status-pass { color: var(--color-success); }
.canvas-status.status-fail { color: var(--color-error); }
.canvas-status.status-review { color: var(--color-warning); }
.measurement-image-frame { position: relative; transform-origin: center; transition: transform 0.05s linear; }
.measurement-image { display: block; max-width: 100%; max-height: 100%; object-fit: contain; pointer-events: none; }
.measurement-overlay { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: auto; }
.measurement-candidate { pointer-events: all; cursor: pointer; opacity: 0.9; }
.measurement-line-halo { stroke: var(--color-canvas); stroke-width: 4; vector-effect: non-scaling-stroke; }
.measurement-line { stroke: var(--color-info); stroke-width: 2.5; vector-effect: non-scaling-stroke; }
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
.measurement-logical-edge { opacity: 1; }
.measurement-logical-edge .measurement-line { stroke: var(--color-primary); stroke-width: 2.5; }
.measurement-corner-candidate,
.measurement-bend-candidate { cursor: pointer; }
.measurement-corner-halo { fill: none; stroke: var(--color-canvas); stroke-width: 6; vector-effect: non-scaling-stroke; }
.measurement-corner-line { fill: none; stroke: var(--color-warning); stroke-width: 2.5; vector-effect: non-scaling-stroke; }
.measurement-corner-center { fill: var(--color-warning); stroke: var(--color-canvas); stroke-width: 2; vector-effect: non-scaling-stroke; }
.measurement-bend-halo { stroke: var(--color-canvas); stroke-width: 6; vector-effect: non-scaling-stroke; }
.measurement-bend-line { stroke: var(--color-error); stroke-width: 2.5; vector-effect: non-scaling-stroke; stroke-dasharray: 6 4; }
.measurement-bend-vertex { fill: var(--color-error); stroke: var(--color-canvas); stroke-width: 2; vector-effect: non-scaling-stroke; }
.selected-measurement { pointer-events: none; }
.selected-measurement .measurement-line { stroke: var(--color-success); stroke-width: 4; stroke-dasharray: 7 4; }
.selected-measurement.status-fail .measurement-line { stroke: var(--color-error); }
.selected-measurement.status-review .measurement-line { stroke: var(--color-warning); }
.measurement-label { pointer-events: none; color: var(--color-success); }
.measurement-label.status-fail { color: var(--color-error); }
.measurement-label.status-review { color: var(--color-warning); }
.measurement-label-leader { stroke: currentColor; stroke-width: 1.5; vector-effect: non-scaling-stroke; }
.measurement-label text { fill: currentColor; font-family: var(--font-mono); font-size: 15px; font-weight: 600; paint-order: stroke; stroke: var(--color-surface-1); stroke-width: 5px; }
.calibration-reference { pointer-events: none; }
.calibration-reference line { stroke: var(--color-warning); stroke-width: 2.5; stroke-dasharray: 5 4; vector-effect: non-scaling-stroke; }
.calibration-reference text { fill: var(--color-warning); font-family: var(--font-mono); font-size: 13px; font-weight: 600; paint-order: stroke; stroke: var(--color-surface-1); stroke-width: 5px; }
.viewport-empty { display: grid; place-items: center; gap: 8px; color: var(--color-ink-muted); text-align: center; }
.viewport-empty span { max-width: 250px; font-size: 12px; }
.empty-crosshair { color: var(--color-primary); font-family: var(--font-mono); font-size: 42px; font-weight: 300; }

.candidate-strip { display: flex; gap: 10px; min-height: 100px; padding: 14px 18px; overflow-x: auto; border-top: 1px solid var(--color-hairline); background: var(--color-canvas); }
.selection-guidance { flex: 0 0 auto; margin: 8px 18px 0; color: var(--color-ink-muted); font-size: 11px; }
.strip-header { display: flex; min-width: 100px; flex-direction: column; justify-content: center; gap: 4px; color: var(--color-ink-muted); font-size: 11px; }
.strip-header span:last-child { font-family: var(--font-mono); }
.candidate-card { display: grid; min-width: 120px; grid-template-columns: 16px 1fr; align-content: center; gap: 2px 6px; padding: 8px; border: 1px solid var(--color-hairline); background: var(--color-surface-1); color: var(--color-ink); text-align: left; cursor: pointer; font-size: 11px; }
.candidate-card.selected { border-color: var(--color-warning); background: color-mix(in srgb, var(--color-warning) 12%, var(--color-canvas)); }
.candidate-card span, .candidate-card small { grid-column: 2; color: var(--color-ink-muted); font-family: var(--font-mono); font-size: 10px; }
.candidate-line { grid-column: 1; grid-row: 1 / span 3; align-self: center; width: 14px; height: 2px; background: var(--color-info); }
.candidate-hole { grid-column: 1; grid-row: 1 / span 3; align-self: center; width: 14px; height: 14px; border: 2px solid var(--color-warning); }
.candidate-corner { grid-column: 1; grid-row: 1 / span 3; align-self: center; width: 14px; height: 14px; border: 2px solid var(--color-warning); border-radius: 50% 0 0 0; }
.candidate-bend { grid-column: 1; grid-row: 1 / span 3; align-self: center; width: 14px; height: 14px; border-left: 2px solid var(--color-error); border-bottom: 2px solid var(--color-error); transform: skew(-20deg); }
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
