import sqlite3

conn = sqlite3.connect('society.db')
c = conn.cursor()

c.execute('SELECT id, visitor_name, photo FROM visitor_entries')
rows = c.fetchall()

print("Visitor Entries Photo Data:")
print("=" * 50)
for row in rows:
    print(f"ID: {row[0]}")
    print(f"Name: {row[1]}")
    print(f"Photo field: {repr(row[2])}")
    print(f"Photo field type: {type(row[2])}")
    print("-" * 30)

conn.close()