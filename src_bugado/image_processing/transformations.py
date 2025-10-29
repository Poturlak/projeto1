"""
Transformações específicas de imagem
"""
from PIL import Image, ImageOps, ImageEnhance
from typing import Tuple

class ImageTransformations:
    
    @staticmethod
    def apply_rotation(image: Image.Image, degrees: float) -> Image.Image:
        if image is None:
            return None
        return image.rotate(degrees, expand=True, resample=Image.Resampling.BICUBIC)
    
    @staticmethod
    def apply_crop(image: Image.Image, coordinates: Tuple[int, int, int, int]) -> Image.Image:
        if image is None:
            return None
            
        x1, y1, x2, y2 = coordinates
        width, height = image.size
        x2 = min(x2, width)
        y2 = min(y2, height)
        
        return image.crop((x1, y1, x2, y2))
    
    @staticmethod
    def apply_resize(image: Image.Image, new_size: Tuple[int, int], 
                    keep_aspect: bool = True) -> Image.Image:
        if image is None:
            return None
            
        if keep_aspect:
            original_width, original_height = image.size
            target_width, target_height = new_size
            
            ratio = min(target_width/original_width, target_height/original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            new_size = (new_width, new_height)
        
        return image.resize(new_size, Image.Resampling.LANCZOS)
    
    @staticmethod
    def apply_flip(image: Image.Image, horizontal: bool = True) -> Image.Image:
        if image is None:
            return None
            
        if horizontal:
            return ImageOps.mirror(image)
        else:
            return ImageOps.flip(image)
    
    @staticmethod
    def calculate_aspect_ratio(width: int, height: int) -> float:
        if height == 0:
            return 0
        return width / height
    
    @staticmethod
    def get_recommended_sizes(original_size: Tuple[int, int]) -> dict:
        width, height = original_size
        return {
            'quarter': (width // 2, height // 2),
            'half': (width // 2, height // 2),
            'double': (width * 2, height * 2),
            '1080p': (1920, 1080),
            '720p': (1280, 720),
            '480p': (854, 480)
        }