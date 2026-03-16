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
    
    print("Checking profile pictures...")
    print("="*50)
    
    for user in users:
        user_id, name, profile_pic = user
        file_path = os.path.join(profile_dir, profile_pic) if profile_pic else None
        
        if profile_pic:
            # Check if file exists
            file_exists = os.path.exists(file_path) if file_path else False
            status = "EXISTS" if file_exists else "MISSING"
            print(f"User {user_id} ({name}): {profile_pic} [{status}]")
        else:
            print(f"User {user_id} ({name}): No profile picture set")
    
    conn.close()
    print("\nDatabase connection closed successfully.")
    
except Exception as e:
    print(f"Error connecting to database: {e}")