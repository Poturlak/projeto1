import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QStatusBar,
                            QToolBar, QFrame, QSplitter, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction

# No início do arquivo, adicione:
from image_processing.image_editor import ImageEditor
from gui.image_viewer import ImageViewer
from utils.image_utils import pil_to_pixmap, get_supported_formats


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multímetro Inteligente - v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Barra de menu principal
        self.setup_menu_bar()
        
        # Barra de ferramentas principal (ATUALIZADA)
        self.setup_toolbars()
        
        # Área central
        self.setup_central_widget()
        
        # Barra de status
        self.setup_status_bar()
        
    def setup_menu_bar(self):
        """Menu bar original"""
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
        """BARRA ATUALIZADA - 3 botões principais + configurações"""
        main_toolbar = QToolBar("Principal")
        self.addToolBar(main_toolbar)
        
        # === 3 BOTÕES PRINCIPAIS ===
        
        # 1. Botão EDIÇÃO DE IMAGEM (Lápis) ✏️
        btn_editar = QPushButton('✏️')
        btn_editar.setToolTip("Editar Imagem")
        btn_editar.clicked.connect(self.editar_imagem)
        main_toolbar.addWidget(btn_editar)
        
        # 2. Botão MARCAÇÃO DE PONTOS (Alvo) 🎯
        btn_marcar = QPushButton('🎯')
        btn_marcar.setToolTip("Marcar Pontos na Placa")
        btn_marcar.clicked.connect(self.marcar_pontos)
        main_toolbar.addWidget(btn_marcar)
        
        # 3. Botão MODO DE TESTE (Teste) 🧪
        btn_teste = QPushButton('🧪')
        btn_teste.setToolTip("Modo de Teste")
        btn_teste.clicked.connect(self.modo_teste)
        main_toolbar.addWidget(btn_teste)
        
        # === ESPAÇADOR PARA EMPURRAR O PRÓXIMO BOTÃO PARA DIREITA ===
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        main_toolbar.addWidget(spacer)
        
        # === BOTÃO CONFIGURAÇÕES ===
        
        # 4. Botão CONFIGURAÇÕES (Engrenagem) ⚙️
        btn_config = QPushButton('⚙️')
        btn_config.setToolTip("Configurações")
        btn_config.clicked.connect(self.abrir_configuracoes)
        main_toolbar.addWidget(btn_config)
        
    def setup_central_widget(self):
        """Área central"""
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
        
        # Label para imagem da placa
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
        """Barra de status"""
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
    
    # ===== NOVOS MÉTODOS PARA OS BOTÕES DA BARRA =====
    
    def editar_imagem(self):
        self.statusBar().showMessage("Abrindo editor de imagem...")
        print("✏️ Editar imagem")
    
    def marcar_pontos(self):
        self.statusBar().showMessage("Modo de marcação de pontos ativado...")
        print("🎯 Marcar pontos na placa")
    
    def modo_teste(self):
        self.statusBar().showMessage("Entrando no modo de teste...")
        print("🧪 Modo de teste")
    
    def abrir_configuracoes(self):
        self.statusBar().showMessage("Abrindo configurações...")
        print("⚙️ Configurações")
    
    # ===== MÉTODOS EXISTENTES MANTIDOS =====
    
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