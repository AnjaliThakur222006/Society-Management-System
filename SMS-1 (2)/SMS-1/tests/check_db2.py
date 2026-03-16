import sqlite3

# Connect to the database
conn = sqlite3.connect('society.db')
c = conn.cursor()

# Get all table names
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()

print('Database tables:')
for table in tables:
    print(table[0])

# Check if deliveries table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deliveries';")
deliveries_exists = c.fetchone()

if deliveries_exists:
    print('\nDeliveries table exists')
    
    # Get deliveries table structure
    c.execute('PRAGMA table_info(deliveries)')
    cols = c.fetchall()
    
    print('Deliveries table structure:')
    for col in cols:
        print(col)
        
    # Check if there are any deliveries in the database
    c.execute('SELECT * FROM deliveries')
    deliveries = c.fetchall()
    
    print('\nExisting deliveries:')
    for delivery in deliveries:
        print(delivery)
else:
    print('\nDeliveries table does not exist')

conn.close()