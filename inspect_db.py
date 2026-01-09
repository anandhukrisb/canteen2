import sqlite3

try:
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    print("--- Tables ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(tables)
    
    if 'app_canteen' in tables:
        print("\n--- Columns in app_canteen ---")
        cursor.execute("PRAGMA table_info(app_canteen);")
        for col in cursor.fetchall():
            print(col[1])

    if 'app_order' in tables:
        print("\n--- Columns in app_order ---")
        cursor.execute("PRAGMA table_info(app_order);")
        for col in cursor.fetchall():
            print(col[1])

    conn.close()
except Exception as e:
    print(e)
