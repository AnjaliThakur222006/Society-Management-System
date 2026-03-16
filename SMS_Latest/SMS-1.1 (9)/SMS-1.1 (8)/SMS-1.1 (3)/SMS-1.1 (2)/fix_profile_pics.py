import mysql.connector
import os

try:
    # Connect to database
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get all users with profile pictures
    c.execute("SELECT id, name, profile_pic FROM users")
    users = c.fetchall()
    
    # Define the profile pictures directory
    profile_dir = "SMS-1.1/SMS-1 (2)/SMS-1/static/uploads/profiles"
    
    print("Fixing profile picture inconsistencies...")
    print("="*50)
    
    updated_count = 0
    
    for user in users:
        user_id, name, profile_pic = user
        file_path = os.path.join(profile_dir, profile_pic) if profile_pic else None
        
        if profile_pic and profile_pic != 'default.png':
            # Check if file exists
            file_exists = os.path.exists(file_path) if file_path else False
            
            if not file_exists:
                print(f"FIXING: User {user_id} ({name}): {profile_pic} -> default.png (FILE MISSING)")
                # Update database to use default.png
                c.execute("UPDATE users SET profile_pic = 'default.png' WHERE id = %s", (user_id,))
                updated_count += 1
            else:
                print(f"OK: User {user_id} ({name}): {profile_pic}")
        elif profile_pic == 'default.png':
            print(f"OK: User {user_id} ({name}): {profile_pic}")
        else:
            print(f"OK: User {user_id} ({name}): No profile picture set")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\nFixed {updated_count} inconsistent profile picture entries.")
    print("Database connection closed successfully.")
    
except Exception as e:
    print(f"Error connecting to database: {e}")