"""
Dialog personalizado para salvar projeto com validação
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QPushButton, QLineEdit, QTextEdit, QCheckBox, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SaveProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💾 Salvar Projeto")
        self.setModal(True)
        self.setFixedSize(450, 350)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura interface do dialog"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Título
        title = QLabel("💾 Salvar Projeto")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Formulário
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Nome do projeto
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: Samsung Galaxy S23 - Cliente João Silva")
        self.name_edit.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        form_layout.addRow("Nome do Projeto:", self.name_edit)
        
        # Modelo do aparelho
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("Ex: SM-G991B")
        self.model_edit.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        form_layout.addRow("Modelo do Aparelho:", self.model_edit)
        
        # Checkbox placa funcional
        self.functional_check = QCheckBox("Placa 100% funcional?")
        self.functional_check.setChecked(True)
        self.functional_check.setStyleSheet("font-weight: bold;")
        self.functional_check.toggled.connect(self.on_functional_changed)
        form_layout.addRow(self.functional_check)
        
        # Campo descrição (inicialmente oculto)
        self.description_label = QLabel("Descrição do Problema:")
        self.description_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Descreva o problema encontrado na placa...")
        self.description_edit.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        
        # Inicialmente ocultos
        self.description_label.setVisible(False)
        self.description_edit.setVisible(False)
        
        form_layout.addRow(self.description_label)
        form_layout.addRow(self.description_edit)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Botões - SEPARADOS para evitar clique acidental
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        
        # Botão Cancelar (topo - neutro)
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        # Espaçamento visual
        spacer = QLabel()
        spacer.setFixedHeight(10)
        
        # Botão Salvar (baixo - ação principal)
        save_btn = QPushButton("✅ Salvar Projeto")
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.validate_and_accept)
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(spacer)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Foco inicial no nome
        self.name_edit.setFocus()
        
    def on_functional_changed(self, checked):
        """Mostrar/ocultar campo de descrição baseado na checkbox"""
        is_defective = not checked
        self.description_label.setVisible(is_defective)
        self.description_edit.setVisible(is_defective)
        
        # Ajustar tamanho do dialog
        if is_defective:
            self.setFixedSize(450, 420)
        else:
            self.setFixedSize(450, 350)
            
        # Foco no campo de descrição se aparecer
        if is_defective:
            self.description_edit.setFocus()
            
    def validate_and_accept(self):
        """Valida dados antes de aceitar"""
        # Validar nome
        if not self.name_edit.text().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", "Nome do projeto é obrigatório.")
            self.name_edit.setFocus()
            return
            
        # Validar modelo
        if not self.model_edit.text().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", "Modelo do aparelho é obrigatório.")
            self.model_edit.setFocus()
            return
            
        # Validar descrição se placa não funcional
        if not self.functional_check.isChecked():
            if not self.description_edit.toPlainText().strip():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erro", "Descrição do problema é obrigatória quando a placa não é 100% funcional.")
                self.description_edit.setFocus()
                return
                
        # Tudo válido
        self.accept()
        
    def get_project_data(self):
        """Retorna dados do projeto"""
        return {
            'nome': self.name_edit.text().strip(),
            'modelo': self.model_edit.text().strip(),
            'funcional': self.functional_check.isChecked(),
            'descricao': self.description_edit.toPlainText().strip() if not self.functional_check.isChecked() else ""
        }
