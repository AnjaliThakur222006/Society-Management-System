import pymysql

try:
    # Test MySQL connection
    db = pymysql.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    cursor = db.cursor()
    
    # Create database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS society_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("Database created successfully or already exists")
    
    # Close connections
    cursor.close()
    db.close()
    
    print("MySQL connection test successful!")
    
except Exception as e:
    print(f"MySQL connection failed: {e}")