import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QStatusBar,
                            QToolBar, QFrame, QSplitter, QSpacerItem, QSizePolicy,
                            QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
                            QSpinBox, QCheckBox, QFormLayout, QStackedWidget, QSlider)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QCursor, QPixmap, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import QPointF

# Importações que podem não existir - adicionando verificações
try:
    from image_processing.image_editor import ImageEditor
    from gui.image_viewer import ImageViewer
    from utils.image_utils import pil_to_pixmap, get_supported_formats
    from models.point import Point
    from gui.point_manager import PointManager
    from gui.points_table import PointsTable
except ImportError:
    # Criando classes stub para evitar erros de importação
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
            self.points_changed = pyqtSignal(list)
            
        def add_point(self, position):
            point = Point(len(self.points) + 1, position.x(), position.y())
            self.points.append(point)
            self.points_changed.emit(self.points)
            return point
        
        def swap_rectangle_dimensions(self):
            self.current_width, self.current_height = self.current_height, self.current_width
            
    class PointsTable(QWidget):
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
        self.setGeometry(100, 100, 1200, 800)
        
        # Inicializar sistema de imagem PRIMEIRO
        self.image_editor = ImageEditor()
        self.image_viewer = ImageViewer()
        
        # Sistema de toolbar dinâmica
        self.toolbar_stack = QStackedWidget()
        self.current_mode = "edicao"
        
        # Sistema de pontos DEPOIS do image_viewer
        self.point_manager = PointManager()
        self.points_table = PointsTable()
        
        # AGORA podemos conectar o point_manager ao image_viewer
        self.image_viewer.set_point_manager(self.point_manager)
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        self.setup_menu_bar()
        self.setup_toolbars()
        self.setup_central_widget()
        self.setup_status_bar()
        
    def setup_toolbars(self):
        """Barra superior COMPACTA"""
        main_toolbar = QToolBar("Principal")
        main_toolbar.setIconSize(QSize(16, 16))
        main_toolbar.setFixedHeight(35)
        self.addToolBar(main_toolbar)

        # Botões principais COMPACTOS
        self.btn_editar = QPushButton('✏️')
        self.btn_editar.setToolTip("Modo Edição de Imagem")
        self.btn_editar.setCheckable(True)
        self.btn_editar.setChecked(True)
        self.btn_editar.setFixedSize(40, 30)
        self.btn_editar.clicked.connect(self.ativar_modo_edicao)
        main_toolbar.addWidget(self.btn_editar)
        
        self.btn_marcar = QPushButton('🎯')
        self.btn_marcar.setToolTip("Modo Marcação de Pontos")
        self.btn_marcar.setCheckable(True)
        self.btn_marcar.setFixedSize(40, 30)
        self.btn_marcar.clicked.connect(self.ativar_modo_marcacao)
        main_toolbar.addWidget(self.btn_marcar)
        
        btn_teste = QPushButton('🧪')
        btn_teste.setToolTip("Modo de Teste")
        btn_teste.setFixedSize(40, 30)
        btn_teste.clicked.connect(self.modo_teste)
        main_toolbar.addWidget(btn_teste)
        
        main_toolbar.addSeparator()

        # Botões de navegação COMPACTOS
        btn_zoom_out = QPushButton('➖')
        btn_zoom_out.setToolTip("Zoom Out")
        btn_zoom_out.setFixedSize(30, 30)
        btn_zoom_out.clicked.connect(self.zoom_out)
        main_toolbar.addWidget(btn_zoom_out)

        btn_zoom_in = QPushButton('➕')
        btn_zoom_in.setToolTip("Zoom In")
        btn_zoom_in.setFixedSize(30, 30)
        btn_zoom_in.clicked.connect(self.zoom_in)
        main_toolbar.addWidget(btn_zoom_in)

        btn_fit = QPushButton('🔍')
        btn_fit.setToolTip("Ajustar à Tela")
        btn_fit.setFixedSize(30, 30)
        btn_fit.clicked.connect(self.ajustar_tela)
        main_toolbar.addWidget(btn_fit)
        
        # Espaçador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        main_toolbar.addWidget(spacer)
        
        btn_config = QPushButton('⚙️')
        btn_config.setToolTip("Configurações")
        btn_config.setFixedSize(40, 30)
        btn_config.clicked.connect(self.abrir_configuracoes)
        main_toolbar.addWidget(btn_config)
        
    def setup_dynamic_toolbars(self):
        """Cria toolbars dinâmicas para círculo e retângulo - VERSÃO ATUALIZADA"""
        
        # ========== TOOLBAR DE EDIÇÃO ==========
        self.toolbar_edicao = QWidget()
        self.toolbar_edicao.setFixedHeight(28)
        layout_edicao = QHBoxLayout()
        layout_edicao.setContentsMargins(2, 1, 2, 1)
        layout_edicao.setSpacing(2)
        self.toolbar_edicao.setLayout(layout_edicao)
        
        # Botões COMPACTOS para edição
        btn_abrir = QPushButton("📂")
        btn_abrir.setToolTip("Abrir Imagem")
        btn_abrir.setFixedSize(30, 24)
        btn_salvar = QPushButton("💾")
        btn_salvar.setToolTip("Salvar")
        btn_salvar.setFixedSize(30, 24)
        btn_desfazer = QPushButton("↩️")
        btn_desfazer.setToolTip("Desfazer")
        btn_desfazer.setFixedSize(30, 24)
        btn_refazer = QPushButton("↪️")
        btn_refazer.setToolTip("Refazer")
        btn_refazer.setFixedSize(30, 24)
        
        btn_abrir.clicked.connect(self.abrir_imagem)
        btn_salvar.clicked.connect(self.salvar_imagem)
        btn_desfazer.clicked.connect(self.desfazer_imagem)
        btn_refazer.clicked.connect(self.refazer_imagem)
        
        layout_edicao.addWidget(btn_abrir)
        layout_edicao.addWidget(btn_salvar)
        layout_edicao.addWidget(btn_desfazer)
        layout_edicao.addWidget(btn_refazer)
        layout_edicao.addStretch()
        
        # ========== TOOLBAR PARA CÍRCULO ==========
        self.toolbar_circulo = QWidget()
        self.toolbar_circulo.setFixedHeight(35)
        layout_circulo = QHBoxLayout()
        layout_circulo.setContentsMargins(5, 2, 5, 2)
        layout_circulo.setSpacing(10)
        self.toolbar_circulo.setLayout(layout_circulo)
        
        # Botões de seleção
        self.btn_circulo = QPushButton("⭕")
        self.btn_circulo.setToolTip("Modo Círculo")
        self.btn_circulo.setCheckable(True)
        self.btn_circulo.setChecked(True)
        self.btn_circulo.setFixedSize(35, 30)
        self.btn_circulo.clicked.connect(self.definir_modo_circulo)
        
        self.btn_retangulo_circle = QPushButton("⬜")
        self.btn_retangulo_circle.setToolTip("Modo Retângulo")
        self.btn_retangulo_circle.setCheckable(True)
        self.btn_retangulo_circle.setFixedSize(35, 30)
        self.btn_retangulo_circle.clicked.connect(self.definir_modo_retangulo)
        
        layout_circulo.addWidget(self.btn_circulo)
        layout_circulo.addWidget(self.btn_retangulo_circle)
        layout_circulo.addWidget(self._create_separator())
        
        # Slider de tamanho para círculo
        label_tamanho = QLabel("Tamanho:")
        layout_circulo.addWidget(label_tamanho)
        
        self.slider_tamanho_circulo = QSlider(Qt.Orientation.Horizontal)
        self.slider_tamanho_circulo.setMinimum(10)
        self.slider_tamanho_circulo.setMaximum(200)
        self.slider_tamanho_circulo.setValue(20)
        self.slider_tamanho_circulo.setFixedWidth(200)
        self.slider_tamanho_circulo.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_tamanho_circulo.setTickInterval(20)
        
        # Preview visível enquanto arrasta o slider
        self.slider_tamanho_circulo.sliderPressed.connect(self._on_slider_pressed)
        self.slider_tamanho_circulo.sliderReleased.connect(self._on_slider_released)
        self.slider_tamanho_circulo.valueChanged.connect(self._on_circulo_size_changed)
        
        layout_circulo.addWidget(self.slider_tamanho_circulo)
        
        self.label_tamanho_circulo = QLabel("20px")
        self.label_tamanho_circulo.setMinimumWidth(50)
        self.label_tamanho_circulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_circulo.addWidget(self.label_tamanho_circulo)
        
        layout_circulo.addStretch()
        
        # ========== TOOLBAR PARA RETÂNGULO ==========
        self.toolbar_retangulo = QWidget()
        self.toolbar_retangulo.setFixedHeight(35)
        layout_retangulo = QHBoxLayout()
        layout_retangulo.setContentsMargins(5, 2, 5, 2)
        layout_retangulo.setSpacing(10)
        self.toolbar_retangulo.setLayout(layout_retangulo)
        
        # Botões de seleção
        self.btn_circulo_rect = QPushButton("⭕")
        self.btn_circulo_rect.setToolTip("Modo Círculo")
        self.btn_circulo_rect.setCheckable(True)
        self.btn_circulo_rect.setFixedSize(35, 30)
        self.btn_circulo_rect.clicked.connect(self.definir_modo_circulo)
        
        self.btn_retangulo = QPushButton("⬜")
        self.btn_retangulo.setToolTip("Modo Retângulo")
        self.btn_retangulo.setCheckable(True)
        self.btn_retangulo.setChecked(True)
        self.btn_retangulo.setFixedSize(35, 30)
        self.btn_retangulo.clicked.connect(self.definir_modo_retangulo)
        
        layout_retangulo.addWidget(self.btn_circulo_rect)
        layout_retangulo.addWidget(self.btn_retangulo)
        layout_retangulo.addWidget(self._create_separator())
        
        # Slider de LARGURA
        label_largura = QLabel("Largura:")
        layout_retangulo.addWidget(label_largura)
        
        self.slider_largura = QSlider(Qt.Orientation.Horizontal)
        self.slider_largura.setMinimum(10)
        self.slider_largura.setMaximum(200)
        self.slider_largura.setValue(20)
        self.slider_largura.setFixedWidth(150)
        self.slider_largura.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_largura.setTickInterval(20)
        
        self.slider_largura.sliderPressed.connect(self._on_slider_pressed)
        self.slider_largura.sliderReleased.connect(self._on_slider_released)
        self.slider_largura.valueChanged.connect(self._on_largura_changed)
        
        layout_retangulo.addWidget(self.slider_largura)
        
        self.label_largura = QLabel("20px")
        self.label_largura.setMinimumWidth(50)
        self.label_largura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_retangulo.addWidget(self.label_largura)
        
        layout_retangulo.addWidget(self._create_separator())
        
        # Slider de ALTURA
        label_altura = QLabel("Altura:")
        layout_retangulo.addWidget(label_altura)
        
        self.slider_altura = QSlider(Qt.Orientation.Horizontal)
        self.slider_altura.setMinimum(10)
        self.slider_altura.setMaximum(200)
        self.slider_altura.setValue(20)
        self.slider_altura.setFixedWidth(150)
        self.slider_altura.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_altura.setTickInterval(20)
        
        self.slider_altura.sliderPressed.connect(self._on_slider_pressed)
        self.slider_altura.sliderReleased.connect(self._on_slider_released)
        self.slider_altura.valueChanged.connect(self._on_altura_changed)
        
        layout_retangulo.addWidget(self.slider_altura)
        
        self.label_altura = QLabel("20px")
        self.label_altura.setMinimumWidth(50)
        self.label_altura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_retangulo.addWidget(self.label_altura)
        
        layout_retangulo.addWidget(self._create_separator())
        
        # Botão trocar dimensões
        btn_trocar = QPushButton("↔️⇅")
        btn_trocar.setToolTip("Trocar Largura ↔ Altura")
        btn_trocar.setFixedSize(40, 30)
        btn_trocar.clicked.connect(self.trocar_dimensoes)
        layout_retangulo.addWidget(btn_trocar)
        
        layout_retangulo.addStretch()
        
        # ========== ADICIONAR AO STACK ==========
        self.toolbar_stack.addWidget(self.toolbar_edicao)
        self.toolbar_stack.addWidget(self.toolbar_circulo)
        self.toolbar_stack.addWidget(self.toolbar_retangulo)
        
        # Iniciar no modo edição
        self.toolbar_stack.setCurrentWidget(self.toolbar_edicao)

    def _create_separator(self):
        """Cria separador vertical para toolbar"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator

    # ========== CALLBACKS DOS SLIDERS ==========

    def _on_slider_pressed(self):
        """Chamado quando usuário CLICA no slider - MOSTRA PREVIEW"""
        self.image_viewer.set_preview_visible(True)
        print("🎚️ Slider pressionado - Preview ativado")

    def _on_slider_released(self):
        """Chamado quando usuário SOLTA o slider - ESCONDE PREVIEW"""
        self.image_viewer.set_preview_visible(False)
        print("🎚️ Slider solto - Preview desativado")

    def _on_circulo_size_changed(self, value):
        """Chamado quando slider de círculo muda"""
        self.point_manager.current_size = value
        self.label_tamanho_circulo.setText(f"{value}px")
        self.image_viewer.update_cursor()
        # Se preview está visível, atualiza
        if hasattr(self.image_viewer, '_show_preview') and self.image_viewer._show_preview:
            self.image_viewer.scene.update()

    def _on_largura_changed(self, value):
        """Chamado quando slider de largura muda"""
        self.point_manager.current_width = value
        self.label_largura.setText(f"{value}px")
        self.image_viewer.update_cursor()
        if hasattr(self.image_viewer, '_show_preview') and self.image_viewer._show_preview:
            self.image_viewer.scene.update()

    def _on_altura_changed(self, value):
        """Chamado quando slider de altura muda"""
        self.point_manager.current_height = value
        self.label_altura.setText(f"{value}px")
        self.image_viewer.update_cursor()
        if hasattr(self.image_viewer, '_show_preview') and self.image_viewer._show_preview:
            self.image_viewer.scene.update()
        
    def setup_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # TOOLBAR DINÂMICA - ALTURA FIXA
        self.setup_dynamic_toolbars()
        self.toolbar_stack.setFixedHeight(37)
        layout.addWidget(self.toolbar_stack)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        left_panel = self.setup_left_panel()
        right_panel = self.setup_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 300])
        
    def setup_left_panel(self):
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.Box)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        self.image_info_label = QLabel("Nenhuma imagem carregada")
        left_layout.addWidget(self.image_info_label)
        
        left_layout.addWidget(self.image_viewer)
        
        measurement_controls = QHBoxLayout()
        
        btn_anterior = QPushButton("↩️ Anterior")
        btn_proximo = QPushButton("↪️ Próximo")
        btn_pular = QPushButton("⏭️ Pular Ponto")
        
        btn_anterior.clicked.connect(self.ponto_anterior)
        btn_proximo.clicked.connect(self.proximo_ponto)
        btn_pular.clicked.connect(self.pular_ponto)
        
        measurement_controls.addWidget(btn_anterior)
        measurement_controls.addWidget(btn_proximo)
        measurement_controls.addWidget(btn_pular)
        
        left_layout.addLayout(measurement_controls)
        
        return left_panel
        
    def setup_right_panel(self):
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.Box)
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        points_label = QLabel("📋 Pontos de Medição:")
        points_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(points_label)
        
        right_layout.addWidget(self.points_table)
        
        hardware_frame = QFrame()
        hardware_frame.setStyleSheet("background-color: #e8f4fd; padding: 10px; border-radius: 5px;")
        hardware_layout = QVBoxLayout()
        hardware_frame.setLayout(hardware_layout)
        
        self.hardware_status = QLabel("🔴 Hardware: Desconectado")
        self.measurement_status = QLabel("📊 Última Medição: ---")
        
        hardware_layout.addWidget(self.hardware_status)
        hardware_layout.addWidget(self.measurement_status)
        
        right_layout.addWidget(hardware_frame)
        
        action_buttons = QVBoxLayout()
        
        btn_analise = QPushButton("📈 Análise Detalhada")
        btn_relatorio = QPushButton("📋 Gerar Relatório")
        btn_compartilhar = QPushButton("🌐 Compartilhar")
        
        btn_analise.clicked.connect(self.analise_detalhada)
        btn_relatorio.clicked.connect(self.gerar_relatorio)
        btn_compartilhar.clicked.connect(self.compartilhar)
        
        action_buttons.addWidget(btn_analise)
        action_buttons.addWidget(btn_relatorio)
        action_buttons.addWidget(btn_compartilhar)
        
        right_layout.addLayout(action_buttons)
        right_layout.addStretch()
        
        return right_panel

    def setup_status_bar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        status_bar.showMessage("Pronto para iniciar")
        
        self.status_hardware = QLabel("🔴 Hardware")
        self.status_medicao = QLabel("ℹ️ Medição Parada")
        self.status_ponto = QLabel("Ponto: --/--")
        self.status_imagem = QLabel("🖼️ Sem imagem")
        self.status_zoom = QLabel("Zoom: 100%")
        self.status_mouse = QLabel("Mouse: (0, 0)")
        
        status_bar.addPermanentWidget(self.status_hardware)
        status_bar.addPermanentWidget(self.status_medicao)
        status_bar.addPermanentWidget(self.status_ponto)
        status_bar.addPermanentWidget(self.status_imagem)
        status_bar.addPermanentWidget(self.status_zoom)
        status_bar.addPermanentWidget(self.status_mouse)

    def connect_signals(self):
        # Conectar sinais apenas se existirem
        if hasattr(self.image_viewer, 'zoom_changed'):
            self.image_viewer.zoom_changed.connect(self._on_zoom_changed_update_cursor)
        if hasattr(self.image_editor, 'image_updated'):
            self.image_editor.image_updated.connect(self.on_image_updated)
        if hasattr(self.image_editor, 'error_occurred'):
            self.image_editor.error_occurred.connect(self.on_image_error)
        if hasattr(self.image_editor, 'dimensions_changed'):
            self.image_editor.dimensions_changed.connect(self.on_dimensions_changed)
        if hasattr(self.image_editor, 'history_changed'):
            self.image_editor.history_changed.connect(self.on_history_changed)
        
        if hasattr(self.image_viewer, 'zoom_changed'):
            self.image_viewer.zoom_changed.connect(self.on_zoom_changed)
        if hasattr(self.image_viewer, 'mouse_position_changed'):
            self.image_viewer.mouse_position_changed.connect(self.on_mouse_position_changed)
        if hasattr(self.image_viewer, 'point_clicked'):
            self.image_viewer.point_clicked.connect(self.on_image_click)
        
        if hasattr(self.point_manager, 'points_changed'):
            self.point_manager.points_changed.connect(self.on_points_changed)
            self.point_manager.points_changed.connect(self.image_viewer.set_points)

    def on_points_changed(self, points):
        self.points_table.update_points(points)

    def on_image_click(self, position: QPointF):
        """Handler para quando o usuário clica na imagem no modo marcação"""
        if self.current_mode == "marcacao":
            point = self.point_manager.add_point(position)
            self.statusBar().showMessage(f"Ponto {point.id} adicionado em ({position.x():.1f}, {position.y():.1f})")
            print(f"🎯 Ponto {point.id} adicionado na posição: {position.x():.1f}, {position.y():.1f}")

    def ativar_modo_edicao(self):
        self.current_mode = "edicao"
        self.btn_editar.setChecked(True)
        self.btn_marcar.setChecked(False)
        self.toolbar_stack.setCurrentWidget(self.toolbar_edicao)
        self.image_viewer.set_points_mode(False)
        self.statusBar().showMessage("Modo: Edição de Imagem")
        print("✏️ Modo Edição ativado")

    def ativar_modo_marcacao(self):
        self.current_mode = "marcacao"
        self.btn_editar.setChecked(False)
        self.btn_marcar.setChecked(True)
        
        # Mostrar toolbar apropriada baseada na forma atual
        if self.point_manager.current_shape == 'circle':
            self.toolbar_stack.setCurrentWidget(self.toolbar_circulo)
        else:
            self.toolbar_stack.setCurrentWidget(self.toolbar_retangulo)
        
        self.image_viewer.set_points_mode(True, self.point_manager.current_shape)
        self.statusBar().showMessage("Modo: Marcação de Pontos - Clique na imagem para adicionar pontos")
        print("🎯 Modo Marcação ativado")

    # ========== MÉTODOS DOS BOTÕES DE FORMA ==========
    
    def definir_modo_circulo(self):
        """Ativa modo círculo e troca toolbar"""
        self.point_manager.current_shape = 'circle'
        
        # Atualizar botões de ambas as toolbars
        self.btn_circulo.setChecked(True)
        self.btn_circulo_rect.setChecked(True)
        self.btn_retangulo_circle.setChecked(False)
        self.btn_retangulo.setChecked(False)
        
        # Trocar para toolbar de círculo
        self.toolbar_stack.setCurrentWidget(self.toolbar_circulo)
        
        self.image_viewer.set_points_mode(True, 'circle')
        self.statusBar().showMessage(f"Modo: Círculo - Ø {self.point_manager.current_size}px")
        print(f"⭕ Modo Círculo ativado - Ø {self.point_manager.current_size}px")

    def definir_modo_retangulo(self):
        """Ativa modo retângulo e troca toolbar"""
        self.point_manager.current_shape = 'rectangle'
        
        # Atualizar botões de ambas as toolbars
        self.btn_circulo.setChecked(False)
        self.btn_circulo_rect.setChecked(False)
        self.btn_retangulo_circle.setChecked(True)
        self.btn_retangulo.setChecked(True)
        
        # Trocar para toolbar de retângulo
        self.toolbar_stack.setCurrentWidget(self.toolbar_retangulo)
        
        self.image_viewer.set_points_mode(True, 'rectangle')
        self.statusBar().showMessage(
            f"Modo: Retângulo - {self.point_manager.current_width}×{self.point_manager.current_height}px"
        )
        print(f"⬜ Modo Retângulo ativado - {self.point_manager.current_width}×{self.point_manager.current_height}px")

    def trocar_dimensoes(self):
        """Troca largura e altura do retângulo"""
        self.point_manager.swap_rectangle_dimensions()
        
        # Atualizar sliders
        self.slider_largura.setValue(self.point_manager.current_width)
        self.slider_altura.setValue(self.point_manager.current_height)
        
        # Atualizar labels
        self.label_largura.setText(f"{self.point_manager.current_width}px")
        self.label_altura.setText(f"{self.point_manager.current_height}px")
        
        # Atualizar cursor
        self.image_viewer.update_cursor()
        
        self.statusBar().showMessage(
            f"Dimensões trocadas: {self.point_manager.current_width}×{self.point_manager.current_height}px"
        )

    # ========== MÉTODOS DE IMAGEM ==========
    
    def abrir_imagem(self):
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
                self.statusBar().showMessage(f"Imagem carregada: {filename}")
                self.status_imagem.setText(f"🖼️ {filename}")
                self.update_image_info()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível carregar a imagem.")
    
    def salvar_imagem(self):
        if not self.image_editor.is_image_loaded():
            QMessageBox.warning(self, "Aviso", "Nenhuma imagem para salvar.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar imagem",
            "",
            get_supported_formats()
        )
        
        if filepath:
            success = self.image_editor.save_image(filepath)
            if success:
                self.statusBar().showMessage(f"Imagem salva: {filepath}")
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível salvar a imagem.")
    
    def desfazer_imagem(self):
        self.image_editor.undo()
    
    def refazer_imagem(self):
        self.image_editor.redo()
    
    def restaurar_original(self):
        if self.image_editor.is_image_loaded():
            self.image_editor.reset_to_original()
    
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
                
            print(f"Aplicando recorte: {crop_rect}")
            success = self.image_editor.apply_crop_selection(crop_rect)
            
            if success:
                self.statusBar().showMessage("Recorte aplicado com sucesso")
                self.image_viewer.set_crop_mode(False)
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível aplicar o recorte. Verifique o console para detalhes.")
                self.image_viewer.set_crop_mode(False)
                
        except Exception as e:
            print(f"Erro em aplicar_recorte: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Erro ao aplicar recorte: {e}")
            self.image_viewer.set_crop_mode(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and hasattr(self.image_viewer, '_crop_mode') and self.image_viewer._crop_mode:
            self.image_viewer.set_crop_mode(False)
            self.statusBar().showMessage("Recorte cancelado")
        else:
            super().keyPressEvent(event)

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
            self.image_editor.resize(
                width_spin.value(), 
                height_spin.value(), 
                keep_ratio_check.isChecked()
            )
    
    def zoom_in(self):
        self.image_viewer.zoom_in()
    
    def zoom_out(self):
        self.image_viewer.zoom_out()
    
    def ajustar_tela(self):
        self.image_viewer.fit_to_view()
    
    def tamanho_real(self):
        self.image_viewer.actual_size()
    
    def update_image_info(self):
        if self.image_editor.is_image_loaded():
            info = self.image_editor.get_file_info()
            dimensions = self.image_editor.get_dimensions()
            self.image_info_label.setText(
                f"{info['filename']} - {dimensions[0]}x{dimensions[1]}"
            )
        else:
            self.image_info_label.setText("Nenhuma imagem carregada")
    
    def on_image_updated(self, pil_image):
        pixmap = pil_to_pixmap(pil_image)
        self.image_viewer.set_pixmap(pixmap)
        self.update_image_info()
    
    def on_image_error(self, error_message):
        QMessageBox.warning(self, "Erro de Imagem", error_message)
        self.statusBar().showMessage(f"Erro: {error_message}")
    
    def on_dimensions_changed(self, dimensions):
        width, height = dimensions
        self.statusBar().showMessage(f"Dimensões alteradas: {width}x{height}")
        self.update_image_info()
    
    def on_history_changed(self, history_info):
        pass
    
    def on_zoom_changed(self, zoom_level):
        self.status_zoom.setText(f"Zoom: {zoom_level:.1%}")
    
    def _on_zoom_changed_update_cursor(self, zoom_level):
        """Atualiza cursor quando o zoom muda - método interno"""
        if hasattr(self.image_viewer, '_points_mode') and self.image_viewer._points_mode:
            self.image_viewer.update_cursor()
            
    def on_mouse_position_changed(self, position):
        x, y = position.x(), position.y()
        self.status_mouse.setText(f"Mouse: ({x:.1f}, {y:.1f})")

    def setup_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('📁 Arquivo')
        file_menu.addAction('Novo Projeto', self.novo_projeto)
        file_menu.addAction('Abrir Projeto', self.abrir_projeto)
        file_menu.addAction('Abrir Imagem', self.abrir_imagem)
        file_menu.addAction('Salvar', self.salvar_projeto)
        file_menu.addAction('Salvar Imagem', self.salvar_imagem)
        file_menu.addSeparator()
        file_menu.addAction('Sair', self.close)
        
        image_menu = menubar.addMenu('🖼️ Imagem')
        image_menu.addAction('Redimensionar', self.redimensionar_imagem)
        image_menu.addAction('Rotacionar 90°', self.rotacionar_90)
        image_menu.addAction('Rotacionar 180°', self.rotacionar_180)
        image_menu.addAction('Espelhar Horizontal', self.espelhar_horizontal)
        image_menu.addAction('Espelhar Vertical', self.espelhar_vertical)
        image_menu.addSeparator()
        image_menu.addAction('Recortar', self.ativar_modo_recorte)
        image_menu.addAction('Desfazer', self.desfazer_imagem)
        image_menu.addAction('Refazer', self.refazer_imagem)
        image_menu.addAction('Restaurar Original', self.restaurar_original)
        
        view_menu = menubar.addMenu('👁️ Visualização')
        view_menu.addAction('Zoom +', self.zoom_in)
        view_menu.addAction('Zoom -', self.zoom_out)
        view_menu.addAction('Ajustar à Tela', self.ajustar_tela)
        view_menu.addAction('Tamanho Real', self.tamanho_real)
        view_menu.addSeparator()
        view_menu.addAction('Mostrar/OCultar Overlay', self.toggle_overlay)
        view_menu.addAction('Legenda de Cores', self.mostrar_legenda)
        
        hardware_menu = menubar.addMenu('🔌 Hardware')
        hardware_menu.addAction('Conectar Multímetro', self.conectar_hardware)
        hardware_menu.addAction('Testar Comunicação', self.testar_comunicacao)
        hardware_menu.addAction('Calibrar', self.calibrar_hardware)

    # ========== MÉTODOS EXISTENTES MANTIDOS ==========
    
    def modo_teste(self):
        self.statusBar().showMessage("Entrando no modo de teste...")
        print("🧪 Modo de teste")
    
    def abrir_configuracoes(self):
        self.statusBar().showMessage("Abrindo configurações...")
        print("⚙️ Configurações")
    
    def novo_projeto(self):
        self.statusBar().showMessage("Criando novo projeto...")
        print("Novo projeto")
    
    def abrir_projeto(self):
        self.statusBar().showMessage("Abrindo projeto...")
        print("📁 Abrir projeto")
    
    def salvar_projeto(self):
        self.statusBar().showMessage("Salvando projeto...")
        print("💾 Salvar projeto")
    
    def conectar_hardware(self):
        self.statusBar().showMessage("Conectando ao hardware...")
        self.hardware_status.setText("🟢 Hardware: Conectado")
        self.status_hardware.setText("🟢 Hardware")
        print("Conectar hardware")
    
    def testar_comunicacao(self):
        self.statusBar().showMessage("Testando comunicação...")
        print("Testar comunicação")
    
    def calibrar_hardware(self):
        self.statusBar().showMessage("Calibrando hardware...")
        print("Calibrar hardware")
    
    def ponto_anterior(self):
        self.statusBar().showMessage("Voltando ao ponto anterior...")
        print("Ponto anterior")
    
    def proximo_ponto(self):
        self.statusBar().showMessage("Avançando para próximo ponto...")
        print("Próximo ponto")
    
    def pular_ponto(self):
        self.statusBar().showMessage("Pulando ponto atual...")
        print("Pular ponto")
    
    def toggle_overlay(self):
        self.statusBar().showMessage("Alternando overlay...")
        print("Toggle overlay")
    
    def mostrar_legenda(self):
        self.statusBar().showMessage("Mostrando legenda...")
        print("Mostrar legenda")
    
    def analise_detalhada(self):
        self.statusBar().showMessage("Gerando análise...")
        print("Análise detalhada")
    
    def gerar_relatorio(self):
        self.statusBar().showMessage("Gerando relatório...")
        print("Gerar relatório")
    
    def compartilhar(self):
        self.statusBar().showMessage("Compartilhando...")
        print("Compartilhar")

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()