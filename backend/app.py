import sys
import json
import sqlite3
import os

# Garante que o banco de dados seja criado na pasta correta
# independente de onde o processo seja iniciado
db_path = os.path.join(os.path.dirname(__file__), "database.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS test (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)
""")
conn.commit()

# Lendo o payload enviado pelo Electron
try:
    payload = json.loads(sys.argv[1])
    
    if payload.get("action") == "insert":
        cur.execute("INSERT INTO test (name) VALUES (?)", (payload["name"],))
        conn.commit()
        # Retorna um JSON para o Electron
        print(json.dumps({"status": "OK", "message": "Inserido com sucesso"}))

    elif payload.get("action") == "list":
        cur.execute("SELECT * FROM test")
        rows = cur.fetchall()
        # Transforma a lista de tuplas em uma lista de dicionários
        results = [{"id": r[0], "name": r[1]} for r in rows]
        print(json.dumps(results))

except Exception as e:
    print(json.dumps({"error": str(e)}))

finally:
    conn.close()