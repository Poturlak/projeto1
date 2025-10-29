from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QCheckBox, QLabel, QGroupBox, QSpinBox, QComboBox,
                            QListWidget, QMessageBox)
from PyQt6.QtGui import QIcon
from models.point import Point
from typing import List

class PointManager(QObject):
    point_added = pyqtSignal(Point)
    point_removed = pyqtSignal(int)
    point_updated = pyqtSignal(Point)
    points_changed = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.points: List[Point] = []
        self.next_id = 1
        self.current_shape = 'circle'
        self.current_size = 20
        self.image_viewer = None
    
    def set_image_viewer(self, image_viewer):
        """Conecta o PointManager ao ImageViewer"""
        self.image_viewer = image_viewer
        if image_viewer:
            image_viewer.set_point_manager(self)
    
    def add_point(self, position, description=""):
        if not description:
            description = f"Ponto {self.next_id}"
            
        # Garantir que o tamanho seja válido
        size = max(10, min(self.current_size, 100))  # Entre 10 e 100 pixels
        
        point = Point(
            id=self.next_id,
            position=position,
            shape=self.current_shape,
            description=description,
            size=size
        )
        self.points.append(point)
        self.next_id += 1
        self.point_added.emit(point)
        self.points_changed.emit(self.points)
        print(f"✅ Ponto {point.id} adicionado - Forma: {point.shape}, Tamanho: {point.size}px")
        return point
    
    def remove_point(self, point_id):
        self.points = [p for p in self.points if p.id != point_id]
        self.point_removed.emit(point_id)
        self.points_changed.emit(self.points)
        print(f"🗑️ Ponto {point_id} removido")
    
    def update_point_measurement(self, point_id, measurement_type, value):
        for point in self.points:
            if point.id == point_id:
                point.measurements[measurement_type] = value
                self.point_updated.emit(point)
                self.points_changed.emit(self.points)
                break
    
    def get_point_by_id(self, point_id):
        for point in self.points:
            if point.id == point_id:
                return point
        return None
    
    def clear_points(self):
        self.points.clear()
        self.next_id = 1
        self.points_changed.emit(self.points)
        print("🧹 Todos os pontos removidos")

class PointControlsWidget(QWidget):
    """Widget de controles para pontos - Interface gráfica"""
    
    def __init__(self, point_manager, image_viewer):
        super().__init__()
        self.point_manager = point_manager
        self.image_viewer = image_viewer
        self.point_manager.set_image_viewer(image_viewer)
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        layout = QVBoxLayout(self)
        
        # Grupo: Modo de Pontos
        mode_group = QGroupBox("Modo de Pontos")
        mode_layout = QVBoxLayout(mode_group)
        
        # Botões de forma
        shape_layout = QHBoxLayout()
        self.circle_btn = QPushButton("● Círculo")
        self.rectangle_btn = QPushButton("■ Quadrado")
        self.circle_btn.setCheckable(True)
        self.rectangle_btn.setCheckable(True)
        self.circle_btn.setChecked(True)
        
        shape_layout.addWidget(self.circle_btn)
        shape_layout.addWidget(self.rectangle_btn)
        mode_layout.addLayout(shape_layout)
        
        # Controles de desenho
        draw_layout = QHBoxLayout()
        self.draw_checkbox = QCheckBox("Modo Desenho")
        self.draw_checkbox.setToolTip("Arraste para definir tamanho do ponto")
        draw_layout.addWidget(self.draw_checkbox)
        mode_layout.addLayout(draw_layout)
        
        layout.addWidget(mode_group)
        
        # Grupo: Controles de Tamanho
        size_group = QGroupBox("Controles de Tamanho")
        size_layout = QVBoxLayout(size_group)
        
        # Tamanho atual
        size_info_layout = QHBoxLayout()
        size_info_layout.addWidget(QLabel("Tamanho atual:"))
        self.size_label = QLabel("20 px")
        size_info_layout.addWidget(self.size_label)
        size_info_layout.addStretch()
        size_layout.addLayout(size_info_layout)
        
        # Botões de ajuste de tamanho
        size_controls_layout = QHBoxLayout()
        self.decrease_btn = QPushButton("−")
        self.increase_btn = QPushButton("+")
        self.decrease_btn.setFixedWidth(40)
        self.increase_btn.setFixedWidth(40)
        
        size_controls_layout.addWidget(self.decrease_btn)
        size_controls_layout.addWidget(self.increase_btn)
        size_layout.addLayout(size_controls_layout)
        
        layout.addWidget(size_group)
        
        # Grupo: Gerenciamento de Pontos
        management_group = QGroupBox("Gerenciamento")
        management_layout = QVBoxLayout(management_group)
        
        # Botões de ação
        action_layout = QHBoxLayout()
        self.undo_btn = QPushButton("↶ Desfazer")
        self.delete_btn = QPushButton("🗑️ Deletar")
        
        action_layout.addWidget(self.undo_btn)
        action_layout.addWidget(self.delete_btn)
        management_layout.addLayout(action_layout)
        
        # Lista de pontos
        self.points_list = QListWidget()
        self.points_list.setMaximumHeight(150)
        management_layout.addWidget(QLabel("Pontos criados:"))
        management_layout.addWidget(self.points_list)
        
        layout.addWidget(management_group)
        
        layout.addStretch()
    
    def connect_signals(self):
        """Conecta os sinais dos controles"""
        # Botões de forma
        self.circle_btn.clicked.connect(self.set_circle_mode)
        self.rectangle_btn.clicked.connect(self.set_rectangle_mode)
        
        # Controles de desenho
        self.draw_checkbox.toggled.connect(self.toggle_draw_mode)
        
        # Controles de tamanho
        self.decrease_btn.clicked.connect(self.decrease_size)
        self.increase_btn.clicked.connect(self.increase_size)
        
        # Gerenciamento
        self.undo_btn.clicked.connect(self.undo_last_point)
        self.delete_btn.clicked.connect(self.delete_selected_point)
        
        # Sinais do PointManager
        self.point_manager.points_changed.connect(self.update_points_list)
        
        # Sinais do ImageViewer
        if self.image_viewer:
            self.image_viewer.point_clicked.connect(self.on_point_clicked)
    
    def set_circle_mode(self):
        """Ativa modo círculo"""
        self.circle_btn.setChecked(True)
        self.rectangle_btn.setChecked(False)
        self.point_manager.current_shape = 'circle'
        
        if self.image_viewer:
            self.image_viewer.set_points_mode(True, 'circle')
            self.update_draw_mode()
        
        print("Modo círculo ativado")
    
    def set_rectangle_mode(self):
        """Ativa modo quadrado"""
        self.rectangle_btn.setChecked(True)
        self.circle_btn.setChecked(False)
        self.point_manager.current_shape = 'rectangle'
        
        if self.image_viewer:
            self.image_viewer.set_points_mode(True, 'rectangle')
            self.update_draw_mode()
        
        print("Modo quadrado ativado")
    
    def toggle_draw_mode(self, enabled):
        """Ativa/desativa modo desenho"""
        if self.image_viewer:
            current_shape = self.point_manager.current_shape
            self.image_viewer.set_draw_point_mode(enabled, current_shape)
        
        if enabled:
            print(f"Modo desenho ativado para {self.point_manager.current_shape}")
        else:
            print(f"Modo desenho desativado")
    
    def update_draw_mode(self):
        """Atualiza estado do modo desenho quando muda a forma"""
        if self.image_viewer and self.draw_checkbox.isChecked():
            current_shape = self.point_manager.current_shape
            self.image_viewer.set_draw_point_mode(True, current_shape)
    
    def increase_size(self):
        """Aumenta tamanho do ponto"""
        if self.image_viewer:
            self.image_viewer.increase_point_size()
            self.update_size_display()
    
    def decrease_size(self):
        """Diminui tamanho do ponto"""
        if self.image_viewer:
            self.image_viewer.decrease_point_size()
            self.update_size_display()
    
    def update_size_display(self):
        """Atualiza exibição do tamanho atual"""
        if self.image_viewer:
            current_size = self.image_viewer._get_current_point_size()
            self.size_label.setText(f"{current_size:.0f} px")
    
    def undo_last_point(self):
        """Remove o último ponto criado"""
        if self.image_viewer:
            self.image_viewer.undo_last_point()
    
    def delete_selected_point(self):
        """Deleta ponto selecionado na lista"""
        selected_items = self.points_list.selectedItems()
        if selected_items:
            point_id = int(selected_items[0].text().split(":")[0])
            if self.image_viewer:
                self.image_viewer.delete_point_by_id(point_id)
        else:
            QMessageBox.information(self, "Selecionar Ponto", 
                                  "Selecione um ponto na lista para deletar.")
    
    def on_point_clicked(self, position):
        """Handle clique em ponto na imagem"""
        print(f"Ponto clicado na posição: {position.x():.1f}, {position.y():.1f}")
        # Aqui pode-se implementar seleção de ponto na imagem
    
    def update_points_list(self, points):
        """Atualiza lista de pontos"""
        self.points_list.clear()
        for point in points:
            item_text = f"{point.id}: {point.shape} ({point.size:.0f}px)"
            self.points_list.addItem(item_text)
        
        self.update_size_display()
    
    def get_current_shape(self):
        """Retorna forma atual"""
        return self.point_manager.current_shape
    
    def get_current_size(self):
        """Retorna tamanho atual"""
        return self.point_manager.current_size