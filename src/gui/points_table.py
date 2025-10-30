"""
Tabela de pontos com 4 colunas: ID, Referência, Comparação, Diferença (%)
Inclui sistema de tolerância e cores dinâmicas
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QLabel, QSpinBox, QPushButton, 
                            QHeaderView, QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont


class PointsTable(QWidget):
    """Tabela de pontos com sistema de comparação e tolerância"""
    
    tolerance_changed = pyqtSignal(float)
    point_selected = pyqtSignal(int)  # Emitido quando ponto é selecionado
    
    def __init__(self):
        super().__init__()
        self.tolerance = 5.0  # Tolerância padrão: 5%
        self.points_data = []
        self.setup_ui()
        
    def setup_ui(self):
        """Configura interface da tabela"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # ========== CABEÇALHO COM TOLERÂNCIA ==========
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Título
        title = QLabel("📋 Pontos de Medição")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        
        # Espaçador
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Controle de tolerância
        tolerance_label = QLabel("Tolerância:")
        tolerance_label.setStyleSheet("font-weight: bold;")
        
        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(1, 100)
        self.tolerance_spin.setValue(int(self.tolerance))
        self.tolerance_spin.setSuffix("%")
        self.tolerance_spin.setFixedWidth(70)
        self.tolerance_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 2px solid #2196F3;
                border-radius: 4px;
                background-color: white;
                font-weight: bold;
            }
            QSpinBox:focus {
                border-color: #1976D2;
            }
        """)
        
        self.apply_tolerance_btn = QPushButton("Aplicar")
        self.apply_tolerance_btn.setFixedSize(70, 28)
        self.apply_tolerance_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.apply_tolerance_btn.clicked.connect(self.apply_tolerance)
        
        header_layout.addWidget(tolerance_label)
        header_layout.addWidget(self.tolerance_spin)
        header_layout.addWidget(self.apply_tolerance_btn)
        
        layout.addLayout(header_layout)
        
        # Linha separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)
        
        # ========== TABELA COM 4 COLUNAS ==========
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "Referência", "Comparação", "Diferença (%)"
        ])
        
        # Configurações da tabela
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)  # Manter ordem dos pontos
        
        # Estilo da tabela
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                selection-background-color: #E3F2FD;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #BBDEFB;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #2196F3;
                font-weight: bold;
            }
        """)
        
        # Configurar largura das colunas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)        # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)      # Referência
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)      # Comparação
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)      # Diferença
        
        self.table.setColumnWidth(0, 50)  # ID mais estreito
        
        # Conectar sinal de seleção
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table)
        
        # ========== ESTATÍSTICAS (OPCIONAL) ==========
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(20)
        
        self.stats_total = QLabel("Total: 0")
        self.stats_normal = QLabel("🟢 Normal: 0")
        self.stats_diferenca = QLabel("🌸 Diferenças: 0")
        self.stats_sem_medicao = QLabel("⚪ Sem medição: 0")
        
        # Estilo das estatísticas
        stats_style = "padding: 5px; border-radius: 3px; font-weight: bold;"
        self.stats_total.setStyleSheet(stats_style + "background-color: #f0f0f0;")
        self.stats_normal.setStyleSheet(stats_style + "background-color: #e8f5e8;")
        self.stats_diferenca.setStyleSheet(stats_style + "background-color: #ffebee;")
        self.stats_sem_medicao.setStyleSheet(stats_style + "background-color: #f5f5f5;")
        
        self.stats_layout.addWidget(self.stats_total)
        self.stats_layout.addWidget(self.stats_normal)
        self.stats_layout.addWidget(self.stats_diferenca)
        self.stats_layout.addWidget(self.stats_sem_medicao)
        self.stats_layout.addStretch()
        
        layout.addLayout(self.stats_layout)
        
    def update_points(self, points):
        """Atualiza tabela com nova lista de pontos"""
        self.points_data = points
        self._refresh_table()
        
    def _refresh_table(self):
        """Atualiza conteúdo da tabela"""
        # Configurar número de linhas
        self.table.setRowCount(len(self.points_data))
        
        # Limpar tabela
        self.table.clearContents()
        
        # Preencher dados
        for row, point in enumerate(self.points_data):
            self._populate_row(row, point)
        
        # Atualizar estatísticas
        self._update_statistics()
        
        print(f"📋 Tabela atualizada: {len(self.points_data)} pontos")
        
    def _populate_row(self, row, point):
        """Preenche uma linha da tabela com dados do ponto"""
        try:
            # Coluna 0: ID
            id_item = QTableWidgetItem(str(getattr(point, 'id', row + 1)))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 0, id_item)
            
            # Coluna 1: Referência
            ref_value = getattr(point, 'medicao_referencia', None)
            if ref_value is not None:
                ref_text = f"{ref_value:.3f}V"
            else:
                ref_text = "---"
                
            ref_item = QTableWidgetItem(ref_text)
            ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ref_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 1, ref_item)
            
            # Coluna 2: Comparação
            comp_value = getattr(point, 'medicao_comparacao', None)
            if comp_value is not None:
                comp_text = f"{comp_value:.3f}V"
            else:
                comp_text = "---"
                
            comp_item = QTableWidgetItem(comp_text)
            comp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            comp_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 2, comp_item)
            
            # Coluna 3: Diferença (%)
            diff_text = "---"
            if ref_value is not None and comp_value is not None:
                if ref_value != 0:
                    diff_percent = ((comp_value - ref_value) / ref_value) * 100
                    diff_text = f"{diff_percent:+.1f}%"
                else:
                    diff_text = "N/A"
                    
            diff_item = QTableWidgetItem(diff_text)
            diff_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            diff_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 3, diff_item)
            
            # Aplicar cor da linha baseada na diferença
            self._apply_row_color(row, point)
            
        except Exception as e:
            print(f"⚠️  Erro ao preencher linha {row}: {e}")
            
    def _apply_row_color(self, row, point):
        """Aplica cor da linha baseada na tolerância"""
        try:
            # Determinar cor baseada na diferença
            color = self._get_row_color(point)
            
            # Aplicar cor a todas as células da linha
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(color)
                    
        except Exception as e:
            print(f"⚠️  Erro ao aplicar cor na linha {row}: {e}")
            
    def _get_row_color(self, point):
        """Determina cor da linha baseada no status do ponto"""
        ref_value = getattr(point, 'medicao_referencia', None)
        comp_value = getattr(point, 'medicao_comparacao', None)
        
        # Sem medições
        if ref_value is None and comp_value is None:
            return QColor(248, 248, 248)  # Cinza muito claro
        
        # Apenas uma medição
        if ref_value is None or comp_value is None:
            return QColor(255, 255, 255)  # Branco (normal)
        
        # Ambas as medições existem - calcular diferença
        if ref_value != 0:
            diff_percent = abs(((comp_value - ref_value) / ref_value) * 100)
            
            if diff_percent > self.tolerance:
                return QColor(255, 182, 193)  # Rosa claro (LightPink)
            else:
                return QColor(232, 245, 233)  # Verde muito claro
        else:
            return QColor(255, 248, 225)  # Amarelo claro (caso especial: ref = 0)
            
    def _update_statistics(self):
        """Atualiza estatísticas mostradas"""
        if not self.points_data:
            self.stats_total.setText("Total: 0")
            self.stats_normal.setText("🟢 Normal: 0")
            self.stats_diferenca.setText("🌸 Diferenças: 0")
            self.stats_sem_medicao.setText("⚪ Sem medição: 0")
            return
        
        # Contar categorias
        total = len(self.points_data)
        normal = 0
        diferenca = 0
        sem_medicao = 0
        
        for point in self.points_data:
            ref_value = getattr(point, 'medicao_referencia', None)
            comp_value = getattr(point, 'medicao_comparacao', None)
            
            if ref_value is None and comp_value is None:
                sem_medicao += 1
            elif ref_value is not None and comp_value is not None:
                if ref_value != 0:
                    diff_percent = abs(((comp_value - ref_value) / ref_value) * 100)
                    if diff_percent > self.tolerance:
                        diferenca += 1
                    else:
                        normal += 1
                else:
                    normal += 1  # Caso especial
            else:
                normal += 1  # Apenas uma medição
        
        # Atualizar labels
        self.stats_total.setText(f"Total: {total}")
        self.stats_normal.setText(f"🟢 Normal: {normal}")
        self.stats_diferenca.setText(f"🌸 Diferenças: {diferenca}")
        self.stats_sem_medicao.setText(f"⚪ Sem medição: {sem_medicao}")
        
    def apply_tolerance(self):
        """Aplica nova tolerância e recalcula cores"""
        new_tolerance = float(self.tolerance_spin.value())
        
        if new_tolerance != self.tolerance:
            self.tolerance = new_tolerance
            
            # Atualizar cores de todas as linhas
            for row in range(self.table.rowCount()):
                if row < len(self.points_data):
                    self._apply_row_color(row, self.points_data[row])
            
            # Atualizar estatísticas
            self._update_statistics()
            
            # Emitir sinal
            self.tolerance_changed.emit(self.tolerance)
            
            print(f"📊 Tolerância aplicada: {self.tolerance}%")
            
    def set_tolerance(self, tolerance):
        """Define tolerância programaticamente"""
        self.tolerance = tolerance
        self.tolerance_spin.setValue(int(tolerance))
        self.apply_tolerance()
        
    def get_tolerance(self):
        """Retorna tolerância atual"""
        return self.tolerance
        
    def _on_selection_changed(self):
        """Callback quando seleção da tabela muda"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
            
        if selected_rows:
            row = list(selected_rows)[0]  # Primeira linha selecionada
            if row < len(self.points_data):
                point_id = getattr(self.points_data[row], 'id', row + 1)
                self.point_selected.emit(point_id)
                print(f"📋 Ponto selecionado: {point_id}")
                
    def select_point(self, point_id):
        """Seleciona ponto na tabela por ID"""
        for row, point in enumerate(self.points_data):
            if getattr(point, 'id', 0) == point_id:
                self.table.selectRow(row)
                self.table.scrollToItem(self.table.item(row, 0))
                break
                
    def clear_selection(self):
        """Limpa seleção da tabela"""
        self.table.clearSelection()
        
    def highlight_differences_only(self, enabled=True):
        """Destaca apenas pontos com diferenças"""
        if not enabled:
            self._refresh_table()
            return
        
        # Filtrar apenas pontos com diferenças
        for row in range(self.table.rowCount()):
            if row < len(self.points_data):
                point = self.points_data[row]
                
                # Verificar se tem diferença significativa
                has_difference = self._point_has_difference(point)
                
                # Ocultar/mostrar linha
                self.table.setRowHidden(row, not has_difference)
                
    def _point_has_difference(self, point):
        """Verifica se ponto tem diferença acima da tolerância"""
        ref_value = getattr(point, 'medicao_referencia', None)
        comp_value = getattr(point, 'medicao_comparacao', None)
        
        if ref_value is not None and comp_value is not None and ref_value != 0:
            diff_percent = abs(((comp_value - ref_value) / ref_value) * 100)
            return diff_percent > self.tolerance
        
        return False
        
    def export_to_csv(self, filepath):
        """Exporta dados da tabela para CSV"""
        try:
            import csv
            
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Cabeçalho
                headers = []
                for col in range(self.table.columnCount()):
                    headers.append(self.table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Dados
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                    
            print(f"📊 Tabela exportada: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar CSV: {e}")
            return False
            
    def get_comparison_summary(self):
        """Retorna resumo da comparação"""
        if not self.points_data:
            return {
                'total': 0,
                'with_comparison': 0,
                'differences': 0,
                'percentage_different': 0.0
            }
        
        total = len(self.points_data)
        with_comparison = 0
        differences = 0
        
        for point in self.points_data:
            ref_value = getattr(point, 'medicao_referencia', None)
            comp_value = getattr(point, 'medicao_comparacao', None)
            
            if ref_value is not None and comp_value is not None:
                with_comparison += 1
                
                if ref_value != 0:
                    diff_percent = abs(((comp_value - ref_value) / ref_value) * 100)
                    if diff_percent > self.tolerance:
                        differences += 1
        
        percentage_different = (differences / with_comparison * 100) if with_comparison > 0 else 0.0
        
        return {
            'total': total,
            'with_comparison': with_comparison,
            'differences': differences,
            'percentage_different': percentage_different,
            'tolerance': self.tolerance
        }
