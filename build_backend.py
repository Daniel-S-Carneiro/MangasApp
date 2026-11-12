"""Script de build do backend.

Este módulo usa o PyInstaller para gerar o executável do backend no modo --onedir,
move a pasta resultante para a raiz correta e faz a limpeza dos arquivos temporários.
"""

import os
import shutil
import subprocess
import sys
import json  # Adicionado para ler o package.json

# Configurações de caminhos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
RAIZ_PROJETO = os.path.abspath(
    os.path.join(BASE_DIR, "..")
)  # Caminho para a raiz onde está o package.json
BACKEND_DIR = (
    os.path.join(BASE_DIR, "backend")
    if os.path.basename(BASE_DIR) != "backend"
    else BASE_DIR
)

# Se o script estiver na raiz ou no backend, reajusta os caminhos dinamicamente
if not os.path.exists(os.path.join(RAIZ_PROJETO, "package.json")):
    RAIZ_PROJETO = BASE_DIR
    BACKEND_DIR = os.path.join(RAIZ_PROJETO, "backend")

DIST_DIR = os.path.join(BACKEND_DIR, "dist")
BUILD_DIR = os.path.join(BACKEND_DIR, "build")
SPEC_FILE = os.path.join(BACKEND_DIR, "app.spec")

FOLDER_FINAL = os.path.join(BACKEND_DIR, "app")
FOLDER_TEMP = os.path.join(DIST_DIR, "app")


def get_product_name() -> str:
    """Lê o productName diretamente do package.json do projeto."""
    package_json_path = os.path.join(RAIZ_PROJETO, "package.json")
    try:
        with open(package_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return str(data.get("productName", "Gerenciador de Mangas"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Aviso: Não foi possível ler o package.json ({e}). Usando fallback.")
        return "Gerenciador de Mangas"


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
    """Executa o processo de build do backend com PyInstaller injetando o nome do JSON."""
    product_name = get_product_name()
    print(f"--- Nome do Produto Detectado do package.json: '{product_name}' ---")
    print("--- Iniciando PyInstaller (--onedir) ---")

    try:
        # O nome do produto e a versão entram no binário pelo file_version_info.txt
        subprocess.run(
            [
                sys.executable,
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
        # Sai com erro para o npm parar o build em vez de empacotar um app.exe antigo
        print(f"Erro ao rodar PyInstaller: {e}")
        sys.exit(1)

    if not os.path.exists(FOLDER_TEMP):
        print(f"Erro: o PyInstaller não gerou a pasta {FOLDER_TEMP}")
        sys.exit(1)

    print("--- Movendo pasta do aplicativo para a raiz do backend ---")
    if os.path.exists(FOLDER_FINAL):
        shutil.rmtree(FOLDER_FINAL)

    shutil.move(FOLDER_TEMP, FOLDER_FINAL)

    clean_up()
    print(f"\n✅ Build do Backend para '{product_name}' concluído com sucesso!")


if __name__ == "__main__":
    # Com a saída redirecionada (CI, log), o Windows usa cp1252 e o emoji quebrava o script
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    build()
