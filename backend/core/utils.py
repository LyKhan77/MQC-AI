import uuid
from datetime import datetime

def generate_uuid(prefix='CAM'):
    """Generate unique camera UUID"""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def calculate_status(current_count, max_capacity, warning_threshold=80, violation_threshold=100):
    """Calculate occupancy status based on capacity"""
    from .constants import OccupancyStatus
    
    if max_capacity == 0:
        return OccupancyStatus.NORMAL
    
    percentage = (current_count / max_capacity) * 100
    
    if percentage >= violation_threshold:
        return OccupancyStatus.VIOLATION
    elif percentage >= warning_threshold:
        return OccupancyStatus.WARNING
    else:
        return OccupancyStatus.NORMAL

def format_timestamp(dt=None):
    """Format datetime to ISO string"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()
