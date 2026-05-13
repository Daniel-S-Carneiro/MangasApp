"""
Script de build do backend.

Este módulo usa o PyInstaller para gerar o executável do backend,
move o resultado para a pasta correta e faz a limpeza dos arquivos temporários.
"""

import os
import shutil
import subprocess

# Configurações de caminhos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DIST_DIR = os.path.join(BACKEND_DIR, "dist")
BUILD_DIR = os.path.join(BACKEND_DIR, "build")
SPEC_FILE = os.path.join(BACKEND_DIR, "app.spec")
EXE_FINAL = os.path.join(BACKEND_DIR, "app.exe")
EXE_TEMP = os.path.join(DIST_DIR, "app.exe")


def clean_up():
    """Remove pastas e arquivos temporários do PyInstaller."""
    print("--- Limpando arquivos temporários ---")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    if os.path.exists(SPEC_FILE):
        os.remove(SPEC_FILE)


def build():
    """Executa o processo de build do backend com PyInstaller.

    - Roda o PyInstaller dentro da pasta backend
    - Move o executável gerado para a raiz do backend
    - Faz a limpeza final dos arquivos temporários
    """
    print("--- Iniciando PyInstaller ---")
    try:
        subprocess.run(
            ["python", "-m", "PyInstaller", "--onefile", "--noconsole", "app.py"],
            cwd=BACKEND_DIR,
            check=True,
        )
    except subprocess.SubprocessError as e:
        print(f"Erro ao rodar PyInstaller: {e}")
        return

    if os.path.exists(EXE_TEMP):
        print("--- Movendo executável para a pasta backend ---")
        if os.path.exists(EXE_FINAL):
            os.remove(EXE_FINAL)
        shutil.move(EXE_TEMP, EXE_FINAL)
        if os.path.exists(EXE_TEMP):
            os.remove(EXE_TEMP)

    clean_up()
    print("\n✅ Build do Backend concluído com sucesso!")


if __name__ == "__main__":
    build()
