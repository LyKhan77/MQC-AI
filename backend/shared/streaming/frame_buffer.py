import threading
from collections import defaultdict
from datetime import datetime

class FrameBuffer:
    """Thread-safe frame buffer for multiple cameras"""
    
    def __init__(self):
        self._buffer = defaultdict(dict)
        self._lock = threading.RLock()
    
    def put_frame(self, camera_uuid, frame_data):
        """
        Store frame data for a camera
        frame_data = {
            'frame': bytes,
            'count': int,
            'status': str,
            'timestamp': str,
            'is_connected': bool
        }
        """
        with self._lock:
            self._buffer[camera_uuid] = frame_data
    
    def get_frame(self, camera_uuid):
        """Get latest frame for a camera"""
        with self._lock:
            return self._buffer.get(camera_uuid, None)
    
    def get_all_frames(self):
        """Get all camera frames"""
        with self._lock:
            return dict(self._buffer)
    
    def remove_camera(self, camera_uuid):
        """Remove camera from buffer"""
        with self._lock:
            if camera_uuid in self._buffer:
                del self._buffer[camera_uuid]
