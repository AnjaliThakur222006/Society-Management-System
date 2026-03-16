import sqlite3
import os

# Get actual photo files
photo_files = []
for file in os.listdir('static/images/visitor_photos'):
    if file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
        photo_files.append(file)

print("Actual photo files found:")
for file in photo_files:
    print(f"  {file}")

# Connect to database
conn = sqlite3.connect('society.db')
c = conn.cursor()

# Get current visitor entries
c.execute('SELECT id, visitor_name, photo FROM visitor_entries WHERE photo IS NOT NULL')
entries = c.fetchall()

print(f"\nCurrent entries with photos ({len(entries)}):")
for entry in entries:
    print(f"  ID: {entry[0]}, Name: {entry[1]}, DB Photo: {entry[2]}")

# Update entries to use actual files (if we have matching patterns)
updated_count = 0
for entry in entries:
    entry_id, name, db_photo = entry
    
    # Extract the UUID part from database path
    if db_photo and '/' in db_photo:
        db_filename = db_photo.split('/')[-1]
        db_uuid = db_filename.split('.')[0]  # Get UUID part
        
        # Look for matching file
        matching_file = None
        for actual_file in photo_files:
            actual_uuid = actual_file.split('.')[0]
            if actual_uuid == db_uuid:
                matching_file = actual_file
                break
        
        if matching_file:
            # File exists, update the path to be correct
            new_photo_path = f'/static/images/visitor_photos/{matching_file}'
            c.execute('UPDATE visitor_entries SET photo = ? WHERE id = ?', 
                     (new_photo_path, entry_id))
            print(f"✓ Updated entry {entry_id} ({name}): {db_photo} -> {new_photo_path}")
            updated_count += 1
        else:
            # No matching file, set to NULL so it shows "No Photo"
            c.execute('UPDATE visitor_entries SET photo = NULL WHERE id = ?', (entry_id,))
            print(f"✗ No file found for entry {entry_id} ({name}), set to NULL")
            updated_count += 1

conn.commit()
print(f"\nUpdated {updated_count} entries")

# Show final state
c.execute('SELECT id, visitor_name, photo FROM visitor_entries')
final_entries = c.fetchall()
print(f"\nFinal state:")
for entry in final_entries:
    status = "HAS PHOTO" if entry[2] else "NO PHOTO"
    print(f"  ID: {entry[0]}, Name: {entry[1]}, Status: {status}")

conn.close()