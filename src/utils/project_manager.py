"""
Gerenciador de projetos - Sistema .mip (ZIP compactado)
Salva/carrega projetos com imagem, pontos e metadados
"""

import zipfile
import json
import os
import io
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from PIL import Image
except ImportError:
    print("⚠️  PIL não encontrado - funcionalidade de imagem limitada")
    Image = None


class ProjectManager:
    """Gerenciador de projetos .mip"""
    
    VERSION = "1.0"
    APP_VERSION = "1.0.0"
    
    @staticmethod
    def save_project(filepath: str, project_data: Dict[str, Any], 
                    image_data: Optional[Any], points_data: List[Any]) -> bool:
        """
        Salva projeto em formato .mip (arquivo ZIP compactado)
        
        Args:
            filepath: Caminho do arquivo .mip
            project_data: Dados do projeto (nome, modelo, etc.)
            image_data: Imagem PIL ou None
            points_data: Lista de pontos
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Garantir extensão .mip
            if not filepath.endswith('.mip'):
                filepath += '.mip'
                
            print(f"💾 Salvando projeto: {filepath}")
            
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                
                # ========== SALVAR METADATA ==========
                metadata = ProjectManager._create_metadata(project_data, image_data, points_data)
                zf.writestr('metadata.json', json.dumps(metadata, indent=2, ensure_ascii=False))
                print(f"   ✅ Metadata salvo - Estado: {metadata['state']}")
                
                # ========== SALVAR IMAGEM ==========
                if image_data and Image:
                    try:
                        img_bytes = io.BytesIO()
                        # Converter para RGB se necessário (remove transparência)
                        if image_data.mode in ('RGBA', 'LA', 'P'):
                            rgb_image = Image.new('RGB', image_data.size, (255, 255, 255))
                            if image_data.mode == 'P':
                                image_data = image_data.convert('RGBA')
                            rgb_image.paste(image_data, mask=image_data.split()[-1] if image_data.mode in ('RGBA', 'LA') else None)
                            image_data = rgb_image
                            
                        image_data.save(img_bytes, format='PNG', optimize=True)
                        zf.writestr('image.png', img_bytes.getvalue())
                        print(f"   ✅ Imagem salva - {image_data.size[0]}x{image_data.size[1]} pixels")
                    except Exception as e:
                        print(f"   ⚠️  Erro ao salvar imagem: {e}")
                else:
                    print(f"   ℹ️  Nenhuma imagem para salvar")
                
                # ========== SALVAR PONTOS ==========
                points_json = ProjectManager._convert_points_to_json(points_data)
                zf.writestr('points.json', json.dumps(points_json, indent=2, ensure_ascii=False))
                print(f"   ✅ {len(points_json)} pontos salvos")
                
                # ========== SALVAR CONFIGURAÇÕES ==========
                settings = ProjectManager._create_settings()
                zf.writestr('settings.json', json.dumps(settings, indent=2, ensure_ascii=False))
                print(f"   ✅ Configurações salvas")
                
            print(f"💾 Projeto salvo com sucesso: {os.path.basename(filepath)}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar projeto: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def load_project(filepath: str) -> Optional[Dict[str, Any]]:
        """
        Carrega projeto .mip
        
        Args:
            filepath: Caminho do arquivo .mip
            
        Returns:
            Dict com 'metadata', 'image', 'points', 'settings' ou None se erro
        """
        try:
            print(f"📁 Carregando projeto: {filepath}")
            
            if not os.path.exists(filepath):
                print(f"❌ Arquivo não encontrado: {filepath}")
                return None
            
            with zipfile.ZipFile(filepath, 'r') as zf:
                
                # Verificar arquivos necessários
                required_files = ['metadata.json', 'points.json']
                missing_files = [f for f in required_files if f not in zf.namelist()]
                if missing_files:
                    print(f"❌ Arquivos obrigatórios faltando: {missing_files}")
                    return None
                
                # ========== CARREGAR METADATA ==========
                metadata_str = zf.read('metadata.json').decode('utf-8')
                metadata = json.loads(metadata_str)
                print(f"   ✅ Metadata carregado - Versão: {metadata.get('version', 'N/A')}")
                
                # ========== CARREGAR IMAGEM ==========
                image_data = None
                if 'image.png' in zf.namelist() and Image:
                    try:
                        image_bytes = zf.read('image.png')
                        image_data = Image.open(io.BytesIO(image_bytes))
                        print(f"   ✅ Imagem carregada - {image_data.size[0]}x{image_data.size[1]} pixels")
                    except Exception as e:
                        print(f"   ⚠️  Erro ao carregar imagem: {e}")
                else:
                    print(f"   ℹ️  Nenhuma imagem no projeto")
                
                # ========== CARREGAR PONTOS ==========
                points_str = zf.read('points.json').decode('utf-8')
                points_data = json.loads(points_str)
                print(f"   ✅ {len(points_data)} pontos carregados")
                
                # ========== CARREGAR CONFIGURAÇÕES ==========
                settings_data = {}
                if 'settings.json' in zf.namelist():
                    try:
                        settings_str = zf.read('settings.json').decode('utf-8')
                        settings_data = json.loads(settings_str)
                        print(f"   ✅ Configurações carregadas")
                    except Exception as e:
                        print(f"   ⚠️  Erro ao carregar configurações: {e}")
                
            result = {
                'metadata': metadata,
                'image': image_data,
                'points': points_data,
                'settings': settings_data
            }
            
            print(f"📁 Projeto carregado com sucesso: {os.path.basename(filepath)}")
            return result
            
        except Exception as e:
            print(f"❌ Erro ao carregar projeto: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _create_metadata(project_data: Dict[str, Any], image_data: Optional[Any], 
                        points_data: List[Any]) -> Dict[str, Any]:
        """Cria metadados do projeto"""
        now = datetime.now().isoformat() + "Z"
        
        # Informações da imagem
        image_info = {
            "has_image": image_data is not None,
            "original_dimensions": list(image_data.size) if image_data else [0, 0],
            "current_dimensions": list(image_data.size) if image_data else [0, 0],
            "format": "PNG",
            "edited": True  # Assumir que foi editada
        }
        
        # Análise dos pontos
        points_with_reference = sum(1 for p in points_data if getattr(p, 'medicao_referencia', None) is not None)
        points_with_comparison = sum(1 for p in points_data if getattr(p, 'medicao_comparacao', None) is not None)
        
        # Detectar diferenças (simulação - será implementado quando houver dados reais)
        points_with_differences = 0
        if points_with_reference > 0 and points_with_comparison > 0:
            # Aqui seria calculado baseado na tolerância
            points_with_differences = max(0, len(points_data) // 5)  # Simulação: ~20% com diferença
        
        metadata = {
            "version": ProjectManager.VERSION,
            "app_version": ProjectManager.APP_VERSION,
            "state": project_data.get('state', 'marcacao'),
            
            "project_info": {
                "nome": project_data.get('nome', ''),
                "modelo_aparelho": project_data.get('modelo', ''),
                "placa_funcional": project_data.get('funcional', True),
                "descricao_problema": project_data.get('descricao', '')
            },
            
            "timestamps": {
                "created": now,
                "modified": now,
                "last_opened": now
            },
            
            "image_info": image_info,
            
            "points_info": {
                "total_points": len(points_data),
                "points_with_reference": points_with_reference,
                "points_with_comparison": points_with_comparison,
                "points_measured": points_with_reference + points_with_comparison
            },
            
            "comparison": {
                "has_comparison": points_with_comparison > 0,
                "has_reference": points_with_reference > 0,
                "mode_active": points_with_comparison > 0,
                "tolerance_percent": 5.0,  # Padrão
                "points_with_differences": points_with_differences,
                "comparison_complete": points_with_comparison == len(points_data) if points_data else False
            },
            
            "statistics": {
                "total_measurements": points_with_reference + points_with_comparison,
                "measurements_complete": points_with_reference > 0 or points_with_comparison > 0,
                "success_rate": 0.0  # Será calculado quando houver dados reais
            }
        }
        
        return metadata
    
    @staticmethod
    def _convert_points_to_json(points_data: List[Any]) -> List[Dict[str, Any]]:
        """Converte objetos Point para formato JSON"""
        points_json = []
        
        for point in points_data:
            point_dict = {
                "id": getattr(point, 'id', 0),
                "x": float(getattr(point, 'x', 0.0)),
                "y": float(getattr(point, 'y', 0.0)),
                "shape": getattr(point, 'shape', 'circle'),
                "size": getattr(point, 'size', 20),
                "width": getattr(point, 'width', 20),
                "height": getattr(point, 'height', 20),
                
                # Medições
                "medicao_referencia": getattr(point, 'medicao_referencia', None),
                "medicao_comparacao": getattr(point, 'medicao_comparacao', None),
                
                # Campos calculados
                "diferenca_absoluta": None,
                "diferenca_percentual": None,
                "acima_tolerancia": False,
                "status": "normal"
            }
            
            # Calcular diferenças se ambos os valores existirem
            ref = point_dict['medicao_referencia']
            comp = point_dict['medicao_comparacao']
            
            if ref is not None and comp is not None:
                point_dict['diferenca_absoluta'] = comp - ref
                point_dict['diferenca_percentual'] = ((comp - ref) / ref) * 100 if ref != 0 else 0
                
                # Status baseado na diferença (tolerância padrão 5%)
                diff_percent = abs(point_dict['diferenca_percentual'])
                if diff_percent <= 5.0:
                    point_dict['status'] = "normal"
                    point_dict['acima_tolerancia'] = False
                else:
                    point_dict['status'] = "diferenca"
                    point_dict['acima_tolerancia'] = True
            
            points_json.append(point_dict)
        
        return points_json
    
    @staticmethod
    def _create_settings() -> Dict[str, Any]:
        """Cria configurações padrão do projeto"""
        return {
            "ui": {
                "zoom_level": 1.0,
                "last_tool": "circle",
                "show_point_ids": True,
                "show_measurements": True,
                "point_opacity": 0.7
            },
            
            "measurement": {
                "auto_advance": True,
                "measurement_timeout": 5.0,
                "decimal_places": 3,
                "units": "V"  # Volts para escala de diodo
            },
            
            "comparison": {
                "default_tolerance": 5.0,
                "highlight_differences": True,
                "auto_calculate": True,
                "show_percentages": True
            },
            
            "export": {
                "include_points": True,
                "include_measurements": True,
                "include_legend": False,
                "image_quality": 95
            }
        }
    
    @staticmethod
    def get_project_info(filepath: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações básicas do projeto sem carregar tudo
        
        Args:
            filepath: Caminho do arquivo .mip
            
        Returns:
            Dict com informações básicas ou None se erro
        """
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                if 'metadata.json' not in zf.namelist():
                    return None
                
                metadata_str = zf.read('metadata.json').decode('utf-8')
                metadata = json.loads(metadata_str)
                
                return {
                    'name': metadata['project_info']['nome'],
                    'model': metadata['project_info']['modelo_aparelho'],
                    'functional': metadata['project_info']['placa_funcional'],
                    'state': metadata['state'],
                    'points': metadata['points_info']['total_points'],
                    'created': metadata['timestamps']['created'],
                    'modified': metadata['timestamps']['modified']
                }
                
        except Exception as e:
            print(f"❌ Erro ao obter info do projeto: {e}")
            return None
    
    @staticmethod
    def is_valid_project_file(filepath: str) -> bool:
        """
        Verifica se um arquivo é um projeto .mip válido
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            bool: True se é um projeto válido
        """
        try:
            if not filepath.endswith('.mip'):
                return False
                
            if not os.path.exists(filepath):
                return False
            
            with zipfile.ZipFile(filepath, 'r') as zf:
                required_files = ['metadata.json', 'points.json']
                return all(f in zf.namelist() for f in required_files)
                
        except Exception:
            return False
    
    @staticmethod
    def backup_project(original_filepath: str) -> Optional[str]:
        """
        Cria backup de um projeto antes de modificar
        
        Args:
            original_filepath: Caminho do projeto original
            
        Returns:
            str: Caminho do backup ou None se erro
        """
        try:
            if not os.path.exists(original_filepath):
                return None
            
            # Gerar nome do backup
            base_name = os.path.splitext(original_filepath)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filepath = f"{base_name}_backup_{timestamp}.mip"
            
            # Copiar arquivo
            import shutil
            shutil.copy2(original_filepath, backup_filepath)
            
            print(f"🔄 Backup criado: {os.path.basename(backup_filepath)}")
            return backup_filepath
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return None
