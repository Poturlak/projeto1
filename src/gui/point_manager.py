"""
Gerenciador de pontos com sistema de desfazer (Ctrl+Z), 
renumeração automática e modo de edição
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from typing import List, Optional, Tuple
import copy


class PointManager(QObject):
    """Gerenciador de pontos com funcionalidades avançadas"""
    
    points_changed = pyqtSignal(list)  # Emitido quando lista de pontos muda
    point_selected = pyqtSignal(object)  # Emitido quando ponto é selecionado
    point_modified = pyqtSignal(object)  # Emitido quando ponto é modificado
    
    def __init__(self):
        super().__init__()
        
        # ========== DADOS DOS PONTOS ==========
        self.points = []
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_history = 20
        
        # ========== CONFIGURAÇÕES ATUAIS ==========
        self.current_shape = 'circle'
        self.current_size = 20
        self.current_width = 20
        self.current_height = 20
        
        # ========== MODO DE EDIÇÃO ==========
        self.edit_mode = False
        self.selected_point = None
        
        # ========== CONFIGURAÇÕES DE DESENHO ==========
        self.point_colors = {
            'normal': (255, 0, 0),        # Vermelho - padrão
            'selected': (255, 255, 0),    # Amarelo - selecionado
            'diferenca': (255, 105, 180), # Rosa - diferença detectada
            'verde': (0, 255, 0),         # Verde - comparação OK
            'sem_medicao': (128, 128, 128) # Cinza - sem medição
        }
        
        print("🎯 PointManager inicializado")
        
    # ========== GERENCIAMENTO DE PONTOS ==========
    
    def add_point(self, position, auto_save_state=True):
        """
        Adiciona novo ponto na posição especificada
        
        Args:
            position: QPointF com coordenadas
            auto_save_state: Se deve salvar estado para undo
            
        Returns:
            Point: Ponto criado
        """
        if auto_save_state:
            self._save_current_state()
        
        # Importar Point dinamicamente para evitar circular import
        from models.point import Point
        
        # Criar novo ponto
        point_id = len(self.points) + 1
        point = Point(
            id=point_id,
            x=position.x(),
            y=position.y(),
            shape=self.current_shape,
            size=self.current_size
        )
        
        # Configurar dimensões se for retângulo
        if self.current_shape == 'rectangle':
            point.width = self.current_width
            point.height = self.current_height
        else:
            point.width = self.current_size
            point.height = self.current_size
            
        self.points.append(point)
        self._renumber_points()
        
        print(f"🎯 Ponto {point.id} adicionado: ({position.x():.1f}, {position.y():.1f}) - {self.current_shape}")
        return point
        
    def remove_point(self, point_id, auto_save_state=True):
        """Remove ponto por ID"""
        if auto_save_state:
            self._save_current_state()
            
        initial_count = len(self.points)
        self.points = [p for p in self.points if p.id != point_id]
        
        if len(self.points) < initial_count:
            self._renumber_points()
            
            # Limpar seleção se o ponto selecionado foi removido
            if self.selected_point and self.selected_point.id == point_id:
                self.selected_point = None
                
            print(f"🗑️ Ponto {point_id} removido")
            return True
        return False
        
    def remove_point_at_position(self, position, tolerance=10):
        """Remove ponto próximo à posição especificada"""
        point = self.get_point_at_position(position, tolerance)
        if point:
            return self.remove_point(point.id)
        return False
        
    def clear_all_points(self, auto_save_state=True):
        """Limpa todos os pontos"""
        if not self.points:
            return
            
        if auto_save_state:
            self._save_current_state()
            
        self.points.clear()
        self.selected_point = None
        self.points_changed.emit(self.points)
        print("🗑️ Todos os pontos removidos")
        
    def get_point_at_position(self, position, tolerance=10):
        """Encontra ponto próximo à posição"""
        for point in self.points:
            distance = ((position.x() - point.x) ** 2 + (position.y() - point.y) ** 2) ** 0.5
            if distance <= tolerance:
                return point
        return None
        
    def get_point_by_id(self, point_id):
        """Encontra ponto por ID"""
        for point in self.points:
            if point.id == point_id:
                return point
        return None
        
    # ========== SISTEMA DE UNDO/REDO ==========
    
    def _save_current_state(self):
        """Salva estado atual no stack de undo"""
        try:
            # Fazer deep copy dos pontos
            current_state = []
            for point in self.points:
                point_copy = copy.deepcopy(point)
                current_state.append(point_copy)
            
            self.undo_stack.append(current_state)
            
            # Limitar tamanho do stack
            if len(self.undo_stack) > self.max_undo_history:
                self.undo_stack.pop(0)
                
            # Limpar redo stack quando nova ação é feita
            self.redo_stack.clear()
            
        except Exception as e:
            print(f"⚠️  Erro ao salvar estado: {e}")
            
    def undo_last_action(self):
        """Desfaz última ação (Ctrl+Z)"""
        if not self.undo_stack:
            print("↩️ Nada para desfazer")
            return False
            
        try:
            # Salvar estado atual no redo stack
            current_state = []
            for point in self.points:
                point_copy = copy.deepcopy(point)
                current_state.append(point_copy)
            self.redo_stack.append(current_state)
            
            # Restaurar estado anterior
            previous_state = self.undo_stack.pop()
            self.points = previous_state
            
            # Limpar seleção
            self.selected_point = None
            
            self.points_changed.emit(self.points)
            print(f"↩️ Ação desfeita - {len(self.points)} pontos restantes")
            return True
            
        except Exception as e:
            print(f"⚠️  Erro ao desfazer: {e}")
            return False
            
    def redo_last_action(self):
        """Refaz última ação desfeita (Ctrl+Shift+Z)"""
        if not self.redo_stack:
            print("↪️ Nada para refazer")
            return False
            
        try:
            # Salvar estado atual no undo stack
            current_state = []
            for point in self.points:
                point_copy = copy.deepcopy(point)
                current_state.append(point_copy)
            self.undo_stack.append(current_state)
            
            # Restaurar estado seguinte
            next_state = self.redo_stack.pop()
            self.points = next_state
            
            self.points_changed.emit(self.points)
            print(f"↪️ Ação refeita - {len(self.points)} pontos")
            return True
            
        except Exception as e:
            print(f"⚠️  Erro ao refazer: {e}")
            return False
            
    def _renumber_points(self):
        """Renumera pontos sequencialmente"""
        for index, point in enumerate(self.points, start=1):
            point.id = index
        self.points_changed.emit(self.points)
        
    # ========== MODO DE EDIÇÃO ==========
    
    def set_edit_mode(self, enabled):
        """Ativa/desativa modo de edição"""
        self.edit_mode = enabled
        if not enabled:
            self.selected_point = None
        print(f"✏️ Modo edição: {'ATIVO' if enabled else 'INATIVO'}")
        
    def select_point(self, point):
        """Seleciona ponto para edição"""
        if self.edit_mode:
            self.selected_point = point
            self.point_selected.emit(point)
            print(f"✏️ Ponto {point.id} selecionado para edição")
        else:
            self.selected_point = None
            
    def deselect_point(self):
        """Deseleciona ponto atual"""
        if self.selected_point:
            print(f"✏️ Ponto {self.selected_point.id} desselecionado")
        self.selected_point = None
        self.point_selected.emit(None)
        
    def move_selected_point(self, new_position):
        """Move ponto selecionado para nova posição"""
        if self.selected_point and self.edit_mode:
            self._save_current_state()
            
            old_pos = (self.selected_point.x, self.selected_point.y)
            self.selected_point.x = new_position.x()
            self.selected_point.y = new_position.y()
            
            self.point_modified.emit(self.selected_point)
            self.points_changed.emit(self.points)
            
            print(f"✏️ Ponto {self.selected_point.id} movido: {old_pos} → ({new_position.x():.1f}, {new_position.y():.1f})")
            return True
        return False
        
    def resize_selected_point(self, new_size):
        """Redimensiona ponto selecionado"""
        if self.selected_point and self.edit_mode:
            self._save_current_state()
            
            if self.selected_point.shape == 'circle':
                self.selected_point.size = new_size
                self.selected_point.width = new_size
                self.selected_point.height = new_size
            else:  # rectangle
                # Manter proporção ou usar tamanho específico
                self.selected_point.size = new_size
                
            self.point_modified.emit(self.selected_point)
            self.points_changed.emit(self.points)
            print(f"✏️ Ponto {self.selected_point.id} redimensionado: {new_size}px")
            return True
        return False
        
    def change_selected_point_shape(self, new_shape):
        """Muda forma do ponto selecionado"""
        if self.selected_point and self.edit_mode:
            if new_shape != self.selected_point.shape:
                self._save_current_state()
                
                old_shape = self.selected_point.shape
                self.selected_point.shape = new_shape
                
                # Ajustar dimensões
                if new_shape == 'circle':
                    self.selected_point.size = max(self.selected_point.width, self.selected_point.height)
                    self.selected_point.width = self.selected_point.size
                    self.selected_point.height = self.selected_point.size
                else:  # rectangle
                    if old_shape == 'circle':
                        self.selected_point.width = self.selected_point.size
                        self.selected_point.height = self.selected_point.size
                        
                self.point_modified.emit(self.selected_point)
                self.points_changed.emit(self.points)
                print(f"✏️ Ponto {self.selected_point.id}: {old_shape} → {new_shape}")
                return True
        return False
        
    # ========== CONFIGURAÇÕES DE FORMA ==========
    
    def set_shape(self, shape):
        """Define forma atual para novos pontos"""
        if shape in ['circle', 'rectangle']:
            self.current_shape = shape
            print(f"🎨 Forma atual: {shape}")
            
    def set_size(self, size):
        """Define tamanho atual para círculos"""
        self.current_size = max(10, min(200, size))
        if self.current_shape == 'circle':
            self.current_width = self.current_size
            self.current_height = self.current_size
            
    def set_width(self, width):
        """Define largura atual para retângulos"""
        self.current_width = max(10, min(200, width))
        
    def set_height(self, height):
        """Define altura atual para retângulos"""
        self.current_height = max(10, min(200, height))
        
    def swap_rectangle_dimensions(self):
        """Troca largura e altura para retângulos"""
        self.current_width, self.current_height = self.current_height, self.current_width
        print(f"↔️⇅ Dimensões trocadas: {self.current_width}x{self.current_height}px")
        
    # ========== MEDIÇÕES E COMPARAÇÕES ==========
    
    def set_point_measurement(self, point_id, measurement_type, value):
        """
        Define medição de um ponto
        
        Args:
            point_id: ID do ponto
            measurement_type: 'referencia' ou 'comparacao'
            value: Valor da medição em volts
        """
        point = self.get_point_by_id(point_id)
        if point:
            if measurement_type == 'referencia':
                point.medicao_referencia = value
            elif measurement_type == 'comparacao':
                point.medicao_comparacao = value
                
            self.point_modified.emit(point)
            self.points_changed.emit(self.points)
            print(f"📊 Ponto {point_id} - {measurement_type}: {value:.3f}V")
            return True
        return False
        
    def get_point_color(self, point, tolerance=5.0):
        """Determina cor do ponto baseada no status"""
        if self.selected_point and point.id == self.selected_point.id:
            return self.point_colors['selected']
            
        # Verificar medições
        ref = getattr(point, 'medicao_referencia', None)
        comp = getattr(point, 'medicao_comparacao', None)
        
        if ref is not None and comp is not None:
            # Calcular diferença percentual
            if ref != 0:
                diff_percent = abs(((comp - ref) / ref) * 100)
                if diff_percent > tolerance:
                    return self.point_colors['diferenca']  # Rosa
                else:
                    return self.point_colors['verde']      # Verde
            else:
                return self.point_colors['normal']         # Vermelho (ref = 0)
        elif ref is not None or comp is not None:
            return self.point_colors['normal']             # Vermelho (uma medição)
        else:
            return self.point_colors['sem_medicao']        # Cinza (sem medição)
            
    def get_points_with_differences(self, tolerance=5.0):
        """Retorna lista de pontos com diferenças acima da tolerância"""
        points_with_diff = []
        
        for point in self.points:
            ref = getattr(point, 'medicao_referencia', None)
            comp = getattr(point, 'medicao_comparacao', None)
            
            if ref is not None and comp is not None and ref != 0:
                diff_percent = abs(((comp - ref) / ref) * 100)
                if diff_percent > tolerance:
                    points_with_diff.append({
                        'point': point,
                        'difference_percent': diff_percent,
                        'difference_absolute': comp - ref
                    })
                    
        return points_with_diff
        
    # ========== UTILITÁRIOS ==========
    
    def get_statistics(self):
        """Retorna estatísticas dos pontos"""
        total = len(self.points)
        with_reference = sum(1 for p in self.points if getattr(p, 'medicao_referencia', None) is not None)
        with_comparison = sum(1 for p in self.points if getattr(p, 'medicao_comparacao', None) is not None)
        
        shapes = {'circle': 0, 'rectangle': 0}
        for point in self.points:
            shapes[point.shape] += 1
            
        return {
            'total_points': total,
            'with_reference': with_reference,
            'with_comparison': with_comparison,
            'circles': shapes['circle'],
            'rectangles': shapes['rectangle'],
            'edit_mode': self.edit_mode,
            'selected_point_id': self.selected_point.id if self.selected_point else None
        }
        
    def import_points_from_data(self, points_data):
        """Importa pontos de dados JSON"""
        self._save_current_state()
        
        from models.point import Point
        
        self.points.clear()
        
        for data in points_data:
            point = Point(
                id=data.get('id', 1),
                x=data.get('x', 0),
                y=data.get('y', 0),
                shape=data.get('shape', 'circle'),
                size=data.get('size', 20)
            )
            
            point.width = data.get('width', point.size)
            point.height = data.get('height', point.size)
            point.medicao_referencia = data.get('medicao_referencia')
            point.medicao_comparacao = data.get('medicao_comparacao')
            
            self.points.append(point)
            
        self.points_changed.emit(self.points)
        print(f"📁 {len(self.points)} pontos importados")
