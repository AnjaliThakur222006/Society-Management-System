import sqlite3

# Test the authentication logic
username = 'A-3'  # This is the flat number
password = '123456'  # This is the actual password from the database

conn = sqlite3.connect('society.db')
c = conn.cursor()

# First, try to authenticate with email
print("Trying email authentication...")
c.execute("SELECT * FROM users WHERE email=? AND password=?", (username, password))
user = c.fetchone()
print("Email auth result:", user)

# If not found with email, try to authenticate with flat number
if not user:
    print("Email auth failed, trying flat number authentication...")
    # Find user by flat number
    c.execute("""SELECT u.* FROM users u 
                JOIN residents r ON u.id = r.user_id 
                WHERE r.flat_number=? AND u.password=?""", (username, password))
    user = c.fetchone()
    print("Flat number auth result:", user)

conn.close()

if user:
    print(f"Authentication successful! User: {user[1]}, Role: {user[4]}")
else:
    print("Authentication failed!")