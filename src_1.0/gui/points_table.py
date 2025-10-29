from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from models.point import Point
from typing import List

class PointsTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setup_table()
    
    def setup_table(self):
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["ID", "Descrição", "Diodo", "Resistência", "Tensão"])
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.setMinimumHeight(200)
    
    def update_points(self, points: List[Point]):
        self.setRowCount(len(points))
        
        for row, point in enumerate(points):
            # ID
            id_item = QTableWidgetItem(str(point.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 0, id_item)
            
            # Descrição
            desc_item = QTableWidgetItem(point.description)
            self.setItem(row, 1, desc_item)
            
            # Medições
            diodo_item = QTableWidgetItem(point.get_measurement_display('diodo'))
            diodo_item.setFlags(diodo_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 2, diodo_item)
            
            resistencia_item = QTableWidgetItem(point.get_measurement_display('resistencia'))
            resistencia_item.setFlags(resistencia_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 3, resistencia_item)
            
            tensao_item = QTableWidgetItem(point.get_measurement_display('tensao'))
            tensao_item.setFlags(tensao_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 4, tensao_item)