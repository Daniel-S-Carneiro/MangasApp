import sys
import json
import sqlite3
import os
import shutil
import uuid

# Configuração de caminhos baseada na localização do script
# BASE_DIR será a pasta 'backend'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# O Banco de dados permanece na pasta que você já usa e funciona
db_path = os.path.join(BASE_DIR, "data", "mangas.db")

# Lógica de detecção de ambiente para Imagens
IS_DEV = getattr(sys, 'frozen', False) == False

if IS_DEV:
    # No desenvolvimento, sobe um nível para frontend/public/img
    IMG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "public", "img"))
else:
    # No build, usa o caminho do executável como base
    IMG_DIR = os.path.join(os.path.dirname(sys.executable), "frontend", "public", "img")

os.makedirs(IMG_DIR, exist_ok=True)

# Garante que os diretórios existam
os.makedirs(os.path.dirname(db_path), exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Criação da tabela de Mangas
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
    if len(sys.argv) > 1:
        payload = json.loads(sys.argv[1])
        action = payload.get("action")

        # --- Lógica de INSERIR ---
        if action == "insert":
            origem_capa = payload.get("caminho_completo")
            nome_final_capa = "default.jpg"

            if origem_capa and os.path.exists(origem_capa):
                try:
                    extensao = os.path.splitext(origem_capa)[1]
                    nome_final_capa = f"manga_{uuid.uuid4().hex}{extensao}"
                    destino_capa = os.path.join(IMG_DIR, nome_final_capa)
                    
                    # Copia a imagem selecionada para dentro do projeto
                    shutil.copy2(origem_capa, destino_capa)
                except Exception as e:
                    print(json.dumps({"debug_error": f"Erro shutil: {str(e)}"}))
                    nome_final_capa = "default.jpg"
            
            cur.execute("SELECT MAX(ordem) FROM mangas")
            result = cur.fetchone()
            proxima_ordem = (result[0] + 1) if (result and result[0] is not None) else 0

            cur.execute("""
                INSERT INTO mangas (nome_pt, nome_en, capitulo, link, capa, status, ordem)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                payload.get("nome_pt"), 
                payload.get("nome_en"), 
                payload.get("capitulo"),
                payload.get("link"), 
                nome_final_capa, 
                payload.get("status", "Lendo"),
                proxima_ordem
            ))
            conn.commit()
            print(json.dumps({"status": "OK", "message": "Salvo com sucesso!", "capa": nome_final_capa}))

        # --- Lógica de LISTAR ---
        elif action == "list":
            cur.execute("SELECT * FROM mangas ORDER BY ordem ASC")
            rows = cur.fetchall()
            results = [
                {
                    "id": r[0], "nome_pt": r[1], "nome_en": r[2], 
                    "capitulo": r[3], "link": r[4], "capa": r[5], 
                    "status": r[6], "ordem": r[7]
                } for r in rows
            ]
            print(json.dumps(results))

        # --- Lógica de ATUALIZAR STATUS ---
        elif action == "update_status":
            cur.execute("UPDATE mangas SET status = ? WHERE id = ?", (payload["status"], payload["id"]))
            conn.commit()
            print(json.dumps({"status": "OK"}))
            
        elif action == "update_chapter":
            cur.execute("UPDATE mangas SET capitulo = ? WHERE id = ?", (payload["capitulo"], payload["id"]))
            conn.commit()
            print(json.dumps({"status": "OK"}))

        elif action == "update_full":
            cur.execute("""
                UPDATE mangas 
                SET capitulo = ?, link = ? 
                WHERE id = ?
            """, (payload["capitulo"], payload["link"], payload["id"]))
            conn.commit()
            print(json.dumps({"status": "OK"}))

        # --- Lógica de EXCLUIR ---
        elif action == "delete":
            cur.execute("SELECT capa FROM mangas WHERE id = ?", (payload.get("id"),))
            res = cur.fetchone()
            if res and res[0] != "default.jpg":
                caminho_arquivo = os.path.join(IMG_DIR, res[0])
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
            
            cur.execute("DELETE FROM mangas WHERE id = ?", (payload.get("id"),))
            conn.commit()
            print(json.dumps({"status": "OK"}))

        # --- Lógica de REORDENAR ---
        elif action == "update_order":
            new_order = payload.get("order_list", [])
            for index, id_manga in enumerate(new_order):
                cur.execute("UPDATE mangas SET ordem = ? WHERE id = ?", (index, id_manga))
            conn.commit()
            print(json.dumps({"status": "OK"}))

except Exception as e:
    print(json.dumps({"error": str(e)}))
finally:
    conn.close()