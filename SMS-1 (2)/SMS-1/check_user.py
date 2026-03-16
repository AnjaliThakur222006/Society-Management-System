import sqlite3

conn = sqlite3.connect('society.db')
c = conn.cursor()

# Check if user with flat A-3 exists
c.execute("SELECT u.name, u.email, u.password, r.flat_number FROM users u JOIN residents r ON u.id = r.user_id WHERE r.flat_number = 'A-3'")
result = c.fetchone()
print('User with flat A-3:', result)

# Also check all residents to see what's available
c.execute("SELECT u.name, u.email, r.flat_number FROM users u JOIN residents r ON u.id = r.user_id")
all_residents = c.fetchall()
print('All residents:', all_residents)

conn.close()