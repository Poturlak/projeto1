"""
Classe principal para manipulação de imagens - Implementação Completa
"""
from PIL import Image, ImageOps, ImageEnhance
import os
from pathlib import Path
from typing import Optional, Tuple, List

class ImageProcessor:
    def __init__(self):
        self.original_image: Optional[Image.Image] = None
        self.current_image: Optional[Image.Image] = None
        self.filename: Optional[str] = None
        self.filepath: Optional[str] = None
        self.history: List[Image.Image] = []
        self.history_index: int = -1
        self.max_history_size: int = 20
        
    def load_image(self, filepath: str) -> bool:
        try:
            self.filepath = filepath
            self.filename = Path(filepath).name
            
            self.original_image = Image.open(filepath)
            
            if self.original_image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', self.original_image.size, (255, 255, 255))
                if self.original_image.mode == 'P':
                    self.original_image = self.original_image.convert('RGBA')
                background.paste(self.original_image, mask=self.original_image.split()[-1] if self.original_image.mode == 'RGBA' else None)
                self.original_image = background
            elif self.original_image.mode != 'RGB':
                self.original_image = self.original_image.convert('RGB')
                
            self.current_image = self.original_image.copy()
            
            self.history = [self.current_image.copy()]
            self.history_index = 0
            
            print(f"Imagem carregada: {self.filename} ({self.current_image.size})")
            return True
            
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")
            return False
    
    def save_image(self, filepath: str = None, format: str = "PNG") -> bool:
        try:
            if self.current_image is None:
                return False
                
            save_path = filepath or self.filepath
            if not save_path:
                return False
                
            self.current_image.save(save_path, format=format)
            print(f"Imagem salva: {save_path}")
            return True
            
        except Exception as e:
            print(f"Erro ao salvar imagem: {e}")
            return False
    
    def save_copy(self, suffix: str = "_editado") -> bool:
        if not self.filepath or not self.current_image:
            return False
            
        try:
            path = Path(self.filepath)
            new_filename = f"{path.stem}{suffix}{path.suffix}"
            new_path = path.parent / new_filename
            
            return self.save_image(str(new_path))
            
        except Exception as e:
            print(f"Erro ao salvar cópia: {e}")
            return False
    
    def resize(self, width: int, height: int, keep_aspect_ratio: bool = True) -> bool:
        try:
            if self.current_image is None:
                return False
                
            if keep_aspect_ratio:
                original_width, original_height = self.current_image.size
                ratio = min(width/original_width, height/original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
            else:
                new_width, new_height = width, height
            
            new_image = self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self._update_image(new_image)
            return True
            
        except Exception as e:
            print(f"Erro ao redimensionar: {e}")
            return False
    
    def rotate(self, degrees: float) -> bool:
        try:
            if self.current_image is None:
                return False
                
            new_image = self.current_image.rotate(degrees, expand=True, resample=Image.Resampling.BICUBIC)
            self._update_image(new_image)
            return True
            
        except Exception as e:
            print(f"Erro ao rotacionar: {e}")
            return False
    
    def rotate_90(self, clockwise: bool = True) -> bool:
        degrees = 90 if clockwise else -90
        return self.rotate(degrees)
    
    def flip(self, horizontal: bool = True) -> bool:
        try:
            if self.current_image is None:
                return False
                
            if horizontal:
                new_image = ImageOps.mirror(self.current_image)
            else:
                new_image = ImageOps.flip(self.current_image)
                
            self._update_image(new_image)
            return True
            
        except Exception as e:
            print(f"Erro ao espelhar: {e}")
            return False
    
    def crop(self, x: int, y: int, width: int, height: int) -> bool:
        try:
            if self.current_image is None:
                print("Erro: Nenhuma imagem para recortar")
                return False
                
            print(f"Recortando: x={x}, y={y}, width={width}, height={height}")
            
            img_width, img_height = self.current_image.size
            print(f"Tamanho original da imagem: {img_width}x{img_height}")
            
            x2 = min(x + width, img_width)
            y2 = min(y + height, img_height)
            
            print(f"Área de recorte final: ({x}, {y}) -> ({x2}, {y2})")
            
            if x2 <= x or y2 <= y:
                print("Erro: Área de recorte inválida")
                return False
                
            new_image = self.current_image.crop((x, y, x2, y2))
            
            print(f"Nova imagem: {new_image.size}, modo: {new_image.mode}")
            
            if new_image.size[0] == 0 or new_image.size[1] == 0:
                print("Erro: Imagem recortada tem tamanho zero")
                return False
                
            self._update_image(new_image)
            print("Recorte concluído com sucesso")
            return True
            
        except Exception as e:
            print(f"Erro ao recortar: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def get_dimensions(self) -> Tuple[int, int]:
        if self.current_image is None:
            return (0, 0)
        return self.current_image.size
    
    def get_original_dimensions(self) -> Tuple[int, int]:
        if self.original_image is None:
            return (0, 0)
        return self.original_image.size
    
    def get_file_info(self) -> dict:
        if not self.filepath:
            return {}
            
        path = Path(self.filepath)
        return {
            'filename': self.filename,
            'filepath': self.filepath,
            'file_size': path.stat().st_size if path.exists() else 0,
            'format': self.current_image.format if self.current_image else 'Unknown',
            'current_size': self.get_dimensions(),
            'original_size': self.get_original_dimensions()
        }
    
    def reset_to_original(self) -> bool:
        if self.original_image is None:
            return False
            
        self.current_image = self.original_image.copy()
        self._update_image(self.current_image, reset_history=True)
        return True
    
    def has_changes(self) -> bool:
        if self.original_image is None or self.current_image is None:
            return False
            
        return self.original_image.tobytes() != self.current_image.tobytes()
    
    def _update_image(self, new_image: Image.Image, reset_history: bool = False):
        if reset_history:
            self.history = [new_image.copy()]
            self.history_index = 0
        else:
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            
            self.history.append(new_image.copy())
            self.history_index += 1
            
            if len(self.history) > self.max_history_size:
                self.history.pop(0)
                self.history_index -= 1
        
        self.current_image = new_image
    
    def undo(self) -> bool:
        if self.history_index <= 0:
            return False
            
        self.history_index -= 1
        self.current_image = self.history[self.history_index].copy()
        return True
    
    def redo(self) -> bool:
        if self.history_index >= len(self.history) - 1:
            return False
            
        self.history_index += 1
        self.current_image = self.history[self.history_index].copy()
        return True
    
    def get_history_info(self) -> dict:
        return {
            'can_undo': self.history_index > 0,
            'can_redo': self.history_index < len(self.history) - 1,
            'history_size': len(self.history),
            'current_index': self.history_index
        }
    
    def is_image_loaded(self) -> bool:
        return self.current_image is not None
    
    def __str__(self) -> str:
        if not self.is_image_loaded():
            return "ImageProcessor: Nenhuma imagem carregada"
            
        info = self.get_file_info()
        return f"ImageProcessor: {info['filename']} {self.get_dimensions()}"