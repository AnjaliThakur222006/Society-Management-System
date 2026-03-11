import sqlite3

# Connect to the database
conn = sqlite3.connect('society.db')
c = conn.cursor()

# Get all users
c.execute('SELECT id, name, email, role, password FROM users')
users = c.fetchall()

print('Available users:')
print('ID | Name | Email | Role | Password')
print('-' * 50)
for user in users:
    print(f'{user[0]} | {user[1]} | {user[2]} | {user[3]} | {user[4]}')

# Get all residents
c.execute('SELECT id, user_id, flat_number, resident_type FROM residents')
residents = c.fetchall()

print('\nResidents:')
print('ID | User ID | Flat Number | Resident Type')
print('-' * 50)
for resident in residents:
    print(f'{resident[0]} | {resident[1]} | {resident[2]} | {resident[3]}')

conn.close()