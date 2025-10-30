from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel, QSpinBox, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from models.point import Point
from typing import List

class PointsTable(QWidget):
    tolerance_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.tolerance_percent = 5.0
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header com título e controle de tolerância
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📋 Pontos de Medição")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Controle de tolerância
        tol_label = QLabel("Tolerância:")
        header_layout.addWidget(tol_label)
        
        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(0, 100)
        self.tolerance_spin.setValue(5)
        self.tolerance_spin.setSuffix("%")
        self.tolerance_spin.setFixedWidth(70)
        header_layout.addWidget(self.tolerance_spin)
        
        self.btn_apply_tolerance = QPushButton("Aplicar")
        self.btn_apply_tolerance.setFixedWidth(70)
        self.btn_apply_tolerance.clicked.connect(self._on_tolerance_changed)
        header_layout.addWidget(self.btn_apply_tolerance)
        
        layout.addLayout(header_layout)
        
        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Referência", "Comparação", "Diferença (%)"])
        
        # Configurar colunas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Referência
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Comparação
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Diferença
        
        self.table.setMinimumHeight(200)
        self.table.setAlternatingRowColors(True)
        
        # Permitir seleção de linha inteira
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.table)
    
    def _on_tolerance_changed(self):
        """Callback quando tolerância é alterada"""
        self.tolerance_percent = self.tolerance_spin.value()
        self.tolerance_changed.emit(self.tolerance_percent)
        print(f"📊 Tolerância alterada para {self.tolerance_percent}%")
        
        # Redesenhar tabela para atualizar cores
        self._update_row_colors()
    
    def update_points(self, points: List[Point]):
        """Atualiza tabela com lista de pontos"""
        self.table.setRowCount(len(points))
        
        for row, point in enumerate(points):
            # ID
            id_item = QTableWidgetItem(str(point.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # Referência
            ref_value = self._format_voltage(point.medicao_referencia)
            ref_item = QTableWidgetItem(ref_value)
            ref_item.setFlags(ref_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, ref_item)
            
            # Comparação
            comp_value = self._format_voltage(point.medicao_comparacao)
            comp_item = QTableWidgetItem(comp_value)
            comp_item.setFlags(comp_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            comp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, comp_item)
            
            # Diferença (%)
            diff_percent = point.calcular_diferenca_percentual()
            if diff_percent is not None:
                diff_text = f"{diff_percent:+.1f}%"
            else:
                diff_text = "---"
            
            diff_item = QTableWidgetItem(diff_text)
            diff_item.setFlags(diff_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            diff_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, diff_item)
            
            # Colorir linha se diferença acima da tolerância
            if point.esta_acima_tolerancia(self.tolerance_percent):
                self._set_row_color(row, QColor(255, 182, 193))  # Rosa claro
            else:
                self._set_row_color(row, QColor(255, 255, 255))  # Branco
    
    def _update_row_colors(self):
        """Atualiza cores das linhas baseado na tolerância atual"""
        # Precisa reprocessar com a nova tolerância
        # Este método será chamado após tolerance_changed signal
        pass
    
    def _set_row_color(self, row: int, color: QColor):
        """Define cor de fundo de uma linha inteira"""
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(color)
    
    def _format_voltage(self, value: float) -> str:
        """Formata valor de tensão para display"""
        if value is None:
            return "---"
        return f"{value:.3f}V"
    
    def get_selected_point_id(self) -> int:
        """Retorna ID do ponto selecionado na tabela"""
        selected_rows = self.table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            id_item = self.table.item(row, 0)
            if id_item:
                return int(id_item.text())
        return -1
    
    def clear(self):
        """Limpa tabela"""
        self.table.setRowCount(0)