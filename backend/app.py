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

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

if sys.stdin.encoding != "utf-8":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

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
    json_output = json.dumps(data, ensure_ascii=False)
    sys.stdout.write(json_output + "\n")
    sys.stdout.flush()


def main():
    """Gerencia as operações do banco de dados e integração com o Electron."""
    try:
        conn = sqlite3.connect(db_path)
        conn.text_factory = lambda b: str(b, "utf-8", "ignore")
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
        input_data = sys.stdin.readline().strip()
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
            new_id = cur.lastrowid
            send_response({"status": "OK", "capa": nome_final_capa, "id": new_id})

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
                (payload.get("status"), payload.get("id")),
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
                    shutil.copy2(origem_capa, os.path.join(IMG_DIR, nome_final_capa))
                except Exception:  # pylint: disable=broad-exception-caught
                    nome_final_capa = "default.jpg"

            cur.execute(
                "UPDATE mangas SET capitulo = ?, link = ?, capa = ? WHERE id = ?",
                (novo_capitulo, novo_link, nome_final_capa, manga_id),
            )
            conn.commit()
            send_response({"status": "OK", "capa": nome_final_capa})

        else:
            send_response({"error": f"Ação desconhecida: {action}"})

    except (json.JSONDecodeError, sqlite3.Error) as e:
        send_response({"error": str(e)})
    finally:
        conn.close()


if __name__ == "__main__":
    main()
