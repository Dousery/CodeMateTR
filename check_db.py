import sqlite3

try:
    conn = sqlite3.connect('btk_project.db')
    cursor = conn.cursor()
    
    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Database tables:")
    for table in tables:
        print(f"  {table[0]}")
    
    # Check TestSession table structure if it exists
    if any('test_session' in table[0].lower() for table in tables):
        cursor.execute("PRAGMA table_info(test_session)")
        columns = cursor.fetchall()
        print("\nTestSession columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    else:
        print("\nTestSession table does not exist yet")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
