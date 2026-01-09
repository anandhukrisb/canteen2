import sqlite3
import os

db_path = 'db.sqlite3'
if not os.path.exists(db_path):
    print("db.sqlite3 not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column_safe(table, col_def, col_name_check):
    try:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cursor.fetchall()]
        if col_name_check in cols:
            print(f"Column {col_name_check} already exists in {table}")
        else:
            print(f"Adding column {col_name_check} to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
            print("Done.")
    except Exception as e:
        print(f"Error adding {col_name_check} to {table}: {e}")

try:
    # Add active_manager_id to app_canteen
    add_column_safe('app_canteen', 'active_manager_id INTEGER REFERENCES auth_user(id)', 'active_manager_id')

    # Add is_active to app_canteen
    add_column_safe('app_canteen', 'is_active BOOLEAN DEFAULT 1', 'is_active')

    conn.commit()
    print("Database patched successfully.")

except Exception as e:
    print(f"Global Error: {e}")
finally:
    conn.close()
