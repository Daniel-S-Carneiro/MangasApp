"""
Script de build do backend.

Este módulo usa o PyInstaller para gerar o executável do backend no modo --onedir,
move a pasta resultante para a raiz correta e faz a limpeza dos arquivos temporários.
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

# Agora o alvo final é a PASTA app na raiz do backend, e a temporária fica dentro de dist
FOLDER_FINAL = os.path.join(BACKEND_DIR, "app")
FOLDER_TEMP = os.path.join(DIST_DIR, "app")


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

    - Roda o PyInstaller em modo --onedir dentro da pasta backend
    - Move a pasta 'app' gerada (contendo o exe e o _internal) para a raiz do backend
    - Faz a limpeza final dos arquivos temporários
    """
    print("--- Iniciando PyInstaller (--onedir) ---")
    try:
        # Trocamos --onefile por --onedir e injetamos o seu arquivo de versão e ícone aqui
        subprocess.run(
            [
                "python",
                "-m",
                "PyInstaller",
                "--onedir",
                "--noconsole",
                "--clean",
                "--noupx",
                "--version-file=file_version_info.txt",
                "--icon=../frontend/public/icon/manga.ico",
                "app.py",
            ],
            cwd=BACKEND_DIR,
            check=True,
        )
    except subprocess.SubprocessError as e:
        print(f"Erro ao rodar PyInstaller: {e}")
        return

    if os.path.exists(FOLDER_TEMP):
        print("--- Movendo pasta do aplicativo para a raiz do backend ---")
        if os.path.exists(FOLDER_FINAL):
            shutil.rmtree(FOLDER_FINAL)  # Remove a pasta app antiga se existir

        shutil.move(FOLDER_TEMP, FOLDER_FINAL)

    clean_up()
    print("\n✅ Build do Backend (--onedir) concluído com sucesso!")


if __name__ == "__main__":
    build()
