"""
Modelo de ponto com suporte a medições de referência e comparação
Inclui campos para análise de diferenças e status
"""

from typing import Optional, Dict, Any
import json


class Point:
    """
    Representa um ponto de medição na imagem
    
    Attributes:
        id: Identificador único do ponto
        x, y: Coordenadas na imagem
        shape: 'circle' ou 'rectangle'
        size: Tamanho base (usado para círculos)
        width, height: Dimensões específicas (usado para retângulos)
        medicao_referencia: Valor de medição da placa de referência (boa)
        medicao_comparacao: Valor de medição da placa sendo testada
        created_at: Timestamp de criação
        modified_at: Timestamp de última modificação
    """
    
    def __init__(self, id: int, x: float, y: float, shape: str = 'circle', size: int = 20):
        # ========== IDENTIFICAÇÃO ==========
        self.id = id
        
        # ========== POSIÇÃO E GEOMETRIA ==========
        self.x = float(x)
        self.y = float(y)
        self.shape = shape  # 'circle' ou 'rectangle'
        self.size = size    # Tamanho base
        
        # Dimensões específicas
        if shape == 'circle':
            self.width = size
            self.height = size
        else:  # rectangle
            self.width = size
            self.height = size
            
        # ========== MEDIÇÕES ==========
        self.medicao_referencia: Optional[float] = None  # Medição da placa boa
        self.medicao_comparacao: Optional[float] = None  # Medição da placa testada
        
        # ========== CAMPOS CALCULADOS ==========
        self._diferenca_absoluta: Optional[float] = None
        self._diferenca_percentual: Optional[float] = None
        self._status: str = 'normal'  # 'normal', 'diferenca', 'sem_medicao'
        
        # ========== METADADOS ==========
        self.description: Optional[str] = None
        self.created_at: Optional[str] = None
        self.modified_at: Optional[str] = None
        
        # Definir timestamps
        from datetime import datetime
        now = datetime.now().isoformat()
        self.created_at = now
        self.modified_at = now
        
        print(f"🎯 Point {self.id} criado: ({self.x:.1f}, {self.y:.1f}) - {self.shape}")
        
    # ========== PROPRIEDADES CALCULADAS ==========
    
    @property
    def diferenca_absoluta(self) -> Optional[float]:
        """Diferença absoluta entre comparação e referência"""
        if self.medicao_referencia is not None and self.medicao_comparacao is not None:
            return self.medicao_comparacao - self.medicao_referencia
        return None
        
    @property
    def diferenca_percentual(self) -> Optional[float]:
        """Diferença percentual entre comparação e referência"""
        if (self.medicao_referencia is not None and 
            self.medicao_comparacao is not None and 
            self.medicao_referencia != 0):
            return ((self.medicao_comparacao - self.medicao_referencia) / self.medicao_referencia) * 100
        return None
        
    @property
    def has_measurements(self) -> bool:
        """Verifica se ponto tem alguma medição"""
        return self.medicao_referencia is not None or self.medicao_comparacao is not None
        
    @property
    def has_complete_comparison(self) -> bool:
        """Verifica se ponto tem ambas as medições para comparação"""
        return self.medicao_referencia is not None and self.medicao_comparacao is not None
        
    @property
    def status(self) -> str:
        """Status do ponto baseado nas medições"""
        return self._calculate_status()
        
    def _calculate_status(self, tolerance: float = 5.0) -> str:
        """Calcula status baseado na tolerância"""
        if not self.has_measurements:
            return 'sem_medicao'
            
        if not self.has_complete_comparison:
            return 'normal'  # Apenas uma medição
            
        # Ambas as medições existem
        diff_percent = self.diferenca_percentual
        if diff_percent is not None and abs(diff_percent) > tolerance:
            return 'diferenca'
        else:
            return 'normal'
            
    def is_above_tolerance(self, tolerance: float = 5.0) -> bool:
        """Verifica se diferença está acima da tolerância"""
        diff_percent = self.diferenca_percentual
        if diff_percent is not None:
            return abs(diff_percent) > tolerance
        return False
        
    # ========== MÉTODOS DE MEDIÇÃO ==========
    
    def set_reference_measurement(self, value: float) -> None:
        """Define medição de referência"""
        self.medicao_referencia = float(value)
        self._update_modified_time()
        print(f"📊 Point {self.id} - Referência: {value:.3f}V")
        
    def set_comparison_measurement(self, value: float) -> None:
        """Define medição de comparação"""
        self.medicao_comparacao = float(value)
        self._update_modified_time()
        print(f"📊 Point {self.id} - Comparação: {value:.3f}V")
        
    def clear_measurements(self) -> None:
        """Limpa todas as medições"""
        self.medicao_referencia = None
        self.medicao_comparacao = None
        self._update_modified_time()
        print(f"🧹 Point {self.id} - Medições limpas")
        
    def get_measurement_summary(self) -> Dict[str, Any]:
        """Retorna resumo das medições"""
        return {
            'id': self.id,
            'referencia': self.medicao_referencia,
            'comparacao': self.medicao_comparacao,
            'diferenca_absoluta': self.diferenca_absoluta,
            'diferenca_percentual': self.diferenca_percentual,
            'status': self.status,
            'has_complete_comparison': self.has_complete_comparison
        }
        
    # ========== MÉTODOS DE GEOMETRIA ==========
    
    def move_to(self, x: float, y: float) -> None:
        """Move ponto para nova posição"""
        old_pos = (self.x, self.y)
        self.x = float(x)
        self.y = float(y)
        self._update_modified_time()
        print(f"📍 Point {self.id} movido: {old_pos} → ({self.x:.1f}, {self.y:.1f})")
        
    def resize(self, new_size: int) -> None:
        """Redimensiona ponto"""
        old_size = self.size
        self.size = new_size
        
        if self.shape == 'circle':
            self.width = new_size
            self.height = new_size
        else:  # rectangle - manter proporção ou aplicar a ambas
            scale = new_size / old_size
            self.width = int(self.width * scale)
            self.height = int(self.height * scale)
            
        self._update_modified_time()
        print(f"📏 Point {self.id} redimensionado: {old_size} → {new_size}")
        
    def set_dimensions(self, width: int, height: int) -> None:
        """Define dimensões específicas (para retângulos)"""
        self.width = width
        self.height = height
        self.size = max(width, height)  # Atualizar size base
        self._update_modified_time()
        print(f"📐 Point {self.id} dimensões: {width}x{height}")
        
    def change_shape(self, new_shape: str) -> None:
        """Muda forma do ponto"""
        if new_shape not in ['circle', 'rectangle']:
            raise ValueError(f"Forma inválida: {new_shape}")
            
        old_shape = self.shape
        self.shape = new_shape
        
        # Ajustar dimensões
        if new_shape == 'circle':
            # Para círculo, usar a maior dimensão
            self.size = max(self.width, self.height)
            self.width = self.size
            self.height = self.size
        else:  # rectangle
            # Para retângulo, manter dimensões atuais
            if old_shape == 'circle':
                # Se era círculo, usar dimensões quadradas
                self.width = self.size
                self.height = self.size
                
        self._update_modified_time()
        print(f"🎨 Point {self.id} forma: {old_shape} → {new_shape}")
        
    def get_bounds(self) -> Dict[str, float]:
        """Retorna limites do ponto (para detecção de clique)"""
        if self.shape == 'circle':
            radius = self.size // 2
            return {
                'left': self.x - radius,
                'right': self.x + radius,
                'top': self.y - radius,
                'bottom': self.y + radius
            }
        else:  # rectangle
            half_w = self.width // 2
            half_h = self.height // 2
            return {
                'left': self.x - half_w,
                'right': self.x + half_w,
                'top': self.y - half_h,
                'bottom': self.y + half_h
            }
            
    def contains_point(self, x: float, y: float) -> bool:
        """Verifica se coordenada está dentro do ponto"""
        bounds = self.get_bounds()
        return (bounds['left'] <= x <= bounds['right'] and 
                bounds['top'] <= y <= bounds['bottom'])
        
    def distance_to_point(self, x: float, y: float) -> float:
        """Calcula distância do centro do ponto até coordenada"""
        return ((x - self.x) ** 2 + (y - self.y) ** 2) ** 0.5
        
    # ========== SERIALIZAÇÃO ==========
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte ponto para dicionário"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'shape': self.shape,
            'size': self.size,
            'width': self.width,
            'height': self.height,
            
            # Medições
            'medicao_referencia': self.medicao_referencia,
            'medicao_comparacao': self.medicao_comparacao,
            
            # Campos calculados (para cache)
            'diferenca_absoluta': self.diferenca_absoluta,
            'diferenca_percentual': self.diferenca_percentual,
            'status': self.status,
            
            # Metadados
            'description': self.description,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            
            # Flags úteis
            'has_measurements': self.has_measurements,
            'has_complete_comparison': self.has_complete_comparison
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Point':
        """Cria ponto a partir de dicionário"""
        point = cls(
            id=data.get('id', 1),
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            shape=data.get('shape', 'circle'),
            size=data.get('size', 20)
        )
        
        # Restaurar dimensões
        point.width = data.get('width', point.size)
        point.height = data.get('height', point.size)
        
        # Restaurar medições
        point.medicao_referencia = data.get('medicao_referencia')
        point.medicao_comparacao = data.get('medicao_comparacao')
        
        # Restaurar metadados
        point.description = data.get('description')
        point.created_at = data.get('created_at')
        point.modified_at = data.get('modified_at')
        
        return point
        
    def to_json(self) -> str:
        """Converte ponto para JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        
    @classmethod
    def from_json(cls, json_str: str) -> 'Point':
        """Cria ponto a partir de JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)
        
    # ========== COMPARAÇÃO E ANÁLISE ==========
    
    def compare_with(self, other_point: 'Point', tolerance: float = 5.0) -> Dict[str, Any]:
        """Compara este ponto com outro"""
        result = {
            'points_match': self.id == other_point.id,
            'position_difference': self.distance_to_point(other_point.x, other_point.y),
            'shape_match': self.shape == other_point.shape,
            'size_difference': abs(self.size - other_point.size),
            'can_compare_measurements': False,
            'measurement_difference': None,
            'within_tolerance': None
        }
        
        # Comparar medições se ambos tiverem
        if self.has_measurements and other_point.has_measurements:
            ref1 = self.medicao_referencia or self.medicao_comparacao
            ref2 = other_point.medicao_referencia or other_point.medicao_comparacao
            
            if ref1 is not None and ref2 is not None:
                result['can_compare_measurements'] = True
                result['measurement_difference'] = abs(ref1 - ref2)
                
                if ref1 != 0:
                    diff_percent = abs(((ref2 - ref1) / ref1) * 100)
                    result['within_tolerance'] = diff_percent <= tolerance
                    
        return result
        
    def get_analysis_report(self, tolerance: float = 5.0) -> Dict[str, Any]:
        """Gera relatório de análise do ponto"""
        report = {
            'point_id': self.id,
            'position': {'x': self.x, 'y': self.y},
            'geometry': {
                'shape': self.shape,
                'size': self.size,
                'width': self.width,
                'height': self.height
            },
            'measurements': {
                'has_reference': self.medicao_referencia is not None,
                'has_comparison': self.medicao_comparacao is not None,
                'reference_value': self.medicao_referencia,
                'comparison_value': self.medicao_comparacao,
                'complete_comparison': self.has_complete_comparison
            },
            'analysis': {
                'status': self.status,
                'difference_absolute': self.diferenca_absoluta,
                'difference_percent': self.diferenca_percentual,
                'above_tolerance': self.is_above_tolerance(tolerance),
                'tolerance_used': tolerance
            },
            'timestamps': {
                'created': self.created_at,
                'modified': self.modified_at
            }
        }
        
        # Adicionar recomendações
        recommendations = []
        if not self.has_measurements:
            recommendations.append("Realizar medição no ponto")
        elif not self.has_complete_comparison:
            recommendations.append("Completar comparação com placa de referência")
        elif self.is_above_tolerance(tolerance):
            recommendations.append("Investigar diferença significativa detectada")
        else:
            recommendations.append("Ponto dentro da tolerância especificada")
            
        report['recommendations'] = recommendations
        
        return report
        
    # ========== UTILITÁRIOS ==========
    
    def _update_modified_time(self) -> None:
        """Atualiza timestamp de modificação"""
        from datetime import datetime
        self.modified_at = datetime.now().isoformat()
        
    def clone(self) -> 'Point':
        """Cria cópia do ponto"""
        return Point.from_dict(self.to_dict())
        
    def __str__(self) -> str:
        """Representação string do ponto"""
        measurements_str = ""
        if self.has_measurements:
            ref = f"R:{self.medicao_referencia:.3f}" if self.medicao_referencia else "R:---"
            comp = f"C:{self.medicao_comparacao:.3f}" if self.medicao_comparacao else "C:---"
            measurements_str = f" [{ref}, {comp}]"
            
        return f"Point({self.id}, {self.x:.1f}, {self.y:.1f}, {self.shape}, {self.size}px{measurements_str})"
        
    def __repr__(self) -> str:
        """Representação detalhada do ponto"""
        return (f"Point(id={self.id}, x={self.x}, y={self.y}, shape='{self.shape}', "
                f"size={self.size}, ref={self.medicao_referencia}, comp={self.medicao_comparacao})")
        
    def __eq__(self, other) -> bool:
        """Comparação de igualdade"""
        if not isinstance(other, Point):
            return False
        return (self.id == other.id and 
                abs(self.x - other.x) < 0.1 and 
                abs(self.y - other.y) < 0.1)
        
    def __hash__(self) -> int:
        """Hash do ponto (para uso em sets/dicts)"""
        return hash((self.id, round(self.x, 1), round(self.y, 1)))
