import sqlite3

conn = sqlite3.connect('society.db')
c = conn.cursor()

# Get all table names
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print('Current tables in the database:')
for table in tables:
    print(f'  - {table[0]}')

print("\n" + "="*50)

# Show record counts for each table
for table in tables:
    table_name = table[0]
    if table_name != 'sqlite_sequence':  # Skip system table
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        print(f'{table_name}: {count} records')

print("\n" + "="*50)

# Show sample records from key tables
key_tables = ['users', 'residents', 'visitors', 'payments', 'complaints']

for table in key_tables:
    if table in [t[0] for t in tables]:
        print(f"\nSample records from {table}:")
        c.execute(f"SELECT * FROM {table} LIMIT 5")
        rows = c.fetchall()
        for row in rows:
            print(f'  {row}')

conn.close()