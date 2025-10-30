from PyQt6.QtCore import QPointF
from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class Point:
    id: int
    position: QPointF
    shape: str
    description: str = ""
    measurements: Dict[str, float] = field(default_factory=dict)
    rotation: float = 0
    size: float = 20          # Para círculos ou maior dimensão
    width: float = 20         # Largura (retângulos)
    height: float = 20        # Altura (retângulos)
    
    # Campos de medição
    medicao_referencia: Optional[float] = None
    medicao_comparacao: Optional[float] = None
    
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
    
    def calcular_diferenca_absoluta(self) -> Optional[float]:
        """Calcula diferença absoluta entre comparação e referência"""
        if self.medicao_referencia is not None and self.medicao_comparacao is not None:
            return self.medicao_comparacao - self.medicao_referencia
        return None
    
    def calcular_diferenca_percentual(self) -> Optional[float]:
        """Calcula diferença percentual"""
        if self.medicao_referencia is not None and self.medicao_comparacao is not None:
            if self.medicao_referencia != 0:
                diff = self.medicao_comparacao - self.medicao_referencia
                return (diff / self.medicao_referencia) * 100
        return None
    
    def esta_acima_tolerancia(self, tolerancia_percent: float) -> bool:
        """Verifica se a diferença está acima da tolerância"""
        diff_percent = self.calcular_diferenca_percentual()
        if diff_percent is not None:
            return abs(diff_percent) > tolerancia_percent
        return False
    
    def get_measurement_display(self, measurement_type: str) -> str:
        """Retorna valor formatado para display"""
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
    
    def to_dict(self) -> dict:
        """Converte ponto para dicionário (para salvar)"""
        return {
            'id': self.id,
            'x': self.position.x(),
            'y': self.position.y(),
            'shape': self.shape,
            'size': self.size,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'medicao_referencia': self.medicao_referencia,
            'medicao_comparacao': self.medicao_comparacao
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Cria ponto a partir de dicionário (para carregar)"""
        position = QPointF(data['x'], data['y'])
        return cls(
            id=data['id'],
            position=position,
            shape=data['shape'],
            size=data.get('size', 20),
            width=data.get('width', 20),
            height=data.get('height', 20),
            rotation=data.get('rotation', 0),
            medicao_referencia=data.get('medicao_referencia'),
            medicao_comparacao=data.get('medicao_comparacao')
        )