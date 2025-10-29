"""
Utilitários para conversão e manipulação de imagens
"""
from PIL import Image, ImageOps
from PIL.ImageQt import ImageQt
from PyQt6.QtGui import QPixmap, QImage
from typing import Optional

def pil_to_pixmap(pil_image: Image.Image) -> QPixmap:
    if pil_image is None:
        print("Erro: Imagem PIL é None")
        return QPixmap()
    
    try:
        print(f"Convertendo PIL para QPixmap: {pil_image.size}, modo: {pil_image.mode}")
        
        if pil_image.mode in ['1', 'L', 'P']:
            pil_image = pil_image.convert('RGB')
            print(f"Imagem convertida para RGB: {pil_image.mode}")
        elif pil_image.mode == 'RGBA':
            pass
        elif pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
            print(f"Imagem convertida para RGB: {pil_image.mode}")
        
        buffer = pil_image.tobytes()
        
        if pil_image.mode == 'RGB':
            qimage = QImage(buffer, pil_image.size[0], pil_image.size[1], 
                           pil_image.size[0] * 3, QImage.Format.Format_RGB888)
        elif pil_image.mode == 'RGBA':
            qimage = QImage(buffer, pil_image.size[0], pil_image.size[1], 
                           pil_image.size[0] * 4, QImage.Format.Format_RGBA8888)
        else:
            print(f"Modo de imagem não suportado: {pil_image.mode}")
            return QPixmap()
        
        if qimage.isNull():
            print("Erro: QImage é nula")
            return QPixmap()
            
        pixmap = QPixmap.fromImage(qimage)
        
        if pixmap.isNull():
            print("Erro: QPixmap é nula")
            return QPixmap()
            
        print(f"Conversão bem-sucedida: {pixmap.width()}x{pixmap.height()}")
        return pixmap
        
    except Exception as e:
        print(f"Erro na conversão PIL para QPixmap: {e}")
        import traceback
        traceback.print_exc()
        return QPixmap()

def pixmap_to_pil(pixmap: QPixmap) -> Optional[Image.Image]:
    if pixmap.isNull():
        return None
        
    try:
        qimage = pixmap.toImage()
        if qimage.format() == QImage.Format.Format_RGB32:
            qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
            
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(height * width * 3)
        
        return Image.frombytes('RGB', (width, height), ptr, 'raw', 'RGB', 0, 1)
        
    except Exception as e:
        print(f"Erro na conversão QPixmap para PIL: {e}")
        return None

def get_supported_formats() -> str:
    return "Imagens (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;Todos os arquivos (*)"

def create_thumbnail(pil_image: Image.Image, size: tuple = (200, 200)) -> Image.Image:
    if pil_image is None:
        return None
        
    return pil_image.copy().thumbnail(size, Image.Resampling.LANCZOS)

def image_to_grayscale(pil_image: Image.Image) -> Image.Image:
    if pil_image is None:
        return None
        
    return ImageOps.grayscale(pil_image)

def get_image_info(pil_image: Image.Image) -> dict:
    if pil_image is None:
        return {}
        
    return {
        'size': pil_image.size,
        'mode': pil_image.mode,
        'format': getattr(pil_image, 'format', 'Unknown')
    }