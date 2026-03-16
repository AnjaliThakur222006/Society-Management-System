import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Check if profile_pic column exists
    c.execute("DESCRIBE users")
    columns = c.fetchall()
    print('Users table columns:')
    for col in columns:
        print(col)
    print()
    
    # Check sample user data
    c.execute("SELECT id, name, profile_pic FROM users LIMIT 10")
    users = c.fetchall()
    print('Sample users with profile pics:')
    for user in users:
        print(user)
    
    conn.close()
    print("\nDatabase connection closed successfully.")
    
except Exception as e:
    print(f"Error connecting to database: {e}")