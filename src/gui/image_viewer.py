"""
Visualizador de imagem com zoom, pan, navegação, preview de pontos e cores - Versão Final
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QApplication
from PyQt6.QtGui import (QPixmap, QWheelEvent, QMouseEvent, QPainter, 
                         QKeyEvent, QPen, QColor, QCursor, QBrush, QFont)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer
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
        
        # Preview com timeout
        self._show_preview = False
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._hide_preview_timeout)
        
        # Pontos para desenhar
        self.points: List[Point] = []
        
        # Referência ao point_manager para sincronizar tamanhos e tolerância
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
        """Desenha o retângulo de seleção de recorte, OS PONTOS e o PREVIEW"""
        # Desenha recorte se ativo
        if self._crop_mode and not self._crop_start.isNull() and not self._crop_end.isNull():
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            
            selection_rect = QRectF(self._crop_start, self._crop_end).normalized()
            painter.drawRect(selection_rect)
            painter.fillRect(selection_rect, QColor(255, 0, 0, 50))
        
        # DESENHA OS PONTOS
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for point in self.points:
            pos = point.position
            
            # Determinar cor baseado em diferença
            if self.point_manager and point.esta_acima_tolerancia(self.point_manager.tolerance_percent):
                cor = QColor(255, 105, 180)  # Rosa (HotPink)
                alpha = 150
            else:
                cor = QColor(255, 0, 0)      # Vermelho
                alpha = 120
            
            font_size = max(8, int(point.size * 0.25))
            font = painter.font()
            font.setPointSize(font_size)
            font.setWeight(QFont.Weight.Bold)
            painter.setFont(font)
            
            if point.shape == 'circle':
                painter.setPen(QPen(cor, 2))
                painter.setBrush(QColor(cor.red(), cor.green(), cor.blue(), alpha))
                painter.drawEllipse(pos, point.size/2, point.size/2)
                
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                text_rect = QRectF(pos.x() - point.size/2, pos.y() - point.size/2, point.size, point.size)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(point.id))
                
            elif point.shape == 'rectangle':
                painter.setPen(QPen(cor, 1))
                painter.setBrush(QColor(cor.red(), cor.green(), cor.blue(), alpha))
                rect_draw = QRectF(pos.x() - point.width/2, pos.y() - point.height/2, point.width, point.height)
                painter.drawRect(rect_draw)
                
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                text_rect = QRectF(pos.x() - point.width/2, pos.y() - point.height/2, point.width, point.height)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(point.id))
        
        # DESENHA PREVIEW CENTRALIZADO
        if self._points_mode and self._show_preview:
            self._draw_preview_overlay(painter)
    
    def _draw_preview_overlay(self, painter):
        """Desenha preview do ponto no centro da viewport"""
        viewport_center = self.viewport().rect().center()
        scene_center = self.mapToScene(viewport_center)
        
        painter.setOpacity(0.8)
        
        shape = self._get_current_point_shape()
        
        if shape == 'circle':
            size = self._get_current_point_size()
            
            painter.setPen(QPen(QColor(0, 150, 255), 3))
            painter.setBrush(QColor(0, 150, 255, 100))
            painter.drawEllipse(scene_center, size/2, size/2)
            
            painter.setPen(QColor(255, 255, 255))
            font = painter.font()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            
            text_rect = QRectF(scene_center.x() - 60, scene_center.y() + size/2 + 10, 120, 30)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"Ø {int(size)}px")
            
        elif shape == 'rectangle':
            width = self._get_current_point_width()
            height = self._get_current_point_height()
            
            painter.setPen(QPen(QColor(0, 150, 255), 3))
            painter.setBrush(QColor(0, 150, 255, 100))
            rect_preview = QRectF(
                scene_center.x() - width/2,
                scene_center.y() - height/2,
                width,
                height
            )
            painter.drawRect(rect_preview)
            
            painter.setPen(QColor(255, 255, 255))
            font = painter.font()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            
            text_rect = QRectF(scene_center.x() - 60, scene_center.y() + height/2 + 10, 120, 30)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{int(width)}×{int(height)}px")
        
        painter.setOpacity(1.0)
    
    def set_preview_visible(self, visible: bool):
        """Define se o preview deve ser exibido"""
        self._show_preview = visible
        self.scene.update()
        
        if visible:
            # Resetar timer quando preview é mostrado
            self._preview_timer.stop()
        else:
            # Iniciar timer de 1 segundo para esconder
            self._preview_timer.start(1000)
    
    def _hide_preview_timeout(self):
        """Esconde preview após timeout"""
        self._show_preview = False
        self.scene.update()
    
    def _show_preview_with_timeout(self):
        """Mostra preview e inicia timer"""
        self._show_preview = True
        self.scene.update()
        self._preview_timer.stop()
        self._preview_timer.start(1000)
    
    def set_points(self, points: List[Point]):
        """Define os pontos a serem exibidos"""
        self.points = points
        self.scene.update()
    
    def set_point_manager(self, point_manager):
        """Define o point_manager para sincronizar tamanhos"""
        self.point_manager = point_manager
    
    def _get_current_point_size(self):
        """Obtém o tamanho atual do ponto do PointManager"""
        if self.point_manager:
            return self.point_manager.current_size
        else:
            return 20
    
    def _get_current_point_width(self):
        """Obtém a largura atual do retângulo do PointManager"""
        if self.point_manager:
            return self.point_manager.current_width
        else:
            return 20
    
    def _get_current_point_height(self):
        """Obtém a altura atual do retângulo do PointManager"""
        if self.point_manager:
            return self.point_manager.current_height
        else:
            return 20
    
    def _get_current_point_shape(self):
        """Obtém a forma atual do ponto do PointManager"""
        if self.point_manager:
            return self.point_manager.current_shape
        else:
            return 'circle'
    
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
    
    # === ZOOM E NAVEGAÇÃO COM MODIFICADORES ===
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom com roda do mouse E ajustes de tamanho com modificadores"""
        if not self.has_image():
            return
        
        modifiers = QApplication.keyboardModifiers()
        delta = event.angleDelta().y()
        
        # SHIFT + Roda = Ajusta tamanho do ponto (círculo) ou largura (retângulo)
        if modifiers == Qt.KeyboardModifier.ShiftModifier and self._points_mode:
            if delta > 0:
                self._adjust_point_size(increase=True)
            else:
                self._adjust_point_size(increase=False)
            event.accept()
            return
        
        # CTRL + Roda = Ajusta LARGURA do retângulo
        if modifiers == Qt.KeyboardModifier.ControlModifier and self._points_mode:
            if self._get_current_point_shape() == 'rectangle':
                if delta > 0:
                    self._adjust_rectangle_width(increase=True)
                else:
                    self._adjust_rectangle_width(increase=False)
            event.accept()
            return
        
        # ALT + Roda = Ajusta ALTURA do retângulo
        if modifiers == Qt.KeyboardModifier.AltModifier and self._points_mode:
            if self._get_current_point_shape() == 'rectangle':
                if delta > 0:
                    self._adjust_rectangle_height(increase=True)
                else:
                    self._adjust_rectangle_height(increase=False)
            event.accept()
            return
        
        # SEM MODIFICADOR = Zoom normal
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()
    
    def _adjust_point_size(self, increase: bool):
        """Ajusta tamanho do ponto (círculo ou largura do retângulo)"""
        if not self.point_manager:
            return
        
        shape = self._get_current_point_shape()
        
        if shape == 'circle':
            if increase and self.point_manager.current_size < 200:
                self.point_manager.current_size += 5
            elif not increase and self.point_manager.current_size > 10:
                self.point_manager.current_size -= 5
        
        elif shape == 'rectangle':
            if increase and self.point_manager.current_width < 200:
                self.point_manager.current_width += 5
            elif not increase and self.point_manager.current_width > 10:
                self.point_manager.current_width -= 5
        
        self.update_cursor()
        self._show_preview_with_timeout()
    
    def _adjust_rectangle_width(self, increase: bool):
        """Ajusta largura do retângulo"""
        if not self.point_manager:
            return
        
        if increase and self.point_manager.current_width < 200:
            self.point_manager.current_width += 5
        elif not increase and self.point_manager.current_width > 10:
            self.point_manager.current_width -= 5
        
        self.update_cursor()
        self._show_preview_with_timeout()
    
    def _adjust_rectangle_height(self, increase: bool):
        """Ajusta altura do retângulo"""
        if not self.point_manager:
            return
        
        if increase and self.point_manager.current_height < 200:
            self.point_manager.current_height += 5
        elif not increase and self.point_manager.current_height > 10:
            self.point_manager.current_height -= 5
        
        self.update_cursor()
        self._show_preview_with_timeout()
    
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
    
    def actual_size(self):
        """Tamanho real (100%)"""
        self.zoom_factor = 1.0
        self._apply_zoom()
    
    def get_current_scale(self) -> float:
        return self.zoom_factor
    
    # === ATALHOS DE TECLADO ===
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle teclas W/S/A/D para ajuste de dimensões"""
        if self._points_mode:
            shape = self._get_current_point_shape()
            
            # W = Aumentar largura (retângulo) ou diâmetro (círculo)
            if event.key() == Qt.Key.Key_W:
                self._adjust_point_size(increase=True)
                event.accept()
                return
            
            # S = Diminuir largura (retângulo) ou diâmetro (círculo)
            elif event.key() == Qt.Key.Key_S:
                self._adjust_point_size(increase=False)
                event.accept()
                return
            
            # D = Aumentar altura (retângulo apenas)
            elif event.key() == Qt.Key.Key_D and shape == 'rectangle':
                self._adjust_rectangle_height(increase=True)
                event.accept()
                return
            
            # A = Diminuir altura (retângulo apenas)
            elif event.key() == Qt.Key.Key_A and shape == 'rectangle':
                self._adjust_rectangle_height(increase=False)
                event.accept()
                return
        
        # ESC = Cancelar recorte
        if event.key() == Qt.Key.Key_Escape and self._crop_mode:
            self.set_crop_mode(False)
            event.accept()
            return
        
        super().keyPressEvent(event)
    
    # === CONTROLE DE MOUSE ===
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._crop_mode:
                scene_pos = self.mapToScene(event.pos())
                self._crop_start = scene_pos
                self._crop_end = scene_pos
                self.crop_selection_started.emit(scene_pos)
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
        """Handle mouse move"""
        scene_pos = self.mapToScene(event.pos())
        self.mouse_position_changed.emit(scene_pos)
        
        if self._is_panning:
            delta = event.pos() - self._last_pan_point
            self._last_pan_point = event.pos()
            
            h_scroll = self.horizontalScrollBar()
            v_scroll = self.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() - delta.x())
            v_scroll.setValue(v_scroll.value() - delta.y())
            
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
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_panning:
                self._is_panning = False
                if self._points_mode:
                    self._set_point_cursor()
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    
            elif self._points_mode and not self._drag_start_pos.isNull():
                move_distance = (event.pos() - self._drag_start_pos).manhattanLength()
                if move_distance <= self._drag_threshold:
                    scene_pos = self.mapToScene(event.pos())
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
    
    # === MODOS DE INTERAÇÃO ===
    
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
        else:
            self._set_point_cursor() if self._points_mode else self.setCursor(Qt.CursorShape.ArrowCursor)
            self._crop_start = QPointF()
            self._crop_end = QPointF()
            self.scene.update()

    def set_points_mode(self, enabled: bool, shape_type: str = None):
        """Ativa/desativa modo de marcação de pontos"""
        self._points_mode = enabled
        if shape_type:
            self._current_point_shape = shape_type
            
        if enabled:
            self._set_point_cursor()
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._show_preview = False
            self._preview_timer.stop()
            self.scene.update()
    
    def update_cursor(self):
        """Atualiza o cursor baseado no modo e tamanho atual"""
        if self._points_mode:
            self._set_point_cursor()
    
    def _set_point_cursor(self):
        """Define cursor personalizado baseado na forma atual"""
        shape = self._get_current_point_shape()
        if shape == 'circle':
            self.setCursor(self._create_circle_cursor())
        elif shape == 'rectangle':
            self.setCursor(self._create_rectangle_cursor())
    
    def _create_circle_cursor(self):
        """Cria cursor personalizado para círculo"""
        size = self._get_current_point_size()
        size = int(size * self.zoom_factor)
        cursor_size = max(24, int(size * 1.5))
                          
        pixmap = QPixmap(cursor_size, cursor_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        
        center = cursor_size // 2
        radius = size // 2
        painter.drawEllipse(center - radius, center - radius, size, size)
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawLine(center, center - radius - 2, center, center + radius + 2)
        painter.drawLine(center - radius - 2, center, center + radius + 2, center)
        
        painter.end()
        
        return QCursor(pixmap, center, center)

    def _create_rectangle_cursor(self):
        """Cria cursor personalizado para retângulo"""
        width = int(self._get_current_point_width() * self.zoom_factor)
        height = int(self._get_current_point_height() * self.zoom_factor)
        
        cursor_size = max(max(width, height) + 20, 24)
        
        pixmap = QPixmap(cursor_size, cursor_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        
        center = cursor_size // 2
        rect_x = center - width // 2
        rect_y = center - height // 2
        painter.drawRect(rect_x, rect_y, width, height)
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawLine(center, rect_y - 2, center, rect_y + height + 2)
        painter.drawLine(rect_x - 2, center, rect_x + width + 2, center)
        
        painter.end()
        
        return QCursor(pixmap, center, center)
    
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