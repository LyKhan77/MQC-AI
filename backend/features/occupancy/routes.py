from flask import Blueprint, request, jsonify, Response
from .services import CameraService
from core.logger import setup_logger
from core.exceptions import CameraNotFoundException
import time

logger = setup_logger(__name__)

occupancy_bp = Blueprint('occupancy', __name__)

# Service instance (will be injected by app.py)
camera_service = None

def init_occupancy_routes(service):
    """Initialize routes with service dependency"""
    global camera_service
    camera_service = service

# ========== Camera CRUD Endpoints ==========

@occupancy_bp.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get all cameras"""
    try:
        cameras = camera_service.get_all_cameras()
        return jsonify({'success': True, 'data': cameras}), 200
    except Exception as e:
        logger.error(f"Error getting cameras: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@occupancy_bp.route('/api/cameras/<int:camera_id>', methods=['GET'])
def get_camera(camera_id):
    """Get camera by ID"""
    try:
        camera = camera_service.get_camera_by_id(camera_id)
        return jsonify({'success': True, 'data': camera}), 200
    except CameraNotFoundException as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting camera: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@occupancy_bp.route('/api/cameras', methods=['POST'])
def create_camera():
    """Create new camera"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'rtsp_url']
        if not all(field in data for field in required):
            return jsonify({
                'success': False, 
                'error': 'Missing required fields: name, rtsp_url'
            }), 400
        
        camera = camera_service.create_camera(data)
        return jsonify({'success': True, 'data': camera}), 201
        
    except Exception as e:
        logger.error(f"Error creating camera: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@occupancy_bp.route('/api/cameras/<int:camera_id>', methods=['PUT'])
def update_camera(camera_id):
    """Update camera configuration"""
    try:
        data = request.get_json()
        camera = camera_service.update_camera(camera_id, data)
        return jsonify({'success': True, 'data': camera}), 200
    except CameraNotFoundException as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error updating camera: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@occupancy_bp.route('/api/cameras/<int:camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    """Delete camera"""
    try:
        camera_service.delete_camera(camera_id)
        return jsonify({'success': True, 'message': 'Camera deleted'}), 200
    except CameraNotFoundException as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error deleting camera: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== Streaming Endpoints ==========

@occupancy_bp.route('/video_feed/<camera_uuid>', methods=['GET'])
def video_feed(camera_uuid):
    """MJPEG stream for specific camera"""
    
    def generate_frames():
        """Generator function for MJPEG stream"""
        while True:
            try:
                # Get latest frame from shared state
                state = camera_service.camera_manager.get_camera_state(camera_uuid)
                
                if state and state.get('frame'):
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + 
                           state['frame'] + b'\r\n')
                else:
                    # No frame available, wait
                    time.sleep(0.1)
                
                # Control frame rate
                time.sleep(1.0 / 30)  # 30 FPS
                
            except Exception as e:
                logger.error(f"Streaming error for {camera_uuid}: {str(e)}")
                time.sleep(1)
    
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@occupancy_bp.route('/api/occupancy/stats', methods=['GET'])
def get_occupancy_stats():
    """Get real-time occupancy statistics for all cameras"""
    try:
        stats = camera_service.get_occupancy_stats()
        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        logger.error(f"Error getting occupancy stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
