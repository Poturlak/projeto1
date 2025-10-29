import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QStatusBar,
                            QToolBar, QFrame, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multímetro Inteligente - v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Barra de menu principal
        self.setup_menu_bar()
        
        # Barra de ferramentas principal
        self.setup_toolbars()
        
        # Área central
        self.setup_central_widget()
        
        # Barra de status
        self.setup_status_bar()
        
    def setup_menu_bar(self):
        menubar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menubar.addMenu('📁 Arquivo')
        file_menu.addAction('Novo Projeto', self.novo_projeto)
        file_menu.addAction('Abrir Projeto', self.abrir_projeto)
        file_menu.addAction('Salvar', self.salvar_projeto)
        file_menu.addSeparator()
        file_menu.addAction('Sair', self.close)
        
        # Menu Hardware
        hardware_menu = menubar.addMenu('🔌 Hardware')
        hardware_menu.addAction('Conectar Multímetro', self.conectar_hardware)
        hardware_menu.addAction('Testar Comunicação', self.testar_comunicacao)
        hardware_menu.addAction('Calibrar', self.calibrar_hardware)
        
        # Menu Visualização
        view_menu = menubar.addMenu('👁️ Visualização')
        view_menu.addAction('Mostrar/OCultar Overlay', self.toggle_overlay)
        view_menu.addAction('Legenda de Cores', self.mostrar_legenda)
        
    def setup_toolbars(self):
        # Toolbar Principal
        main_toolbar = QToolBar("Principal")
        self.addToolBar(main_toolbar)
        
        # Botões de Projeto
        main_toolbar.addAction('📁', self.novo_projeto).setToolTip("Novo Projeto")
        main_toolbar.addAction('📂', self.abrir_projeto).setToolTip("Abrir Projeto")
        main_toolbar.addAction('💾', self.salvar_projeto).setToolTip("Salvar Projeto")
        main_toolbar.addSeparator()
        
        # Botões de Hardware
        main_toolbar.addAction('🔗', self.conectar_hardware).setToolTip("Conectar Multímetro")
        main_toolbar.addAction('🎛️', self.calibrar_hardware).setToolTip("Calibrar Hardware")
        main_toolbar.addSeparator()
        
        # Botões de Medição
        main_toolbar.addAction('▶️', self.iniciar_medicao).setToolTip("Iniciar Medição")
        main_toolbar.addAction('⏸️', self.pausar_medicao).setToolTip("Pausar Medição")
        main_toolbar.addAction('⏹️', self.parar_medicao).setToolTip("Parar Medição")
        
        # Toolbar Secundária (Visualização)
        view_toolbar = QToolBar("Visualização")
        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, view_toolbar)
        
        view_toolbar.addAction('🎨', self.toggle_overlay).setToolTip("Toggle Overlay")
        view_toolbar.addAction('🔍', self.zoom_in).setToolTip("Zoom In")
        view_toolbar.addAction('🔎', self.zoom_out).setToolTip("Zoom Out")
        view_toolbar.addAction('🔄', self.reset_view).setToolTip("Reset Visualização")
        
    def setup_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Splitter para área principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Painel Esquerdo - Visualização da Placa
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.Box)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Label para imagem da placa (placeholder)
        self.image_label = QLabel("Área de Visualização da Placa\n\n🖼️ Imagem será carregada aqui")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #ccc; min-height: 400px;")
        left_layout.addWidget(self.image_label)
        
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
        
        # Painel Direito - Controles e Informações
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
        
        # Lista de Pontos
        points_frame = QFrame()
        points_layout = QVBoxLayout()
        points_frame.setLayout(points_layout)
        
        points_label = QLabel("📋 Pontos de Medição:")
        points_label.setStyleSheet("font-weight: bold;")
        points_layout.addWidget(points_label)
        
        # Placeholder para lista de pontos
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
        
        # Adiciona painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 300])
        
    def setup_status_bar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Status permanente
        status_bar.showMessage("Pronto para iniciar")
        
        # Indicadores de status
        self.status_hardware = QLabel("🔴 Hardware")
        self.status_medicao = QLabel("⏹️ Medição Parada")
        self.status_ponto = QLabel("Ponto: --/--")
        
        status_bar.addPermanentWidget(self.status_hardware)
        status_bar.addPermanentWidget(self.status_medicao)
        status_bar.addPermanentWidget(self.status_ponto)
    
    # ===== MÉTODOS DOS BOTÕES =====
    
    def novo_projeto(self):
        self.statusBar().showMessage("Criando novo projeto...")
        print("Novo projeto")
    
    def abrir_projeto(self):
        self.statusBar().showMessage("Abrindo projeto...")
        print("Abrir projeto")
    
    def salvar_projeto(self):
        self.statusBar().showMessage("Salvando projeto...")
        print("Salvar projeto")
    
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
    
    def iniciar_medicao(self):
        self.statusBar().showMessage("Iniciando medição...")
        self.status_medicao.setText("🟢 Medição Ativa")
        print("Iniciar medição")
    
    def pausar_medicao(self):
        self.statusBar().showMessage("Medição pausada")
        self.status_medicao.setText("🟡 Medição Pausada")
        print("Pausar medição")
    
    def parar_medicao(self):
        self.statusBar().showMessage("Medição parada")
        self.status_medicao.setText("⏹️ Medição Parada")
        print("Parar medição")
    
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
    
    def zoom_in(self):
        self.statusBar().showMessage("Aplicando zoom...")
        print("Zoom in")
    
    def zoom_out(self):
        self.statusBar().showMessage("Reduzindo zoom...")
        print("Zoom out")
    
    def reset_view(self):
        self.statusBar().showMessage("Resetando visualização...")
        print("Reset view")
    
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