import sqlite3

conn = sqlite3.connect('society.db')
c = conn.cursor()

# Check visitor entries table
print("=== Visitor Entries Table ===")
try:
    c.execute('SELECT COUNT(*) FROM visitor_entries')
    count = c.fetchone()[0]
    print(f'Total visitor entries: {count}')
    
    if count > 0:
        c.execute('SELECT * FROM visitor_entries LIMIT 5')
        rows = c.fetchall()
        print('Sample entries:')
        for i, row in enumerate(rows):
            print(f'{i+1}. {row}')
    else:
        print('No visitor entries found')
except Exception as e:
    print(f'Error: {e}')

# Check table structure
print("\n=== Table Structure ===")
try:
    c.execute("PRAGMA table_info(visitor_entries)")
    columns = c.fetchall()
    print("Columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
except Exception as e:
    print(f'Error getting table info: {e}')

conn.close()