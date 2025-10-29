"""
Editor de imagem com interface integrada - Ponte entre UI e ImageProcessor
"""
from PyQt6.QtCore import QObject, pyqtSignal, QPoint
from .image_processor import ImageProcessor
from .transformations import ImageTransformations
from typing import Tuple, Optional

class ImageEditor(QObject):
    image_updated = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    dimensions_changed = pyqtSignal(tuple)
    history_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.processor = ImageProcessor()
        self._crop_start: Optional[QPoint] = None
        self._crop_end: Optional[QPoint] = None
    
    def load_image(self, filepath: str) -> bool:
        success = self.processor.load_image(filepath)
        if success:
            self.image_updated.emit(self.processor.current_image)
            self.dimensions_changed.emit(self.processor.get_dimensions())
            self._update_history_signal()
        else:
            self.error_occurred.emit("Falha ao carregar a imagem.")
        return success
    
    def save_image(self, filepath: str = None, format: str = "PNG") -> bool:
        return self.processor.save_image(filepath, format)
    
    def save_copy(self, suffix: str = "_editado") -> bool:
        return self.processor.save_copy(suffix)
    
    def resize(self, width: int, height: int, keep_aspect_ratio: bool = True) -> bool:
        success = self.processor.resize(width, height, keep_aspect_ratio)
        if success:
            self.image_updated.emit(self.processor.current_image)
            self.dimensions_changed.emit(self.processor.get_dimensions())
            self._update_history_signal()
        else:
            self.error_occurred.emit("Falha ao redimensionar a imagem.")
        return success
    
    def rotate(self, degrees: float) -> bool:
        success = self.processor.rotate(degrees)
        if success:
            self.image_updated.emit(self.processor.current_image)
            self.dimensions_changed.emit(self.processor.get_dimensions())
            self._update_history_signal()
        else:
            self.error_occurred.emit("Falha ao rotacionar a imagem.")
        return success
    
    def rotate_90(self, clockwise: bool = True) -> bool:
        return self.rotate(90 if clockwise else -90)
    
    def flip(self, horizontal: bool = True) -> bool:
        success = self.processor.flip(horizontal)
        if success:
            self.image_updated.emit(self.processor.current_image)
            self._update_history_signal()
        else:
            self.error_occurred.emit("Falha ao espelhar a imagem.")
        return success
    
    def crop(self, x: int, y: int, width: int, height: int) -> bool:
        success = self.processor.crop(x, y, width, height)
        if success:
            self.image_updated.emit(self.processor.current_image)
            self.dimensions_changed.emit(self.processor.get_dimensions())
            self._update_history_signal()
        else:
            self.error_occurred.emit("Falha ao recortar a imagem.")
        return success
    
    def start_crop_selection(self, start_point: QPoint):
        self._crop_start = start_point
        self._crop_end = None
    
    def update_crop_selection(self, end_point: QPoint):
        self._crop_end = end_point
    
    def apply_crop_selection(self, crop_rect) -> bool:
        try:
            if not crop_rect or not self.processor.current_image:
                return False
                
            x1 = int(crop_rect.x())
            y1 = int(crop_rect.y())
            x2 = int(crop_rect.x() + crop_rect.width())
            y2 = int(crop_rect.y() + crop_rect.height())
            
            width, height = self.processor.current_image.size
            
            x1 = max(0, min(x1, width - 1))
            y1 = max(0, min(y1, height - 1))
            x2 = max(x1 + 1, min(x2, width))
            y2 = max(y1 + 1, min(y2, height))
            
            crop_width = x2 - x1
            crop_height = y2 - y1
            
            if crop_width >= 10 and crop_height >= 10:
                success = self.crop(x1, y1, crop_width, crop_height)
                return success
            else:
                return False
                
        except Exception as e:
            print(f"Erro ao aplicar recorte: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def reset_to_original(self) -> bool:
        success = self.processor.reset_to_original()
        if success:
            self.image_updated.emit(self.processor.current_image)
            self.dimensions_changed.emit(self.processor.get_dimensions())
            self._update_history_signal()
        else:
            self.error_occurred.emit("Falha ao restaurar imagem original.")
        return success
    
    def undo(self) -> bool:
        success = self.processor.undo()
        if success:
            self.image_updated.emit(self.processor.current_image)
            self.dimensions_changed.emit(self.processor.get_dimensions())
            self._update_history_signal()
        else:
            self.error_occurred.emit("Não há ações para desfazer.")
        return success
    
    def redo(self) -> bool:
        success = self.processor.redo()
        if success:
            self.image_updated.emit(self.processor.current_image)
            self.dimensions_changed.emit(self.processor.get_dimensions())
            self._update_history_signal()
        else:
            self.error_occurred.emit("Não há ações para refazer.")
        return success
    
    def get_current_image(self):
        return self.processor.current_image
    
    def get_original_image(self):
        return self.processor.original_image
    
    def get_dimensions(self) -> Tuple[int, int]:
        return self.processor.get_dimensions()
    
    def get_original_dimensions(self) -> Tuple[int, int]:
        return self.processor.get_original_dimensions()
    
    def get_file_info(self) -> dict:
        return self.processor.get_file_info()

    def has_changes(self) -> bool:
        return self.processor.has_changes()
          
    def is_image_loaded(self) -> bool:
        return self.processor.is_image_loaded()
    
    def get_crop_selection(self) -> Tuple[Optional[QPoint], Optional[QPoint]]:
        return (self._crop_start, self._crop_end)
    
    def _update_history_signal(self):
        history_info = self.processor.get_history_info()
        self.history_changed.emit(history_info)