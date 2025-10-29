import subprocess
import sys
import os

def install_requirements():
    """Instala todas as dependências do projeto"""
    requirements = [
        "PyQt6",
        "opencv-python", 
        "pyserial",
        "sqlalchemy",
        "matplotlib",
        "pyqtgraph",
        "psycopg2-binary",
        "pillow"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado com sucesso!")
        except subprocess.CalledProcessError:
            print(f"❌ Erro ao instalar {package}")

def create_folder_structure():
    """Cria a estrutura de pastas do projeto"""
    folders = [
        "src/gui",
        "src/hardware", 
        "src/database",
        "src/image_processing",
        "src/utils",
        "docs",
        "tests",
        "resources/images",
        "resources/icons"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"📁 Pasta criada: {folder}")

if __name__ == "__main__":
    print("🚀 Configurando ambiente de desenvolvimento...")
    create_folder_structure()
    install_requirements()
    print("✅ Configuração concluída! Ambiente pronto para desenvolvimento.")