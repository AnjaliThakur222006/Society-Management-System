import sqlite3

# Connect to the database
conn = sqlite3.connect('society.db')
c = conn.cursor()

# Get visitors table structure
c.execute('PRAGMA table_info(visitors)')
cols = c.fetchall()

print('Visitors table structure:')
for col in cols:
    print(col)

# Check if there are any visitors in the database
c.execute('SELECT * FROM visitors')
visitors = c.fetchall()

print('\nExisting visitors:')
for visitor in visitors:
    print(visitor)

conn.close()