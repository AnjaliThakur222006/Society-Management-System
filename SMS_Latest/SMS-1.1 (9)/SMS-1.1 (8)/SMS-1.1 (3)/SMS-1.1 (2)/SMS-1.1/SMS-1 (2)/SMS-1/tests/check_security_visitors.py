import sqlite3

# Connect to the database
conn = sqlite3.connect('society.db')
c = conn.cursor()

# Check what the security dashboard query would return
c.execute("""SELECT v.id, u.name, r.flat_number, v.visitor_name, v.contact, v.visit_purpose, v.visit_date, v.visit_time, v.status 
             FROM visitors v
             JOIN residents r ON v.resident_id = r.id 
             JOIN users u ON r.user_id = u.id 
             WHERE v.status = 'Pending'
             ORDER BY v.visit_date DESC, v.visit_time DESC""")
pending_visitors = c.fetchall()

print('Pending visitors for security dashboard:')
print('ID | Resident Name | Flat | Visitor Name | Contact | Purpose | Date | Time | Status')
print('-' * 100)
for visitor in pending_visitors:
    print(f'{visitor[0]} | {visitor[1]} | {visitor[2]} | {visitor[3]} | {visitor[4]} | {visitor[5]} | {visitor[6]} | {visitor[7]} | {visitor[8]}')

conn.close()