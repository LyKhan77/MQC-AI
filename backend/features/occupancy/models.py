from database import db
from datetime import datetime

class Camera(db.Model):
    """Camera configuration model"""
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_uuid = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    rtsp_url = db.Column(db.String(255), nullable=False)
    area_name = db.Column(db.String(100))
    max_capacity = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    occupancy_logs = db.relationship('OccupancyLog', backref='camera', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Serialize to JSON"""
        return {
            'id': self.id,
            'camera_uuid': self.camera_uuid,
            'name': self.name,
            'rtsp_url': self.rtsp_url,
            'area_name': self.area_name,
            'max_capacity': self.max_capacity,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Camera {self.camera_uuid}: {self.name}>"


class OccupancyLog(db.Model):
    """Occupancy log model (for historical data)"""
    __tablename__ = 'occupancy_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    camera_uuid = db.Column(db.String(50), db.ForeignKey('cameras.camera_uuid'), nullable=False)
    person_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('NORMAL', 'WARNING', 'VIOLATION'), default='NORMAL')
    snapshot_path = db.Column(db.String(255), nullable=True)
    
    def to_dict(self):
        """Serialize to JSON"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'camera_uuid': self.camera_uuid,
            'person_count': self.person_count,
            'status': self.status,
            'snapshot_path': self.snapshot_path
        }
    
    def __repr__(self):
        return f"<OccupancyLog {self.camera_uuid} @ {self.timestamp}: {self.person_count} persons>"
