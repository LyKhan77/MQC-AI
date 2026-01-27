import cv2
import time
from shared.streaming.camera_base import CameraBase
from shared.ai_models.yolo_detector import YOLODetector
from core.logger import setup_logger
from core.utils import calculate_status
from core.constants import OccupancyStatus

logger = setup_logger(__name__)

class OccupancyCameraThread(CameraBase):
    """Camera thread for occupancy monitoring"""
    
    def __init__(self, camera_uuid, source_url, max_capacity, config, frame_buffer):
        super().__init__(camera_uuid, source_url, config)
        
        self.max_capacity = max_capacity
        self.frame_buffer = frame_buffer
        
        # Initialize YOLO detector (singleton)
        self.yolo = YOLODetector(
            model_path=config.YOLO_MODEL,
            device=config.YOLO_DEVICE
        )
        
        logger.info(f"Occupancy thread initialized: {camera_uuid}, capacity: {max_capacity}")
    
    def run(self):
        """Main thread loop"""
        logger.info(f"Starting occupancy monitoring: {self.camera_uuid}")
        
        # Connect to stream
        if not self.connect_stream():
            logger.error(f"Failed to establish stream: {self.camera_uuid}")
        
        last_log_time = time.time()
        
        while not self.stop_event.is_set():
            try:
                # Read frame
                frame = self.read_frame()
                
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Process frame (with skip logic)
                if self.should_process_frame():
                    person_count, annotated_frame = self.process_frame(frame)
                    
                    # Calculate status
                    status = calculate_status(
                        person_count, 
                        self.max_capacity,
                        self.config.WARNING_THRESHOLD_PERCENT,
                        self.config.VIOLATION_THRESHOLD_PERCENT
                    )
                    
                    # Encode frame as JPEG
                    _, jpeg_bytes = cv2.imencode(
                        '.jpg', 
                        annotated_frame,
                        [cv2.IMWRITE_JPEG_QUALITY, self.config.MJPEG_QUALITY]
                    )
                    
                    # Update shared state
                    self.frame_buffer.put_frame(self.camera_uuid, {
                        'frame': jpeg_bytes.tobytes(),
                        'count': person_count,
                        'status': status.value,
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                        'is_connected': self.status.value == 'CONNECTED',
                        'source_type': self.source_type.value
                    })
                    
                    # Log to console
                    logger.debug(
                        f"{self.camera_uuid}: count={person_count}, "
                        f"status={status.value}, source={self.source_type.value}"
                    )
                    
                    # Save to database periodically (future enhancement)
                    current_time = time.time()
                    if current_time - last_log_time >= self.config.DB_LOG_INTERVAL:
                        # TODO: Save to database
                        last_log_time = current_time
                
                # Small sleep to prevent CPU overload
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in camera thread {self.camera_uuid}: {str(e)}")
                time.sleep(1)
        
        # Cleanup
        if self.cap:
            self.cap.release()
        
        logger.info(f"Stopped occupancy monitoring: {self.camera_uuid}")
    
    def process_frame(self, frame):
        """Process frame with YOLO detection"""
        # Resize frame for YOLO
        resized = cv2.resize(frame, (self.config.FRAME_WIDTH, self.config.FRAME_HEIGHT))
        
        # Run YOLO detection
        person_count, annotated_frame = self.yolo.detect_persons(
            resized,
            confidence=self.config.YOLO_CONFIDENCE,
            iou=self.config.YOLO_IOU_THRESHOLD
        )
        
        # Add occupancy info overlay
        annotated_frame = self.add_overlay(annotated_frame, person_count)
        
        return person_count, annotated_frame
    
    def add_overlay(self, frame, count):
        """Add occupancy info overlay to frame"""
        # Add count text
        text = f"Persons: {count}/{self.max_capacity}"
        cv2.putText(
            frame, text, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
        )
        
        # Add camera UUID
        cv2.putText(
            frame, self.camera_uuid, (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1
        )
        
        return frame
