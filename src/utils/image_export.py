"""
Exportador de imagens com pontos desenhados
Gera imagem final com pontos, IDs e valores de medição
"""

import os
from typing import List, Optional, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import io


class ImageExporter:
    """Exportador de imagens com pontos e medições"""
    
    # Configurações visuais
    POINT_COLORS = {
        'normal': (255, 0, 0),        # Vermelho - pontos normais
        'diferenca': (255, 105, 180), # Rosa - pontos com diferença
        'verde': (0, 255, 0),         # Verde - pontos OK na comparação
        'sem_medicao': (128, 128, 128) # Cinza - sem medição
    }
    
    POINT_ALPHA = 150
    FONT_SIZE = 14
    ID_FONT_SIZE = 12
    
    @staticmethod
    def export_with_points(image_data: Any, points_data: List[Any], 
                          filepath: str, tolerance: float = 5.0) -> bool:
        """
        Exporta imagem com pontos desenhados
        
        Args:
            image_data: Imagem PIL
            points_data: Lista de pontos
            filepath: Caminho de destino
            tolerance: Tolerância para destacar diferenças
            
        Returns:
            bool: True se exportou com sucesso
        """
        try:
            if not image_data:
                print("❌ Nenhuma imagem para exportar")
                return False
            
            print(f"📸 Exportando imagem com {len(points_data)} pontos")
            
            # Criar cópia da imagem para desenhar
            if image_data.mode != 'RGBA':
                export_image = image_data.convert('RGBA')
            else:
                export_image = image_data.copy()
            
            # Criar overlay transparente para desenhar pontos
            overlay = Image.new('RGBA', export_image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Tentar carregar fonte
            try:
                # Fontes padrão do sistema (Windows/Linux/Mac)
                font_paths = [
                    "arial.ttf",
                    "/System/Library/Fonts/Arial.ttf",  # macOS
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                    "C:/Windows/Fonts/arial.ttf"  # Windows
                ]
                
                font = None
                id_font = None
                
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, ImageExporter.FONT_SIZE)
                        id_font = ImageFont.truetype(font_path, ImageExporter.ID_FONT_SIZE)
                        break
                    except:
                        continue
                
                if not font:
                    font = ImageFont.load_default()
                    id_font = ImageFont.load_default()
                    
            except Exception as e:
                print(f"⚠️  Usando fonte padrão: {e}")
                font = ImageFont.load_default()
                id_font = ImageFont.load_default()
            
            # Desenhar cada ponto
            for point in points_data:
                ImageExporter._draw_single_point(draw, point, font, id_font, tolerance)
            
            # Combinar imagem original com overlay
            export_image = Image.alpha_composite(export_image, overlay)
            
            # Converter para RGB se necessário (remove transparência para JPEG)
            if filepath.lower().endswith(('.jpg', '.jpeg')):
                final_image = Image.new('RGB', export_image.size, (255, 255, 255))
                final_image.paste(export_image, mask=export_image.split()[-1])
                export_image = final_image
            
            # Salvar imagem
            export_image.save(filepath, quality=95, optimize=True)
            
            print(f"📸 Imagem exportada: {os.path.basename(filepath)}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar imagem: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def _draw_single_point(draw: ImageDraw, point: Any, font: ImageFont, 
                          id_font: ImageFont, tolerance: float) -> None:
        """Desenha um único ponto na imagem"""
        try:
            # Obter propriedades do ponto
            x = getattr(point, 'x', 0)
            y = getattr(point, 'y', 0)
            point_id = getattr(point, 'id', 0)
            shape = getattr(point, 'shape', 'circle')
            size = getattr(point, 'size', 20)
            width = getattr(point, 'width', size)
            height = getattr(point, 'height', size)
            
            # Determinar cor baseada no status
            color = ImageExporter._get_point_color(point, tolerance)
            
            # Desenhar forma
            if shape == 'circle':
                ImageExporter._draw_circle(draw, x, y, size, color, point_id, id_font)
            else:  # rectangle
                ImageExporter._draw_rectangle(draw, x, y, width, height, color, point_id, id_font)
            
            # Desenhar valor de medição se existir
            ImageExporter._draw_measurement_value(draw, point, x, y, font, size)
            
        except Exception as e:
            print(f"⚠️  Erro ao desenhar ponto {getattr(point, 'id', '?')}: {e}")
    
    @staticmethod
    def _get_point_color(point: Any, tolerance: float) -> Tuple[int, int, int]:
        """Determina cor do ponto baseada no status"""
        # Verificar se tem medições
        ref = getattr(point, 'medicao_referencia', None)
        comp = getattr(point, 'medicao_comparacao', None)
        
        if ref is not None and comp is not None:
            # Calcular diferença percentual
            diff_percent = abs(((comp - ref) / ref) * 100) if ref != 0 else 0
            
            if diff_percent > tolerance:
                return ImageExporter.POINT_COLORS['diferenca']  # Rosa
            else:
                return ImageExporter.POINT_COLORS['verde']      # Verde
        
        elif ref is not None or comp is not None:
            return ImageExporter.POINT_COLORS['normal']         # Vermelho (só uma medição)
        
        else:
            return ImageExporter.POINT_COLORS['sem_medicao']    # Cinza (sem medição)
    
    @staticmethod
    def _draw_circle(draw: ImageDraw, x: float, y: float, size: int, 
                    color: Tuple[int, int, int], point_id: int, font: ImageFont) -> None:
        """Desenha círculo"""
        radius = size // 2
        
        # Círculo preenchido com transparência
        circle_color = (*color, ImageExporter.POINT_ALPHA)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                    fill=circle_color, outline=(*color, 255), width=2)
        
        # ID do ponto no centro
        id_text = str(point_id)
        bbox = draw.textbbox((0, 0), id_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x - text_width // 2
        text_y = y - text_height // 2
        
        # Fundo branco para o texto
        draw.rectangle([text_x - 2, text_y - 1, text_x + text_width + 2, text_y + text_height + 1], 
                      fill=(255, 255, 255, 200))
        draw.text((text_x, text_y), id_text, fill=(0, 0, 0, 255), font=font)
    
    @staticmethod
    def _draw_rectangle(draw: ImageDraw, x: float, y: float, width: int, height: int,
                       color: Tuple[int, int, int], point_id: int, font: ImageFont) -> None:
        """Desenha retângulo"""
        half_w = width // 2
        half_h = height // 2
        
        # Retângulo preenchido com transparência
        rect_color = (*color, ImageExporter.POINT_ALPHA)
        draw.rectangle([x - half_w, y - half_h, x + half_w, y + half_h], 
                      fill=rect_color, outline=(*color, 255), width=2)
        
        # ID do ponto no centro
        id_text = str(point_id)
        bbox = draw.textbbox((0, 0), id_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x - text_width // 2
        text_y = y - text_height // 2
        
        # Fundo branco para o texto
        draw.rectangle([text_x - 2, text_y - 1, text_x + text_width + 2, text_y + text_height + 1], 
                      fill=(255, 255, 255, 200))
        draw.text((text_x, text_y), id_text, fill=(0, 0, 0, 255), font=font)
    
    @staticmethod
    def _draw_measurement_value(draw: ImageDraw, point: Any, x: float, y: float, 
                              font: ImageFont, point_size: int) -> None:
        """Desenha valor de medição próximo ao ponto"""
        # Obter valor para mostrar
        comp = getattr(point, 'medicao_comparacao', None)
        ref = getattr(point, 'medicao_referencia', None)
        
        # Priorizar comparação, depois referência
        value = comp if comp is not None else ref
        
        if value is not None:
            # Formatar valor
            value_text = f"{value:.3f}V"
            
            # Posição do texto (abaixo do ponto)
            text_y = y + point_size // 2 + 5
            
            # Centralizar texto
            bbox = draw.textbbox((0, 0), value_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = x - text_width // 2
            
            # Fundo semi-transparente para o texto
            padding = 3
            draw.rectangle([text_x - padding, text_y - padding, 
                           text_x + text_width + padding, text_y + bbox[3] - bbox[1] + padding], 
                          fill=(0, 0, 0, 150))
            
            # Texto em branco
            draw.text((text_x, text_y), value_text, fill=(255, 255, 255, 255), font=font)
    
    @staticmethod
    def create_legend(points_data: List[Any], tolerance: float = 5.0) -> Image.Image:
        """
        Cria legenda explicativa dos pontos (para uso futuro)
        
        Args:
            points_data: Lista de pontos
            tolerance: Tolerância para classificação
            
        Returns:
            Image: Imagem da legenda
        """
        try:
            # Analisar pontos
            stats = {
                'normal': 0,
                'diferenca': 0,
                'verde': 0,
                'sem_medicao': 0
            }
            
            for point in points_data:
                ref = getattr(point, 'medicao_referencia', None)
                comp = getattr(point, 'medicao_comparacao', None)
                
                if ref is not None and comp is not None:
                    diff_percent = abs(((comp - ref) / ref) * 100) if ref != 0 else 0
                    if diff_percent > tolerance:
                        stats['diferenca'] += 1
                    else:
                        stats['verde'] += 1
                elif ref is not None or comp is not None:
                    stats['normal'] += 1
                else:
                    stats['sem_medicao'] += 1
            
            # Criar imagem da legenda
            legend_width = 200
            legend_height = 150
            legend = Image.new('RGBA', (legend_width, legend_height), (255, 255, 255, 240))
            draw = ImageDraw.Draw(legend)
            
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            y_pos = 10
            
            # Título
            draw.text((10, y_pos), "Legenda dos Pontos:", fill=(0, 0, 0), font=font)
            y_pos += 25
            
            # Itens da legenda
            legend_items = [
                (ImageExporter.POINT_COLORS['verde'], f"✓ OK ({stats['verde']})"),
                (ImageExporter.POINT_COLORS['diferenca'], f"⚠ Diferença ({stats['diferenca']})"),
                (ImageExporter.POINT_COLORS['normal'], f"• Medido ({stats['normal']})"),
                (ImageExporter.POINT_COLORS['sem_medicao'], f"○ Sem medição ({stats['sem_medicao']})")
            ]
            
            for color, text in legend_items:
                # Desenhar quadrado colorido
                draw.rectangle([10, y_pos, 20, y_pos + 10], fill=(*color, 255))
                # Desenhar texto
                draw.text((25, y_pos - 2), text, fill=(0, 0, 0), font=font)
                y_pos += 20
            
            return legend
            
        except Exception as e:
            print(f"❌ Erro ao criar legenda: {e}")
            return Image.new('RGBA', (200, 150), (255, 255, 255, 240))
