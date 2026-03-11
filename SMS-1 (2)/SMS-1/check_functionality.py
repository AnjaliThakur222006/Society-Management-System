import sqlite3

conn = sqlite3.connect('society.db')
c = conn.cursor()

print("=== Checking Visitors Table ===")
c.execute("SELECT COUNT(*) FROM visitors;")
visitor_count = c.fetchone()[0]
print(f"Total visitors in database: {visitor_count}")

print("\n=== Checking Charity Table ===")
c.execute("SELECT COUNT(*) FROM charity;")
charity_count = c.fetchone()[0]
print(f"Total charity records in database: {charity_count}")

print("\n=== Checking Users for Tenant Access ===")
c.execute("SELECT id, name, email, role FROM users WHERE role IN ('Owner', 'Tenant');")
users = c.fetchall()
print("Users with Owner/Tenant roles:")
for user in users:
    print(f"  - ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}")

print("\n=== Checking Residents ===")
c.execute("SELECT id, user_id, flat_number, resident_type FROM residents;")
residents = c.fetchall()
print("Residents:")
for resident in residents:
    print(f"  - ID: {resident[0]}, User ID: {resident[1]}, Flat: {resident[2]}, Type: {resident[3]}")

conn.close()