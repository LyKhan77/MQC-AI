from flask import Flask
from flask_socketio import SocketIO, emit
from flask_migrate import Migrate
import atexit
import os

from database import db
from config import OccupancyConfig
from core.logger import setup_logger
from shared.streaming.frame_buffer import FrameBuffer
from features.occupancy.camera_manager import CameraManager
from features.occupancy.services import CameraService
from features.occupancy.routes import occupancy_bp, init_occupancy_routes
from features.occupancy.models import Camera

# Initialize extensions
socketio = SocketIO()
migrate = Migrate()

# Global instances
frame_buffer = None
camera_manager = None
camera_service = None
logger = None

def create_app(config_class=OccupancyConfig):
    """Flask application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    global logger
    logger = setup_logger(__name__, 
                         level=app.config.get('LOG_LEVEL', 'INFO'),
                         log_format=app.config.get('LOG_FORMAT', 'json'))
    
    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize SocketIO
    socketio.init_app(app, 
                      cors_allowed_origins=app.config.get('SOCKETIO_CORS_ALLOWED_ORIGINS'),
                      async_mode='eventlet')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
    
    # Initialize global instances
    global frame_buffer, camera_manager, camera_service
    frame_buffer = FrameBuffer()
    camera_manager = CameraManager(config_class, frame_buffer)
    camera_service = CameraService(camera_manager)
    
    # Initialize routes
    init_occupancy_routes(camera_service)
    
    # Register blueprints
    app.register_blueprint(occupancy_bp)
    
    # Basic routes
    @app.route('/')
    def index():
        return {
            'service': 'MQC Backend Service',
            'status': 'running',
            'version': '1.0.0',
            'features': ['occupancy']
        }
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    # Auto-start active cameras from database
    with app.app_context():
        logger.info("Loading active cameras from database...")
        cameras = Camera.query.filter_by(is_active=True).all()
        
        for camera in cameras:
            camera_manager.start_camera(
                camera.camera_uuid,
                camera.rtsp_url,
                camera.max_capacity
            )
            logger.info(f"Auto-started camera: {camera.camera_uuid}")
    
    # Register cleanup handler
    atexit.register(lambda: cleanup(camera_manager))
    
    logger.info("Flask application created successfully")
    return app

def cleanup(manager):
    """Cleanup on application shutdown"""
    logger.info("Shutting down application...")
    manager.stop_all()

# ========== WebSocket Events ==========

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected'})
    # Start background task
    socketio.start_background_task(broadcast_stats)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_stats')
def handle_stats_request():
    """Handle manual stats request"""
    try:
        stats = camera_service.get_occupancy_stats()
        emit('stats_update', {'data': stats})
    except Exception as e:
        logger.error(f"Error sending stats: {str(e)}")
        emit('error', {'message': str(e)})

def broadcast_stats():
    """Background task to broadcast stats periodically"""
    while True:
        try:
            stats = camera_service.get_occupancy_stats()
            socketio.emit('stats_update', {'data': stats}, broadcast=True)
            socketio.sleep(2)  # Broadcast every 2 seconds
        except Exception as e:
            logger.error(f"Error broadcasting stats: {str(e)}")
            socketio.sleep(5)

# ========== Main Entry Point ==========

if __name__ == '__main__':
    app = create_app()
    
    # Get host from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    logger.info(f"Starting Flask-SocketIO server on {host}:{port}")
    
    socketio.run(
        app, 
        host=host,
        port=port,
        debug=False,
        use_reloader=False
    )
