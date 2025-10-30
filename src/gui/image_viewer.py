"""
Visualizador de imagem com suporte a pontos, preview timeout e cores dinâmicas
Versão atualizada com sistema de preview com timeout de 1 segundo
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, 
                            QGraphicsScene, QGraphicsPixmapItem, QGraphicsEllipseItem,
                            QGraphicsRectItem, QApplication, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer
from PyQt6.QtGui import (QPixmap, QPainter, QColor, QPen, QBrush, QCursor, 
                        QFont, QTransform, QPainterPath, QPolygonF)
import math


class ImageViewer(QGraphicsView):
    """Visualizador de imagem com suporte a pontos e preview"""
    
    # Sinais emitidos
    zoom_changed = pyqtSignal(float)
    mouse_position_changed = pyqtSignal(QPointF)
    point_clicked = pyqtSignal(QPointF)
    crop_selection_finished = pyqtSignal(QRectF)
    point_context_menu = pyqtSignal(object, QPointF)  # ponto, posição global
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ========== CONFIGURAÇÃO BÁSICA ==========
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configurações da view
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # ========== ELEMENTOS GRÁFICOS ==========
        self.pixmap_item = None
        self.points_items = []  # Lista de items gráficos dos pontos
        
        # ========== SISTEMA DE MODOS ==========
        self._points_mode = False
        self._crop_mode = False
        self._edit_mode = False
        
        # ========== SISTEMA DE PREVIEW COM TIMEOUT ==========
        self._show_preview = False
        self._preview_item = None
        
        # Timer para esconder preview automaticamente
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._hide_preview_timeout)
        
        # ========== CONFIGURAÇÕES DE DESENHO ==========
        self.point_manager = None
        self.current_shape = 'circle'
        self.current_size = 20
        self.tolerance = 5.0
        
        # Cores dos pontos
        self.point_colors = {
            'normal': QColor(255, 0, 0, 150),        # Vermelho semi-transparente
            'selected': QColor(255, 255, 0, 180),    # Amarelo mais opaco
            'diferenca': QColor(255, 105, 180, 170), # Rosa (HotPink)
            'verde': QColor(0, 255, 0, 150),         # Verde
            'sem_medicao': QColor(128, 128, 128, 120) # Cinza
        }
        
        # ========== CONFIGURAÇÕES DE ZOOM ==========
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        
        # ========== SISTEMA DE RECORTE ==========
        self.crop_start_point = None
        self.crop_rect_item = None
        
        # ========== CONFIGURAR SINAIS ==========
        self.setMouseTracking(True)  # Para capturar movimento do mouse
        
        print("🖼️ ImageViewer inicializado")
        
    # ========== CONFIGURAÇÃO ==========
    
    def set_point_manager(self, point_manager):
        """Define o gerenciador de pontos"""
        self.point_manager = point_manager
        if point_manager:
            # Conectar sinais do point manager
            if hasattr(point_manager, 'points_changed'):
                point_manager.points_changed.connect(self.update_points_display)
            print("🔗 PointManager conectado ao ImageViewer")
        
    def set_pixmap(self, pixmap):
        """Define imagem a ser exibida"""
        if self.pixmap_item:
            self.scene.removeItem(self.pixmap_item)
            
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        
        # Ajustar cena ao tamanho da imagem - CORREÇÃO AQUI
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        
        # Ajustar zoom inicial
        self.fit_to_view()
        
        print(f"🖼️ Imagem carregada: {pixmap.width()}x{pixmap.height()}")

        
    # ========== SISTEMA DE MODOS ==========
    
    def set_points_mode(self, enabled, shape='circle'):
        """Ativa/desativa modo de marcação de pontos"""
        self._points_mode = enabled
        self.current_shape = shape
        
        if enabled:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            
        self.update_cursor()
        print(f"🎯 Modo pontos: {'ATIVO' if enabled else 'INATIVO'} - {shape}")
        
    def set_crop_mode(self, enabled):
        """Ativa/desativa modo de recorte"""
        self._crop_mode = enabled
        
        if enabled:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            # Limpar seleção de recorte
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
                self.crop_rect_item = None
                
        print(f"✂️ Modo recorte: {'ATIVO' if enabled else 'INATIVO'}")
        
    def update_cursor(self):
        """Atualiza cursor baseado no modo atual"""
        if self._crop_mode:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self._points_mode:
            # Cursor personalizado para modo pontos
            if hasattr(self, 'point_manager') and self.point_manager:
                if self.point_manager.edit_mode:
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
                else:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
    # ========== SISTEMA DE PREVIEW COM TIMEOUT ==========
    
    def set_preview_visible(self, visible):
        """Controla visibilidade do preview"""
        self._show_preview = visible
        if visible:
            self._show_preview_cursor()
        else:
            self._hide_preview_cursor()
            
    def show_preview_with_timeout(self):
        """Mostra preview e agenda esconder após 1 segundo"""
        self.set_preview_visible(True)
        self.preview_timer.start(1000)  # 1 segundo
        print("🎚️ Preview mostrado com timeout de 1 segundo")
        
    def _hide_preview_timeout(self):
        """Callback para esconder preview após timeout"""
        self.set_preview_visible(False)
        print("🎚️ Preview escondido após timeout")
        
    def _show_preview_cursor(self):
        """Mostra preview do cursor com forma atual"""
        # Remover preview anterior
        self._hide_preview_cursor()
        
        # Obter posição atual do cursor na cena
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        scene_pos = self.mapToScene(cursor_pos)
        
        # Obter configurações atuais
        if self.point_manager:
            size = self.point_manager.current_size
            shape = self.point_manager.current_shape
            width = self.point_manager.current_width
            height = self.point_manager.current_height
        else:
            size = self.current_size
            shape = self.current_shape
            width = height = size
            
        # Criar item de preview
        color = QColor(255, 255, 255, 100)  # Branco semi-transparente
        pen = QPen(QColor(255, 255, 255, 200), 2, Qt.PenStyle.DashLine)
        
        if shape == 'circle':
            radius = size // 2
            self._preview_item = self.scene.addEllipse(
                scene_pos.x() - radius, scene_pos.y() - radius,
                size, size, pen, QBrush(color)
            )
        else:  # rectangle
            half_w = width // 2
            half_h = height // 2
            self._preview_item = self.scene.addRect(
                scene_pos.x() - half_w, scene_pos.y() - half_h,
                width, height, pen, QBrush(color)
            )
            
        # Garantir que preview fique no topo
        if self._preview_item:
            self._preview_item.setZValue(1000)
            
    def _hide_preview_cursor(self):
        """Remove preview do cursor"""
        if self._preview_item:
            self.scene.removeItem(self._preview_item)
            self._preview_item = None
            
    # ========== EXIBIÇÃO DE PONTOS ==========
    
    def set_points(self, points):
        """Define lista de pontos a serem exibidos"""
        self.update_points_display(points)
        
    def update_points_display(self, points):
        """Atualiza exibição dos pontos na cena"""
        # Remover pontos existentes
        for item in self.points_items:
            self.scene.removeItem(item)
        self.points_items.clear()
        
        # Adicionar novos pontos
        for point in points:
            self._add_point_to_scene(point)
            
        print(f"🎯 {len(points)} pontos atualizados na visualização")
        
    def _add_point_to_scene(self, point):
        """Adiciona um ponto à cena gráfica"""
        try:
            # Determinar cor baseada no status
            color = self._get_point_display_color(point)
            
            # Configurar pincel e caneta
            pen = QPen(color.darker(150), 2)
            brush = QBrush(color)
            
            # Criar item gráfico baseado na forma
            if point.shape == 'circle':
                radius = point.size // 2
                item = self.scene.addEllipse(
                    point.x - radius, point.y - radius,
                    point.size, point.size, pen, brush
                )
            else:  # rectangle
                half_w = point.width // 2
                half_h = point.height // 2
                item = self.scene.addRect(
                    point.x - half_w, point.y - half_h,
                    point.width, point.height, pen, brush
                )
            
            # Adicionar número do ponto
            text_item = self.scene.addText(str(point.id), QFont("Arial", 10, QFont.Weight.Bold))
            text_item.setDefaultTextColor(QColor(255, 255, 255))
            
            # Centralizar texto no ponto
            text_rect = text_item.boundingRect()
            text_item.setPos(
                point.x - text_rect.width() / 2,
                point.y - text_rect.height() / 2
            )
            
            # Adicionar fundo escuro para o texto
            bg_item = self.scene.addRect(
                text_item.x() - 2, text_item.y() - 1,
                text_rect.width() + 4, text_rect.height() + 2,
                QPen(QColor(0, 0, 0, 0)), QBrush(QColor(0, 0, 0, 150))
            )
            
            # Definir Z-order
            item.setZValue(100)
            bg_item.setZValue(101)
            text_item.setZValue(102)
            
            # Armazenar referências
            self.points_items.extend([item, bg_item, text_item])
            
            # Adicionar dados do ponto ao item (para detecção de clique)
            item.setData(0, point)  # Chave 0 = objeto point
            
        except Exception as e:
            print(f"⚠️  Erro ao adicionar ponto {getattr(point, 'id', '?')} à cena: {e}")
            
    def _get_point_display_color(self, point):
        """Determina cor de exibição do ponto"""
        # Verificar se está selecionado
        if (self.point_manager and self.point_manager.selected_point and 
            self.point_manager.selected_point.id == point.id):
            return self.point_colors['selected']
        
        # Determinar cor baseada no status das medições
        ref = getattr(point, 'medicao_referencia', None)
        comp = getattr(point, 'medicao_comparacao', None)
        
        if ref is not None and comp is not None:
            # Ambas as medições - calcular diferença
            if ref != 0:
                diff_percent = abs(((comp - ref) / ref) * 100)
                if diff_percent > self.tolerance:
                    return self.point_colors['diferenca']  # Rosa
                else:
                    return self.point_colors['verde']      # Verde
            else:
                return self.point_colors['normal']         # Vermelho (caso especial)
        elif ref is not None or comp is not None:
            return self.point_colors['normal']             # Vermelho (uma medição)
        else:
            return self.point_colors['sem_medicao']        # Cinza (sem medição)
            
    def set_tolerance(self, tolerance):
        """Define tolerância para coloração de pontos"""
        self.tolerance = tolerance
        # Atualizar cores se há pontos
        if self.point_manager:
            self.update_points_display(self.point_manager.points)
        print(f"📊 Tolerância de cores atualizada: {tolerance}%")
        
    # ========== CONTROLE DE ZOOM ==========
    
    def zoom_in(self):
        """Aumenta zoom"""
        if self.zoom_factor < self.max_zoom:
            scale_factor = 1.25
            self.scale(scale_factor, scale_factor)
            self.zoom_factor *= scale_factor
            self.zoom_changed.emit(self.zoom_factor)
            
    def zoom_out(self):
        """Diminui zoom"""
        if self.zoom_factor > self.min_zoom:
            scale_factor = 0.8
            self.scale(scale_factor, scale_factor)
            self.zoom_factor *= scale_factor
            self.zoom_changed.emit(self.zoom_factor)
            
    def fit_to_view(self):
        """Ajusta imagem à view"""
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom_factor = self.transform().m11()  # Obter fator de zoom atual
            self.zoom_changed.emit(self.zoom_factor)
            
    def actual_size(self):
        """Zoom 100% (tamanho real)"""
        if self.pixmap_item:
            self.resetTransform()
            self.zoom_factor = 1.0
            self.zoom_changed.emit(self.zoom_factor)
            
    # ========== EVENTOS DE MOUSE ==========
    
    def mousePressEvent(self, event):
        """Evento de pressionar botão do mouse"""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            
            if self._points_mode and self.point_manager:
                if self.point_manager.edit_mode:
                    # Modo edição - selecionar ponto
                    point = self._get_point_at_scene_pos(scene_pos)
                    if point:
                        self.point_manager.select_point(point)
                        self.update_points_display(self.point_manager.points)
                    else:
                        self.point_manager.deselect_point()
                        self.update_points_display(self.point_manager.points)
                else:
                    # Modo normal - adicionar ponto
                    self.point_clicked.emit(scene_pos)
                    
            elif self._crop_mode:
                # Iniciar seleção de recorte
                self.crop_start_point = scene_pos
                
        elif event.button() == Qt.MouseButton.RightButton:
            # Menu de contexto
            scene_pos = self.mapToScene(event.pos())
            point = self._get_point_at_scene_pos(scene_pos)
            if point:
                self._show_point_context_menu(point, event.globalPos())
                return
                
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Evento de movimento do mouse"""
        scene_pos = self.mapToScene(event.pos())
        self.mouse_position_changed.emit(scene_pos)
        
        # Atualizar preview se visível
        if self._show_preview and self._points_mode:
            self._hide_preview_cursor()
            self._show_preview_cursor()
            
        # Recorte
        if (self._crop_mode and self.crop_start_point and 
            event.buttons() & Qt.MouseButton.LeftButton):
            
            # Atualizar retângulo de seleção
            crop_rect = QRectF(self.crop_start_point, scene_pos).normalized()
            
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
                
            pen = QPen(QColor(255, 255, 0), 2, Qt.PenStyle.DashLine)
            brush = QBrush(QColor(255, 255, 0, 30))
            self.crop_rect_item = self.scene.addRect(crop_rect, pen, brush)
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Evento de soltar botão do mouse"""
        if (event.button() == Qt.MouseButton.LeftButton and 
            self._crop_mode and self.crop_start_point):
            
            scene_pos = self.mapToScene(event.pos())
            crop_rect = QRectF(self.crop_start_point, scene_pos).normalized()
            
            # Emitir sinal de recorte concluído
            self.crop_selection_finished.emit(crop_rect)
            
            # Limpar seleção
            self.crop_start_point = None
            
        super().mouseReleaseEvent(event)
        
    def wheelEvent(self, event):
        """Evento de scroll do mouse (zoom)"""
        # Zoom com roda do mouse
        delta = event.angleDelta().y()
        
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl + Scroll = Zoom
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        elif (event.modifiers() & Qt.KeyboardModifier.ShiftModifier and 
              self._points_mode and self.point_manager):
            # Shift + Scroll = Ajustar tamanho
            if self.point_manager.current_shape == 'circle':
                if delta > 0:
                    new_size = min(200, self.point_manager.current_size + 5)
                else:
                    new_size = max(10, self.point_manager.current_size - 5)
                self.point_manager.set_size(new_size)
                
                # Mostrar preview com timeout
                self.show_preview_with_timeout()
        else:
            super().wheelEvent(event)
            
    def keyPressEvent(self, event):
        """Evento de tecla pressionada"""
        if event.key() == Qt.Key.Key_Escape:
            if self._crop_mode:
                self.set_crop_mode(False)
            elif self._show_preview:
                self.set_preview_visible(False)
        else:
            super().keyPressEvent(event)
            
    # ========== MENU DE CONTEXTO ==========
    
    def _show_point_context_menu(self, point, global_pos):
        """Mostra menu de contexto para um ponto"""
        menu = QMenu(self)
        
        # Ação editar
        edit_action = menu.addAction("✏️ Editar")
        edit_action.triggered.connect(lambda: self._edit_point(point))
        
        # Ação deletar
        delete_action = menu.addAction("🗑️ Deletar")
        delete_action.triggered.connect(lambda: self._delete_point(point))
        
        # Separador
        menu.addSeparator()
        
        # Informações do ponto
        info_action = menu.addAction(f"📍 Ponto {point.id} ({point.x:.1f}, {point.y:.1f})")
        info_action.setEnabled(False)
        
        # Mostrar menu
        menu.exec(global_pos)
        
    def _edit_point(self, point):
        """Inicia edição de um ponto"""
        if self.point_manager:
            self.point_manager.set_edit_mode(True)
            self.point_manager.select_point(point)
            self.update_cursor()
            print(f"✏️ Iniciando edição do ponto {point.id}")
            
    def _delete_point(self, point):
        """Deleta um ponto"""
        if self.point_manager:
            self.point_manager.remove_point(point.id)
            print(f"🗑️ Ponto {point.id} deletado via menu contexto")
            
    def _get_point_at_scene_pos(self, scene_pos):
        """Encontra ponto na posição da cena"""
        if not self.point_manager:
            return None
            
        # Buscar ponto próximo à posição
        tolerance = 15  # pixels
        for point in self.point_manager.points:
            distance = math.sqrt((scene_pos.x() - point.x) ** 2 + 
                               (scene_pos.y() - point.y) ** 2)
            if distance <= tolerance:
                return point
        return None
        
    # ========== UTILITÁRIOS ==========
    
    def get_scene_rect(self):
        """Retorna retângulo da cena"""
        return self.scene.sceneRect()
        
    def get_image_size(self):
        """Retorna tamanho da imagem atual"""
        if self.pixmap_item:
            return self.pixmap_item.pixmap().size()
        return None
        
    def export_scene_to_image(self, target_size=None):
        """Exporta cena atual para QPixmap"""
        if not self.pixmap_item:
            return QPixmap()
            
        # Determinar tamanho
        scene_rect = self.scene.sceneRect()
        if target_size:
            pixmap = QPixmap(target_size)
        else:
            pixmap = QPixmap(scene_rect.size().toSize())
            
        pixmap.fill(Qt.GlobalColor.white)
        
        # Renderizar cena
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter)
        painter.end()
        
        return pixmap
        
    def clear_scene(self):
        """Limpa todos os elementos da cena"""
        self.scene.clear()
        self.pixmap_item = None
        self.points_items.clear()
        self._preview_item = None
        self.crop_rect_item = None
        print("🧹 Cena limpa")
