"""
Seed database with sample camera configurations
Usage: python seed_data.py
"""

from app import create_app
from database import db
from features.occupancy.models import Camera

def seed_cameras():
    """Create sample cameras including Hikvision RTSP"""
    app = create_app()
    
    with app.app_context():
        # Clear existing cameras
        Camera.query.delete()
        
        cameras_data = [
            {
                'camera_uuid': 'CAM-HIKVISION-01',
                'name': 'Hikvision Production Floor',
                'rtsp_url': 'rtsp://admin:gspe-intercon@192.168.0.64:554/Streaming/Channels/1',
                'area_name': 'Production Floor',
                'max_capacity': 10,
                'is_active': True  # Enable by default
            },
            {
                'camera_uuid': 'CAM-TEST-VIDEO',
                'name': 'Test Video Fallback',
                'rtsp_url': 'invalid_rtsp_will_trigger_fallback',
                'area_name': 'Testing Zone',
                'max_capacity': 15,
                'is_active': True  # Will use crowd_test.mp4
            },
            {
                'camera_uuid': 'CAM-ASSEMBLY',
                'name': 'Assembly Line Camera',
                'rtsp_url': 'rtsp://admin:password@192.168.2.101:554/stream1',
                'area_name': 'Assembly Area',
                'max_capacity': 12,
                'is_active': False  # Placeholder, enable when ready
            },
        ]
        
        for cam_data in cameras_data:
            camera = Camera(**cam_data)
            db.session.add(camera)
            print(f"✅ Added: {camera.name} ({camera.camera_uuid})")
        
        db.session.commit()
        print(f"\n🎉 Successfully seeded {len(cameras_data)} cameras!")
        print("\n📌 Active cameras will start automatically on app launch")
        print("   • CAM-HIKVISION-01: Real RTSP camera")
        print("   • CAM-TEST-VIDEO: Falls back to crowd_test.mp4\n")

if __name__ == '__main__':
    seed_cameras()
