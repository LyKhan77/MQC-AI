import { apiGet, apiPut } from './client.js'

export function mapSettings(s) {
  return {
    confidenceThreshold: s.confidence_threshold,
    detectionModel: s.detection_model,
    segmentationModel: s.segmentation_model,
    defectStrategy: s.defect_strategy,
  }
}

export async function getSettings() {
  return mapSettings(await apiGet('/settings'))
}

export async function updateSettings(patch) {
  const body = {}
  if (patch.confidenceThreshold !== undefined) body.confidence_threshold = Number(patch.confidenceThreshold)
  if (patch.detectionModel !== undefined) body.detection_model = patch.detectionModel
  if (patch.segmentationModel !== undefined) body.segmentation_model = patch.segmentationModel
  if (patch.defectStrategy !== undefined) body.defect_strategy = patch.defectStrategy
  return mapSettings(await apiPut('/settings', body))
}
