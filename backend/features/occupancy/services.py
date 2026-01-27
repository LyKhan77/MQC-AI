from database import db
from .models import Camera, OccupancyLog
from core.logger import setup_logger
from core.utils import generate_uuid
from core.exceptions import CameraNotFoundException

logger = setup_logger(__name__)

class CameraService:
    """Service layer for camera operations"""
    
    def __init__(self, camera_manager):
        self.camera_manager = camera_manager
    
    def get_all_cameras(self):
        """Get all cameras from database"""
        cameras = Camera.query.all()
        return [cam.to_dict() for cam in cameras]
    
    def get_camera_by_id(self, camera_id):
        """Get camera by ID"""
        camera = Camera.query.get(camera_id)
        if not camera:
            raise CameraNotFoundException(f"Camera ID {camera_id} not found")
        return camera.to_dict()
    
    def get_camera_by_uuid(self, camera_uuid):
        """Get camera by UUID"""
        camera = Camera.query.filter_by(camera_uuid=camera_uuid).first()
        if not camera:
            raise CameraNotFoundException(f"Camera UUID {camera_uuid} not found")
        return camera.to_dict()
    
    def create_camera(self, data):
        """Create new camera and start thread"""
        # Generate UUID if not provided
        if 'camera_uuid' not in data or not data['camera_uuid']:
            data['camera_uuid'] = generate_uuid('CAM')
        
        # Create database record
        camera = Camera(
            camera_uuid=data['camera_uuid'],
            name=data['name'],
            rtsp_url=data['rtsp_url'],
            area_name=data.get('area_name', ''),
            max_capacity=data.get('max_capacity', 10),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(camera)
        db.session.commit()
        
        logger.info(f"Camera created: {camera.camera_uuid}")
        
        # Start camera thread if active
        if camera.is_active:
            self.camera_manager.start_camera(
                camera.camera_uuid,
                camera.rtsp_url,
                camera.max_capacity
            )
        
        return camera.to_dict()
    
    def update_camera(self, camera_id, data):
        """Update camera configuration"""
        camera = Camera.query.get(camera_id)
        if not camera:
            raise CameraNotFoundException(f"Camera ID {camera_id} not found")
        
        # Check if RTSP URL changed (need to restart thread)
        rtsp_changed = 'rtsp_url' in data and data['rtsp_url'] != camera.rtsp_url
        
        # Update fields
        for key, value in data.items():
            if hasattr(camera, key):
                setattr(camera, key, value)
        
        db.session.commit()
        
        logger.info(f"Camera updated: {camera.camera_uuid}")
        
        # Restart thread if needed
        if rtsp_changed and camera.is_active:
            self.camera_manager.restart_camera(
                camera.camera_uuid,
                camera.rtsp_url,
                camera.max_capacity
            )
        
        return camera.to_dict()
    
    def delete_camera(self, camera_id):
        """Delete camera and stop thread"""
        camera = Camera.query.get(camera_id)
        if not camera:
            raise CameraNotFoundException(f"Camera ID {camera_id} not found")
        
        camera_uuid = camera.camera_uuid
        
        # Stop thread first
        self.camera_manager.stop_camera(camera_uuid)
        
        # Delete from database
        db.session.delete(camera)
        db.session.commit()
        
        logger.info(f"Camera deleted: {camera_uuid}")
        return True
    
    def get_occupancy_stats(self):
        """Get real-time occupancy stats for all cameras"""
        cameras = Camera.query.filter_by(is_active=True).all()
        states = self.camera_manager.get_all_states()
        
        stats = []
        for camera in cameras:
            state = states.get(camera.camera_uuid, {})
            stats.append({
                'camera_uuid': camera.camera_uuid,
                'name': camera.name,
                'area_name': camera.area_name,
                'current_count': state.get('count', 0),
                'max_capacity': camera.max_capacity,
                'status': state.get('status', 'NORMAL'),
                'is_connected': state.get('is_connected', False),
                'timestamp': state.get('timestamp', None)
            })
        
        return stats
