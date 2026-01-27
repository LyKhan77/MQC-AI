import threading
import cv2
import time
from abc import ABC, abstractmethod
from core.logger import setup_logger
from core.constants import CameraStatus, StreamSource

logger = setup_logger(__name__)

class CameraBase(threading.Thread, ABC):
    """Abstract base class for camera threads"""
    
    def __init__(self, camera_uuid, source_url, config):
        super().__init__(daemon=True)
        
        self.camera_uuid = camera_uuid
        self.source_url = source_url
        self.config = config
        
        self.cap = None
        self.stop_event = threading.Event()
        self.frame_count = 0
        self.status = CameraStatus.DISCONNECTED
        self.source_type = StreamSource.RTSP
        
        logger.info(f"Camera thread initialized: {camera_uuid}")
    
    def connect_stream(self):
        """Connect to RTSP stream with fallback"""
        try:
            # Try RTSP first
            logger.info(f"Connecting to RTSP: {self.source_url}")
            self.cap = cv2.VideoCapture(self.source_url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency
            
            if self.cap.isOpened():
                self.status = CameraStatus.CONNECTED
                self.source_type = StreamSource.RTSP
                logger.info(f"RTSP connected: {self.camera_uuid}")
                return True
            
            # Fallback to video file
            return self.fallback_to_video()
            
        except Exception as e:
            logger.error(f"Stream connection failed: {str(e)}")
            return self.fallback_to_video()
    
    def fallback_to_video(self):
        """Fallback to sample video file"""
        try:
            import os
            video_path = os.path.join(
                self.config.FALLBACK_VIDEO_PATH, 
                'crowd_test.mp4'
            )
            
            if os.path.exists(video_path):
                logger.info(f"Falling back to video file: {video_path}")
                self.cap = cv2.VideoCapture(video_path)
                
                if self.cap.isOpened():
                    self.status = CameraStatus.CONNECTED
                    self.source_type = StreamSource.VIDEO_FILE
                    return True
            
            # Final fallback: blank frame
            logger.warning(f"No video file found, using blank frame")
            self.source_type = StreamSource.BLANK
            self.status = CameraStatus.ERROR
            return False
            
        except Exception as e:
            logger.error(f"Fallback failed: {str(e)}")
            self.source_type = StreamSource.BLANK
            self.status = CameraStatus.ERROR
            return False
    
    def read_frame(self):
        """Read frame with error handling"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if ret:
                return frame
            else:
                # Handle loop for video files
                if self.source_type == StreamSource.VIDEO_FILE:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
                    return self.read_frame()
                else:
                    logger.warning(f"Failed to read frame: {self.camera_uuid}")
                    return self.generate_blank_frame("Connection Lost")
        
        return self.generate_blank_frame("No Stream")
    
    def generate_blank_frame(self, message="No Signal"):
        """Generate blank frame with error message"""
        import numpy as np
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(
            blank, message, (200, 240),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
        )
        return blank
    
    def should_process_frame(self):
        """Check if current frame should be processed (frame skip logic)"""
        self.frame_count += 1
        return self.frame_count % self.config.FRAME_SKIP == 0
    
    def stop(self):
        """Signal thread to stop"""
        logger.info(f"Stopping camera thread: {self.camera_uuid}")
        self.stop_event.set()
    
    @abstractmethod
    def run(self):
        """Main thread loop - must be implemented by subclass"""
        pass
    
    def __del__(self):
        """Cleanup resources"""
        if self.cap:
            self.cap.release()
