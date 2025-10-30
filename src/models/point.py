from PyQt6.QtCore import QPointF
from dataclasses import dataclass
from typing import Dict

@dataclass
class Point:
    id: int
    position: QPointF
    shape: str
    description: str = ""
    measurements: Dict[str, float] = None
    rotation: float = 0
    size: float = 20          # Para círculos ou maior dimensão
    width: float = 20         # Largura (retângulos)
    height: float = 20        # Altura (retângulos)
    
    def __post_init__(self):
        if self.measurements is None:
            self.measurements = {}
        
        # Garantir que as dimensões sejam válidas
        self.size = max(5, min(self.size, 200))
        self.width = max(5, min(self.width, 200))
        self.height = max(5, min(self.height, 200))
        
        # Garantir que a forma seja válida
        if self.shape not in ['circle', 'rectangle']:
            self.shape = 'circle'
        
        # Para círculos, sincronizar dimensões
        if self.shape == 'circle':
            self.width = self.size
            self.height = self.size
    
    def get_measurement_display(self, measurement_type: str) -> str:
        value = self.measurements.get(measurement_type)
        if value is None:
            return "---"
        elif measurement_type == 'diodo':
            return f"{value:.3f}V"
        elif measurement_type == 'resistencia':
            return f"{value:.1f}Ω"
        elif measurement_type == 'tensao':
            return f"{value:.2f}V"
        else:
            return f"{value:.2f}"