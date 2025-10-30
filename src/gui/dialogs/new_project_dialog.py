"""
Dialog WYSIWYG para novo projeto com botões separados para evitar clique acidental
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Novo Projeto")
        self.setModal(True)
        self.setFixedSize(400, 320)
        self.result_action = 'cancel'  # 'save', 'discard', 'cancel'
        self.setup_ui()
        
    def setup_ui(self):
        """Configura interface WYSIWYG"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)
        self.setLayout(layout)
        
        # Ícone de aviso
        icon_label = QLabel("⚠️")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        layout.addWidget(icon_label)
        
        # Título
        title = QLabel("Alterações Não Salvas")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Linha separadora
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ccc;")
        layout.addWidget(line)
        
        # Mensagem explicativa
        message = QLabel(
            "O projeto atual possui alterações não salvas.\n\n"
            "O que deseja fazer?"
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("color: #555; line-height: 1.4;")
        message_font = QFont()
        message_font.setPointSize(11)
        message.setFont(message_font)
        layout.addWidget(message)
        
        layout.addStretch()
        
        # Container para botões com espaçamento estratégico
        buttons_container = QVBoxLayout()
        buttons_container.setSpacing(15)
        
        # BOTÃO 1: DESCARTAR (TOPO - Destrutivo, mas separado)
        discard_btn = QPushButton("🗑️ Descartar alterações")
        discard_btn.setFixedHeight(45)
        discard_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                color: #c62828;
                border: 2px solid #ffcdd2;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
                border-color: #ef5350;
            }
        """)
        discard_btn.clicked.connect(self.discard_changes)
        
        # ESPAÇADOR VISUAL
        spacer1 = QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        # BOTÃO 2: CANCELAR (MEIO - Neutro)
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.setFixedHeight(45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #424242;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eeeeee;
                border-color: #bdbdbd;
            }
        """)
        cancel_btn.clicked.connect(self.cancel_action)
        
        # ESPAÇADOR VISUAL
        spacer2 = QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        # BOTÃO 3: SALVAR (BAIXO - Ação principal/segura)
        save_btn = QPushButton("💾 Salvar e criar novo projeto")
        save_btn.setFixedHeight(45)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f5e8;
                color: #2e7d32;
                border: 2px solid #c8e6c9;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
                border-color: #4caf50;
            }
        """)
        save_btn.clicked.connect(self.save_changes)
        save_btn.setDefault(True)  # Botão padrão (Enter)
        
        # Adicionar botões com espaçadores
        buttons_container.addWidget(discard_btn)
        buttons_container.addItem(spacer1)
        buttons_container.addWidget(cancel_btn)
        buttons_container.addItem(spacer2)
        buttons_container.addWidget(save_btn)
        
        layout.addLayout(buttons_container)
        
        # Adicionar dica visual
        hint = QLabel("💡 Dica: Use Enter para salvar, Esc para cancelar")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #888; font-size: 10px; margin-top: 10px;")
        layout.addWidget(hint)
        
    def save_changes(self):
        """Salvar alterações e criar novo projeto"""
        self.result_action = 'save'
        self.accept()
        
    def discard_changes(self):
        """Descartar alterações e criar novo projeto"""
        self.result_action = 'discard'
        self.accept()
        
    def cancel_action(self):
        """Cancelar criação de novo projeto"""
        self.result_action = 'cancel'
        self.reject()
        
    def get_action(self):
        """Retorna a ação escolhida pelo usuário"""
        return self.result_action
        
    def keyPressEvent(self, event):
        """Intercepta teclas para atalhos"""
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_action()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.save_changes()
        else:
            super().keyPressEvent(event)
