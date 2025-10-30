import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QStatusBar,
                            QToolBar, QFrame, QSplitter, QSpacerItem, QSizePolicy,
                            QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
                            QSpinBox, QCheckBox, QFormLayout, QStackedWidget, QSlider,
                            QMenu, QTextEdit, QLineEdit)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QCursor, QPixmap, QPainter, QColor, QPen, QBrush, QKeySequence, QShortcut
from PyQt6.QtCore import QPointF
# Adicionar estes imports após os existentes
import copy
from datetime import datetime


# Importações que podem não existir - adicionando verificações
try:
    from image_processing.image_editor import ImageEditor
    from gui.image_viewer import ImageViewer
    from utils.image_utils import pil_to_pixmap, get_supported_formats
    from models.point import Point
    from gui.point_manager import PointManager
    from gui.points_table import PointsTable
    from gui.dialogs.save_project_dialog import SaveProjectDialog
    from gui.dialogs.new_project_dialog import NewProjectDialog
    from utils.project_manager import ProjectManager
    from utils.image_export import ImageExporter
except ImportError:
    # Criando classes stub para desenvolvimento gradual
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
        def get_current_image(self): return None
        
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
            self.preview_timer = QTimer()
            self.preview_timer.setSingleShot(True)
            self.preview_timer.timeout.connect(self._hide_preview_timeout)
            
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
        def set_preview_visible(self, visible): 
            self._show_preview = visible
        def show_preview_with_timeout(self):
            self.set_preview_visible(True)
            self.preview_timer.start(1000)  # 1 segundo
        def _hide_preview_timeout(self):
            self.set_preview_visible(False)
        
    def pil_to_pixmap(pil_image):
        return QPixmap()
        
    def get_supported_formats():
        return "Imagens (*.png *.jpg *.jpeg *.bmp *.tiff)"
        
    class Point:
        def __init__(self, id, x, y, shape='circle', size=20):
            self.id = id
            self.x = x
            self.y = y
            self.shape = shape
            self.size = size
            self.width = size
            self.height = size
            self.medicao_referencia = None
            self.medicao_comparacao = None
            
    class PointManager:
        points_changed = pyqtSignal(list)
        
        def __init__(self):
            self.points = []
            self.undo_stack = []
            self.current_shape = 'circle'
            self.current_size = 20
            self.current_width = 20
            self.current_height = 20
            self.edit_mode = False
            self.selected_point = None
            
        def add_point(self, position):
            # Salvar estado atual para undo
            self.undo_stack.append([p for p in self.points])
            if len(self.undo_stack) > 20:
                self.undo_stack.pop(0)
                
            point = Point(len(self.points) + 1, position.x(), position.y(), 
                         self.current_shape, self.current_size)
            if self.current_shape == 'rectangle':
                point.width = self.current_width
                point.height = self.current_height
            self.points.append(point)
            self._renumber_points()
            return point
            
        def remove_point(self, point_id):
            self.undo_stack.append([p for p in self.points])
            if len(self.undo_stack) > 20:
                self.undo_stack.pop(0)
            self.points = [p for p in self.points if p.id != point_id]
            self._renumber_points()
            
        def undo_last_action(self):
            if self.undo_stack:
                self.points = self.undo_stack.pop()
                self._renumber_points()
                return True
            return False
            
        def _renumber_points(self):
            for index, point in enumerate(self.points, start=1):
                point.id = index
            # Emitir sinal se disponível
            if hasattr(self, 'points_changed'):
                self.points_changed.emit(self.points)
        
        def swap_rectangle_dimensions(self):
            self.current_width, self.current_height = self.current_height, self.current_width
            
        def set_edit_mode(self, enabled):
            self.edit_mode = enabled
            self.selected_point = None
            
        def clear_all_points(self):
            if self.points:
                self.undo_stack.append([p for p in self.points])
                if len(self.undo_stack) > 20:
                    self.undo_stack.pop(0)
                self.points.clear()
                self._renumber_points()
            
    class PointsTable(QWidget):
        def __init__(self):
            super().__init__()
            self.layout = QVBoxLayout()
            self.setLayout(self.layout)
            self.label = QLabel("Tabela de pontos vazia")
            self.layout.addWidget(self.label)
            self.tolerance = 5.0
            
        def update_points(self, points):
            self.label.setText(f"{len(points)} pontos registrados")
            
        def set_tolerance(self, tolerance):
            self.tolerance = tolerance
            
        def apply_tolerance(self):
            pass
            
    # Classes stub para novos dialogs
    class SaveProjectDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("💾 Salvar Projeto")
            self.data = {}
            
        def get_project_data(self):
            return {
                'nome': 'Projeto Teste',
                'modelo': 'Teste',
                'funcional': True,
                'descricao': ''
            }
            
    class NewProjectDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("🆕 Novo Projeto")
            self.result_action = None
            
        def get_action(self):
            return 'continue'  # 'save', 'discard', 'cancel'
            
    class ProjectManager:
        @staticmethod
        def save_project(filepath, project_data, image_data, points_data):
            print(f"Salvando projeto: {filepath}")
            return True
            
        @staticmethod
        def load_project(filepath):
            print(f"Carregando projeto: {filepath}")
            return None
            
    class ImageExporter:
        @staticmethod
        def export_with_points(image, points, filepath):
            print(f"Exportando imagem com pontos: {filepath}")
            return True


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ========== CONFIGURAÇÃO INICIAL ==========
        self.setWindowTitle("Multímetro Inteligente - v1.0")
        self.resize(1200, 800)
        self._center_window()
        
        # ========== ESTADOS DO PROGRAMA ==========
        # Estados: "inicial", "edicao", "marcacao", "medicao"
        self.current_state = "inicial"
        self.project_data = None
        self.has_unsaved_changes = False
        self.tolerance = 5.0
        
        # ========== SISTEMA DE IMAGEM ==========
        self.image_editor = ImageEditor()
        self.image_viewer = ImageViewer()
        
        # ========== SISTEMA DE PONTOS ==========
        self.point_manager = PointManager()
        self.points_table = PointsTable()
        
        # Conectar point_manager ao image_viewer
        self.image_viewer.set_point_manager(self.point_manager)
        
        try:
            # ========== CONFIGURAR INTERFACE ==========
            self.setup_ui()
            self.setup_shortcuts()
            self.connect_signals()
            
            # Iniciar no estado inicial
            self._change_state("inicial")
            
            print("✅ MainWindow inicializada com sucesso")
            
        except Exception as e:
            print(f"❌ Erro durante inicialização: {e}")
            import traceback
            traceback.print_exc()
            
            # Interface mínima em caso de erro
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Erro na inicialização: {str(e)}"))
            central_widget.setLayout(layout)

        
    def _center_window(self):
        """Centraliza a janela na tela"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1200) // 2
        y = (screen.height() - 800) // 2
        self.move(x, y)
        
    def setup_ui(self):
        """Configura interface sem menu bar"""
        # ========== SEM MENU BAR ==========
        self.menuBar().hide()
        
        # ========== CONFIGURAR TOOLBARS E WIDGET CENTRAL ==========
        self.setup_toolbars()
        self.setup_central_widget()
        self.setup_status_bar()
        
    def setup_toolbars(self):
        """Configura sistema de toolbars reorganizado"""
        
        # ========== TOOLBAR SUPERIOR (PERSISTENTE) ==========
        self.persistent_toolbar = QToolBar("Persistente")
        self.persistent_toolbar.setIconSize(QSize(24, 24))
        self.persistent_toolbar.setFixedHeight(40)
        self.addToolBar(self.persistent_toolbar)
        
        # Botões persistentes (visíveis após carregar imagem)
        self.btn_save_project = QPushButton("💾 Salvar (Ctrl+S)")
        self.btn_save_project.setFixedSize(140, 32)
        self.btn_save_project.clicked.connect(self.save_project)
        self.btn_save_project.setVisible(False)  # Oculto inicialmente
        
        self.btn_export_image = QPushButton("📸 Exportar (Ctrl+E)")
        self.btn_export_image.setFixedSize(140, 32)
        self.btn_export_image.clicked.connect(self.export_image)
        self.btn_export_image.setVisible(False)  # Oculto inicialmente
        
        self.btn_new_project = QPushButton("🆕 Novo")
        self.btn_new_project.setFixedSize(100, 32)
        self.btn_new_project.clicked.connect(self.new_project)
        self.btn_new_project.setVisible(False)  # Oculto inicialmente
        
        self.persistent_toolbar.addWidget(self.btn_save_project)
        self.persistent_toolbar.addWidget(self.btn_export_image)
        self.persistent_toolbar.addWidget(self.btn_new_project)
        
        # ========== TOOLBAR DINÂMICA (STACK) ==========
        self.dynamic_toolbar_stack = QStackedWidget()
        self.dynamic_toolbar_stack.setFixedHeight(45)
        
        # Criar e adicionar segunda toolbar para container dinâmico
        self.dynamic_toolbar = QToolBar("Dinâmica")
        self.dynamic_toolbar.setFixedHeight(50)
        self.addToolBar(self.dynamic_toolbar)
        
        # Adicionar stack à segunda toolbar
        self.dynamic_toolbar.addWidget(self.dynamic_toolbar_stack)
        
        # Configurar toolbars dinâmicas
        self.setup_dynamic_toolbars()

        
    def setup_dynamic_toolbars(self):
        """Cria todas as toolbars dinâmicas por estado"""
        
        # ========== TOOLBAR INICIAL ==========
        self.toolbar_inicial = self._create_toolbar_inicial()
        self.dynamic_toolbar_stack.addWidget(self.toolbar_inicial)
        
        # ========== TOOLBAR EDIÇÃO ==========
        self.toolbar_edicao = self._create_toolbar_edicao()
        self.dynamic_toolbar_stack.addWidget(self.toolbar_edicao)
        
        # ========== TOOLBAR MARCAÇÃO - CÍRCULO ==========
        self.toolbar_marcacao_circulo = self._create_toolbar_marcacao_circulo()
        self.dynamic_toolbar_stack.addWidget(self.toolbar_marcacao_circulo)
        
        # ========== TOOLBAR MARCAÇÃO - RETÂNGULO ==========
        self.toolbar_marcacao_retangulo = self._create_toolbar_marcacao_retangulo()
        self.dynamic_toolbar_stack.addWidget(self.toolbar_marcacao_retangulo)
        
        # ========== TOOLBAR MEDIÇÃO (FUTURO) ==========
        self.toolbar_medicao = self._create_toolbar_medicao()
        self.dynamic_toolbar_stack.addWidget(self.toolbar_medicao)
        
    def _create_toolbar_inicial(self):
        """ESTADO INICIAL: [📂 Abrir Imagem] [📁 Abrir Projeto]"""
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        toolbar.setLayout(layout)
        
        btn_open_image = QPushButton("📂 Abrir Imagem (Ctrl+O)")
        btn_open_image.setFixedSize(180, 32)
        btn_open_image.clicked.connect(self.open_image)
        
        btn_open_project = QPushButton("📁 Abrir Projeto (Ctrl+P)")
        btn_open_project.setFixedSize(180, 32)
        btn_open_project.clicked.connect(self.open_project)
        
        layout.addWidget(btn_open_image)
        layout.addWidget(btn_open_project)
        layout.addStretch()
        
        return toolbar
        
    def _create_toolbar_edicao(self):
        """ESTADO EDIÇÃO: [↩️↪️] [↻] [✂️📏] [✅ Concluir]"""
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        toolbar.setLayout(layout)
        
        # Grupo desfazer/refazer
        btn_undo = QPushButton("↩️")
        btn_undo.setFixedSize(32, 32)
        btn_undo.setToolTip("Desfazer")
        btn_undo.clicked.connect(self.image_undo)
        
        btn_redo = QPushButton("↪️")
        btn_redo.setFixedSize(32, 32)
        btn_redo.setToolTip("Refazer")
        btn_redo.clicked.connect(self.image_redo)
        
        # Grupo rotação
        btn_rotate_90 = QPushButton("↻90°")
        btn_rotate_90.setFixedSize(50, 32)
        btn_rotate_90.setToolTip("Rotacionar 90°")
        btn_rotate_90.clicked.connect(self.rotate_90)
        
        btn_rotate_180 = QPushButton("↻180°")
        btn_rotate_180.setFixedSize(55, 32)
        btn_rotate_180.setToolTip("Rotacionar 180°")
        btn_rotate_180.clicked.connect(self.rotate_180)
        
        btn_flip_h = QPushButton("⬌")
        btn_flip_h.setFixedSize(32, 32)
        btn_flip_h.setToolTip("Espelhar Horizontal")
        btn_flip_h.clicked.connect(self.flip_horizontal)
        
        btn_flip_v = QPushButton("⬍")
        btn_flip_v.setFixedSize(32, 32)
        btn_flip_v.setToolTip("Espelhar Vertical")
        btn_flip_v.clicked.connect(self.flip_vertical)
        
        # Grupo ferramentas
        btn_crop = QPushButton("✂️")
        btn_crop.setFixedSize(32, 32)
        btn_crop.setToolTip("Recortar")
        btn_crop.clicked.connect(self.activate_crop_mode)
        
        btn_resize = QPushButton("📏")
        btn_resize.setFixedSize(32, 32)
        btn_resize.setToolTip("Redimensionar")
        btn_resize.clicked.connect(self.resize_image)
        
        # Botão concluir
        btn_finish_edit = QPushButton("✅ Concluir Edição")
        btn_finish_edit.setFixedSize(130, 32)
        btn_finish_edit.clicked.connect(self.finish_image_editing)
        
        layout.addWidget(btn_undo)
        layout.addWidget(btn_redo)
        layout.addWidget(self._create_separator())
        layout.addWidget(btn_rotate_90)
        layout.addWidget(btn_rotate_180)
        layout.addWidget(btn_flip_h)
        layout.addWidget(btn_flip_v)
        layout.addWidget(self._create_separator())
        layout.addWidget(btn_crop)
        layout.addWidget(btn_resize)
        layout.addWidget(self._create_separator())
        layout.addWidget(btn_finish_edit)
        layout.addStretch()
        
        return toolbar
        
    def _create_toolbar_marcacao_circulo(self):
        """MARCAÇÃO CÍRCULO: [⭕(W)][⬜(R)] S[━━●━━]W [✏️(E)][🗑️] [✅]"""
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        toolbar.setLayout(layout)
        
        # Botões de forma
        self.btn_circle_c = QPushButton("⭕(W)")
        self.btn_circle_c.setFixedSize(60, 32)
        self.btn_circle_c.setCheckable(True)
        self.btn_circle_c.setChecked(True)
        self.btn_circle_c.clicked.connect(self.set_circle_mode)
        
        self.btn_rect_c = QPushButton("⬜(R)")
        self.btn_rect_c.setFixedSize(60, 32)
        self.btn_rect_c.setCheckable(True)
        self.btn_rect_c.clicked.connect(self.set_rectangle_mode)
        
        # Slider de tamanho com atalhos visíveis
        size_layout, self.size_slider_c, self.size_label_c = self._create_size_slider("Tamanho:", 10, 200, 20)
        self.size_slider_c.valueChanged.connect(self._on_circle_size_changed)
        self.size_slider_c.sliderPressed.connect(self._on_slider_pressed)
        self.size_slider_c.sliderReleased.connect(self._on_slider_released)
        
        # Botões de ação
        self.btn_edit_points_c = QPushButton("✏️(E)")
        self.btn_edit_points_c.setFixedSize(60, 32)
        self.btn_edit_points_c.setCheckable(True)
        self.btn_edit_points_c.clicked.connect(self.toggle_edit_mode)
        
        btn_clear_points = QPushButton("🗑️")
        btn_clear_points.setFixedSize(32, 32)
        btn_clear_points.setToolTip("Limpar Todos os Pontos")
        btn_clear_points.clicked.connect(self.clear_all_points)
        
        btn_finish_points = QPushButton("✅ Concluir")
        btn_finish_points.setFixedSize(100, 32)
        btn_finish_points.clicked.connect(self.finish_point_marking)
        
        layout.addWidget(self.btn_circle_c)
        layout.addWidget(self.btn_rect_c)
        layout.addWidget(self._create_separator())
        layout.addLayout(size_layout)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.btn_edit_points_c)
        layout.addWidget(btn_clear_points)
        layout.addWidget(self._create_separator())
        layout.addWidget(btn_finish_points)
        layout.addStretch()
        
        return toolbar
        
    def _create_toolbar_marcacao_retangulo(self):
        """MARCAÇÃO RETÂNGULO: [⭕(W)][⬜(R)] S[━━●━━]W L: A[━━●━━]D A: [↔️⇅] [✏️(E)][🗑️] [✅]"""
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        toolbar.setLayout(layout)
        
        # Botões de forma
        self.btn_circle_r = QPushButton("⭕(W)")
        self.btn_circle_r.setFixedSize(60, 32)
        self.btn_circle_r.setCheckable(True)
        self.btn_circle_r.clicked.connect(self.set_circle_mode)
        
        self.btn_rect_r = QPushButton("⬜(R)")
        self.btn_rect_r.setFixedSize(60, 32)
        self.btn_rect_r.setCheckable(True)
        self.btn_rect_r.setChecked(True)
        self.btn_rect_r.clicked.connect(self.set_rectangle_mode)
        
        # Slider largura
        width_layout, self.width_slider, self.width_label = self._create_size_slider("L:", 10, 200, 20)
        self.width_slider.valueChanged.connect(self._on_width_changed)
        self.width_slider.sliderPressed.connect(self._on_slider_pressed)
        self.width_slider.sliderReleased.connect(self._on_slider_released)
        
        # Slider altura
        height_layout, self.height_slider, self.height_label = self._create_size_slider("A:", 10, 200, 20)
        self.height_slider.valueChanged.connect(self._on_height_changed)
        self.height_slider.sliderPressed.connect(self._on_slider_pressed)
        self.height_slider.sliderReleased.connect(self._on_slider_released)
        
        # Botão trocar dimensões
        btn_swap = QPushButton("↔️⇅")
        btn_swap.setFixedSize(40, 32)
        btn_swap.setToolTip("Trocar Largura ↔ Altura")
        btn_swap.clicked.connect(self.swap_dimensions)
        
        # Botões de ação
        self.btn_edit_points_r = QPushButton("✏️(E)")
        self.btn_edit_points_r.setFixedSize(60, 32)
        self.btn_edit_points_r.setCheckable(True)
        self.btn_edit_points_r.clicked.connect(self.toggle_edit_mode)
        
        btn_clear_points_r = QPushButton("🗑️")
        btn_clear_points_r.setFixedSize(32, 32)
        btn_clear_points_r.setToolTip("Limpar Todos os Pontos")
        btn_clear_points_r.clicked.connect(self.clear_all_points)
        
        btn_finish_points_r = QPushButton("✅ Concluir")
        btn_finish_points_r.setFixedSize(100, 32)
        btn_finish_points_r.clicked.connect(self.finish_point_marking)
        
        layout.addWidget(self.btn_circle_r)
        layout.addWidget(self.btn_rect_r)
        layout.addWidget(self._create_separator())
        layout.addLayout(width_layout)
        layout.addLayout(height_layout)
        layout.addWidget(btn_swap)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.btn_edit_points_r)
        layout.addWidget(btn_clear_points_r)
        layout.addWidget(self._create_separator())
        layout.addWidget(btn_finish_points_r)
        layout.addStretch()
        
        return toolbar
        
    def _create_toolbar_medicao(self):
        """TOOLBAR MEDIÇÃO (FUTURO): [🔌] [▶️⏸️⏹️] [📊 Comparar]"""
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        toolbar.setLayout(layout)
        
        btn_connect = QPushButton("🔌 Conectar")
        btn_connect.setFixedSize(100, 32)
        
        btn_start = QPushButton("▶️")
        btn_start.setFixedSize(32, 32)
        btn_start.setToolTip("Iniciar Medição")
        
        btn_pause = QPushButton("⏸️")
        btn_pause.setFixedSize(32, 32)
        btn_pause.setToolTip("Pausar")
        
        btn_stop = QPushButton("⏹️")
        btn_stop.setFixedSize(32, 32)
        btn_stop.setToolTip("Parar")
        
        btn_compare = QPushButton("📊 Comparar")
        btn_compare.setFixedSize(120, 32)
        btn_compare.clicked.connect(self.start_comparison_mode)
        
        layout.addWidget(btn_connect)
        layout.addWidget(self._create_separator())
        layout.addWidget(btn_start)
        layout.addWidget(btn_pause)
        layout.addWidget(btn_stop)
        layout.addWidget(self._create_separator())
        layout.addWidget(btn_compare)
        layout.addStretch()
        
        return toolbar
        
    def _create_separator(self):
        """Cria separador vertical"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedWidth(2)
        return separator
        
    def _create_size_slider(self, label_text, min_val, max_val, initial_val):
        """Cria slider com atalhos visíveis: S [━━●━━] W"""
        layout = QHBoxLayout()
        layout.setSpacing(5)
        
        # Label do campo
        if label_text:
            field_label = QLabel(label_text)
            layout.addWidget(field_label)
        
        # Label "S" (diminuir)
        label_s = QLabel("S")
        label_s.setStyleSheet("font-weight: bold; color: #0066cc;")
        label_s.setFixedWidth(12)
        
        # Slider
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(initial_val)
        slider.setFixedWidth(120)
        
        # Label "W" (aumentar)
        label_w = QLabel("W")
        label_w.setStyleSheet("font-weight: bold; color: #0066cc;")
        label_w.setFixedWidth(12)
        
        # Label valor
        value_label = QLabel(f"{initial_val}px")
        value_label.setFixedWidth(40)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label_s)
        layout.addWidget(slider)
        layout.addWidget(label_w)
        layout.addWidget(value_label)
        
        return layout, slider, value_label
        
    def setup_central_widget(self):
        """Configura widget central com splitter"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Splitter horizontal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Painel esquerdo (imagem)
        left_panel = self._create_left_panel()
        
        # Painel direito (apenas tabela)
        right_panel = self._create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 400])  # Proporção inicial
        
    def _create_left_panel(self):
        """Painel esquerdo - apenas área de imagem"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Box)
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Info da imagem
        self.image_info_label = QLabel("Nenhuma imagem carregada")
        self.image_info_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.image_info_label)
        
        # Viewer da imagem
        layout.addWidget(self.image_viewer)
        
        return panel
        
    def _create_right_panel(self):
        """Painel direito - APENAS TABELA (sem hardware/ações)"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Box)
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Apenas a tabela de pontos
        layout.addWidget(self.points_table)
        layout.addStretch()
        
        return panel
        
    def setup_status_bar(self):
        """Configura barra de status"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        status_bar.showMessage("Multímetro Inteligente - Pronto para iniciar")
        
        # Labels permanentes
        self.status_state = QLabel("Estado: Inicial")
        self.status_points = QLabel("Pontos: 0")
        self.status_zoom = QLabel("Zoom: 100%")
        self.status_mouse = QLabel("Mouse: (0, 0)")
        
        status_bar.addPermanentWidget(self.status_state)
        status_bar.addPermanentWidget(self.status_points)
        status_bar.addPermanentWidget(self.status_zoom)
        status_bar.addPermanentWidget(self.status_mouse)
        
    def setup_shortcuts(self):
        """Configura atalhos de teclado"""
        
        # Atalhos globais
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_image)
        QShortcut(QKeySequence("Ctrl+P"), self, self.open_project)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_project)
        QShortcut(QKeySequence("Ctrl+E"), self, self.export_image)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo_action)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.redo_action)
        
        # Atalhos de formas
        QShortcut(QKeySequence("W"), self, self.set_circle_mode)
        QShortcut(QKeySequence("R"), self, self.set_rectangle_mode)
        QShortcut(QKeySequence("E"), self, self.toggle_edit_mode)
        
        # Atalhos de ajuste de tamanho
        QShortcut(QKeySequence("S"), self, self.decrease_size)
        QShortcut(QKeySequence("Shift+S"), self, self.increase_size)  # W não funciona como esperado
        
        # Atalhos de retângulo
        QShortcut(QKeySequence("A"), self, self.decrease_height)
        QShortcut(QKeySequence("D"), self, self.increase_height)
        
    def connect_signals(self):
        """Conecta sinais"""
        try:
            # Sinais do image_viewer
            if hasattr(self.image_viewer, 'zoom_changed'):
                self.image_viewer.zoom_changed.connect(self._on_zoom_changed)
            if hasattr(self.image_viewer, 'mouse_position_changed'):
                self.image_viewer.mouse_position_changed.connect(self._on_mouse_position_changed)
            if hasattr(self.image_viewer, 'point_clicked'):
                self.image_viewer.point_clicked.connect(self._on_image_click)
                
            # Sinais do point_manager
            if hasattr(self.point_manager, 'points_changed'):
                self.point_manager.points_changed.connect(self._on_points_changed)
                # Conectar pontos ao image_viewer apenas se ambos sinais existirem
                if hasattr(self.image_viewer, 'set_points'):
                    self.point_manager.points_changed.connect(self.image_viewer.set_points)
                
            # Sinais do image_editor
            if hasattr(self.image_editor, 'image_updated'):
                self.image_editor.image_updated.connect(self._on_image_updated)
                
            print("🔗 Sinais conectados com sucesso")
            
        except Exception as e:
            print(f"⚠️  Erro ao conectar sinais: {e}")

            
    # ========== GERENCIAMENTO DE ESTADOS ==========
    
    def _change_state(self, new_state):
        """Muda o estado do programa e atualiza interface"""
        print(f"🔄 Mudando estado: {self.current_state} → {new_state}")
        
        self.current_state = new_state
        self.status_state.setText(f"Estado: {new_state.title()}")
        
        # Mostrar/ocultar toolbar persistente
        if new_state == "inicial":
            self.btn_save_project.setVisible(False)
            self.btn_export_image.setVisible(False)
            self.btn_new_project.setVisible(False)
            self.dynamic_toolbar_stack.setCurrentWidget(self.toolbar_inicial)
        else:
            self.btn_save_project.setVisible(True)
            self.btn_export_image.setVisible(True)
            self.btn_new_project.setVisible(True)
            
        # Trocar toolbar dinâmica
        if new_state == "edicao":
            self.dynamic_toolbar_stack.setCurrentWidget(self.toolbar_edicao)
            self.image_viewer.set_points_mode(False)
            
        elif new_state == "marcacao":
            if self.point_manager.current_shape == 'circle':
                self.dynamic_toolbar_stack.setCurrentWidget(self.toolbar_marcacao_circulo)
            else:
                self.dynamic_toolbar_stack.setCurrentWidget(self.toolbar_marcacao_retangulo)
            self.image_viewer.set_points_mode(True, self.point_manager.current_shape)
            
        elif new_state == "medicao":
            self.dynamic_toolbar_stack.setCurrentWidget(self.toolbar_medicao)
            self.image_viewer.set_points_mode(False)
            
        self.statusBar().showMessage(f"Estado alterado para: {new_state.title()}")
        
    # ========== CALLBACKS DOS SLIDERS ==========
    
    def _on_slider_pressed(self):
        """Mostra preview quando slider é pressionado"""
        if hasattr(self.image_viewer, 'show_preview_with_timeout'):
            self.image_viewer.show_preview_with_timeout()
        print("🎚️ Slider pressionado - Preview com timeout iniciado")
        
    def _on_slider_released(self):
        """Chamado quando slider é solto - preview continua até timeout"""
        print("🎚️ Slider solto - Preview continuará por 1 segundo")
        
    def _on_circle_size_changed(self, value):
        """Atualiza tamanho do círculo"""
        self.point_manager.current_size = value
        self.size_label_c.setText(f"{value}px")
        if hasattr(self.image_viewer, 'update_cursor'):
            self.image_viewer.update_cursor()
        
    def _on_width_changed(self, value):
        """Atualiza largura do retângulo"""
        self.point_manager.current_width = value
        self.width_label.setText(f"{value}px")
        if hasattr(self.image_viewer, 'update_cursor'):
            self.image_viewer.update_cursor()
        
    def _on_height_changed(self, value):
        """Atualiza altura do retângulo"""
        self.point_manager.current_height = value
        self.height_label.setText(f"{value}px")
        if hasattr(self.image_viewer, 'update_cursor'):
            self.image_viewer.update_cursor()
            
    # ========== AÇÕES DOS BOTÕES ==========
    
    def open_image(self):
        """Abre uma imagem e muda para estado de edição"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            "Abrir imagem da placa", 
            "", 
            get_supported_formats()
        )
        
        if filepath:
            success = self.image_editor.load_image(filepath)
            if success:
                filename = os.path.basename(filepath)
                self.image_info_label.setText(f"📁 {filename} - {self.image_editor.get_dimensions()[0]}x{self.image_editor.get_dimensions()[1]}")
                self.has_unsaved_changes = True
                
                # Mudar para estado de edição
                self._change_state("edicao")
                
                self.statusBar().showMessage(f"Imagem carregada: {filename}")
                print(f"📂 Imagem carregada: {filepath}")
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível carregar a imagem.")
                
    def open_project(self):
        """Abre um projeto .mip e restaura o estado"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Projeto",
            "",
            "Projetos Multímetro (*.mip)"
        )
        
        if filepath:
            project_data = ProjectManager.load_project(filepath)
            if project_data:
                self.project_data = project_data
                
                # Carregar imagem se existir
                if project_data.get('image'):
                    pixmap = pil_to_pixmap(project_data['image'])
                    self.image_viewer.set_pixmap(pixmap)
                    
                # Carregar pontos se existir
                if project_data.get('points'):
                    # Aqui você converteria os dados JSON de volta para objetos Point
                    print(f"📋 Carregando {len(project_data['points'])} pontos")
                    
                # Restaurar estado
                saved_state = project_data['metadata'].get('state', 'marcacao')
                self._change_state(saved_state)
                
                self.has_unsaved_changes = False
                self.statusBar().showMessage(f"Projeto carregado: {os.path.basename(filepath)}")
                print(f"📁 Projeto carregado: {filepath}")
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível carregar o projeto.")
                
    def save_project(self):
        """Salva projeto com dialog personalizado"""
        if not self.image_editor.is_image_loaded():
            QMessageBox.warning(self, "Aviso", "Carregue uma imagem primeiro.")
            return
            
        # Abrir dialog personalizado
        dialog = SaveProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_data = dialog.get_project_data()
            
            # Validar dados
            if not project_data['nome'] or not project_data['modelo']:
                QMessageBox.warning(self, "Erro", "Nome do projeto e modelo são obrigatórios.")
                return
                
            if not project_data['funcional'] and not project_data['descricao']:
                QMessageBox.warning(self, "Erro", "Descrição do problema é obrigatória quando a placa não é funcional.")
                return
            
            # Abrir dialog de salvar arquivo
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Projeto",
                f"{project_data['nome']}.mip",
                "Projetos Multímetro (*.mip)"
            )
            
            if filepath:
                project_data['state'] = self.current_state
                
                image_data = self.image_editor.get_current_image()
                points_data = self.point_manager.points
                
                success = ProjectManager.save_project(filepath, project_data, image_data, points_data)
                if success:
                    self.has_unsaved_changes = False
                    self.statusBar().showMessage(f"Projeto salvo: {os.path.basename(filepath)}")
                    print(f"💾 Projeto salvo: {filepath}")
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível salvar o projeto.")
                    
    def export_image(self):
        """Exporta imagem com pontos desenhados"""
        if not self.image_editor.is_image_loaded():
            QMessageBox.warning(self, "Aviso", "Nenhuma imagem para exportar.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Imagem com Pontos",
            "",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)"
        )
        
        if filepath:
            image_data = self.image_editor.get_current_image()
            points_data = self.point_manager.points
            
            success = ImageExporter.export_with_points(image_data, points_data, filepath)
            if success:
                self.statusBar().showMessage(f"Imagem exportada: {os.path.basename(filepath)}")
                print(f"📸 Imagem exportada: {filepath}")
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível exportar a imagem.")
                
    def new_project(self):
        """Cria novo projeto com dialog WYSIWYG"""
        if self.has_unsaved_changes:
            dialog = NewProjectDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                action = dialog.get_action()
                
                if action == 'save':
                    self.save_project()
                    self._create_new_project()
                elif action == 'discard':
                    self._create_new_project()
                # Se action == 'cancel', não faz nada
        else:
            self._create_new_project()
            
    def _create_new_project(self):
        """Limpa tudo e volta ao estado inicial"""
        self.point_manager.points.clear()
        if hasattr(self.point_manager, 'points_changed'):
            self.point_manager.points_changed.emit([])
        
        self.image_viewer.set_pixmap(QPixmap())
        self.image_info_label.setText("Nenhuma imagem carregada")
        self.project_data = None
        self.has_unsaved_changes = False
        
        self._change_state("inicial")
        self.statusBar().showMessage("Novo projeto criado")
        print("🆕 Novo projeto criado")
        
    # ========== AÇÕES DE FORMAS ==========
    
    def set_circle_mode(self):
        """Ativa modo círculo"""
        self.point_manager.current_shape = 'circle'
        
        # Atualizar botões
        if self.current_state == "marcacao":
            self.btn_circle_c.setChecked(True)
            self.btn_rect_c.setChecked(False)
            self.btn_circle_r.setChecked(True)
            self.btn_rect_r.setChecked(False)
            
            # Trocar para toolbar de círculo
            self.dynamic_toolbar_stack.setCurrentWidget(self.toolbar_marcacao_circulo)
            
        self.image_viewer.set_points_mode(True, 'circle')
        self.statusBar().showMessage(f"Modo Círculo - Tamanho: {self.point_manager.current_size}px")
        print(f"⭕ Modo Círculo ativado - {self.point_manager.current_size}px")
        
    def set_rectangle_mode(self):
        """Ativa modo retângulo"""
        self.point_manager.current_shape = 'rectangle'
        
        # Atualizar botões
        if self.current_state == "marcacao":
            self.btn_circle_c.setChecked(False)
            self.btn_rect_c.setChecked(True)
            self.btn_circle_r.setChecked(False)
            self.btn_rect_r.setChecked(True)
            
            # Trocar para toolbar de retângulo
            self.dynamic_toolbar_stack.setCurrentWidget(self.toolbar_marcacao_retangulo)
            
        self.image_viewer.set_points_mode(True, 'rectangle')
        self.statusBar().showMessage(f"Modo Retângulo - {self.point_manager.current_width}x{self.point_manager.current_height}px")
        print(f"⬜ Modo Retângulo ativado - {self.point_manager.current_width}x{self.point_manager.current_height}px")
        
    def toggle_edit_mode(self):
        """Alterna modo de edição de pontos"""
        self.point_manager.set_edit_mode(not self.point_manager.edit_mode)
        
        # Atualizar botões
        if self.current_state == "marcacao":
            self.btn_edit_points_c.setChecked(self.point_manager.edit_mode)
            self.btn_edit_points_r.setChecked(self.point_manager.edit_mode)
            
        mode_text = "ATIVO" if self.point_manager.edit_mode else "INATIVO"
        self.statusBar().showMessage(f"Modo Edição de Pontos: {mode_text}")
        print(f"✏️ Modo Edição: {mode_text}")
        
    def swap_dimensions(self):
        """Troca largura e altura do retângulo"""
        self.point_manager.swap_rectangle_dimensions()
        
        # Atualizar sliders
        self.width_slider.setValue(self.point_manager.current_width)
        self.height_slider.setValue(self.point_manager.current_height)
        self.width_label.setText(f"{self.point_manager.current_width}px")
        self.height_label.setText(f"{self.point_manager.current_height}px")
        
        self.image_viewer.update_cursor()
        self.statusBar().showMessage(f"Dimensões trocadas: {self.point_manager.current_width}x{self.point_manager.current_height}px")
        print(f"↔️⇅ Dimensões trocadas: {self.point_manager.current_width}x{self.point_manager.current_height}px")
        
    def clear_all_points(self):
        """Limpa todos os pontos com confirmação"""
        if self.point_manager.points:
            reply = QMessageBox.question(
                self, 
                "Confirmar",
                f"Tem certeza que deseja apagar todos os {len(self.point_manager.points)} pontos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.point_manager.clear_all_points()
                self.statusBar().showMessage("Todos os pontos foram apagados")
                print("🗑️ Todos os pontos apagados")
                
    # ========== AÇÕES DE TECLADO ==========
    
    def undo_action(self):
        """Ctrl+Z - Desfazer última ação de ponto"""
        if self.current_state == "marcacao":
            if self.point_manager.undo_last_action():
                self.statusBar().showMessage("Última ação desfeita")
                print("↩️ Ctrl+Z - Ação desfeita")
            else:
                self.statusBar().showMessage("Nada para desfazer")
        elif self.current_state == "edicao":
            self.image_undo()
            
    def redo_action(self):
        """Ctrl+Shift+Z - Refazer"""
        if self.current_state == "edicao":
            self.image_redo()
            
    def decrease_size(self):
        """Tecla S - Diminuir tamanho"""
        if self.current_state == "marcacao":
            if self.point_manager.current_shape == 'circle':
                new_value = max(10, self.size_slider_c.value() - 5)
                self.size_slider_c.setValue(new_value)
            else:
                new_value = max(10, self.width_slider.value() - 5)
                self.width_slider.setValue(new_value)
                
    def increase_size(self):
        """Shift+S (simulando W) - Aumentar tamanho"""
        if self.current_state == "marcacao":
            if self.point_manager.current_shape == 'circle':
                new_value = min(200, self.size_slider_c.value() + 5)
                self.size_slider_c.setValue(new_value)
            else:
                new_value = min(200, self.width_slider.value() + 5)
                self.width_slider.setValue(new_value)
                
    def decrease_height(self):
        """Tecla A - Diminuir altura (retângulo)"""
        if self.current_state == "marcacao" and self.point_manager.current_shape == 'rectangle':
            new_value = max(10, self.height_slider.value() - 5)
            self.height_slider.setValue(new_value)
            
    def increase_height(self):
        """Tecla D - Aumentar altura (retângulo)"""
        if self.current_state == "marcacao" and self.point_manager.current_shape == 'rectangle':
            new_value = min(200, self.height_slider.value() + 5)
            self.height_slider.setValue(new_value)
            
    # ========== TRANSIÇÕES DE ESTADO ==========
    
    def finish_image_editing(self):
        """Conclui edição de imagem e vai para marcação"""
        self._change_state("marcacao")
        self.statusBar().showMessage("Edição concluída - Agora você pode marcar pontos na imagem")
        print("✅ Edição de imagem concluída")
        
    def finish_point_marking(self):
        """Conclui marcação de pontos e vai para medição (futuro)"""
        if not self.point_manager.points:
            QMessageBox.information(self, "Aviso", "Marque pelo menos um ponto antes de concluir.")
            return
            
        reply = QMessageBox.question(
            self,
            "Concluir Marcação",
            f"Você marcou {len(self.point_manager.points)} pontos.\n\nDeseja prosseguir para a medição?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # self._change_state("medicao")  # Futuramente
            QMessageBox.information(self, "Em Desenvolvimento", "Modo de medição será implementado em breve.")
            print(f"✅ Marcação concluída - {len(self.point_manager.points)} pontos")
            
    # ========== AÇÕES DE IMAGEM ==========
    
    def image_undo(self):
        """Desfazer edição de imagem"""
        self.image_editor.undo()
        print("↩️ Desfazer imagem")
        
    def image_redo(self):
        """Refazer edição de imagem"""
        self.image_editor.redo()
        print("↪️ Refazer imagem")
        
    def rotate_90(self):
        """Rotacionar 90°"""
        if self.image_editor.is_image_loaded():
            self.image_editor.rotate_90(clockwise=True)
            self.has_unsaved_changes = True
            print("↻ Rotação 90°")
            
    def rotate_180(self):
        """Rotacionar 180°"""
        if self.image_editor.is_image_loaded():
            self.image_editor.rotate(180)
            self.has_unsaved_changes = True
            print("↻ Rotação 180°")
            
    def flip_horizontal(self):
        """Espelhar horizontal"""
        if self.image_editor.is_image_loaded():
            self.image_editor.flip(horizontal=True)
            self.has_unsaved_changes = True
            print("⬌ Espelhamento horizontal")
            
    def flip_vertical(self):
        """Espelhar vertical"""
        if self.image_editor.is_image_loaded():
            self.image_editor.flip(horizontal=False)
            self.has_unsaved_changes = True
            print("⬍ Espelhamento vertical")
            
    def activate_crop_mode(self):
        """Ativar modo recorte"""
        if self.image_editor.is_image_loaded():
            self.image_viewer.set_crop_mode(True)
            self.statusBar().showMessage("Modo recorte ativado - Arraste para selecionar área")
            print("✂️ Modo recorte ativado")
        else:
            QMessageBox.warning(self, "Aviso", "Carregue uma imagem primeiro.")
            
    def resize_image(self):
        """Redimensionar imagem"""
        if not self.image_editor.is_image_loaded():
            QMessageBox.warning(self, "Aviso", "Carregue uma imagem primeiro.")
            return
            
        # Dialog simples para redimensionamento
        dialog = QDialog(self)
        dialog.setWindowTitle("📏 Redimensionar Imagem")
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
            self.image_editor.resize(
                width_spin.value(), 
                height_spin.value(), 
                keep_ratio_check.isChecked()
            )
            self.has_unsaved_changes = True
            print(f"📏 Imagem redimensionada: {width_spin.value()}x{height_spin.value()}")
            
    # ========== MODO COMPARAÇÃO (FUTURO) ==========
    
    def start_comparison_mode(self):
        """Inicia modo de comparação (futuro)"""
        QMessageBox.information(
            self, 
            "Em Desenvolvimento", 
            "Modo de comparação será implementado na próxima versão.\n\n"
            "Funcionalidade:\n"
            "• Repetir medições nos mesmos pontos\n"
            "• Comparar com placa de referência\n"
            "• Destacar diferenças em rosa\n"
            "• Sistema de tolerância customizável"
        )
        print("📊 Modo comparação (em desenvolvimento)")
        
    # ========== CALLBACKS DE SINAIS ==========
    
    def _on_image_updated(self, pil_image):
        """Callback quando imagem é atualizada"""
        pixmap = pil_to_pixmap(pil_image)
        self.image_viewer.set_pixmap(pixmap)
        
        # Atualizar info
        dimensions = self.image_editor.get_dimensions()
        filename = self.image_editor.get_file_info()['filename']
        self.image_info_label.setText(f"📁 {filename} - {dimensions[0]}x{dimensions[1]}")
        
    def _on_points_changed(self, points):
        """Callback quando pontos mudam"""
        try:
            if hasattr(self.points_table, 'update_points'):
                self.points_table.update_points(points)
            self.status_points.setText(f"Pontos: {len(points)}")
            self.has_unsaved_changes = True if points else self.has_unsaved_changes
            print(f"📊 Pontos atualizados: {len(points)}")
        except Exception as e:
            print(f"⚠️  Erro ao atualizar pontos: {e}")

        
    def _on_image_click(self, position):
        """Callback quando usuário clica na imagem"""
        if self.current_state == "marcacao" and not self.point_manager.edit_mode:
            point = self.point_manager.add_point(position)
            self.statusBar().showMessage(f"Ponto {point.id} adicionado em ({position.x():.1f}, {position.y():.1f})")
            print(f"🎯 Ponto {point.id} adicionado: ({position.x():.1f}, {position.y():.1f})")
            
    def _on_zoom_changed(self, zoom_level):
        """Callback quando zoom muda"""
        self.status_zoom.setText(f"Zoom: {zoom_level:.1%}")
        
    def _on_mouse_position_changed(self, position):
        """Callback quando posição do mouse muda"""
        self.status_mouse.setText(f"Mouse: ({position.x():.1f}, {position.y():.1f})")
        
    # ========== FECHAR PROGRAMA ==========
    
    def closeEvent(self, event):
        """Intercepta fechamento para verificar alterações não salvas"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Alterações Não Salvas",
                "Você tem alterações não salvas. Deseja salvar antes de sair?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_project()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    
    # Configurar aplicação
    app.setApplicationName("Multímetro Inteligente")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("TechLab")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
