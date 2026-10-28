# database.py
import sqlite3

def init_local_db():
    # Conecta o crea la base de datos local SQLite
    conn = sqlite3.connect('farmapp_cache.db')
    cursor = conn.cursor()
    
    # Crear una tabla básica para el caché local del inventario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            stock INTEGER NOT NULL,
            price REAL NOT NULL,
            last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Base de datos local (SQLite) inicializada.")

if __name__ == "__main__":
    init_local_db()