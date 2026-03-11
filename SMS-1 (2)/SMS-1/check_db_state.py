import pymysql

db = pymysql.connect(
    host='localhost',
    user='root',
    password='anjali@2',
    database='society_management',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = db.cursor()

cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
print('Tables in database:')
for table in tables:
    print(f'- {table[0]}')

# Check visitors table structure
cursor.execute("DESCRIBE visitors")
columns = cursor.fetchall()
print("\nColumns in visitors table:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Check if there are any visitor records
cursor.execute("SELECT COUNT(*) FROM visitors")
visitor_count = cursor.fetchone()[0]
print(f"\nTotal visitors in database: {visitor_count}")

if visitor_count > 0:
    print("\nSample visitor records:")
    cursor.execute("SELECT * FROM visitors LIMIT 5")
    sample_visitors = cursor.fetchall()
    for i, visitor in enumerate(sample_visitors):
        print(f"  {i+1}. {visitor}")

cursor.close()
db.close()