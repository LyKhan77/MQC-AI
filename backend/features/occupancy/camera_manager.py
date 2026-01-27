from core.logger import setup_logger
from .camera_thread import OccupancyCameraThread

logger = setup_logger(__name__)

class CameraManager:
    """Singleton manager for all camera threads"""
    
    _instance = None
    
    def __new__(cls, config, frame_buffer):
        if cls._instance is None:
            cls._instance = super(CameraManager, cls).__new__(cls)
            cls._instance._initialize(config, frame_buffer)
        return cls._instance
    
    def _initialize(self, config, frame_buffer):
        """Initialize manager"""
        self.config = config
        self.frame_buffer = frame_buffer
        self.active_threads = {}
        logger.info("CameraManager initialized")
    
    def start_camera(self, camera_uuid, rtsp_url, max_capacity):
        """Start a new camera thread"""
        if camera_uuid in self.active_threads:
            logger.warning(f"Camera already running: {camera_uuid}")
            return False
        
        try:
            thread = OccupancyCameraThread(
                camera_uuid=camera_uuid,
                source_url=rtsp_url,
                max_capacity=max_capacity,
                config=self.config,
                frame_buffer=self.frame_buffer
            )
            
            thread.start()
            self.active_threads[camera_uuid] = thread
            
            logger.info(f"Camera started: {camera_uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera {camera_uuid}: {str(e)}")
            return False
    
    def stop_camera(self, camera_uuid):
        """Stop a camera thread"""
        if camera_uuid not in self.active_threads:
            logger.warning(f"Camera not running: {camera_uuid}")
            return False
        
        try:
            thread = self.active_threads[camera_uuid]
            thread.stop()
            thread.join(timeout=5)
            
            del self.active_threads[camera_uuid]
            self.frame_buffer.remove_camera(camera_uuid)
            
            logger.info(f"Camera stopped: {camera_uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop camera {camera_uuid}: {str(e)}")
            return False
    
    def restart_camera(self, camera_uuid, rtsp_url, max_capacity):
        """Restart a camera thread"""
        logger.info(f"Restarting camera: {camera_uuid}")
        self.stop_camera(camera_uuid)
        return self.start_camera(camera_uuid, rtsp_url, max_capacity)
    
    def get_camera_state(self, camera_uuid):
        """Get state for a specific camera"""
        return self.frame_buffer.get_frame(camera_uuid)
    
    def get_all_states(self):
        """Get states for all cameras"""
        return self.frame_buffer.get_all_frames()
    
    def stop_all(self):
        """Stop all camera threads"""
        logger.info("Stopping all cameras")
        for camera_uuid in list(self.active_threads.keys()):
            self.stop_camera(camera_uuid)
