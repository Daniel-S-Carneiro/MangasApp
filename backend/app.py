"""
Manga Manager Backend
Gerencia o banco de dados SQLite e integração de imagens para o Electron.
"""

import sys
import json
import sqlite3
import os
import shutil
import uuid
import io

# Força o stdout a usar UTF-8 para que o Electron receba os acentos corretamente
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# --- CONFIGURAÇÃO DE CAMINHOS ---
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    IMG_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend", "public", "img")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "public", "img"))

db_path = os.path.join(BASE_DIR, "data", "mangas.db")

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(db_path), exist_ok=True)


def send_response(data):
    """Envia o JSON garantindo que caracteres acentuados não sejam escapados."""
    # O ensure_ascii=False mantém o "í" como "í" em vez de "\u00ed"
    json_output = json.dumps(data, ensure_ascii=False)
    sys.stdout.write(json_output + "\n")
    sys.stdout.flush()


def main():
    """Função principal que gerencia as operações do banco de dados e integra com o Electron."""
    try:
        conn = sqlite3.connect(db_path)
        # Força o retorno de strings em vez de bytes (ajuda com encoding)
        conn.text_factory = str
        cur = conn.cursor()
    except sqlite3.Error as e:
        send_response({"error": f"Erro de conexão DB: {str(e)}"})
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

    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            send_response([])
            return

        payload = json.loads(input_data)
        action = payload.get("action")

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
            send_response({"status": "OK", "capa": nome_final_capa})

        elif action == "list":
            cur.execute("SELECT * FROM mangas ORDER BY ordem ASC")
            rows = cur.fetchall()
            results = [
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
            send_response(results)

        elif action == "delete":
            cur.execute("SELECT capa FROM mangas WHERE id = ?", (payload.get("id"),))
            res = cur.fetchone()
            if res and res[0] != "default.jpg":
                path_arq = os.path.join(IMG_DIR, res[0])
                if os.path.exists(path_arq):
                    os.remove(path_arq)
            cur.execute("DELETE FROM mangas WHERE id = ?", (payload.get("id"),))
            conn.commit()
            send_response({"status": "OK"})

        elif action == "update_status":
            cur.execute(
                "UPDATE mangas SET status = ? WHERE id = ?",
                (payload["status"], payload["id"]),
            )
            conn.commit()
            send_response({"status": "OK"})

        elif action == "update_order":
            for index, manga_id in enumerate(payload.get("order_list", [])):
                cur.execute(
                    "UPDATE mangas SET ordem = ? WHERE id = ?", (index, manga_id)
                )
            conn.commit()
            send_response({"status": "OK"})

        elif action == "update_full":
            cur.execute(
                "UPDATE mangas SET capitulo = ?, link = ? WHERE id = ?",
                (payload.get("capitulo"), payload.get("link"), payload.get("id")),
            )
            conn.commit()
            send_response({"status": "OK"})

    except (json.JSONDecodeError, sqlite3.Error) as e:
        send_response({"error": str(e)})
    finally:
        conn.close()


if __name__ == "__main__":
    main()
