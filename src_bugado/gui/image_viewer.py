"""
Visualizador de imagem com zoom, pan e navegação - Implementação Completa
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QApplication
from PyQt6.QtGui import (QPixmap, QWheelEvent, QMouseEvent, QPainter, 
                         QKeyEvent, QPen, QColor, QCursor, QBrush, QFont)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from models.point import Point
from typing import List


class ImageViewer(QGraphicsView):
    # Signals
    zoom_changed = pyqtSignal(float)
    image_loaded = pyqtSignal(bool)
    mouse_position_changed = pyqtSignal(QPointF)
    crop_selection_started = pyqtSignal(QPointF)
    crop_selection_updated = pyqtSignal(QRectF)
    crop_selection_finished = pyqtSignal(QRectF)
    point_clicked = pyqtSignal(QPointF)
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.pixmap_item = None
        
        # Configuração de zoom
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.zoom_step = 0.25
        
        # Modos de interação
        self._is_panning = False
        self._last_pan_point = QPointF()
        self._crop_mode = False
        self._crop_start = QPointF()
        self._crop_end = QPointF()
        
        # Controle para modo de pontos
        self._points_mode = False
        self._current_point_shape = 'circle'
        self._drag_start_pos = QPointF()
        self._drag_threshold = 5
        
        # 👇 NOVO: Controle para modo de desenho de pontos
        self._draw_point_mode = False
        self._draw_point_shape = 'circle'
        self._draw_start = QPointF()
        self._draw_end = QPointF()
        self._last_size_per_shape = {'circle': 20, 'rectangle': 20}
        self._draw_mode_active = {'circle': False, 'rectangle': False}
        
        # Pontos para desenhar
        self.points: List[Point] = []
        
        # Referência ao point_manager para sincronizar tamanhos
        self.point_manager = None
        
        self.setup_viewer()
    
    def setup_viewer(self):
        """Configura o visualizador"""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameStyle(0)
        
    def drawForeground(self, painter, rect):
        """Desenha o retângulo de seleção de recorte E OS PONTOS"""
        # Desenha recorte se ativo
        if self._crop_mode and not self._crop_start.isNull() and not self._crop_end.isNull():
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            
            selection_rect = QRectF(self._crop_start, self._crop_end).normalized()
            painter.drawRect(selection_rect)
            painter.fillRect(selection_rect, QColor(255, 0, 0, 50))
        
        # 👇 NOVO: Desenha preview do ponto durante o desenho
        if (self._draw_point_mode and not self._draw_start.isNull() and 
            not self._draw_end.isNull()):
            
            draw_rect = QRectF(self._draw_start, self._draw_end).normalized()
            if self._draw_point_shape == 'circle':
                painter.setPen(QPen(QColor(0, 255, 0), 2))  # Verde para preview
                painter.setBrush(QColor(0, 255, 0, 50))
                center = draw_rect.center()
                radius = max(draw_rect.width(), draw_rect.height()) / 2
                painter.drawEllipse(center, radius, radius)
            else:  # rectangle
                painter.setPen(QPen(QColor(0, 255, 0), 2))
                painter.setBrush(QColor(0, 255, 0, 50))
                painter.drawRect(draw_rect)
        
        # DESENHA OS PONTOS
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for point in self.points:
            pos = point.position
            size = point.size
            
            # CORREÇÃO: Remove self.zoom_factor - usa apenas proporção do tamanho do ponto
            font_size = max(8, int(size * 0.25))  # 25% do tamanho do ponto, mínimo 8px
            font = painter.font()
            font.setPointSize(font_size)
            font.setWeight(QFont.Weight.Bold)  # 👈 AQUI ESTÁ A CORREÇÃO - FONTE NEGRITO
            painter.setFont(font)
            
            if point.shape == 'circle':
                # Círculo vermelho com MENOS transparência
                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.setBrush(QColor(255, 0, 0, 120))
                painter.drawEllipse(pos, size/2, size/2)
                
                # Texto BRANCO com FONTE MAIS ESPESSA
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                text_rect = QRectF(pos.x() - size/2, pos.y() - size/2, size, size)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(point.id))
                
            elif point.shape == 'rectangle':
                # Retângulo vermelho com MENOS transparência
                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.setBrush(QColor(255, 0, 0, 120))
                rect_draw = QRectF(pos.x() - size/2, pos.y() - size/2, size, size)
                painter.drawRect(rect_draw)
                
                # Texto BRANCO com FONTE MAIS ESPESSA
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                text_rect = QRectF(pos.x() - size/2, pos.y() - size/2, size, size)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(point.id))
    
    def set_points(self, points: List[Point]):
        """Define os pontos a serem exibidos"""
        self.points = points
        self.scene.update()  # Força redesenho
    
    def set_point_manager(self, point_manager):
        """Define o point_manager para sincronizar tamanhos"""
        self.point_manager = point_manager
    
    def _get_current_point_size(self):
        """Obtém o tamanho atual do ponto do PointManager"""
        if self.point_manager:
            return self.point_manager.current_size
        else:
            return 20  # Tamanho padrão
    
    def _get_current_point_shape(self):
        """Obtém a forma atual do ponto do PointManager"""
        if self.point_manager:
            return self.point_manager.current_shape
        else:
            return 'circle'  # Forma padrão
    
    # 👇 NOVO: Métodos para controle do modo desenho
    def set_draw_point_mode(self, enabled: bool, shape_type: str):
        """Ativa/desativa modo de desenho de pontos"""
        self._draw_point_mode = enabled
        self._draw_point_shape = shape_type
        self._crop_mode = False  # Desativa recorte
        
        # Ativa/desativa o modo desenho apenas para a forma específica
        if shape_type in self._draw_mode_active:
            self._draw_mode_active[shape_type] = enabled
        
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            print(f"Modo desenho {shape_type} ativado - Arraste para definir tamanho")
        else:
            # Mantém cursor de ponto se estiver no modo pontos, senão volta para arrow
            self._set_point_cursor() if self._points_mode else self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def increase_point_size(self):
        """Aumenta tamanho do ponto atual OU último tamanho memorizado"""
        current_shape = self._get_current_point_shape()
        if self.points and self.points[-1].shape == current_shape:
            # Aumenta último ponto criado
            self.points[-1].size *= 1.2
        else:
            # Aumenta tamanho memorizado para futuros pontos
            self._last_size_per_shape[current_shape] *= 1.2
        
        self.scene.update()
        self.update_cursor()  # Atualiza cursor se necessário
    
    def decrease_point_size(self):
        """Diminui tamanho do ponto atual OU último tamanho memorizado"""
        current_shape = self._get_current_point_shape()
        if self.points and self.points[-1].shape == current_shape:
            # Diminui último ponto criado
            self.points[-1].size = max(5, self.points[-1].size * 0.8)
        else:
            # Diminui tamanho memorizado para futuros pontos
            self._last_size_per_shape[current_shape] = max(5, self._last_size_per_shape[current_shape] * 0.8)
        
        self.scene.update()
        self.update_cursor()  # Atualiza cursor se necessário
    
    def undo_last_point(self):
        """Remove último ponto"""
        if self.points:
            removed_point = self.points.pop()
            print(f"Ponto {removed_point.id} removido")
            self.scene.update()
    
    def delete_point_by_id(self, point_id: int):
        """Remove ponto específico"""
        self.points = [p for p in self.points if p.id != point_id]
        self.scene.update()
        print(f"Ponto {point_id} removido")
    
    def load_image(self, image_path: str) -> bool:
        """Carrega imagem do arquivo"""
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.image_loaded.emit(False)
                return False
                
            return self.set_pixmap(pixmap)
            
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")
            self.image_loaded.emit(False)
            return False
    
    def set_pixmap(self, pixmap: QPixmap) -> bool:
        """Define pixmap atual"""
        try:
            self.scene.clear()
            self.pixmap_item = None
            
            if pixmap.isNull():
                return False
            
            self.pixmap_item = self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(self.pixmap_item.boundingRect())
            
            self.fit_to_view()
            
            self.image_loaded.emit(True)
            return True
            
        except Exception as e:
            print(f"Erro ao definir pixmap: {e}")
            return False
    
    def has_image(self) -> bool:
        """Verifica se há imagem carregada"""
        return self.pixmap_item is not None and not self.pixmap_item.pixmap().isNull()
    
    # === ZOOM E NAVEGAÇÃO ===
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom com roda do mouse"""
        if not self.has_image():
            return
            
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()
    
    def zoom_in(self):
        """Aumenta zoom"""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor *= (1.0 + self.zoom_step)
            self._apply_zoom()
    
    def zoom_out(self):
        """Diminui zoom"""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor /= (1.0 + self.zoom_step)
            self._apply_zoom()
    
    def _apply_zoom(self):
        """Aplica o fator de zoom atual"""
        if not self.has_image():
            return
            
        self.resetTransform()
        self.scale(self.zoom_factor, self.zoom_factor)
        self.zoom_changed.emit(self.zoom_factor)
        # ATUALIZA O CURSOR SE ESTIVER NO MODO PONTOS
        if self._points_mode:
            self.update_cursor()
    
    def fit_to_view(self):
        """Ajusta imagem à tela"""
        if not self.has_image():
            return
            
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        transform = self.transform()
        self.zoom_factor = transform.m11()
        self.zoom_changed.emit(self.zoom_factor)
        # ATUALIZA O CURSOR SE ESTIVER NO MODO PONTOS
        if self._points_mode:
            self.update_cursor()
    
    def actual_size(self):
        """Tamanho real (100%)"""
        self.zoom_factor = 1.0
        self._apply_zoom()
    
    def get_current_scale(self) -> float:
        return self.zoom_factor
    
    # === CONTROLE DE MOUSE ATUALIZADO ===
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press - SUPORTA CLIQUE PARA PONTOS"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._crop_mode:
                scene_pos = self.mapToScene(event.pos())
                self._crop_start = scene_pos
                self._crop_end = scene_pos
                self.crop_selection_started.emit(scene_pos)
                self.scene.update()
            elif self._draw_point_mode:
                # 👇 NOVO: Inicia desenho de ponto
                scene_pos = self.mapToScene(event.pos())
                self._draw_start = scene_pos
                self._draw_end = scene_pos
                self.scene.update()
            elif self._points_mode:
                self._drag_start_pos = event.pos()
                self._is_panning = False
            else:
                self._is_panning = True
                self._last_pan_point = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move - DIFERENCIA ENTRE CLIQUE E ARRASTE"""
        scene_pos = self.mapToScene(event.pos())
        self.mouse_position_changed.emit(scene_pos)
        
        if self._is_panning:
            delta = event.pos() - self._last_pan_point
            self._last_pan_point = event.pos()
            
            h_scroll = self.horizontalScrollBar()
            v_scroll = self.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() - delta.x())
            v_scroll.setValue(v_scroll.value() - delta.y())
            
        elif self._draw_point_mode and not self._draw_start.isNull():
            # 👇 NOVO: Atualiza preview do desenho
            self._draw_end = scene_pos
            self.scene.update()
            
        elif self._points_mode and not self._drag_start_pos.isNull():
            move_distance = (event.pos() - self._drag_start_pos).manhattanLength()
            if move_distance > self._drag_threshold:
                self._is_panning = True
                self._last_pan_point = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        elif self._crop_mode and not self._crop_start.isNull():
            scene_pos = self.mapToScene(event.pos())
            self._crop_end = scene_pos
            rect = QRectF(self._crop_start, self._crop_end).normalized()
            self.crop_selection_updated.emit(rect)
            self.scene.update()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release - EMITE CLIQUE PARA PONTOS"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_panning:
                self._is_panning = False
                if self._points_mode:
                    self._set_point_cursor()
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    
            elif self._draw_point_mode and not self._draw_start.isNull():
                # 👇 NOVO: Finaliza desenho de ponto
                scene_pos = self.mapToScene(event.pos())
                self._draw_end = scene_pos
                
                # Calcula tamanho baseado na área de desenho
                draw_rect = QRectF(self._draw_start, self._draw_end).normalized()
                size = max(draw_rect.width(), draw_rect.height())
                
                if size > 5:  # Tamanho mínimo
                    point_id = len(self.points) + 1
                    new_point = Point(
                        id=point_id,
                        position=draw_rect.center(),
                        size=size,
                        shape=self._draw_point_shape
                    )
                    self.points.append(new_point)
                    
                    # Memoriza o tamanho usado e DESATIVA modo desenho
                    self._last_size_per_shape[self._draw_point_shape] = size
                    self._draw_mode_active[self._draw_point_shape] = False
                    self._draw_point_mode = False
                    
                    # Atualiza cursor para o modo normal de pontos
                    self._set_point_cursor()
                    
                    self.scene.update()
                    print(f"Ponto {self._draw_point_shape} criado - Tamanho: {size:.1f}px")
                
                self._draw_start = QPointF()
                self._draw_end = QPointF()
                    
            elif self._points_mode and not self._drag_start_pos.isNull():
                move_distance = (event.pos() - self._drag_start_pos).manhattanLength()
                if move_distance <= self._drag_threshold:
                    scene_pos = self.mapToScene(event.pos())
                    
                    # 👇 NOVO: Comportamento para cliques normais quando modo desenho está INATIVO
                    current_shape = self._get_current_point_shape()
                    if not self._draw_mode_active.get(current_shape, False):
                        # Usa o último tamanho memorizado para esta forma
                        last_size = self._last_size_per_shape.get(current_shape, 20)
                        
                        point_id = len(self.points) + 1
                        new_point = Point(
                            id=point_id,
                            position=scene_pos,
                            size=last_size,
                            shape=current_shape
                        )
                        self.points.append(new_point)
                        self.scene.update()
                        print(f"Ponto {current_shape} criado - Tamanho: {last_size:.1f}px (repetido)")
                    else:
                        self.point_clicked.emit(scene_pos)
            
            elif self._crop_mode and not self._crop_start.isNull() and not self._crop_end.isNull():
                scene_pos = self.mapToScene(event.pos())
                self._crop_end = scene_pos
                rect = QRectF(self._crop_start, self._crop_end).normalized()
                
                if rect.width() > 10 and rect.height() > 10:
                    if self.pixmap_item:
                        topLeft = self.pixmap_item.mapFromScene(rect.topLeft())
                        bottomRight = self.pixmap_item.mapFromScene(rect.bottomRight())
                        image_rect = QRectF(topLeft, bottomRight).normalized()
                        pixmap_rect = self.pixmap_item.boundingRect()
                        image_rect = image_rect.intersected(pixmap_rect)
                        
                        if image_rect.width() > 10 and image_rect.height() > 10:
                            self.crop_selection_finished.emit(image_rect)
                            self._crop_start = QPointF()
                            self._crop_end = QPointF()
                            self.scene.update()
                    else:
                        self.crop_selection_finished.emit(rect)
                        self._crop_start = QPointF()
                        self._crop_end = QPointF()
                        self.scene.update()
                else:
                    self._crop_start = QPointF()
                    self._crop_end = QPointF()
                    self.scene.update()
        
        self._drag_start_pos = QPointF()
        super().mouseReleaseEvent(event)
    
    # === MODOS DE INTERAÇÃO ATUALIZADOS ===
    
    def set_pan_mode(self, enabled: bool):
        """Ativa/desativa modo pan"""
        if enabled:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
    
    def set_crop_mode(self, enabled: bool):
        """Ativa/desativa modo recorte"""
        self._crop_mode = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self._crop_start = QPointF()
            self._crop_end = QPointF()
            print("Modo recorte ativado - Arraste para selecionar a área")
        else:
            self.update_cursor()
            self._crop_start = QPointF()
            self._crop_end = QPointF()
            self.scene.update()
            print("Modo recorte desativado")

    def set_points_mode(self, enabled: bool, shape_type: str = None):
        """Ativa/desativa modo de marcação de pontos"""
        self._points_mode = enabled
        if shape_type:
            self._current_point_shape = shape_type
            
        if enabled:
            self.update_cursor()
            current_size = self._get_current_point_size()
            print(f"Modo marcação de pontos ativado - Forma: {self._current_point_shape}, Tamanho: {current_size}px")
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            print("Modo marcação de pontos desativado")
    
    def update_cursor(self):
        """Atualiza o cursor baseado no modo atual"""
        if self._points_mode:
            current_shape = self._get_current_point_shape()
            if self._draw_mode_active.get(current_shape, False):
                # Modo desenho ativo - cursor de cruz
                self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                # Modo normal - cursor personalizado do ponto
                self._set_point_cursor()
    
    def _set_point_cursor(self):
        """Define cursor personalizado baseado na forma atual"""
        shape = self._get_current_point_shape()
        if shape == 'circle':
            self.setCursor(self._create_circle_cursor())
        elif shape == 'rectangle':
            self.setCursor(self._create_rectangle_cursor())
    
    def _create_circle_cursor(self):
        """Cria cursor personalizado para círculo com tamanho proporcional"""
        size = self._get_current_point_size()
        size = int(size * self.zoom_factor)
        cursor_size = max(24, int(size * 1.5))
                          
        pixmap = QPixmap(cursor_size, cursor_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Círculo vermelho com tamanho proporcional
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        
        # Centralizar o círculo no cursor
        center = cursor_size // 2
        radius = size // 2
        painter.drawEllipse(center - radius, center - radius, size, size)
        
        # Cruz de mira no centro
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawLine(center, center - radius - 2, center, center + radius + 2)  # Vertical
        painter.drawLine(center - radius - 2, center, center + radius + 2, center)  # Horizontal
        
        painter.end()
        
        return QCursor(pixmap, center, center)

    def _create_rectangle_cursor(self):
        """Cria cursor personalizado para retângulo com tamanho proporcional"""
        size = self._get_current_point_size()
        size = int(size * self.zoom_factor)
        cursor_size = max(24, int(size * 1.5))
        pixmap = QPixmap(cursor_size, cursor_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Retângulo vermelho com tamanho proporcional
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        
        # Centralizar o retângulo no cursor
        center = cursor_size // 2
        half_size = size // 2
        rect_x = center - half_size
        rect_y = center - half_size
        painter.drawRect(rect_x, rect_y, size, size)
        
        # Cruz de mira no centro
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawLine(center, center - half_size - 2, center, center + half_size + 2)  # Vertical
        painter.drawLine(center - half_size - 2, center, center + half_size + 2, center)  # Horizontal
        
        painter.end()
        
        return QCursor(pixmap, center, center)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press - ESC para cancelar recorte"""
        if event.key() == Qt.Key.Key_Escape and self._crop_mode:
            self.set_crop_mode(False)
            print("Recorte cancelado pelo usuário")
        else:
            super().keyPressEvent(event)
    
    # === UTILITÁRIOS ===
    
    def get_image_size(self) -> QPointF:
        """Retorna tamanho da imagem atual"""
        if not self.has_image():
            return QPointF(0, 0)
        rect = self.pixmap_item.boundingRect()
        return QPointF(rect.width(), rect.height())
    
    def get_crop_rect(self) -> QRectF:
        """Retorna o retângulo de recorte atual"""
        if self._crop_start.isNull() or self._crop_end.isNull():
            return QRectF()
        
        return QRectF(self._crop_start, self._crop_end).normalized()
    
    def clear(self):
        """Limpa visualizador"""
        self.scene.clear()
        self.pixmap_item = None
        self.zoom_factor = 1.0
        self.resetTransform()
        self.points.clear()