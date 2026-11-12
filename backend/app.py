"""Manga Manager Backend.

Gerencia o banco de dados SQLite e a integração de imagens para o Electron.
"""

import io
import json
import os
import shutil
import sqlite3
import sys
import uuid
import traceback
import argparse

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

if sys.stdin.encoding != "utf-8":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

# --- TRATAMENTO DE ARGUMENTOS VIA CLI ---
parser = argparse.ArgumentParser()
parser.add_argument(
    "--userdata", type=str, help="Caminho da pasta de dados do Electron"
)
args, unknown = parser.parse_known_args()


# --- FUNÇÕES DE SUPORTE ---
def get_compiled_product_name() -> str:
    """Recupera o nome do produto padrão caso o app rode sem argumentos."""
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return "Gerenciador de Mangas"
    return "Gerenciador de Mangas"


# --- LÓGICA DE DETECÇÃO DE AMBIENTE (DYNAMIC USERDATA VS LOCAL DEV) ---

# Agora ela está perfeitamente definida aqui em cima!
PRODUCT_NAME = get_compiled_product_name()

# No app instalado o app.exe fica em resources/backend/app/, e os recursos que
# vêm com o instalador (como o default.jpg) ficam dois níveis acima, em
# resources/. Apontar para a pasta do app.exe fazia o default.jpg nunca ser
# copiado, e os mangás sem capa apareciam com a imagem quebrada.
RECURSOS_INSTALADOS = os.path.abspath(
    os.path.join(os.path.dirname(sys.executable), "..", "..")
)

if args.userdata:
    # ---- MODO DINÂMICO (Garantido pelo Electron via argumento) ----
    APPDATA_DIR = args.userdata
    BASE_RESOURCES_DIR = (
        RECURSOS_INSTALADOS
        if getattr(sys, "frozen", False)
        else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )

    db_path = os.path.join(APPDATA_DIR, "data", "mangas.db")
    IMG_DIR = os.path.join(APPDATA_DIR, "frontend", "public", "img")

elif getattr(sys, "frozen", False):
    # ---- FALLBACK PRODUÇÃO COMPILADO (Caso o EXE rode isolado sem argumento) ----
    APPDATA_BASE = os.environ.get("APPDATA", os.path.expanduser("~"))
    APPDATA_DIR = os.path.join(APPDATA_BASE, PRODUCT_NAME)
    BASE_RESOURCES_DIR = RECURSOS_INSTALADOS

    db_path = os.path.join(APPDATA_DIR, "data", "mangas.db")
    IMG_DIR = os.path.join(APPDATA_DIR, "frontend", "public", "img")
else:
    # ---- MODO DESENVOLVIMENTO (Rodando via VS Code puro) ----
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_RESOURCES_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

    db_path = os.path.join(BASE_DIR, "data", "mangas.db")
    IMG_DIR = os.path.join(BASE_RESOURCES_DIR, "frontend", "public", "img")


# Garante que as pastas do ambiente ativo existam
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# --- PONTE PARA O SEU FLUXO DE DUAL BUILDS ---
default_jpg_source = os.path.join(
    BASE_RESOURCES_DIR, "frontend", "public", "img", "default.jpg"
)
default_jpg_destination = os.path.join(IMG_DIR, "default.jpg")

if os.path.exists(default_jpg_source) and not os.path.exists(default_jpg_destination):
    try:
        shutil.copy2(default_jpg_source, default_jpg_destination)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Erro ao copiar imagem padrao: {e}", file=sys.stderr)

# Se houver um banco pré-moldado nos recursos originais
default_db_source = os.path.join(BASE_RESOURCES_DIR, "backend", "data", "mangas.db")
if os.path.exists(default_db_source) and not os.path.exists(db_path):
    try:
        shutil.copy2(default_db_source, db_path)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Erro ao copiar banco inicial: {e}", file=sys.stderr)


# Modificado para receber a resposta empacotada contendo o ID correspondente da consulta
def send_response(response_packet):
    """Envia o JSON garantindo que caracteres acentuados não sejam escapados."""
    json_output = json.dumps(response_packet, ensure_ascii=False)
    sys.stdout.write(json_output + "\n")
    sys.stdout.flush()


def main():
    """Gerencia as operações do banco de dados e integração com o Electron."""
    try:
        conn = sqlite3.connect(db_path)
        conn.text_factory = lambda b: str(b, "utf-8", "ignore")
        cur = conn.cursor()
    except sqlite3.Error as e:
        # Se falhar no boot, retorna erro genérico inicial empacotado sem ID
        send_response(
            {"id": None, "data": None, "error": f"Erro de conexão DB: {str(e)}"}
        )
        return

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mangas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_pt TEXT,
        nome_en TEXT,
        capitulo INTEGER,
        link TEXT,
        capa TEXT,
        status TEXT,
        ordem INTEGER
    )
    """)
    conn.commit()

    # Início do Loop Infinito do Sidecar. O Python fica escutando o sys.stdin continuamente.
    while True:
        req_id = None
        try:
            input_data = sys.stdin.readline()

            # Se o Electron fechar a conexão, a linha virá vazia e encerramos o loop
            if not input_data:
                break

            input_data = input_data.strip()
            if not input_data:
                continue

            # Desembrulha o pacote recebido do Electron
            request_packet = json.loads(input_data)
            req_id = request_packet.get("id")
            payload = request_packet.get("payload", {})
            action = payload.get("action")

            # Variáveis padrão para retorno interno da iteração
            result_data = None
            error_message = None

            if action == "insert":
                origem_capa = payload.get("caminho_completo")
                nome_final_capa = "default.jpg"

                if origem_capa and os.path.exists(origem_capa):
                    extensao = os.path.splitext(origem_capa)[1]
                    nome_final_capa = f"capa_{uuid.uuid4().hex}{extensao}"
                    shutil.copy2(origem_capa, os.path.join(IMG_DIR, nome_final_capa))

                cur.execute("SELECT MAX(ordem) FROM mangas")
                res = cur.fetchone()
                proxima_ordem = (res[0] + 1) if (res and res[0] is not None) else 0

                cur.execute(
                    "INSERT INTO mangas (nome_pt, nome_en, capitulo, link, capa, status, ordem) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (
                        payload.get("nome_pt"),
                        payload.get("nome_en"),
                        payload.get("capitulo"),
                        payload.get("link"),
                        nome_final_capa,
                        payload.get("status", "Lendo"),
                        proxima_ordem,
                    ),
                )

                conn.commit()
                new_id = cur.lastrowid
                result_data = {"status": "OK", "capa": nome_final_capa, "id": new_id}

            elif action == "list":
                limite = payload.get("limite", 20)
                pagina = payload.get("pagina", 1)
                filtro_texto = payload.get("filtro", "").strip()

                offset = (pagina - 1) * limite

                if filtro_texto:
                    query = (
                        "SELECT * FROM mangas "
                        "WHERE nome_pt LIKE ? "
                        "ORDER BY ordem ASC LIMIT ? OFFSET ?"
                    )
                    cur.execute(query, (f"%{filtro_texto}%", limite, offset))
                else:
                    query = "SELECT * FROM mangas ORDER BY ordem ASC LIMIT ? OFFSET ?"
                    cur.execute(query, (limite, offset))

                rows = cur.fetchall()
                result_data = [
                    {
                        "id": r[0],
                        "nome_pt": r[1],
                        "nome_en": r[2],
                        "capitulo": r[3],
                        "link": r[4],
                        "capa": r[5],
                        "status": r[6],
                        "ordem": r[7],
                    }
                    for r in rows
                ]

            elif action == "delete":
                cur.execute(
                    "SELECT capa FROM mangas WHERE id = ?", (payload.get("id"),)
                )
                res = cur.fetchone()
                if res and res[0] != "default.jpg":
                    path_arq = os.path.join(IMG_DIR, res[0])
                    if os.path.exists(path_arq):
                        os.remove(path_arq)
                cur.execute("DELETE FROM mangas WHERE id = ?", (payload.get("id"),))
                conn.commit()
                result_data = {"status": "OK"}

            elif action == "update_status":
                cur.execute(
                    "UPDATE mangas SET status = ? WHERE id = ?",
                    (payload.get("status"), payload.get("id")),
                )
                conn.commit()
                result_data = {"status": "OK"}

            elif action == "update_order":
                for index, manga_id in enumerate(payload.get("order_list", [])):
                    cur.execute(
                        "UPDATE mangas SET ordem = ? WHERE id = ?", (index, manga_id)
                    )
                conn.commit()
                result_data = {"status": "OK"}

            elif action == "update_full":
                manga_id = payload.get("id")
                novo_capitulo = payload.get("capitulo")
                novo_link = payload.get("link")
                origem_capa = payload.get("caminho_completo")
                capa_atual = payload.get("capa")

                nome_final_capa = capa_atual

                if origem_capa and os.path.exists(origem_capa):
                    try:
                        cur.execute("SELECT capa FROM mangas WHERE id = ?", (manga_id,))
                        res_antigo = cur.fetchone()
                        if res_antigo and res_antigo[0] != "default.jpg":
                            path_antigo = os.path.join(IMG_DIR, res_antigo[0])
                            if os.path.exists(path_antigo):
                                os.remove(path_antigo)

                        extensao = os.path.splitext(origem_capa)[1]
                        nome_final_capa = f"capa_{uuid.uuid4().hex}{extensao}"
                        shutil.copy2(
                            origem_capa, os.path.join(IMG_DIR, nome_final_capa)
                        )
                    except Exception:  # pylint: disable=broad-exception-caught
                        nome_final_capa = "default.jpg"

                cur.execute(
                    "UPDATE mangas SET capitulo = ?, link = ?, capa = ? WHERE id = ?",
                    (novo_capitulo, novo_link, nome_final_capa, manga_id),
                )
                conn.commit()
                result_data = {"status": "OK", "capa": nome_final_capa}

            elif action == "clear_database":
                conn.close()  # Libera o arquivo mangas.db no Windows imediatamente
                try:
                    # 1. Remove o arquivo físico do banco de dados active
                    if os.path.exists(db_path):
                        os.remove(db_path)

                    # 2. Reseta a pasta de capas excluindo as geradas
                    if os.path.exists(IMG_DIR):
                        shutil.rmtree(IMG_DIR)
                        os.makedirs(IMG_DIR, exist_ok=True)

                    # 3. Restaura o default.jpg se ele estiver nos recursos originais
                    if os.path.exists(default_jpg_source):
                        shutil.copy2(default_jpg_source, default_jpg_destination)

                    # 4. Recria um banco vazio estruturado e atualiza os ponteiros do loop
                    conn = sqlite3.connect(db_path)
                    conn.text_factory = lambda b: str(b, "utf-8", "ignore")
                    cur = conn.cursor()
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS mangas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome_pt TEXT,
                        nome_en TEXT,
                        capitulo INTEGER,
                        link TEXT,
                        capa TEXT,
                        status TEXT,
                        ordem INTEGER
                    )
                    """)
                    conn.commit()
                    result_data = {
                        "status": "OK",
                        "message": "Dados limpos com sucesso!",
                    }
                except Exception as e:  # pylint: disable=broad-exception-caught
                    error_message = f"Falha ao limpar dados: {str(e)}"
                    # Se falhou, reconecta no banco de dados por segurança para não quebrar o loop
                    conn = sqlite3.connect(db_path)
                    conn.text_factory = lambda b: str(b, "utf-8", "ignore")
                    cur = conn.cursor()

            else:
                error_message = f"Ação desconhecida: {action}"

            # Devolve a resposta estruturada para o Electron mapeada com o ID correspondente
            send_response({"id": req_id, "data": result_data, "error": error_message})

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Evita que erros inesperados
            # de processamento de JSON matem o loop persistente do Sidecar
            send_response(
                {
                    "id": req_id,
                    "data": None,
                    "error": f"Erro crítico no loop do Python: {str(e)}\n{traceback.format_exc()}",
                }
            )

    # Fora do while: fechamento seguro caso o loop seja quebrado voluntariamente
    try:
        conn.close()
    except Exception:  # pylint: disable=broad-exception-caught
        pass


if __name__ == "__main__":
    main()
