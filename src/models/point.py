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
    size: float = 20
    
    def __post_init__(self):
        if self.measurements is None:
            self.measurements = {}
        # Garantir que o tamanho seja válido
        self.size = max(5, min(self.size, 200))  # Entre 5 e 200 pixels
        # Garantir que a forma seja válida
        if self.shape not in ['circle', 'rectangle']:
            self.shape = 'circle'
    
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