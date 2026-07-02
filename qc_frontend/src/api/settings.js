import { apiGet, apiPut } from './client.js'

export function mapSettings(s) {
  return {
    confidenceThreshold: s.confidence_threshold,
    qcConfidenceThreshold: s.qc_confidence_threshold,
    detectionModel: s.detection_model,
    segmentationModel: s.segmentation_model,
    defectStrategy: s.defect_strategy,
    activeModel: s.active_model,
    qcModel: s.qc_model,
    inputModeEnabled: s.input_mode_enabled,
    quantityModel: s.quantity_model,
    quantityConfidenceThreshold: s.quantity_confidence_threshold,
    quantityNmsIou: s.quantity_nms_iou,
    quantityAgnosticNms: s.quantity_agnostic_nms,
  }
}

export async function getSettings() {
  return mapSettings(await apiGet('/settings'))
}

export async function updateSettings(patch) {
  const body = {}
  if (patch.confidenceThreshold !== undefined) body.confidence_threshold = Number(patch.confidenceThreshold)
  if (patch.qcConfidenceThreshold !== undefined) body.qc_confidence_threshold = Number(patch.qcConfidenceThreshold)
  if (patch.detectionModel !== undefined) body.detection_model = patch.detectionModel
  if (patch.segmentationModel !== undefined) body.segmentation_model = patch.segmentationModel
  if (patch.defectStrategy !== undefined) body.defect_strategy = patch.defectStrategy
  if (patch.activeModel !== undefined) body.active_model = patch.activeModel
  if (patch.qcModel !== undefined) body.qc_model = patch.qcModel
  if (patch.inputModeEnabled !== undefined) body.input_mode_enabled = patch.inputModeEnabled
  if (patch.quantityModel !== undefined) body.quantity_model = patch.quantityModel
  if (patch.quantityConfidenceThreshold !== undefined) body.quantity_confidence_threshold = Number(patch.quantityConfidenceThreshold)
  if (patch.quantityNmsIou !== undefined) body.quantity_nms_iou = Number(patch.quantityNmsIou)
  if (patch.quantityAgnosticNms !== undefined) body.quantity_agnostic_nms = patch.quantityAgnosticNms
  return mapSettings(await apiPut('/settings', body))
}
