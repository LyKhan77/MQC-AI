import os
from .base import BaseConfig

class OccupancyConfig(BaseConfig):
    """Configuration for Crowd Control / Occupancy Monitoring"""
    
    # YOLO Model
    YOLO_MODEL = os.getenv('YOLO_MODEL', 'yolo11n.pt')
    YOLO_DEVICE = os.getenv('YOLO_DEVICE', 'cuda')  # 'cuda' or 'cpu'
    YOLO_CONFIDENCE = float(os.getenv('YOLO_CONFIDENCE', '0.5'))
    YOLO_IOU_THRESHOLD = float(os.getenv('YOLO_IOU', '0.45'))
    
    # Frame Processing
    FRAME_SKIP = int(os.getenv('FRAME_SKIP', '3'))  # Process every 3rd frame (10 FPS)
    FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '640'))
    FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '640'))
    
    # Streaming
    MJPEG_FPS = int(os.getenv('MJPEG_FPS', '30'))
    MJPEG_QUALITY = int(os.getenv('MJPEG_QUALITY', '85'))
    
    # Occupancy Thresholds
    WARNING_THRESHOLD_PERCENT = int(os.getenv('WARNING_THRESHOLD', '80'))  # 80% capacity
    VIOLATION_THRESHOLD_PERCENT = int(os.getenv('VIOLATION_THRESHOLD', '100'))
    
    # Camera Connection
    RTSP_TIMEOUT = int(os.getenv('RTSP_TIMEOUT', '10'))  # seconds
    RTSP_RETRY_INTERVAL = int(os.getenv('RTSP_RETRY', '5'))  # seconds
    FALLBACK_VIDEO_PATH = os.path.join(BaseConfig.ROOT_DIR, 'static', 'sample_videos')
    
    # WebSocket
    STATS_BROADCAST_INTERVAL = int(os.getenv('STATS_INTERVAL', '2'))  # seconds
    
    # Database Logging
    DB_LOG_INTERVAL = int(os.getenv('DB_LOG_INTERVAL', '60'))  # Log to DB every 60s
    SNAPSHOT_ON_VIOLATION = os.getenv('SNAPSHOT_VIOLATION', 'True') == 'True'
    SNAPSHOT_PATH = os.path.join(BaseConfig.ROOT_DIR, 'static', 'snapshots')
