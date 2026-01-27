import logging
import sys
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for production"""
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logger(name, level='INFO', log_format='json'):
    """Setup structured logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    
    if log_format == 'json':
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    logger.addHandler(handler)
    return logger
