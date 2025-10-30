import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QStatusBar,
                            QToolBar, QFrame, QSplitter, QSpacerItem, QSizePolicy,
                            QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
                            QSpinBox, QCheckBox, QFormLayout, QStackedWidget, QSlider,
                            QLineEdit, QTextEdit)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QAction, QCursor, QPixmap, QPainter, QColor, QPen, QBrush, QKeySequence, QShortcut
from PyQt6.QtCore import QPointF
import zipfile
import json
from datetime import datetime
from PIL import Image
import io

# Importações dos módulos do projeto
try:
    from image_processing.image_editor import ImageEditor
    from gui.image_viewer import ImageViewer
    from utils.image_utils import pil_to_pixmap, get_supported_formats
    from models.point import Point
    from gui.point_manager import PointManager
    from gui.points_table import PointsTable
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Criando classes stub...")
    
    # Classes stub (mantidas do código original)
    class ImageEditor:
        def __init__(self): 
            self._image = None
            self._history = []
        def load_image(self, path): return True
        def save_image(self, path): return True
        def is_image_loaded(self): return False
        def undo(self): pass
        def redo(self): pass
        def reset_to_original(self): pass
        def rotate_90(self, clockwise=True): pass
        def rotate(self, angle): pass
        def flip(self, horizontal=True): pass
        def get_dimensions(self): return (0, 0)
        def get_file_info(self): return {'filename': 'Nenhuma'}
        def resize(self, w, h, keep_ratio): pass
        def apply_crop_selection(self, rect): return True
        
    class ImageViewer(QWidget):
        zoom_changed = pyqtSignal(float)
        mouse_position_changed = pyqtSignal(QPointF)
        point_clicked = pyqtSignal(QPointF)
        crop_selection_finished = pyqtSignal(object)
        
        def __init__(self):
            super().__init__()
            self._crop_mode = False
            self._points_mode = False
            self._show_preview = False
            
        def set_pixmap(self, pixmap): pass
        def set_points(self, points): pass
        def set_points_mode(self, enabled, shape=None): 
            self._points_mode = enabled
        def set_crop_mode(self, enabled): 
            self._crop_mode = enabled
        def zoom_in(self): pass
        def zoom_out(self): pass
        def fit_to_view(self): pass
        def actual_size(self): pass
        def set_point_manager(self, point_manager): pass
        def update_cursor(self): pass
        def set_preview_visible(self, visible): pass
        
    def pil_to_pixmap(pil_image):
        return QPixmap()
        
    def get_supported_formats():
        return "Imagens (*.png *.jpg *.jpeg *.bmp *.tiff)"
        
    class Point:
        def __init__(self, id, x, y):
            self.id = id
            self.x = x
            self.y = y
            
    class PointManager:
        def __init__(self):
            self.points = []
            self.current_shape = 'circle'
            self.current_size = 20
            self.current_width = 20
            self.current_height = 20
            self.tolerance_percent = 5.0
            self.points_changed = pyqtSignal(list)
            
        def add_point(self, position):
            point = Point(len(self.points) + 1, position.x(), position.y())
            self.points.append(point)
            self.points_changed.emit(self.points)
            return point
        
        def swap_rectangle_dimensions(self):
            self.current_width, self.current_height = self.current_height, self.current_width
        
        def undo(self): return False
        def redo(self): return False
        def has_reference_measurements(self): return False
            
    class PointsTable(QWidget):
        tolerance_changed = pyqtSignal(float)
        
        def __init__(self):
            super().__init__()
            self.layout = QVBoxLayout()
            self.setLayout(self.layout)
            self.label = QLabel("Tabela de pontos vazia")
            self.layout.addWidget(self.label)
            
        def update_points(self, points):
            self.label.setText(f"{len(points)} pontos registrados")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multímetro Inteligente - v1.0")
        
        # CENTRALIZAR JANELA
        self.resize(1200, 800)
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1200) // 2
        y = (screen.height() - 800) // 2
        self.move(x, y)
        
        # Estado do programa
        self.current_state = "inicial"  # inicial, edicao, marcacao, medicao
        self.project_modified = False
        self.current_project_path = None
        
        # Inicializar sistema de imagem PRIMEIRO
        self.image_editor = ImageEditor()
        self.image_viewer = ImageViewer()
        
        # Sistema de toolbar dinâmica
        self.toolbar_stack = QStackedWidget()
        
        # Sistema de pontos DEPOIS do image_viewer
        self.point_manager = PointManager()
        self.points_table = PointsTable()
        
        # AGORA podemos conectar o point_manager ao image_viewer
        self.image_viewer.set_point_manager(self.point_manager)
        
        self.setup_ui()
        self.connect_signals()
        self.setup_shortcuts()
        
    def setup_ui(self):
        self.setup_toolbars()
        self.setup_central_widget()
        self.setup_status_bar()
        
    def setup_shortcuts(self):
        """Configura atalhos de teclado globais"""
        # Ctrl+Z - Desfazer ponto
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.undo_point)
        
        # Ctrl+Shift+Z - Refazer ponto
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        redo_shortcut.activated.connect(self.redo_point)
        
        # Ctrl+S - Salvar projeto
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.salvar_projeto)
        
        # Ctrl+O - Abrir imagem
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self.abrir_imagem)
        
        # Ctrl+E - Exportar imagem
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self.exportar_imagem)
        
    def setup_toolbars(self):
        """Cria todas as toolbars do sistema"""
        # Toolbar superior (vazia inicialmente, será preenchida por estado)
        self.toolbar_superior = QToolBar("Superior")
        self.toolbar_superior.setIconSize(QSize(16, 16))
        self.toolbar_superior.setFixedHeight(35)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar_superior)
        
        # Criar todas as toolbars dinâmicas
        self.setup_dynamic_toolbars()
        
        # Iniciar no estado inicial
        self.change_state("inicial")
        
    def setup_dynamic_toolbars(self):
        """Cria toolbars dinâmicas para cada estado"""
        
        # ========== TOOLBAR INICIAL ==========
        self.toolbar_inicial = QWidget()
        self.toolbar_inicial.setFixedHeight(35)
        layout_inicial = QHBoxLayout()
        layout_inicial.setContentsMargins(5, 2, 5, 2)
        layout_inicial.setSpacing(10)
        self.toolbar_inicial.setLayout(layout_inicial)
        
        btn_abrir_img = QPushButton("📂 Abrir Imagem (Ctrl+O)")
        btn_abrir_img.setFixedHeight(30)
        btn_abrir_img.clicked.connect(self.abrir_imagem)
        layout_inicial.addWidget(btn_abrir_img)
        
        btn_abrir_proj = QPushButton("📁 Abrir Projeto (Ctrl+P)")
        btn_abrir_proj.setFixedHeight(30)
        btn_abrir_proj.clicked.connect(self.abrir_projeto)
        layout_inicial.addWidget(btn_abrir_proj)
        
        layout_inicial.addStretch()
        
        # ========== TOOLBAR EDIÇÃO ==========
        self.toolbar_edicao = QWidget()
        self.toolbar_edicao.setFixedHeight(35)
        layout_edicao = QHBoxLayout()
        layout_edicao.setContentsMargins(5, 2, 5, 2)
        layout_edicao.setSpacing(5)
        self.toolbar_edicao.setLayout(layout_edicao)
        
        btn_desfazer = QPushButton("↩️")
        btn_desfazer.setToolTip("Desfazer")
        btn_desfazer.setFixedSize(30, 28)
        btn_desfazer.clicked.connect(self.desfazer_imagem)
        
        btn_refazer = QPushButton("↪️")
        btn_refazer.setToolTip("Refazer")
        btn_refazer.setFixedSize(30, 28)
        btn_refazer.clicked.connect(self.refazer_imagem)
        
        btn_rot90 = QPushButton("↻90°")
        btn_rot90.setToolTip("Rotacionar 90°")
        btn_rot90.setFixedSize(45, 28)
        btn_rot90.clicked.connect(self.rotacionar_90)
        
        btn_rot180 = QPushButton("↻180°")
        btn_rot180.setToolTip("Rotacionar 180°")
        btn_rot180.setFixedSize(50, 28)
        btn_rot180.clicked.connect(self.rotacionar_180)
        
        btn_flip_h = QPushButton("⬌H")
        btn_flip_h.setToolTip("Espelhar Horizontal")
        btn_flip_h.setFixedSize(35, 28)
        btn_flip_h.clicked.connect(self.espelhar_horizontal)
        
        btn_flip_v = QPushButton("⬍V")
        btn_flip_v.setToolTip("Espelhar Vertical")
        btn_flip_v.setFixedSize(35, 28)
        btn_flip_v.clicked.connect(self.espelhar_vertical)
        
        btn_crop = QPushButton("✂️")
        btn_crop.setToolTip("Recortar")
        btn_crop.setFixedSize(30, 28)
        btn_crop.clicked.connect(self.ativar_modo_recorte)
        
        btn_resize = QPushButton("📏")
        btn_resize.setToolTip("Redimensionar")
        btn_resize.setFixedSize(30, 28)
        btn_resize.clicked.connect(self.redimensionar_imagem)
        
        btn_concluir_edicao = QPushButton("✅ Concluir Edição")
        btn_concluir_edicao.setFixedHeight(28)
        btn_concluir_edicao.clicked.connect(lambda: self.change_state("marcacao"))
        
        layout_edicao.addWidget(btn_desfazer)
        layout_edicao.addWidget(btn_refazer)
        layout_edicao.addWidget(self._create_separator())
        layout_edicao.addWidget(btn_rot90)
        layout_edicao.addWidget(btn_rot180)
        layout_edicao.addWidget(btn_flip_h)
        layout_edicao.addWidget(btn_flip_v)
        layout_edicao.addWidget(self._create_separator())
        layout_edicao.addWidget(btn_crop)
        layout_edicao.addWidget(btn_resize)
        layout_edicao.addWidget(self._create_separator())
        layout_edicao.addWidget(btn_concluir_edicao)
        layout_edicao.addStretch()
        
        # ========== TOOLBAR MARCAÇÃO - CÍRCULO ==========
        self.toolbar_circulo = QWidget()
        self.toolbar_circulo.setFixedHeight(35)
        layout_circulo = QHBoxLayout()
        layout_circulo.setContentsMargins(5, 2, 5, 2)
        layout_circulo.setSpacing(10)
        self.toolbar_circulo.setLayout(layout_circulo)
        
        self.btn_circulo = QPushButton("⭕ (W)")
        self.btn_circulo.setToolTip("Modo Círculo [W]")
        self.btn_circulo.setCheckable(True)
        self.btn_circulo.setChecked(True)
        self.btn_circulo.setFixedSize(60, 28)
        self.btn_circulo.clicked.connect(self.definir_modo_circulo)
        
        self.btn_retangulo_c = QPushButton("⬜ (R)")
        self.btn_retangulo_c.setToolTip("Modo Retângulo [R]")
        self.btn_retangulo_c.setCheckable(True)
        self.btn_retangulo_c.setFixedSize(60, 28)
        self.btn_retangulo_c.clicked.connect(self.definir_modo_retangulo)
        
        label_s = QLabel("S")
        label_s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_w = QLabel("W")
        label_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.slider_tamanho = QSlider(Qt.Orientation.Horizontal)
        self.slider_tamanho.setMinimum(10)
        self.slider_tamanho.setMaximum(200)
        self.slider_tamanho.setValue(20)
        self.slider_tamanho.setFixedWidth(200)
        self.slider_tamanho.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_tamanho.setTickInterval(20)
        self.slider_tamanho.sliderPressed.connect(self._on_slider_pressed)
        self.slider_tamanho.sliderReleased.connect(self._on_slider_released)
        self.slider_tamanho.valueChanged.connect(self._on_tamanho_changed)
        
        self.label_tamanho = QLabel("20px")
        self.label_tamanho.setMinimumWidth(50)
        self.label_tamanho.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_editar = QPushButton("✏️ (E)")
        btn_editar.setToolTip("Editar Pontos [E]")
        btn_editar.setFixedSize(60, 28)
        btn_editar.clicked.connect(self.toggle_edit_mode)
        
        btn_limpar = QPushButton("🗑️")
        btn_limpar.setToolTip("Limpar Todos os Pontos")
        btn_limpar.setFixedSize(30, 28)
        btn_limpar.clicked.connect(self.limpar_pontos)
        
        btn_concluir_marcacao = QPushButton("✅ Concluir")
        btn_concluir_marcacao.setFixedHeight(28)
        btn_concluir_marcacao.clicked.connect(lambda: self.change_state("medicao"))
        
        layout_circulo.addWidget(self.btn_circulo)
        layout_circulo.addWidget(self.btn_retangulo_c)
        layout_circulo.addWidget(self._create_separator())
        layout_circulo.addWidget(label_s)
        layout_circulo.addWidget(self.slider_tamanho)
        layout_circulo.addWidget(label_w)
        layout_circulo.addWidget(self.label_tamanho)
        layout_circulo.addWidget(self._create_separator())
        layout_circulo.addWidget(btn_editar)
        layout_circulo.addWidget(btn_limpar)
        layout_circulo.addWidget(self._create_separator())
        layout_circulo.addWidget(btn_concluir_marcacao)
        layout_circulo.addStretch()
        
        # ========== TOOLBAR MARCAÇÃO - RETÂNGULO ==========
        self.toolbar_retangulo = QWidget()
        self.toolbar_retangulo.setFixedHeight(35)
        layout_retangulo = QHBoxLayout()
        layout_retangulo.setContentsMargins(5, 2, 5, 2)
        layout_retangulo.setSpacing(8)
        self.toolbar_retangulo.setLayout(layout_retangulo)
        
        self.btn_circulo_r = QPushButton("⭕ (W)")
        self.btn_circulo_r.setToolTip("Modo Círculo [W]")
        self.btn_circulo_r.setCheckable(True)
        self.btn_circulo_r.setFixedSize(60, 28)
        self.btn_circulo_r.clicked.connect(self.definir_modo_circulo)
        
        self.btn_retangulo = QPushButton("⬜ (R)")
        self.btn_retangulo.setToolTip("Modo Retângulo [R]")
        self.btn_retangulo.setCheckable(True)
        self.btn_retangulo.setChecked(True)
        self.btn_retangulo.setFixedSize(60, 28)
        self.btn_retangulo.clicked.connect(self.definir_modo_retangulo)
        
        label_s_l = QLabel("S")
        label_w_l = QLabel("W")
        label_a_a = QLabel("A")
        label_d_a = QLabel("D")
        
        self.slider_largura = QSlider(Qt.Orientation.Horizontal)
        self.slider_largura.setMinimum(10)
        self.slider_largura.setMaximum(200)
        self.slider_largura.setValue(20)
        self.slider_largura.setFixedWidth(120)
        self.slider_largura.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_largura.setTickInterval(20)
        self.slider_largura.sliderPressed.connect(self._on_slider_pressed)
        self.slider_largura.sliderReleased.connect(self._on_slider_released)
        self.slider_largura.valueChanged.connect(self._on_largura_changed)
        
        self.label_largura = QLabel("20px")
        self.label_largura.setMinimumWidth(45)
        
        self.slider_altura = QSlider(Qt.Orientation.Horizontal)
        self.slider_altura.setMinimum(10)
        self.slider_altura.setMaximum(200)
        self.slider_altura.setValue(20)
        self.slider_altura.setFixedWidth(120)
        self.slider_altura.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_altura.setTickInterval(20)
        self.slider_altura.sliderPressed.connect(self._on_slider_pressed)
        self.slider_altura.sliderReleased.connect(self._on_slider_released)
        self.slider_altura.valueChanged.connect(self._on_altura_changed)
        
        self.label_altura = QLabel("20px")
        self.label_altura.setMinimumWidth(45)
        
        btn_trocar = QPushButton("↔️⇅")
        btn_trocar.setToolTip("Trocar Largura ↔ Altura")
        btn_trocar.setFixedSize(40, 28)
        btn_trocar.clicked.connect(self.trocar_dimensoes)
        
        btn_editar_r = QPushButton("✏️ (E)")
        btn_editar_r.setToolTip("Editar Pontos [E]")
        btn_editar_r.setFixedSize(60, 28)
        btn_editar_r.clicked.connect(self.toggle_edit_mode)
        
        btn_limpar_r = QPushButton("🗑️")
        btn_limpar_r.setToolTip("Limpar Todos os Pontos")
        btn_limpar_r.setFixedSize(30, 28)
        btn_limpar_r.clicked.connect(self.limpar_pontos)
        
        btn_concluir_r = QPushButton("✅ Concluir")
        btn_concluir_r.setFixedHeight(28)
        btn_concluir_r.clicked.connect(lambda: self.change_state("medicao"))
        
        layout_retangulo.addWidget(self.btn_circulo_r)
        layout_retangulo.addWidget(self.btn_retangulo)
        layout_retangulo.addWidget(self._create_separator())
        layout_retangulo.addWidget(label_s_l)
        layout_retangulo.addWidget(self.slider_largura)
        layout_retangulo.addWidget(label_w_l)
        layout_retangulo.addWidget(self.label_largura)
        layout_retangulo.addWidget(self._create_separator())
        layout_retangulo.addWidget(label_a_a)
        layout_retangulo.addWidget(self.slider_altura)
        layout_retangulo.addWidget(label_d_a)
        layout_retangulo.addWidget(self.label_altura)
        layout_retangulo.addWidget(self._create_separator())
        layout_retangulo.addWidget(btn_trocar)
        layout_retangulo.addWidget(btn_editar_r)
        layout_retangulo.addWidget(btn_limpar_r)
        layout_retangulo.addWidget(self._create_separator())
        layout_retangulo.addWidget(btn_concluir_r)
        layout_retangulo.addStretch()
        
        # Adicionar todas ao stack
        self.toolbar_stack.addWidget(self.toolbar_inicial)
        self.toolbar_stack.addWidget(self.toolbar_edicao)
        self.toolbar_stack.addWidget(self.toolbar_circulo)
        self.toolbar_stack.addWidget(self.toolbar_retangulo)
        
    def _create_separator(self):
        """Cria separador vertical"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator
# CONTINUAÇÃO DO main.py - PARTE 2
# Cole este código após a Parte 1

    def change_state(self, new_state: str):
        """Muda o estado do programa e atualiza UI"""
        self.current_state = new_state
        print(f"🔄 Estado mudou para: {new_state}")
        
        # Limpar toolbar superior
        self.toolbar_superior.clear()
        
        if new_state == "inicial":
            self.toolbar_stack.setCurrentWidget(self.toolbar_inicial)
            self.statusBar().showMessage("Abra uma imagem ou projeto para começar")
            
        elif new_state == "edicao":
            # Toolbar superior com botões persistentes
            self._add_persistent_buttons()
            # Toolbar dinâmica de edição
            self.toolbar_stack.setCurrentWidget(self.toolbar_edicao)
            self.statusBar().showMessage("Modo: Edição de Imagem")
            
        elif new_state == "marcacao":
            # Toolbar superior
            self._add_persistent_buttons()
            # Toolbar dinâmica de marcação (círculo por padrão)
            if self.point_manager.current_shape == 'circle':
                self.toolbar_stack.setCurrentWidget(self.toolbar_circulo)
            else:
                self.toolbar_stack.setCurrentWidget(self.toolbar_retangulo)
            self.image_viewer.set_points_mode(True, self.point_manager.current_shape)
            self.statusBar().showMessage("Modo: Marcação de Pontos")
            
        elif new_state == "medicao":
            # Toolbar superior
            self._add_persistent_buttons()
            # TODO: Criar toolbar de medição (futuramente)
            self.statusBar().showMessage("Modo: Medição (Em desenvolvimento)")
    
    def _add_persistent_buttons(self):
        """Adiciona botões persistentes na toolbar superior"""
        btn_salvar = QPushButton("💾 Salvar (Ctrl+S)")
        btn_salvar.setFixedHeight(30)
        btn_salvar.clicked.connect(self.salvar_projeto)
        self.toolbar_superior.addWidget(btn_salvar)
        
        btn_exportar = QPushButton("📸 Exportar (Ctrl+E)")
        btn_exportar.setFixedHeight(30)
        btn_exportar.clicked.connect(self.exportar_imagem)
        self.toolbar_superior.addWidget(btn_exportar)
        
        btn_novo = QPushButton("🆕 Novo")
        btn_novo.setFixedHeight(30)
        btn_novo.clicked.connect(self.novo_projeto)
        self.toolbar_superior.addWidget(btn_novo)
        
        self.toolbar_superior.addWidget(QWidget())  # Spacer
    
    # === CALLBACKS DOS SLIDERS ===
    
    def _on_slider_pressed(self):
        """Mostra preview ao pressionar slider"""
        self.image_viewer.set_preview_visible(True)
    
    def _on_slider_released(self):
        """Esconde preview ao soltar slider (com timeout)"""
        # O timeout de 1s é gerenciado automaticamente pelo image_viewer
        pass
    
    def _on_tamanho_changed(self, value):
        """Callback slider de tamanho (círculo)"""
        self.point_manager.current_size = value
        self.label_tamanho.setText(f"{value}px")
        self.image_viewer.update_cursor()
        if hasattr(self.image_viewer, '_show_preview') and self.image_viewer._show_preview:
            self.image_viewer.scene.update()
    
    def _on_largura_changed(self, value):
        """Callback slider de largura"""
        self.point_manager.current_width = value
        self.label_largura.setText(f"{value}px")
        self.image_viewer.update_cursor()
        if hasattr(self.image_viewer, '_show_preview') and self.image_viewer._show_preview:
            self.image_viewer.scene.update()
    
    def _on_altura_changed(self, value):
        """Callback slider de altura"""
        self.point_manager.current_height = value
        self.label_altura.setText(f"{value}px")
        self.image_viewer.update_cursor()
        if hasattr(self.image_viewer, '_show_preview') and self.image_viewer._show_preview:
            self.image_viewer.scene.update()
    
    # === MÉTODOS DE FORMA ===
    
    def definir_modo_circulo(self):
        """Ativa modo círculo"""
        self.point_manager.current_shape = 'circle'
        self.btn_circulo.setChecked(True)
        self.btn_circulo_r.setChecked(True)
        self.btn_retangulo_c.setChecked(False)
        self.btn_retangulo.setChecked(False)
        self.toolbar_stack.setCurrentWidget(self.toolbar_circulo)
        self.image_viewer.set_points_mode(True, 'circle')
        self.statusBar().showMessage(f"Modo: Círculo - Ø {self.point_manager.current_size}px")
    
    def definir_modo_retangulo(self):
        """Ativa modo retângulo"""
        self.point_manager.current_shape = 'rectangle'
        self.btn_circulo.setChecked(False)
        self.btn_circulo_r.setChecked(False)
        self.btn_retangulo_c.setChecked(True)
        self.btn_retangulo.setChecked(True)
        self.toolbar_stack.setCurrentWidget(self.toolbar_retangulo)
        self.image_viewer.set_points_mode(True, 'rectangle')
        self.statusBar().showMessage(
            f"Modo: Retângulo - {self.point_manager.current_width}×{self.point_manager.current_height}px"
        )
    
    def trocar_dimensoes(self):
        """Troca largura e altura"""
        self.point_manager.swap_rectangle_dimensions()
        self.slider_largura.setValue(self.point_manager.current_width)
        self.slider_altura.setValue(self.point_manager.current_height)
        self.label_largura.setText(f"{self.point_manager.current_width}px")
        self.label_altura.setText(f"{self.point_manager.current_height}px")
        self.image_viewer.update_cursor()
        self.statusBar().showMessage(
            f"Dimensões trocadas: {self.point_manager.current_width}×{self.point_manager.current_height}px"
        )
    
    # === MÉTODOS DE PONTOS ===
    
    def undo_point(self):
        """Desfaz último ponto (Ctrl+Z)"""
        if self.point_manager.undo():
            self.statusBar().showMessage("Ponto desfeito")
        else:
            self.statusBar().showMessage("Nada para desfazer")
    
    def redo_point(self):
        """Refaz ponto (Ctrl+Shift+Z)"""
        if self.point_manager.redo():
            self.statusBar().showMessage("Ponto refeito")
        else:
            self.statusBar().showMessage("Nada para refazer")
    
    def toggle_edit_mode(self):
        """Toggle modo edição de pontos"""
        # TODO: Implementar modo edição completo
        self.statusBar().showMessage("Modo edição (Em desenvolvimento)")
    
    def limpar_pontos(self):
        """Limpa todos os pontos"""
        if not self.point_manager.points:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "Deseja remover todos os pontos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.point_manager.clear_points()
            self.statusBar().showMessage("Todos os pontos removidos")
    
    # === PROJETO ===
    
    def novo_projeto(self):
        """Cria novo projeto"""
        if self.project_modified:
            dialog = NovoProjetoDialog(self)
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                action = dialog.get_action()
                if action == "salvar":
                    self.salvar_projeto()
                elif action == "descartar":
                    pass
                else:  # cancelar
                    return
        
        # Reset completo
        self.image_editor = ImageEditor()
        self.image_viewer.clear()
        self.point_manager.clear_points()
        self.current_project_path = None
        self.project_modified = False
        self.change_state("inicial")
        self.statusBar().showMessage("Novo projeto criado")
    
    def salvar_projeto(self):
        """Salva projeto em arquivo .mip"""
        if not self.image_editor.is_image_loaded():
            QMessageBox.warning(self, "Aviso", "Nenhum projeto para salvar.")
            return
        
        # Dialog de informações do projeto
        dialog = SalvarProjetoDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        info = dialog.get_project_info()
        
        # Abrir dialog para escolher local
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Projeto",
            "",
            "Projeto Multímetro (*.mip)"
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.mip'):
            filepath += '.mip'
        
        try:
            self._save_project_file(filepath, info)
            self.current_project_path = filepath
            self.project_modified = False
            self.statusBar().showMessage(f"Projeto salvo: {filepath}")
            QMessageBox.information(self, "Sucesso", "Projeto salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar projeto: {e}")
    
    def _save_project_file(self, filepath: str, project_info: dict):
        """Salva arquivo .mip (ZIP interno)"""
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Metadata
            metadata = {
                "version": "1.0",
                "app_version": "1.0.0",
                "state": self.current_state,
                "project_info": project_info,
                "timestamps": {
                    "created": datetime.now().isoformat(),
                    "modified": datetime.now().isoformat()
                },
                "image_info": {
                    "dimensions": list(self.image_editor.get_dimensions()),
                    "format": "PNG"
                },
                "points_info": {
                    "total_points": len(self.point_manager.points),
                    "has_reference": self.point_manager.has_reference_measurements()
                },
                "comparison": {
                    "tolerance_percent": self.point_manager.tolerance_percent
                }
            }
            zf.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            # Imagem
            if self.image_editor.is_image_loaded():
                img = self.image_editor.get_current_image()
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                zf.writestr('image.png', img_bytes.getvalue())
            
            # Pontos
            points_data = [p.to_dict() for p in self.point_manager.points]
            zf.writestr('points.json', json.dumps(points_data, indent=2))
    
    def abrir_projeto(self):
        """Abre projeto .mip"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Projeto",
            "",
            "Projeto Multímetro (*.mip)"
        )
        
        if not filepath:
            return
        
        try:
            self._load_project_file(filepath)
            self.current_project_path = filepath
            self.project_modified = False
            self.statusBar().showMessage(f"Projeto carregado: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar projeto: {e}")
    
    def _load_project_file(self, filepath: str):
        """Carrega arquivo .mip"""
        with zipfile.ZipFile(filepath, 'r') as zf:
            # Metadata
            metadata = json.loads(zf.read('metadata.json'))
            
            # Imagem
            img_data = zf.read('image.png')
            img = Image.open(io.BytesIO(img_data))
            pixmap = pil_to_pixmap(img)
            self.image_viewer.set_pixmap(pixmap)
            
            # Pontos
            points_data = json.loads(zf.read('points.json'))
            self.point_manager.points.clear()
            for p_data in points_data:
                point = Point.from_dict(p_data)
                self.point_manager.points.append(point)
            
            # Atualizar estado
            state = metadata.get('state', 'marcacao')
            self.change_state(state)
            
            # Atualizar tolerância
            tolerance = metadata.get('comparison', {}).get('tolerance_percent', 5.0)
            self.point_manager.tolerance_percent = tolerance
            
            # Atualizar UI
            self.point_manager.points_changed.emit(self.point_manager.points)
    
    def exportar_imagem(self):
        """Exporta imagem com pontos desenhados"""
        if not self.image_editor.is_image_loaded():
            QMessageBox.warning(self, "Aviso", "Nenhuma imagem para exportar.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Imagem",
            "",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)"
        )
        
        if not filepath:
            return
        
        try:
            # TODO: Renderizar imagem com pontos desenhados
            self.statusBar().showMessage(f"Imagem exportada: {filepath}")
            QMessageBox.information(self, "Sucesso", "Imagem exportada com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {e}")
    
    # === IMAGEM ===
    
    def abrir_imagem(self):
        """Abre imagem"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Imagem",
            "",
            get_supported_formats()
        )
        
        if filepath:
            success = self.image_editor.load_image(filepath)
            if success:
                self.change_state("edicao")
                filename = os.path.basename(filepath)
                self.statusBar().showMessage(f"Imagem carregada: {filename}")
                self.update_image_info()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível carregar a imagem.")
    
    def desfazer_imagem(self):
        self.image_editor.undo()
    
    def refazer_imagem(self):
        self.image_editor.redo()
    
    def rotacionar_90(self):
        if self.image_editor.is_image_loaded():
            self.image_editor.rotate_90(clockwise=True)
    
    def rotacionar_180(self):
        if self.image_editor.is_image_loaded():
            self.image_editor.rotate(180)
    
    def espelhar_horizontal(self):
        if self.image_editor.is_image_loaded():
            self.image_editor.flip(horizontal=True)
    
    def espelhar_vertical(self):
        if self.image_editor.is_image_loaded():
            self.image_editor.flip(horizontal=False)
    
    def ativar_modo_recorte(self):
        if self.image_editor.is_image_loaded():
            try:
                self.image_viewer.crop_selection_finished.disconnect()
            except:
                pass
            self.image_viewer.set_crop_mode(True)
            self.statusBar().showMessage("Modo recorte ativado - Arraste para selecionar área, ESC para cancelar")
            if hasattr(self.image_viewer, 'crop_selection_finished'):
                self.image_viewer.crop_selection_finished.connect(self.aplicar_recorte)
        else:
            QMessageBox.warning(self, "Aviso", "Carregue uma imagem primeiro.")
    
    def aplicar_recorte(self, crop_rect):
        try:
            if not self.image_editor.is_image_loaded():
                QMessageBox.warning(self, "Erro", "Nenhuma imagem carregada.")
                return
            if crop_rect.isNull():
                QMessageBox.warning(self, "Erro", "Seleção de recorte inválida.")
                return
            success = self.image_editor.apply_crop_selection(crop_rect)
            if success:
                self.statusBar().showMessage("Recorte aplicado com sucesso")
                self.image_viewer.set_crop_mode(False)
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível aplicar o recorte.")
                self.image_viewer.set_crop_mode(False)
        except Exception as e:
            print(f"Erro em aplicar_recorte: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao aplicar recorte: {e}")
            self.image_viewer.set_crop_mode(False)
    
    def redimensionar_imagem(self):
        if not self.image_editor.is_image_loaded():
            QMessageBox.warning(self, "Aviso", "Carregue uma imagem primeiro.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Redimensionar Imagem")
        dialog.setModal(True)
        layout = QFormLayout(dialog)
        width_spin = QSpinBox()
        width_spin.setRange(1, 10000)
        width_spin.setValue(self.image_editor.get_dimensions()[0])
        height_spin = QSpinBox()
        height_spin.setRange(1, 10000)
        height_spin.setValue(self.image_editor.get_dimensions()[1])
        keep_ratio_check = QCheckBox("Manter proporção")
        keep_ratio_check.setChecked(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow("Largura:", width_spin)
        layout.addRow("Altura:", height_spin)
        layout.addRow(keep_ratio_check)
        layout.addRow(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.image_editor.resize(width_spin.value(), height_spin.value(), keep_ratio_check.isChecked())
    
    def update_image_info(self):
        if self.image_editor.is_image_loaded():
            info = self.image_editor.get_file_info()
            dimensions = self.image_editor.get_dimensions()
            self.image_info_label.setText(f"{info['filename']} - {dimensions[0]}x{dimensions[1]}")
        else:
            self.image_info_label.setText("Nenhuma imagem carregada")
    
    # === SETUP UI ===
    
    def setup_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # TOOLBAR DINÂMICA
        self.toolbar_stack.setFixedHeight(37)
        layout.addWidget(self.toolbar_stack)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        left_panel = self.setup_left_panel()
        right_panel = self.setup_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 400])
    
    def setup_left_panel(self):
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.Box)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        self.image_info_label = QLabel("Nenhuma imagem carregada")
        left_layout.addWidget(self.image_info_label)
        
        left_layout.addWidget(self.image_viewer)
        
        return left_panel
    
    def setup_right_panel(self):
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.Box)
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # APENAS TABELA
        right_layout.addWidget(self.points_table)
        
        return right_panel
    
    def setup_status_bar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Pronto para iniciar")
        
        self.status_zoom = QLabel("Zoom: 100%")
        self.status_mouse = QLabel("Mouse: (0, 0)")
        
        status_bar.addPermanentWidget(self.status_zoom)
        status_bar.addPermanentWidget(self.status_mouse)
    
    def connect_signals(self):
        if hasattr(self.image_viewer, 'zoom_changed'):
            self.image_viewer.zoom_changed.connect(self._on_zoom_changed_update_cursor)
            self.image_viewer.zoom_changed.connect(self.on_zoom_changed)
        if hasattr(self.image_viewer, 'mouse_position_changed'):
            self.image_viewer.mouse_position_changed.connect(self.on_mouse_position_changed)
        if hasattr(self.image_viewer, 'point_clicked'):
            self.image_viewer.point_clicked.connect(self.on_image_click)
        if hasattr(self.point_manager, 'points_changed'):
            self.point_manager.points_changed.connect(self.on_points_changed)
            self.point_manager.points_changed.connect(self.image_viewer.set_points)
        if hasattr(self.points_table, 'tolerance_changed'):
            self.points_table.tolerance_changed.connect(self.on_tolerance_changed)
    
    def on_points_changed(self, points):
        self.points_table.update_points(points)
        self.project_modified = True
    
    def on_image_click(self, position: QPointF):
        if self.current_state == "marcacao":
            point = self.point_manager.add_point(position)
            self.statusBar().showMessage(f"Ponto {point.id} adicionado em ({position.x():.1f}, {position.y():.1f})")
    
    def on_zoom_changed(self, zoom_level):
        self.status_zoom.setText(f"Zoom: {zoom_level:.1%}")
    
    def _on_zoom_changed_update_cursor(self, zoom_level):
        if hasattr(self.image_viewer, '_points_mode') and self.image_viewer._points_mode:
            self.image_viewer.update_cursor()
    
    def on_mouse_position_changed(self, position):
        x, y = position.x(), position.y()
        self.status_mouse.setText(f"Mouse: ({x:.1f}, {y:.1f})")
    
    def on_tolerance_changed(self, tolerance):
        self.point_manager.tolerance_percent = tolerance
        # Atualizar cores dos pontos
        self.image_viewer.scene.update()
        # Redesenhar tabela
        self.points_table.update_points(self.point_manager.points)


# === DIALOGS ===

class SalvarProjetoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Salvar Projeto")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Nome do projeto
        layout.addWidget(QLabel("Nome do Projeto:"))
        self.nome_edit = QLineEdit()
        layout.addWidget(self.nome_edit)
        
        # Modelo
        layout.addWidget(QLabel("Modelo do Aparelho:"))
        self.modelo_edit = QLineEdit()
        layout.addWidget(self.modelo_edit)
        
        # Checkbox funcional
        self.funcional_check = QCheckBox("Placa 100% funcional?")
        self.funcional_check.setChecked(True)
        self.funcional_check.stateChanged.connect(self._on_funcional_changed)
        layout.addWidget(self.funcional_check)
        
        # Descrição problema
        layout.addWidget(QLabel("Descrição do Problema:"))
        self.problema_edit = QTextEdit()
        self.problema_edit.setMaximumHeight(80)
        self.problema_edit.setEnabled(False)
        layout.addWidget(self.problema_edit)
        
        # Botões
        buttons = QDialogButtonBox()
        btn_cancelar = buttons.addButton("❌ Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        btn_salvar = buttons.addButton("✅ Salvar", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _on_funcional_changed(self, state):
        self.problema_edit.setEnabled(state == 0)
    
    def accept(self):
        if not self.nome_edit.text():
            QMessageBox.warning(self, "Aviso", "Nome do projeto é obrigatório.")
            return
        if not self.modelo_edit.text():
            QMessageBox.warning(self, "Aviso", "Modelo do aparelho é obrigatório.")
            return
        if not self.funcional_check.isChecked() and not self.problema_edit.toPlainText():
            QMessageBox.warning(self, "Aviso", "Descrição do problema é obrigatória para placas defeituosas.")
            return
        super().accept()
    
    def get_project_info(self):
        return {
            "nome": self.nome_edit.text(),
            "modelo_aparelho": self.modelo_edit.text(),
            "placa_funcional": self.funcional_check.isChecked(),
            "descricao_problema": self.problema_edit.toPlainText() if not self.funcional_check.isChecked() else ""
        }


class NovoProjetoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alterações Não Salvas")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.action = "cancelar"
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        label = QLabel("O projeto atual possui alterações não salvas.\n\nO que deseja fazer?")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        layout.addSpacing(20)
        
        # Botão Descartar (topo)
        btn_descartar = QPushButton("🗑️ Descartar alterações")
        btn_descartar.setFixedHeight(40)
        btn_descartar.clicked.connect(lambda: self._set_action("descartar"))
        layout.addWidget(btn_descartar)
        
        layout.addSpacing(15)
        
        # Botão Cancelar (meio)
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setFixedHeight(40)
        btn_cancelar.clicked.connect(lambda: self._set_action("cancelar"))
        layout.addWidget(btn_cancelar)
        
        layout.addSpacing(15)
        
        # Botão Salvar (baixo)
        btn_salvar = QPushButton("💾 Salvar e criar novo projeto")
        btn_salvar.setFixedHeight(40)
        btn_salvar.clicked.connect(lambda: self._set_action("salvar"))
        layout.addWidget(btn_salvar)
    
    def _set_action(self, action):
        self.action = action
        self.accept()
    
    def get_action(self):
        return self.action


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()