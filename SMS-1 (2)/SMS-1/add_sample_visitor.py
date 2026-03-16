import pymysql
import os
from datetime import datetime

# Connect to database
db = pymysql.connect(
    host='localhost',
    user='root',
    password='anjali@2',
    database='society_management',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.Cursor
)
cursor = db.cursor()

# Insert a sample visitor entry without photo to test the display
sample_visitor = (
    'Test Visitor',
    '9876543210',
    'Personal Visit',
    '101',
    None,  # No photo
    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    None,
    'In'
)

cursor.execute("""INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, photo, entry_time, exit_time, status)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", sample_visitor)

db.commit()
cursor.execute("SELECT LAST_INSERT_ID()")
visitor_id = cursor.fetchone()[0]
print(f"Added sample visitor entry with ID: {visitor_id}")

# Also check what entries exist now
cursor.execute("SELECT id, visitor_name, mobile_number, purpose, flat_number, status FROM visitor_entries")
entries = cursor.fetchall()
print(f"\nCurrent visitor entries ({len(entries)} total):")
for entry in entries:
    print(f"  ID: {entry[0]}, Name: {entry[1]}, Mobile: {entry[2]}, Purpose: {entry[3]}, Flat: {entry[4]}, Status: {entry[5]}")

cursor.close()
db.close()