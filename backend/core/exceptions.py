class MQCException(Exception):
    """Base exception for MQC application"""
    pass

class CameraNotFoundException(MQCException):
    """Raised when camera UUID not found"""
    pass

class StreamConnectionException(MQCException):
    """Raised when stream connection fails"""
    pass

class ModelLoadException(MQCException):
    """Raised when AI model fails to load"""
    pass

class InvalidConfigException(MQCException):
    """Raised when configuration is invalid"""
    pass
