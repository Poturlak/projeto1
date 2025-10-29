# main.py - ATUALIZADO COM TOOLBAR DINÂMICA

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QStatusBar,
                            QToolBar, QFrame, QSplitter, QSpacerItem, QSizePolicy,
                            QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
                            QSpinBox, QCheckBox, QFormLayout, QStackedWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction

# Importações dos novos módulos
from image_processing.image_editor import ImageEditor
from gui.image_viewer import ImageViewer
from utils.image_utils import pil_to_pixmap, get_supported_formats


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multímetro Inteligente - v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # Inicializar sistema de imagem
        self.image_editor = ImageEditor()
        self.image_viewer = ImageViewer()
        
        # Sistema de toolbar dinâmica
        self.toolbar_stack = QStackedWidget()
        self.current_mode = "edicao"  # "edicao" ou "marcacao"
        
        self.setup_ui()
        self.connect_image_signals()
        
    def setup_ui(self):
        # Barra de menu principal
        self.setup_menu_bar()
        
        # Barra de ferramentas principal (ATUALIZADA)
        self.setup_toolbars()
        
        # Área central COM TOOLBAR DINÂMICA
        self.setup_central_widget()
        
        # Barra de status
        self.setup_status_bar()
        
    def setup_toolbars(self):
        """BARRA SUPERIOR ATUALIZADA - 3 botões principais + configurações"""
        main_toolbar = QToolBar("Principal")
        self.addToolBar(main_toolbar)
        
        # === 3 BOTÕES PRINCIPAIS ===
        
        # 1. Botão EDIÇÃO DE IMAGEM (Lápis) ✏️
        self.btn_editar = QPushButton('✏️ Editar Imagem')
        self.btn_editar.setToolTip("Modo Edição de Imagem")
        self.btn_editar.setCheckable(True)
        self.btn_editar.setChecked(True)
        self.btn_editar.clicked.connect(self.ativar_modo_edicao)
        main_toolbar.addWidget(self.btn_editar)
        
        # 2. Botão MARCAÇÃO DE PONTOS (Alvo) 🎯
        self.btn_marcar = QPushButton('🎯 Marcar Pontos')
        self.btn_marcar.setToolTip("Modo Marcação de Pontos")
        self.btn_marcar.setCheckable(True)
        self.btn_marcar.clicked.connect(self.ativar_modo_marcacao)
        main_toolbar.addWidget(self.btn_marcar)
        
        # 3. Botão MODO DE TESTE (Teste) 🧪
        btn_teste = QPushButton('🧪 Modo Teste')
        btn_teste.setToolTip("Modo de Teste")
        btn_teste.clicked.connect(self.modo_teste)
        main_toolbar.addWidget(btn_teste)
        
        # Botões de navegação de imagem
        main_toolbar.addSeparator()
        
        btn_zoom_in = QPushButton('➕')
        btn_zoom_in.setToolTip("Zoom In")
        btn_zoom_in.clicked.connect(self.zoom_in)
        main_toolbar.addWidget(btn_zoom_in)
        
        btn_zoom_out = QPushButton('➖')
        btn_zoom_out.setToolTip("Zoom Out")
        btn_zoom_out.clicked.connect(self.zoom_out)
        main_toolbar.addWidget(btn_zoom_out)
        
        btn_fit = QPushButton('📐')
        btn_fit.setToolTip("Ajustar à Tela")
        btn_fit.clicked.connect(self.ajustar_tela)
        main_toolbar.addWidget(btn_fit)
        
        # === ESPAÇADOR ===
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        main_toolbar.addWidget(spacer)
        
        # === BOTÃO CONFIGURAÇÕES ===
        btn_config = QPushButton('⚙️ Configurações')
        btn_config.setToolTip("Configurações")
        btn_config.clicked.connect(self.abrir_configuracoes)
        main_toolbar.addWidget(btn_config)
        
    def setup_central_widget(self):
        """Área central COM TOOLBAR DINÂMICA"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # === TOOLBAR DINÂMICA (STACKED WIDGET) ===
        self.setup_dynamic_toolbars()
        layout.addWidget(self.toolbar_stack)
        
        # Splitter para área principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Painel Esquerdo - Visualização da Placa
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.Box)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Label de informações
        self.image_info_label = QLabel("Nenhuma imagem carregada")
        left_layout.addWidget(self.image_info_label)
        
        # ImageViewer
        left_layout.addWidget(self.image_viewer)
        
        # Controles de medição abaixo da imagem
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
        
        # Painel Direito - Controles e Informações (mantido igual)
        right_panel = self.setup_right_panel()
        
        # Adiciona painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 300])
        
    def setup_dynamic_toolbars(self):
        """Configura as toolbars dinâmicas no stacked widget"""
        
        # === TOOLBAR 1: EDIÇÃO DE IMAGEM ===
        self.toolbar_edicao = QWidget()
        layout_edicao = QHBoxLayout()
        self.toolbar_edicao.setLayout(layout_edicao)
        
        btn_abrir = QPushButton("📁 Abrir Imagem")
        btn_salvar = QPushButton("💾 Salvar")
        btn_desfazer = QPushButton("↩️ Desfazer")
        btn_refazer = QPushButton("↪️ Refazer")
        
        btn_abrir.clicked.connect(self.abrir_imagem)
        btn_salvar.clicked.connect(self.salvar_imagem)
        btn_desfazer.clicked.connect(self.desfazer_imagem)
        btn_refazer.clicked.connect(self.refazer_imagem)
        
        layout_edicao.addWidget(btn_abrir)
        layout_edicao.addWidget(btn_salvar)
        layout_edicao.addWidget(btn_desfazer)
        layout_edicao.addWidget(btn_refazer)
        layout_edicao.addStretch()
        
        # === TOOLBAR 2: MARCAÇÃO DE PONTOS ===
        self.toolbar_marcacao = QWidget()
        layout_marcacao = QHBoxLayout()
        self.toolbar_marcacao.setLayout(layout_marcacao)
        
        # Botões da barra de marcação
        btn_circulo = QPushButton("⭕ Círculo")
        btn_retangulo = QPushButton("⬜ Retângulo")
        btn_mais = QPushButton("➕ +")
        btn_menos = QPushButton("➖ -")
        btn_girar = QPushButton("🔄 Girar")
        btn_comprimento = QPushButton("📏 Comprimento")
        
        # Conectar botões (por enquanto só mudam o status)
        btn_circulo.clicked.connect(lambda: self.statusBar().showMessage("Modo: Círculo"))
        btn_retangulo.clicked.connect(lambda: self.statusBar().showMessage("Modo: Retângulo"))
        btn_mais.clicked.connect(lambda: self.statusBar().showMessage("Adicionar ponto"))
        btn_menos.clicked.connect(lambda: self.statusBar().showMessage("Remover ponto"))
        btn_girar.clicked.connect(lambda: self.statusBar().showMessage("Girar retângulo"))
        btn_comprimento.clicked.connect(lambda: self.statusBar().showMessage("Medir comprimento"))
        
        layout_marcacao.addWidget(btn_circulo)
        layout_marcacao.addWidget(btn_retangulo)
        layout_marcacao.addWidget(btn_mais)
        layout_marcacao.addWidget(btn_menos)
        layout_marcacao.addWidget(btn_girar)
        layout_marcacao.addWidget(btn_comprimento)
        layout_marcacao.addStretch()
        
        # Adiciona as toolbars ao stacked widget
        self.toolbar_stack.addWidget(self.toolbar_edicao)
        self.toolbar_stack.addWidget(self.toolbar_marcacao)
        
        # Define a toolbar inicial (edição)
        self.toolbar_stack.setCurrentWidget(self.toolbar_edicao)
        
    def setup_right_panel(self):
        """Configura o painel direito (mantido do código original)"""
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.Box)
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Status do Hardware
        hardware_frame = QFrame()
        hardware_frame.setStyleSheet("background-color: #e8f4fd; padding: 10px; border-radius: 5px;")
        hardware_layout = QVBoxLayout()
        hardware_frame.setLayout(hardware_layout)
        
        self.hardware_status = QLabel("🔴 Hardware: Desconectado")
        self.measurement_status = QLabel("📊 Última Medição: ---")
        
        hardware_layout.addWidget(self.hardware_status)
        hardware_layout.addWidget(self.measurement_status)
        
        right_layout.addWidget(hardware_frame)
        
        # Controles de Imagem
        image_controls_frame = QFrame()
        image_controls_frame.setStyleSheet("background-color: #f0f8ff; padding: 10px; border-radius: 5px;")
        image_controls_layout = QVBoxLayout()
        image_controls_frame.setLayout(image_controls_layout)
        
        image_controls_label = QLabel("🖼️ Controles de Imagem:")
        image_controls_label.setStyleSheet("font-weight: bold;")
        image_controls_layout.addWidget(image_controls_label)
        
        btn_rotacionar = QPushButton("🔄 Rotacionar 90°")
        btn_espelhar_h = QPushButton("↔️ Espelhar Horizontal")
        btn_espelhar_v = QPushButton("↕️ Espelhar Vertical")
        btn_recortar = QPushButton("✂️ Ativar Recorte")
        btn_redimensionar = QPushButton("📏 Redimensionar")
        
        btn_rotacionar.clicked.connect(self.rotacionar_90)
        btn_espelhar_h.clicked.connect(self.espelhar_horizontal)
        btn_espelhar_v.clicked.connect(self.espelhar_vertical)
        btn_recortar.clicked.connect(self.ativar_modo_recorte)
        btn_redimensionar.clicked.connect(self.redimensionar_imagem)
        
        image_controls_layout.addWidget(btn_rotacionar)
        image_controls_layout.addWidget(btn_espelhar_h)
        image_controls_layout.addWidget(btn_espelhar_v)
        image_controls_layout.addWidget(btn_recortar)
        image_controls_layout.addWidget(btn_redimensionar)
        
        right_layout.addWidget(image_controls_frame)
        
        # Lista de Pontos
        points_frame = QFrame()
        points_layout = QVBoxLayout()
        points_frame.setLayout(points_layout)
        
        points_label = QLabel("📋 Pontos de Medição:")
        points_label.setStyleSheet("font-weight: bold;")
        points_layout.addWidget(points_label)
        
        self.points_list = QLabel("1. VCC_CPU\n2. GND_MAIN\n3. VCC_GPU\n...")
        points_layout.addWidget(self.points_list)
        
        right_layout.addWidget(points_frame)
        
        # Botões de Ação Rápidos
        action_buttons = QVBoxLayout()
        
        btn_analise = QPushButton("📈 Análise Detalhada")
        btn_relatorio = QPushButton("📋 Gerar Relatório")
        btn_comunidade = QPushButton("🌐 Compartilhar")
        
        btn_analise.clicked.connect(self.analise_detalhada)
        btn_relatorio.clicked.connect(self.gerar_relatorio)
        btn_comunidade.clicked.connect(self.compartilhar)
        
        action_buttons.addWidget(btn_analise)
        action_buttons.addWidget(btn_relatorio)
        action_buttons.addWidget(btn_comunidade)
        
        right_layout.addLayout(action_buttons)
        right_layout.addStretch()
        
        return right_panel

    # === NOVOS MÉTODOS PARA CONTROLE DE MODO ===
    
    def ativar_modo_edicao(self):
        """Ativa o modo de edição de imagem"""
        self.current_mode = "edicao"
        self.btn_editar.setChecked(True)
        self.btn_marcar.setChecked(False)
        self.toolbar_stack.setCurrentWidget(self.toolbar_edicao)
        self.statusBar().showMessage("Modo: Edição de Imagem")
        print("✏️ Modo Edição ativado")
    
    def ativar_modo_marcacao(self):
        """Ativa o modo de marcação de pontos"""
        self.current_mode = "marcacao"
        self.btn_editar.setChecked(False)
        self.btn_marcar.setChecked(True)
        self.toolbar_stack.setCurrentWidget(self.toolbar_marcacao)
        self.statusBar().showMessage("Modo: Marcação de Pontos")
        print("🎯 Modo Marcação ativado")

    # === MÉTODOS EXISTENTES MANTIDOS ===
    
    def connect_image_signals(self):
        """Conecta os signals do sistema de imagem"""
        self.image_editor.image_updated.connect(self.on_image_updated)
        self.image_editor.error_occurred.connect(self.on_image_error)
        self.image_editor.dimensions_changed.connect(self.on_dimensions_changed)
        self.image_editor.history_changed.connect(self.on_history_changed)
        
        self.image_viewer.zoom_changed.connect(self.on_zoom_changed)
        self.image_viewer.mouse_position_changed.connect(self.on_mouse_position_changed)
    
    def setup_menu_bar(self):
        """Menu bar com opções de imagem"""
        menubar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menubar.addMenu('📁 Arquivo')
        file_menu.addAction('Novo Projeto', self.novo_projeto)
        file_menu.addAction('Abrir Projeto', self.abrir_projeto)
        file_menu.addAction('Abrir Imagem', self.abrir_imagem)
        file_menu.addAction('Salvar', self.salvar_projeto)
        file_menu.addAction('Salvar Imagem', self.salvar_imagem)
        file_menu.addSeparator()
        file_menu.addAction('Sair', self.close)
        
        # Menu Imagem
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
        
        # Menu Visualização
        view_menu = menubar.addMenu('👁️ Visualização')
        view_menu.addAction('Zoom +', self.zoom_in)
        view_menu.addAction('Zoom -', self.zoom_out)
        view_menu.addAction('Ajustar à Tela', self.ajustar_tela)
        view_menu.addAction('Tamanho Real', self.tamanho_real)
        view_menu.addSeparator()
        view_menu.addAction('Mostrar/OCultar Overlay', self.toggle_overlay)
        view_menu.addAction('Legenda de Cores', self.mostrar_legenda)
        
        # Menu Hardware
        hardware_menu = menubar.addMenu('🔌 Hardware')
        hardware_menu.addAction('Conectar Multímetro', self.conectar_hardware)
        hardware_menu.addAction('Testar Comunicação', self.testar_comunicacao)
        hardware_menu.addAction('Calibrar', self.calibrar_hardware)
    
    def setup_status_bar(self):
        """Barra de status expandida"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Status permanente
        status_bar.showMessage("Pronto para iniciar")
        
        # Indicadores de status
        self.status_hardware = QLabel("🔴 Hardware")
        self.status_medicao = QLabel("⏹️ Medição Parada")
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

    # === MÉTODOS DE IMAGEM (MANTIDOS) ===
    
    def abrir_imagem(self):
        """Abre diálogo para carregar imagem"""
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
        """Salva imagem atual"""
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
        """Desfaz última operação na imagem"""
        self.image_editor.undo()
    
    def refazer_imagem(self):
        """Refaz operação desfeita na imagem"""
        self.image_editor.redo()
    
    def restaurar_original(self):
        """Restaura imagem original"""
        if self.image_editor.is_image_loaded():
            self.image_editor.reset_to_original()
    
    def rotacionar_90(self):
        """Rotaciona imagem 90° no sentido horário"""
        if self.image_editor.is_image_loaded():
            self.image_editor.rotate_90(clockwise=True)
    
    def rotacionar_180(self):
        """Rotaciona imagem 180°"""
        if self.image_editor.is_image_loaded():
            self.image_editor.rotate(180)
    
    def espelhar_horizontal(self):
        """Espelha imagem horizontalmente"""
        if self.image_editor.is_image_loaded():
            self.image_editor.flip(horizontal=True)
    
    def espelhar_vertical(self):
        """Espelha imagem verticalmente"""
        if self.image_editor.is_image_loaded():
            self.image_editor.flip(horizontal=False)
    
    def ativar_modo_recorte(self):
        """Ativa modo de recorte"""
        if self.image_editor.is_image_loaded():
            try:
                self.image_viewer.crop_selection_finished.disconnect()
            except:
                pass
                
            self.image_viewer.set_crop_mode(True)
            self.statusBar().showMessage("Modo recorte ativado - Arraste para selecionar área, ESC para cancelar")
            self.image_viewer.crop_selection_finished.connect(self.aplicar_recorte)
        else:
            QMessageBox.warning(self, "Aviso", "Carregue uma imagem primeiro.")

    def aplicar_recorte(self, crop_rect):
        """Aplica o recorte quando a seleção é finalizada"""
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
        """Handle global key events"""
        if event.key() == Qt.Key.Key_Escape and self.image_viewer._crop_mode:
            self.image_viewer.set_crop_mode(False)
            self.statusBar().showMessage("Recorte cancelado")
        else:
            super().keyPressEvent(event)

    def redimensionar_imagem(self):
        """Abre diálogo para redimensionar imagem"""
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
        """Aumenta zoom"""
        self.image_viewer.zoom_in()
    
    def zoom_out(self):
        """Diminui zoom"""
        self.image_viewer.zoom_out()
    
    def ajustar_tela(self):
        """Ajusta imagem à tela"""
        self.image_viewer.fit_to_view()
    
    def tamanho_real(self):
        """Mostra imagem em tamanho real"""
        self.image_viewer.actual_size()
    
    def update_image_info(self):
        """Atualiza informações da imagem na UI"""
        if self.image_editor.is_image_loaded():
            info = self.image_editor.get_file_info()
            dimensions = self.image_editor.get_dimensions()
            self.image_info_label.setText(
                f"{info['filename']} - {dimensions[0]}x{dimensions[1]}"
            )
        else:
            self.image_info_label.setText("Nenhuma imagem carregada")
    
    # === SLOTS DE SINAIS DE IMAGEM ===
    
    def on_image_updated(self, pil_image):
        """Atualiza a visualização quando a imagem é editada"""
        pixmap = pil_to_pixmap(pil_image)
        self.image_viewer.set_pixmap(pixmap)
        self.update_image_info()
    
    def on_image_error(self, error_message):
        """Trata erros de processamento de imagem"""
        QMessageBox.warning(self, "Erro de Imagem", error_message)
        self.statusBar().showMessage(f"Erro: {error_message}")
    
    def on_dimensions_changed(self, dimensions):
        """Atualiza UI quando dimensões mudam"""
        width, height = dimensions
        self.statusBar().showMessage(f"Dimensões alteradas: {width}x{height}")
        self.update_image_info()
    
    def on_history_changed(self, history_info):
        """Atualiza estado dos botões de undo/redo"""
        pass
    
    def on_zoom_changed(self, zoom_level):
        """Atualiza indicador de zoom"""
        self.status_zoom.setText(f"Zoom: {zoom_level:.1%}")
    
    def on_mouse_position_changed(self, position):
        """Atualiza posição do mouse"""
        x, y = position.x(), position.y()
        self.status_mouse.setText(f"Mouse: ({x:.1f}, {y:.1f})")
    
    # === MÉTODOS EXISTENTES MANTIDOS ===
    
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