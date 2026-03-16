"""
Project Cleanup Script
Deletes unnecessary files and creates clean database
"""
import os
import mysql.connector

# Files to delete
files_to_delete = [
    'add_sample_visitor.py',
    'check_charity.py', 
    'check_db_state.py',
    'check_db_structure.py',
    'check_db.py',
    'check_full_data.py',
    'check_functionality.py',
    'check_photo_data.py',
    'check_report_data.py',
    'check_resident_data.py',
    'check_security.py',
    'check_user.py',
    'check_visitor_data.py',
    'check_visitor_entries.py',
    'export_sqlite_to_sql.py',
    'fix_photo_paths.py',
    'test_auth.py',
    'test_endpoints.py',
    'test_report.py',
    'verify_endpoints.py',
    'view_db_content.py',
    'app.py.mysql',
    'society.db',
    'FIXES_APPLIED.md',
    'ADMIN_PANEL_DOCUMENTATION.md',
    'API_ENDPOINTS.md',
    'COMPLETE_PROJECT_GUIDE.md',
    'PANELS_EXPLAINED_HINDI.md',
    'SESSION_AUTHENTICATION.md',
    'TECHNICAL_DETAILS.md',
]

# Documentation files to keep
docs_to_keep = [
    'README.md',
    'SETUP.md',
]

project_path = r"c:\Users\thaku\Downloads\SMS_Latest (2)\SMS_Latest\SMS-1.1 (9)\SMS-1.1 (8)\SMS-1.1 (3)\SMS-1.1 (2)\SMS-1.1\SMS-1 (2)\SMS-1"

print("=" * 50)
print("CLEANING PROJECT FILES")
print("=" * 50)

# Delete unnecessary files
for filename in files_to_delete:
    filepath = os.path.join(project_path, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"Deleted: {filename}")
        except Exception as e:
            print(f"Error deleting {filename}: {e}")
    else:
        print(f"File not found: {filename}")

print("\n" + "=" * 50)
print("CLEANING DATABASE")
print("=" * 50)

# Connect to MySQL and clean database
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2'
    )
    c = conn.cursor()
    
    # Drop and recreate database
    print("Dropping database 'society'...")
    c.execute("DROP DATABASE IF EXISTS society")
    
    print("Creating database 'society'...")
    c.execute("CREATE DATABASE society")
    
    conn.close()
    
    # Now connect to the new database and create tables
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Create tables
    print("\nCreating tables...")
    
    # Users table
    c.execute("""
        CREATE TABLE users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password VARCHAR(100),
            role ENUM('Admin', 'Owner', 'Tenant', 'Security'),
            phone VARCHAR(20),
            profile_pic VARCHAR(200),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ users table created")
    
    # Blocks table
    c.execute("""
        CREATE TABLE blocks (
            id INT PRIMARY KEY AUTO_INCREMENT,
            block_name VARCHAR(10)
        )
    """)
    print("✓ blocks table created")
    
    # Flats table
    c.execute("""
        CREATE TABLE flats (
            id INT PRIMARY KEY AUTO_INCREMENT,
            block_id INT,
            flat_number VARCHAR(20),
            status ENUM('Occupied', 'Vacant'),
            owner_name VARCHAR(100)
        )
    """)
    print("✓ flats table created")
    
    # Residents table
    c.execute("""
        CREATE TABLE residents (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            flat_number VARCHAR(20),
            resident_type ENUM('Owner', 'Tenant'),
            occupancy_start DATE
        )
    """)
    print("✓ residents table created")
    
    # Maintenance bills table
    c.execute("""
        CREATE TABLE maintenance_bills (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            flat_number VARCHAR(20),
            amount DECIMAL(10,2),
            due_date DATE,
            status ENUM('Paid', 'Unpaid'),
            late_fine DECIMAL(10,2) DEFAULT 0,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ maintenance_bills table created")
    
    # Payments table
    c.execute("""
        CREATE TABLE payments (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            amount DECIMAL(10,2),
            payment_date DATE,
            payment_method VARCHAR(50),
            receipt_number VARCHAR(50),
            status ENUM('Paid', 'Pending')
        )
    """)
    print("✓ payments table created")
    
    # Complaints table
    c.execute("""
        CREATE TABLE complaints (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            category VARCHAR(50),
            description TEXT,
            status ENUM('Open', 'Assigned', 'Resolved'),
            priority ENUM('Normal', 'Medium', 'Urgent'),
            ai_score INT,
            complaint_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolution_date DATE
        )
    """)
    print("✓ complaints table created")
    
    # Parking table
    c.execute("""
        CREATE TABLE parking (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            slot_number VARCHAR(20),
            slot_type ENUM('Fixed', 'Shared'),
            vehicle_number VARCHAR(20),
            status ENUM('Available', 'Occupied')
        )
    """)
    print("✓ parking table created")
    
    # Notices table
    c.execute("""
        CREATE TABLE notices (
            id INT PRIMARY KEY AUTO_INCREMENT,
            admin_id INT,
            title VARCHAR(200),
            content TEXT,
            priority ENUM('Normal', 'High', 'Urgent'),
            notice_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ notices table created")
    
    # Events table
    c.execute("""
        CREATE TABLE events (
            id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(200),
            event_type VARCHAR(50),
            event_date DATE,
            event_time TIME,
            venue VARCHAR(100),
            description TEXT,
            image VARCHAR(200),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ events table created")
    
    # Visitors table
    c.execute("""
        CREATE TABLE visitors (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            visitor_name VARCHAR(100),
            mobile_number VARCHAR(20),
            purpose VARCHAR(100),
            visit_date DATE,
            entry_time DATETIME,
            exit_time DATETIME,
            status VARCHAR(20)
        )
    """)
    print("✓ visitors table created")
    
    # Visitor entries table
    c.execute("""
        CREATE TABLE visitor_entries (
            id INT PRIMARY KEY AUTO_INCREMENT,
            visitor_name VARCHAR(100),
            mobile_number VARCHAR(20),
            purpose VARCHAR(100),
            flat_number VARCHAR(20),
            photo VARCHAR(200),
            entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            exit_time DATETIME,
            status VARCHAR(20)
        )
    """)
    print("✓ visitor_entries table created")
    
    # Deliveries table
    c.execute("""
        CREATE TABLE deliveries (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            delivery_company VARCHAR(100),
            delivery_item VARCHAR(200),
            arrival_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status ENUM('Pending', 'Allowed', 'Collected', 'Delivered'),
            collected_time DATETIME
        )
    """)
    print("✓ deliveries table created")
    
    # Charity table
    c.execute("""
        CREATE TABLE charity (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            item_type VARCHAR(100),
            quantity INT,
            description TEXT,
            status ENUM('Pending', 'Approved', 'Picked', 'Completed'),
            pickup_date DATE
        )
    """)
    print("✓ charity table created")
    
    # Emergency contacts table
    c.execute("""
        CREATE TABLE emergency_contacts (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100),
            contact_type VARCHAR(50),
            phone_number VARCHAR(20),
            priority INT,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    print("✓ emergency_contacts table created")
    
    # Settings table
    c.execute("""
        CREATE TABLE settings (
            id INT PRIMARY KEY AUTO_INCREMENT,
            society_name VARCHAR(200),
            society_address TEXT,
            society_phone VARCHAR(20),
            society_email VARCHAR(100)
        )
    """)
    print("✓ settings table created")
    
    # Emergency logs table
    c.execute("""
        CREATE TABLE emergency_logs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            emergency_type VARCHAR(50),
            description TEXT,
            log_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            action_taken TEXT,
            resolved BOOLEAN DEFAULT FALSE
        )
    """)
    print("✓ emergency_logs table created")
    
    # Vehicles table
    c.execute("""
        CREATE TABLE vehicles (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT,
            vehicle_number VARCHAR(20),
            vehicle_type VARCHAR(50),
            registration_date DATE,
            status VARCHAR(20)
        )
    """)
    print("✓ vehicles table created")
    
    # Insert default admin user
    print("\n" + "=" * 50)
    print("INSERTING DEFAULT DATA")
    print("=" * 50)
    
    c.execute("""
        INSERT INTO users (name, email, password, role, phone) 
        VALUES ('Admin', 'admin@society.com', 'admin123', 'Admin', '9876543210')
    """)
    print("✓ Admin user created: admin@society.com / admin123")
    
    # Insert default settings
    c.execute("""
        INSERT INTO settings (society_name, society_address, society_phone, society_email)
        VALUES ('My Society', '123 Society Address, City - 123456', '+91 9876543210', 'info@society.com')
    """)
    print("✓ Default settings created")
    
    # Insert some sample blocks
    c.execute("INSERT INTO blocks (block_name) VALUES ('A')")
    c.execute("INSERT INTO blocks (block_name) VALUES ('B')")
    c.execute("INSERT INTO blocks (block_name) VALUES ('C')")
    print("✓ Sample blocks created: A, B, C")
    
    # Insert some sample flats
    c.execute("SELECT id FROM blocks WHERE block_name = 'A'")
    block_a = c.fetchone()[0]
    c.execute("SELECT id FROM blocks WHERE block_name = 'B'")
    block_b = c.fetchone()[0]
    c.execute("SELECT id FROM blocks WHERE block_name = 'C'")
    block_c = c.fetchone()[0]
    
    # Block A flats
    for i in range(1, 11):
        c.execute(f"INSERT INTO flats (block_id, flat_number, status) VALUES ({block_a}, 'A-{i:03d}', 'Vacant')")
    
    # Block B flats
    for i in range(1, 11):
        c.execute(f"INSERT INTO flats (block_id, flat_number, status) VALUES ({block_b}, 'B-{i:03d}', 'Vacant')")
    
    # Block C flats
    for i in range(1, 11):
        c.execute(f"INSERT INTO flats (block_id, flat_number, status) VALUES ({block_c}, 'C-{i:03d}', 'Vacant')")
    
    print("✓ 30 sample flats created (10 each for A, B, C blocks)")
    
    # Insert sample emergency contacts
    emergency_contacts = [
        ('Ambulance', 'Medical', '108', 1),
        ('Fire Brigade', 'Fire', '101', 2),
        ('Police', 'Police', '100', 3),
        ('Society Security', 'Security', '9876543210', 4),
        ('Society Admin', 'Admin', '9876543211', 5),
    ]
    c.executemany("INSERT INTO emergency_contacts (name, contact_type, phone_number, priority) VALUES (%s, %s, %s, %s)", emergency_contacts)
    print("✓ Emergency contacts created")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("PROJECT CLEANUP COMPLETE!")
    print("=" * 50)
    print("\nDatabase is now CLEAN with:")
    print("- 0 users (except 1 admin)")
    print("- 0 residents")
    print("- 0 bills")
    print("- 0 payments")
    print("- 0 complaints")
    print("- 3 blocks (A, B, C)")
    print("- 30 vacant flats")
    print("\nLogin credentials:")
    print("Admin: admin@society.com / admin123")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure MySQL is running and credentials are correct!")
