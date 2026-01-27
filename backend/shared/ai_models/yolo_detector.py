from ultralytics import YOLO
import torch
import numpy as np
from core.logger import setup_logger
from core.exceptions import ModelLoadException

logger = setup_logger(__name__)

class YOLODetector:
    """Singleton YOLO detector wrapper"""
    
    _instance = None
    _model = None
    
    def __new__(cls, model_path='yolo11n.pt', device='cuda'):
        if cls._instance is None:
            cls._instance = super(YOLODetector, cls).__new__(cls)
            cls._instance._initialize(model_path, device)
        return cls._instance
    
    def _initialize(self, model_path, device):
        """Load YOLO model once"""
        try:
            logger.info(f"Loading YOLO model: {model_path} on device: {device}")
            
            # Check device availability
            if device == 'cuda' and not torch.cuda.is_available():
                logger.warning("CUDA not available, falling back to CPU")
                device = 'cpu'
            
            self._model = YOLO(model_path)
            self._device = device
            self.model_path = model_path
            
            logger.info(f"YOLO model loaded successfully on {device}")
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {str(e)}")
            raise ModelLoadException(f"YOLO model load failed: {str(e)}")
    
    def detect_persons(self, frame, confidence=0.5, iou=0.45):
        """
        Detect persons in frame
        Returns: (person_count, annotated_frame)
        """
        try:
            # Run inference
            results = self._model(
                frame, 
                device=self._device, 
                conf=confidence,
                iou=iou,
                verbose=False
            )
            
            # Filter for person class (class_id = 0 in COCO)
            person_count = 0
            if len(results) > 0 and results[0].boxes is not None:
                for box in results[0].boxes:
                    if int(box.cls) == 0:  # Person class
                        person_count += 1
            
            # Get annotated frame
            annotated_frame = results[0].plot() if len(results) > 0 else frame
            
            return person_count, annotated_frame
            
        except Exception as e:
            logger.error(f"YOLO detection failed: {str(e)}")
            return 0, frame
    
    @property
    def device(self):
        return self._device
