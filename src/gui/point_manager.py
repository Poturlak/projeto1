from PyQt6.QtCore import QObject, pyqtSignal
from models.point import Point
from typing import List

class PointManager(QObject):
    point_added = pyqtSignal(Point)
    point_removed = pyqtSignal(int)
    point_updated = pyqtSignal(Point)
    points_changed = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.points: List[Point] = []
        self.next_id = 1
        self.current_shape = 'circle'
        self.current_size = 20
    
    def add_point(self, position, description=""):
        if not description:
            description = f"Ponto {self.next_id}"
            
        # Garantir que o tamanho seja válido
        size = max(10, min(self.current_size, 100))  # Entre 10 e 100 pixels
        
        point = Point(
            id=self.next_id,
            position=position,
            shape=self.current_shape,
            description=description,
            size=size
        )
        self.points.append(point)
        self.next_id += 1
        self.point_added.emit(point)
        self.points_changed.emit(self.points)
        print(f"✅ Ponto {point.id} adicionado - Forma: {point.shape}, Tamanho: {point.size}px")
        return point
    
    def remove_point(self, point_id):
        self.points = [p for p in self.points if p.id != point_id]
        self.point_removed.emit(point_id)
        self.points_changed.emit(self.points)
        print(f"🗑️ Ponto {point_id} removido")
    
    def update_point_measurement(self, point_id, measurement_type, value):
        for point in self.points:
            if point.id == point_id:
                point.measurements[measurement_type] = value
                self.point_updated.emit(point)
                self.points_changed.emit(self.points)
                break
    
    def get_point_by_id(self, point_id):
        for point in self.points:
            if point.id == point_id:
                return point
        return None
    
    def clear_points(self):
        self.points.clear()
        self.next_id = 1
        self.points_changed.emit(self.points)
        print("🧹 Todos os pontos removidos")

from PyQt6.QtCore import QObject, pyqtSignal
from models.point import Point
from typing import List

class PointManager(QObject):
    point_added = pyqtSignal(Point)
    point_removed = pyqtSignal(int)
    point_updated = pyqtSignal(Point)
    points_changed = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.points: List[Point] = []
        self.next_id = 1
        
        # Configurações atuais de forma
        self.current_shape = 'circle'
        
        # Para círculos
        self.current_size = 20
        
        # Para retângulos
        self.current_width = 20
        self.current_height = 20
    
    def add_point(self, position, description=""):
        if not description:
            description = f"Ponto {self.next_id}"
        
        # Criar ponto com dimensões apropriadas
        if self.current_shape == 'circle':
            size = max(10, min(self.current_size, 200))
            point = Point(
                id=self.next_id,
                position=position,
                shape=self.current_shape,
                description=description,
                size=size,
                width=size,  # Para círculos, width = height = size
                height=size
            )
            print(f"✅ Ponto {point.id} adicionado - Círculo: Ø {size}px")
            
        elif self.current_shape == 'rectangle':
            width = max(10, min(self.current_width, 200))
            height = max(10, min(self.current_height, 200))
            point = Point(
                id=self.next_id,
                position=position,
                shape=self.current_shape,
                description=description,
                size=max(width, height),  # size = maior dimensão
                width=width,
                height=height
            )
            print(f"✅ Ponto {point.id} adicionado - Retângulo: {width}×{height}px")
        
        self.points.append(point)
        self.next_id += 1
        self.point_added.emit(point)
        self.points_changed.emit(self.points)
        return point
    
    def remove_point(self, point_id):
        self.points = [p for p in self.points if p.id != point_id]
        self.point_removed.emit(point_id)
        self.points_changed.emit(self.points)
        print(f"🗑️ Ponto {point_id} removido")
    
    def update_point_measurement(self, point_id, measurement_type, value):
        for point in self.points:
            if point.id == point_id:
                point.measurements[measurement_type] = value
                self.point_updated.emit(point)
                self.points_changed.emit(self.points)
                break
    
    def get_point_by_id(self, point_id):
        for point in self.points:
            if point.id == point_id:
                return point
        return None
    
    def swap_rectangle_dimensions(self):
        """Troca largura e altura do retângulo"""
        if self.current_shape == 'rectangle':
            self.current_width, self.current_height = self.current_height, self.current_width
            print(f"↔️⇅ Dimensões trocadas: {self.current_width}×{self.current_height}px")
    
    def clear_points(self):
        self.points.clear()
        self.next_id = 1
        self.points_changed.emit(self.points)
        print("🧹 Todos os pontos removidos")