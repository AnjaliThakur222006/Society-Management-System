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

# Get all table names
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
print('Current tables:', [row[0] for row in tables])

# Check the structure of existing residents table
cursor.execute("DESCRIBE residents")
residents_structure = cursor.fetchall()
print('\nResidents table structure:')
for col in residents_structure:
    print(f'  {col}')

cursor.close()
db.close()