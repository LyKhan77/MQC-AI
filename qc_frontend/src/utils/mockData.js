const CAMERAS = [
  {
    id: 'cam-01',
    name: 'RaspyCam-01',
    type: 'rpi',
    source: 'csi://0',
    location: 'Line A - Welding',
    status: 'online',
    resolution: '1280x720',
    fps: 30,
  },
  {
    id: 'cam-02',
    name: 'RTSP-Cam-02',
    type: 'rtsp',
    source: 'rtsp://192.168.1.60:554/stream',
    location: 'Line B - Coating',
    status: 'online',
    resolution: '1920x1080',
    fps: 25,
  },
  {
    id: 'cam-03',
    name: 'USB-Cam-03',
    type: 'usb',
    source: '/dev/video0',
    location: 'Line C - Assembly',
    status: 'offline',
    resolution: '640x480',
    fps: 15,
  },
]

const BATCH_HISTORY = [
  {
    id: 'batch-001',
    name: 'shift1_2026-06-25_08-00-00',
    cameraId: 'cam-01',
    cameraName: 'RaspyCam-01',
    createdAt: '2026-06-25T08:00:00',
    imageCount: 24,
    defectCount: 6,
    status: 'reviewed',
    reviewer: 'inspector@gspemail.com',
    modelInfo: { detection: 'YOLOv8n', segmentation: 'SAM3', confidence: 0.5 },
  },
  {
    id: 'batch-002',
    name: 'shift2_2026-06-25_16-00-00',
    cameraId: 'cam-02',
    cameraName: 'RTSP-Cam-02',
    createdAt: '2026-06-25T16:00:00',
    imageCount: 18,
    defectCount: 3,
    status: 'pending',
    reviewer: null,
    modelInfo: { detection: 'YOLOv8n', segmentation: 'SAM3', confidence: 0.5 },
  },
  {
    id: 'batch-003',
    name: 'shift1_2026-06-24_08-00-00',
    cameraId: 'cam-01',
    cameraName: 'RaspyCam-01',
    createdAt: '2026-06-24T08:00:00',
    imageCount: 32,
    defectCount: 8,
    status: 'reviewed',
    reviewer: 'inspector@gspemail.com',
    modelInfo: { detection: 'YOLOv8n', segmentation: 'SAM3', confidence: 0.5 },
  },
  {
    id: 'batch-004',
    name: 'shift1_2026-06-23_08-00-00',
    cameraId: 'cam-01',
    cameraName: 'RaspyCam-01',
    createdAt: '2026-06-23T08:00:00',
    imageCount: 20,
    defectCount: 0,
    status: 'reviewed',
    reviewer: 'inspector@gspemail.com',
    modelInfo: { detection: 'YOLOv8n', segmentation: 'SAM3', confidence: 0.5 },
  },
  {
    id: 'batch-005',
    name: 'shift2_2026-06-22_16-00-00',
    cameraId: 'cam-02',
    cameraName: 'RTSP-Cam-02',
    createdAt: '2026-06-22T16:00:00',
    imageCount: 15,
    defectCount: 2,
    status: 'processing',
    reviewer: null,
    modelInfo: { detection: 'YOLOv8n', segmentation: 'SAM3', confidence: 0.5 },
  },
]

function timeAgo(offsetMin) {
  const d = new Date(Date.now() - offsetMin * 60000)
  return d.toISOString()
}

const AUDIT_LOGS = [
  { id: 'log-001', timestamp: timeAgo(5), user: 'inspector@gspemail.com', action: 'BATCH_LOADED', detail: 'Loaded batch shift1_2026-06-25 (24 images)' },
  { id: 'log-002', timestamp: timeAgo(12), user: 'inspector@gspemail.com', action: 'IMAGE_REVIEWED', detail: 'Marked weld_0001.jpg as reviewed' },
  { id: 'log-003', timestamp: timeAgo(15), user: 'inspector@gspemail.com', action: 'IMAGE_REVIEWED', detail: 'Marked coat_0002.jpg as reviewed' },
  { id: 'log-004', timestamp: timeAgo(20), user: 'inspector@gspemail.com', action: 'EXPORT_CROP', detail: 'Exported crop: weld_0001.jpg_crop.png' },
  { id: 'log-005', timestamp: timeAgo(25), user: 'inspector@gspemail.com', action: 'EXPORT_FULL', detail: 'Exported full: coat_0002.jpg_full.png' },
  { id: 'log-006', timestamp: timeAgo(35), user: 'inspector@gspemail.com', action: 'BATCH_SENT', detail: 'Sent batch shift1_2026-06-26 to QC' },
  { id: 'log-007', timestamp: timeAgo(40), user: 'inspector@gspemail.com', action: 'CAMERA_STARTED', detail: 'Started RaspyCam-01 (cam-01)' },
  { id: 'log-008', timestamp: timeAgo(45), user: 'inspector@gspemail.com', action: 'CAMERA_STOPPED', detail: 'Stopped RaspyCam-01 (cam-01)' },
  { id: 'log-009', timestamp: timeAgo(60), user: 'inspector@gspemail.com', action: 'REPORT_GENERATED', detail: 'Generated PDF report for batch-001' },
  { id: 'log-010', timestamp: timeAgo(120), user: 'inspector@gspemail.com', action: 'SETTINGS_CHANGED', detail: 'Changed language to English' },
  { id: 'log-011', timestamp: timeAgo(180), user: 'inspector@gspemail.com', action: 'CAMERA_ADDED', detail: 'Added camera: RTSP-Cam-02' },
  { id: 'log-012', timestamp: timeAgo(240), user: 'inspector@gspemail.com', action: 'BATCH_REVIEWED', detail: 'Completed review: shift1_2026-06-25' },
  { id: 'log-013', timestamp: timeAgo(300), user: 'inspector@gspemail.com', action: 'CAMERA_EDITED', detail: 'Edited camera: RaspyCam-01 location' },
  { id: 'log-014', timestamp: timeAgo(600), user: 'admin@gspemail.com', action: 'CAMERA_DELETED', detail: 'Deleted camera: Old-USB-Cam' },
  { id: 'log-015', timestamp: timeAgo(720), user: 'inspector@gspemail.com', action: 'BATCH_LOADED', detail: 'Loaded batch shift2_2026-06-25 (18 images)' },
]

export const MOCK = {
  cameras: CAMERAS,
  batchHistory: BATCH_HISTORY,
  auditLogs: AUDIT_LOGS,
  settings: {
    confidenceThreshold: 0.5,
    detectionModel: 'YOLOv8n',
    segmentationModel: 'SAM3',
  },
}
