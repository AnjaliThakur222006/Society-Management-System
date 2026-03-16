import pymysql

try:
    db = pymysql.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society_management',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = db.cursor()
    
    # Check all tables
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    print('Tables in database:', tables)
    
    # Check blocks table
    if 'blocks' in tables:
        cursor.execute("SELECT * FROM blocks")
        blocks = cursor.fetchall()
        print('Blocks:', blocks)
    else:
        print('Blocks table does not exist')
    
    # Check flats table
    if 'flats' in tables:
        cursor.execute("SELECT * FROM flats")
        flats = cursor.fetchall()
        print('Flats:', flats)
    else:
        print('Flats table does not exist')
    
    cursor.close()
    db.close()
except Exception as e:
    print(f"Error: {e}")