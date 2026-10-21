import sqlite3
import os

# Locate the app.db file relative to this script
db_path = os.path.join(os.path.dirname(__file__), 'app.db')

print(f"Connecting directly to SQLite database at: {db_path}...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the LabSchedule table using standard SQL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_labschedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject VARCHAR(255) NOT NULL,
            section VARCHAR(100) NOT NULL,
            date DATE NOT NULL,
            time_start VARCHAR(50) NOT NULL,
            time_end VARCHAR(50) NOT NULL,
            lab VARCHAR(100) NOT NULL,
            instructor VARCHAR(255) NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✨ Success! The lab schedule table structure has been built directly inside app.db.")

except Exception as e:
    print(f"Error building table: {e}")