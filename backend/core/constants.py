from enum import Enum

class OccupancyStatus(str, Enum):
    """Occupancy status levels"""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    VIOLATION = "VIOLATION"

class CameraStatus(str, Enum):
    """Camera connection status"""
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    ERROR = "ERROR"

class StreamSource(str, Enum):
    """Video stream source type"""
    RTSP = "RTSP"
    VIDEO_FILE = "VIDEO_FILE"
    BLANK = "BLANK"
