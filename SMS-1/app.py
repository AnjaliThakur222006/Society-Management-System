

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import mysql.connector
import os
import time
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'society_management_secret_key'

# Configure upload folders
UPLOAD_FOLDER = 'static/images/events'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure profile picture upload folder
PROFILE_FOLDER = 'static/uploads/profiles'
app.config['PROFILE_FOLDER'] = PROFILE_FOLDER

# Ensure upload directories exist
os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static/images/visitor_photos'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, app.config['PROFILE_FOLDER']), exist_ok=True)

# Get society settings
# Database connection helper function
def get_db():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    return conn

def get_society_settings():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("SELECT society_name, society_address, society_phone, society_email FROM settings WHERE id = 1")
    result = c.fetchone()
    conn.close()

    if result:
        return {
            'society_name': result[0],
            'society_address': result[1],
            'society_phone': result[2],
            'society_email': result[3]
        }
    else:
        # Return default values if no settings found
        return {
            'society_name': 'SOCIETY MANAGEMENT SYSTEM',
            'society_address': '123 Society Address, City, State - 123456',
            'society_phone': '+91 9876543210',
            'society_email': 'info@society.com'
        }

# Database initialization
def init_db():
    import os
    print(f"Current working directory: {os.getcwd()}")
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Create vehicles table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resident_id INT NOT NULL,
            vehicle_number VARCHAR(50) NOT NULL UNIQUE,
            vehicle_type VARCHAR(50) NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'Registered',
            FOREIGN KEY (resident_id) REFERENCES residents(id)
        )
    """)
    
    # Check if users table exists and is empty
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]

    # Insert sample users if table is empty
    if user_count == 0:
        # Sample users with INSERT IGNORE for idempotency
        sample_users = [
            ('Admin User', 'admin@society.com', 'admin123', 'Admin', '9876543210'),
            ('John Owner', 'john.owner@gmail.com', 'owner123', 'Owner', '9876543211'),
            ('Jane Tenant', 'jane.tenant@gmail.com', 'tenant123', 'Tenant', '9876543212'),
            ('Security Guard', 'security@society.com', 'security123', 'Security', '9876543213')
        ]
        for user in sample_users:
            c.execute("INSERT IGNORE INTO users (name, email, password, role, phone) VALUES (%s, %s, %s, %s, %s)", user)

        # Add sample blocks
        c.execute("INSERT INTO blocks (block_name) VALUES (%s)", ('A',))
        c.execute("INSERT INTO blocks (block_name) VALUES (%s)", ('B',))

        # Add sample flats
        c.execute("SELECT id FROM blocks WHERE block_name = %s", ('A',))
        block_a_id = c.fetchone()[0]
        c.execute("SELECT id FROM blocks WHERE block_name = %s", ('B',))
        block_b_id = c.fetchone()[0]

        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_a_id, 'A-101', 'Occupied', 'John Owner'))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_a_id, 'A-102', 'Vacant', None))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_a_id, 'A-103', 'Vacant', None))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_b_id, 'B-202', 'Occupied', 'Jane Tenant'))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_b_id, 'B-203', 'Vacant', None))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_b_id, 'B-204', 'Vacant', None))

        # Add sample residents
        c.execute("SELECT id FROM users WHERE email = %s", ('john.owner@gmail.com',))
        owner_result = c.fetchone()
        owner_resident_id = None
        if owner_result:
            owner_id = owner_result[0]
            c.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                      (owner_id, 'A-101', 'Owner', '2023-01-01'))
            owner_resident_id = c.lastrowid

        c.execute("SELECT id FROM users WHERE email = %s", ('jane.tenant@gmail.com',))
        tenant_result = c.fetchone()
        tenant_resident_id = None
        if tenant_result:
            tenant_id = tenant_result[0]
            c.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                      (tenant_id, 'B-202', 'Tenant', '2023-06-01'))
            tenant_resident_id = c.lastrowid

        # Add sample parking slots
        if owner_resident_id:
            c.execute("INSERT INTO parking (resident_id, slot_number, slot_type, status) VALUES (%s, %s, %s, %s)",
                      (owner_resident_id, 'P-101', 'Fixed', 'Available'))

        if tenant_resident_id:
            c.execute("INSERT INTO parking (resident_id, slot_number, slot_type, status) VALUES (%s, %s, %s, %s)",
                      (tenant_resident_id, 'P-202', 'Shared', 'Available'))

        # Add sample vacant parking slots for new residents
        c.execute("INSERT INTO parking (slot_number, slot_type, status) VALUES (%s, %s, %s)",
                  ('P-301', 'Fixed', 'Available'))
        c.execute("INSERT INTO parking (slot_number, slot_type, status) VALUES (%s, %s, %s)",
                  ('P-302', 'Fixed', 'Available'))
        c.execute("INSERT INTO parking (slot_number, slot_type, status) VALUES (%s, %s, %s)",
                  ('P-303', 'Fixed', 'Available'))
        c.execute("INSERT INTO parking (slot_number, slot_type, status) VALUES (%s, %s, %s)",
                  ('P-304', 'Shared', 'Available'))
        c.execute("INSERT INTO parking (slot_number, slot_type, status) VALUES (%s, %s, %s)",
                  ('P-305', 'Shared', 'Available'))

        # Add sample maintenance bills and payments
        if owner_resident_id:
            # Add unpaid bill
            c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                      (owner_resident_id, 'A-101', 2500, '2024-01-15', 'Unpaid'))
            # Add paid bill
            c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                      (owner_resident_id, 'A-101', 2500, '2024-02-15', 'Paid'))
            # Add payment record for paid bill
            c.execute("INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status) VALUES (%s, %s, %s, %s, %s, %s)",
                      (owner_resident_id, 2500, '2024-02-10', 'Online', 'REC-001', 'Paid'))

        if tenant_resident_id:
            # Add unpaid bill for tenant
            c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                      (tenant_resident_id, 'B-202', 2500, '2024-01-15', 'Unpaid'))
            # Add paid bill
            c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                      (tenant_resident_id, 'B-202', 2500, '2024-02-15', 'Paid'))
            # Add payment record
            c.execute("INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status) VALUES (%s, %s, %s, %s, %s, %s)",
                      (tenant_resident_id, 2500, '2024-02-10', 'Cash', 'REC-002', 'Paid'))

        # Add sample visitor entries
        c.execute("SELECT id FROM residents WHERE flat_number = 'A-101'")
        owner_res = c.fetchone()
        if owner_res:
            # Add sample visitors for owner A-101
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, NOW())",
                      ('Ravi Kumar', '9876543210', 'Family Visit', 'A-101', 'In'))
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL 1 DAY))",
                      ('Priya Sharma', '9876543211', 'Friend Visit', 'A-101', 'Out'))
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL 2 DAY))",
                      ('Delivery Person', '9876543212', 'Package Delivery', 'A-101', 'Out'))

        c.execute("SELECT id FROM residents WHERE flat_number = 'B-202'")
        tenant_res = c.fetchone()
        if tenant_res:
            # Add sample visitors for tenant B-202
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL 3 DAY))",
                      ('Amit Patel', '9876543213', 'Colleague Visit', 'B-202', 'Out'))
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL 5 DAY))",
                      ('Food Delivery', '9876543214', 'Food Delivery', 'B-202', 'Out'))

        # Add default settings
        c.execute("SELECT COUNT(*) FROM settings")
        settings_count = c.fetchone()[0]
        if settings_count == 0:
            c.execute("INSERT INTO settings (id, society_name, society_address, society_phone, society_email) VALUES (1, %s, %s, %s, %s)",
                      ('SOCIETY MANAGEMENT SYSTEM', '123 Society Address, City, State - 123456', '+91 9876543210', 'info@society.com'))

        # Add sample emergency contacts if none exist
        c.execute("SELECT COUNT(*) FROM emergency_contacts")
        emergency_contacts_count = c.fetchone()[0]
        if emergency_contacts_count == 0:
            # Add predefined emergency contacts
            emergency_contacts = [
                ('Admin Emergency', 'Admin', '9876543210', 1, True),
                ('Security Guard', 'Security', '9876543211', 2, True),
                ('Ambulance Service', 'Ambulance', '108', 3, True),
                ('Fire Department', 'Fire', '101', 4, True),
                ('Police Department', 'Police', '100', 5, True),
                ('Maintenance', 'Maintenance', '9876543212', 6, True),
                ('Nearby Doctor', 'Doctor', '9876543213', 7, True),
            ]
            c.executemany("INSERT INTO emergency_contacts (name, contact_type, phone_number, priority, is_active) VALUES (%s, %s, %s, %s, %s)",
                          emergency_contacts)

    # Add sample blocks if none exist
    c.execute("SELECT COUNT(*) FROM blocks")
    block_count = c.fetchone()[0]
    if block_count == 0:
        c.execute("INSERT INTO blocks (block_name) VALUES (%s)", ('A',))
        c.execute("INSERT INTO blocks (block_name) VALUES (%s)", ('B',))

    # Add sample flats if none exist
    c.execute("SELECT COUNT(*) FROM flats")
    flat_count = c.fetchone()[0]
    if flat_count == 0:
        c.execute("SELECT id FROM blocks WHERE block_name = %s", ('A',))
        block_a_id = c.fetchone()[0]
        c.execute("SELECT id FROM blocks WHERE block_name = %s", ('B',))
        block_b_id = c.fetchone()[0]

        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_a_id, 'A-101', 'Occupied', 'John Owner'))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_a_id, 'A-102', 'Vacant', None))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_a_id, 'A-103', 'Vacant', None))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_b_id, 'B-202', 'Occupied', 'Jane Tenant'))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_b_id, 'B-203', 'Vacant', None))
        c.execute("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)",
                  (block_b_id, 'B-204', 'Vacant', None))

    # Add sample residents if none exist
    c.execute("SELECT COUNT(*) FROM residents")
    resident_count = c.fetchone()[0]
    if resident_count == 0:
        c.execute("SELECT id FROM users WHERE email = %s", ('john.owner@gmail.com',))
        owner_result = c.fetchone()
        owner_id = owner_result[0] if owner_result else None

        c.execute("SELECT id FROM users WHERE email = %s", ('jane.tenant@gmail.com',))
        tenant_result = c.fetchone()
        tenant_id = tenant_result[0] if tenant_result else None

        if owner_id:
            c.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                      (owner_id, 'A-101', 'Owner', '2023-01-01'))

        if tenant_id:
            c.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                      (tenant_id, 'B-202', 'Tenant', '2023-06-01'))

    # Add sample maintenance bills and payments if not exist
    c.execute("SELECT COUNT(*) FROM payments")
    payment_count = c.fetchone()[0]
    if payment_count == 0:
        # Get resident ids
        c.execute("SELECT id FROM residents WHERE flat_number = 'A-101'")
        owner_resident = c.fetchone()
        owner_resident_id = owner_resident[0] if owner_resident else None

        c.execute("SELECT id FROM residents WHERE flat_number = 'B-202'")
        tenant_resident = c.fetchone()
        tenant_resident_id = tenant_resident[0] if tenant_resident else None

        # Add sample maintenance bills and payments
        if owner_resident_id:
            # Add unpaid bill
            c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                      (owner_resident_id, 'A-101', 2500, '2024-01-15', 'Unpaid'))
            # Add paid bill
            c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                      (owner_resident_id, 'A-101', 2500, '2024-02-15', 'Paid'))
            # Add payment record for paid bill
            c.execute("INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status) VALUES (%s, %s, %s, %s, %s, %s)",
                      (owner_resident_id, 2500, '2024-02-10', 'Online', 'REC-001', 'Paid'))

        if tenant_resident_id:
            # Add unpaid bill for tenant
            c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                      (tenant_resident_id, 'B-202', 2500, '2024-01-15', 'Unpaid'))
            # Add paid bill
            c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                      (tenant_resident_id, 'B-202', 2500, '2024-02-15', 'Paid'))
            # Add payment record
            c.execute("INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status) VALUES (%s, %s, %s, %s, %s, %s)",
                      (tenant_resident_id, 2500, '2024-02-10', 'Cash', 'REC-002', 'Paid'))

        # Add sample visitor entries if none exist
        c.execute("SELECT COUNT(*) FROM visitor_entries")
        visitor_count = c.fetchone()[0]
        if visitor_count == 0:
            # Add sample visitors for A-101
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, NOW())",
                      ('Ravi Kumar', '9876543210', 'Family Visit', 'A-101', 'In'))
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL 1 DAY))",
                      ('Priya Sharma', '9876543211', 'Friend Visit', 'A-101', 'Out'))
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL 2 DAY))",
                      ('Delivery Person', '9876543212', 'Package Delivery', 'A-101', 'Out'))
            
            # Add sample visitors for B-202
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL 3 DAY))",
                      ('Amit Patel', '9876543213', 'Colleague Visit', 'B-202', 'Out'))
            c.execute("INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status, entry_time) VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL 5 DAY))",
                      ('Food Delivery', '9876543214', 'Food Delivery', 'B-202', 'Out'))

# Add more sample residents and payments for reports (idempotent)
    c.execute("SELECT COUNT(*) FROM users WHERE role = 'Owner'")
    owner_count = c.fetchone()[0]
    
    if owner_count < 10:  # Add more residents if we don't have enough
        print("Adding additional sample users safely...")
        additional_users = [
            ('Mike Wilson', 'mike.wilson@gmail.com', 'owner123', 'Owner', '9876543215'),
            ('Sarah Davis', 'sarah.davis@gmail.com', 'owner123', 'Owner', '9876543216'),
            ('David Brown', 'david.brown@gmail.com', 'owner123', 'Owner', '9876543217'),
            ('Lisa Johnson', 'lisa.johnson@gmail.com', 'owner123', 'Owner', '9876543218'),
            ('James Smith', 'james.smith@gmail.com', 'tenant123', 'Tenant', '9876543219'),
            ('Emily White', 'emily.white@gmail.com', 'tenant123', 'Tenant', '9876543220'),
            ('Robert Taylor', 'robert.taylor@gmail.com', 'owner123', 'Owner', '9876543221'),
            ('Jennifer Lee', 'jennifer.lee@gmail.com', 'tenant123', 'Tenant', '9876543222'),
        ]
        new_user_ids = []
        for user in additional_users:
            c.execute("INSERT IGNORE INTO users (name, email, password, role, phone) VALUES (%s, %s, %s, %s, %s)", user)
            if c.rowcount > 0:
                new_user_ids.append(c.lastrowid)
        print(f"Inserted {len(new_user_ids)} new users (duplicates skipped).")
        
        # Get block IDs
        c.execute("SELECT id FROM blocks WHERE block_name = 'A'")
        block_a_id = c.fetchone()[0]
        c.execute("SELECT id FROM blocks WHERE block_name = 'B'")
        block_b_id = c.fetchone()[0]
        
        # Add more flats
        additional_flats = [
            (block_a_id, 'A-104', 'Vacant', None),
            (block_a_id, 'A-105', 'Vacant', None),
            (block_b_id, 'B-205', 'Vacant', None),
            (block_b_id, 'B-206', 'Vacant', None),
            (block_b_id, 'B-207', 'Vacant', None),
        ]
        c.executemany("INSERT INTO flats (block_id, flat_number, status, owner_name) VALUES (%s, %s, %s, %s)", additional_flats)
        
        # Only proceed with residents if we have new users
        if new_user_ids:
            print(f"Setting up residents for {len(new_user_ids)} new users.")
            # Use only available new_user_ids (slice to match flat availability)
            available_ids = new_user_ids[:5]  # Limit to available flats
            flat_numbers = ['A-104', 'A-105', 'B-205', 'B-206', 'B-207']
            resident_types = ['Owner', 'Owner', 'Owner', 'Owner', 'Tenant']
            
            for i, user_id in enumerate(available_ids):
                c.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                          (user_id, flat_numbers[i], resident_types[i], '2024-01-01'))
            
            # Update corresponding flat statuses
            owner_names = ['Mike Wilson', 'Sarah Davis', 'David Brown', 'Lisa Johnson', 'James Smith']
            for i, flat_num in enumerate(flat_numbers[:len(available_ids)]):
                c.execute("UPDATE flats SET status = 'Occupied', owner_name = %s WHERE flat_number = %s",
                          (owner_names[i], flat_num))
        else:
            print("No new users inserted, skipping resident setup.")

    # Add more payments with different statuses
    c.execute("SELECT COUNT(*) FROM payments")
    payment_count = c.fetchone()[0]
    
    if payment_count < 20:
        # Get all resident IDs
        c.execute("SELECT id, flat_number FROM residents ORDER BY id")
        all_residents = c.fetchall()
        
        import random
        from datetime import datetime, timedelta
        
        payment_methods = ['Online', 'Cash', 'UPI', 'Bank Transfer']
        
        # Add more payments with various statuses
        for resident_id, flat_num in all_residents:
            # Add some paid payments
            for month in range(1, 6):  # 5 months of payments
                days_ago = random.randint(10, 150)
                payment_date = datetime.now() - timedelta(days=days_ago)
                amount = random.randint(2000, 5000)
                
                # 70% paid, 20% pending, 10% overdue
                status_rand = random.random()
                if status_rand < 0.7:
                    status = 'Paid'
                    payment_date_str = payment_date.strftime('%Y-%m-%d')
                    c.execute("""INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status) 
                                  VALUES (%s, %s, %s, %s, %s, %s)""",
                              (resident_id, amount, payment_date_str, random.choice(payment_methods), f'REC-{random.randint(1000,9999)}', 'Paid'))
                elif status_rand < 0.9:
                    status = 'Pending'
                    c.execute("""INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status) 
                                  VALUES (%s, %s, %s, %s, %s, %s)""",
                              (resident_id, amount, None, random.choice(payment_methods), None, 'Pending'))
                else:
                    # Overdue - past due date
                    due_date = (datetime.now() - timedelta(days=random.randint(5, 30))).strftime('%Y-%m-%d')
                    c.execute("""INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status, late_fine) 
                                  VALUES (%s, %s, %s, %s, 'Unpaid', %s)""",
                              (resident_id, flat_num, amount, due_date, random.randint(100, 500)))

    # Add complaints with different statuses
    c.execute("SELECT COUNT(*) FROM complaints")
    complaint_count = c.fetchone()[0]
    
    if complaint_count < 15:
        # Get resident IDs
        c.execute("SELECT id FROM residents ORDER BY id")
        resident_ids = [row[0] for row in c.fetchall()]
        
        categories = ['Water', 'Electricity', 'Lift', 'Noise', 'Parking', 'Security', 'Cleaning', 'Other']
        statuses = ['Open', 'In Progress', 'Resolved']
        priorities = ['Low', 'Normal', 'High']
        
        import random
        from datetime import datetime, timedelta
        
        for i, resident_id in enumerate(resident_ids[:8]):  # Use first 8 residents
            # Add 2 complaints per resident
            for j in range(2):
                category = random.choice(categories)
                status = random.choice(statuses)
                priority = random.choice(priorities)
                days_ago = random.randint(1, 60)
                complaint_date = datetime.now() - timedelta(days=days_ago)
                
                descriptions = [
                    f'{category} issue in the apartment',
                    f'{category} not working properly',
                    f'Emergency: {category} problem',
                    f'Need immediate attention for {category}',
                    f'Regular maintenance required for {category}',
                ]
                description = random.choice(descriptions)
                
                if status == 'Resolved':
                    resolution_date = complaint_date + timedelta(days=random.randint(3, 15))
                    c.execute("""INSERT INTO complaints (resident_id, category, description, status, priority, complaint_date, resolution_date) 
                                  VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                              (resident_id, category, description, status, priority, complaint_date.strftime('%Y-%m-%d'), resolution_date.strftime('%Y-%m-%d')))
                else:
                    c.execute("""INSERT INTO complaints (resident_id, category, description, status, priority, complaint_date) 
                                  VALUES (%s, %s, %s, %s, %s, %s)""",
                              (resident_id, category, description, status, priority, complaint_date.strftime('%Y-%m-%d')))



# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Login page
@app.route('/login')
def login():
    return render_template('login.html')

# Login authentication
@app.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form['email']  # Using 'email' field to accept both email and flat number
    password = request.form['password']

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # First, try to authenticate with email
    c.execute("SELECT * FROM users WHERE email=%s AND password=%s", (username, password))
    user = c.fetchone()

    # If not found with email, try to authenticate with flat number
    if not user:
        c.close()
        c = conn.cursor()
        # Find user by flat number
        c.execute("""SELECT u.* FROM users u
                    JOIN residents r ON u.id = r.user_id
                    WHERE r.flat_number=%s AND u.password=%s""", (username, password))
        user = c.fetchone()

    conn.close()

    if user:
        session['user_id'] = user[0]
        session['name'] = user[1]
        # Get user role from the users table (index 4 in the users table)
        session['role'] = user[4]
        # Get user profile picture (index 7 in the users table)
        # Handle case where profile_pic column might not exist in some rows
        if len(user) > 7 and user[7]:
            session['profile_pic'] = user[7]
        else:
            session['profile_pic'] = 'default.png'

        if user[4] == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif user[4] == 'Owner':
            return redirect(url_for('resident_dashboard'))
        elif user[4] == 'Tenant':
            return redirect(url_for('tenant_dashboard'))
        elif user[4] == 'Security':
            return redirect(url_for('security_dashboard'))
    else:
        # Check if user exists but password is wrong
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        # First, try to find user with email
        c.execute("SELECT * FROM users WHERE email=%s", (username,))
        user_exists = c.fetchone()

        # If not found with email, try to find via flat number
        if not user_exists:
            c.close()
            c = conn.cursor()
            c.execute("SELECT u.* FROM users u \n                        JOIN residents r ON u.id = r.user_id \n                        WHERE r.flat_number=%s", (username,))
            user_exists = c.fetchone()

        conn.close()

        if user_exists:
            # User exists but password is wrong
            return redirect(url_for('login', error='Incorrect password. Please try again.'))
        else:
            # User doesn't exist
            return redirect(url_for('login', error='User not found. Please check your email or flat number.'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Registration page
@app.route('/register')
def register():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get all blocks for dropdown
    c.execute("SELECT * FROM blocks")
    blocks = c.fetchall()

    conn.close()

    return render_template('register.html', blocks=blocks)

# Registration form submission
@app.route('/register', methods=['POST'])
def register_submit():
    # Server-side validation
    name = request.form.get('name', '').strip()
    block_id = request.form.get('block', '').strip()
    flat_number = request.form.get('flat_number', '').strip()
    mobile = request.form.get('mobile', '').strip()
    email = request.form.get('email', '').strip()
    user_type = request.form.get('user_type', '').strip()
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    # Handle profile picture upload
    profile_pic = 'default.png'
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and file.filename != '':
            # Validate file type
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
            ext = os.path.splitext(file.filename)[1].lower()
            if ext in allowed_extensions:
                # Generate unique filename
                unique_filename = str(uuid.uuid4()) + ext
                # Use app.root_path to ensure path is relative to app directory
                filepath = os.path.join(app.root_path, app.config['PROFILE_FOLDER'], unique_filename)
                file.save(filepath)
                profile_pic = unique_filename
            else:
                return jsonify({'success': False, 'message': 'Invalid file type. Only JPG, PNG, and GIF files are allowed.'})
    
    # Validate required fields
    if not all([name, block_id, flat_number, mobile, email, user_type, password, confirm_password]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate email format
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address'})
    
    # Validate mobile (should be 10 digits)
    mobile_digits = ''.join(filter(str.isdigit, mobile))
    if len(mobile_digits) != 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit phone number'})
    
    # Validate user type
    if user_type not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Invalid user type'})
    
    # Validate password length
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'})
    
    # Validate password match
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})
    
    # Validate name (should contain letters)
    if not any(c.isalpha() for c in name):
        return jsonify({'success': False, 'message': 'Name must contain at least one letter'})
    
    # Validate flat number format
    if '-' not in flat_number:
        return jsonify({'success': False, 'message': 'Invalid flat number format. Use format like A-101'})
    
    # Validate mobile number (ensure it's all digits)
    if not mobile_digits.isdigit():
        return jsonify({'success': False, 'message': 'Mobile number should contain only digits'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Check if email already exists
    c.execute("SELECT id FROM users WHERE email = %s", (email,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'A user with this email already exists'})

    # Check if flat exists in flats table - flat_number from form is already complete (e.g., A-1, A-2)
    c.execute("SELECT id, status FROM flats WHERE flat_number = %s", (flat_number,))
    flat_result = c.fetchone()
    if not flat_result:
        conn.close()
        return jsonify({'success': False, 'message': 'Flat number does not exist in the society records'})

    # Check if flat is vacant before allowing registration
    flat_id, flat_status = flat_result
    if flat_status != 'Vacant':
        conn.close()
        return jsonify({'success': False, 'message': 'Selected flat is not available for registration. Please select a vacant flat.'})

    # Double-check if flat is already registered in residents table
    c.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'This flat is already registered'})

    try:
        # Insert user
        c.execute("INSERT INTO users (name, email, password, role, phone, profile_pic) VALUES (%s, %s, %s, %s, %s, %s)",
                  (name, email, password, user_type, mobile_digits, profile_pic))
        user_id = c.lastrowid

        # Insert resident
        c.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                  (user_id, flat_number, user_type, datetime.now().strftime('%Y-%m-%d')))

        # Update flat status to Occupied
        c.execute("UPDATE flats SET status = 'Occupied', owner_name = %s WHERE flat_number = %s",
                  (name, flat_number))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Registration successful. You can now login.'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to register: ' + str(e)})

# Get flats for a specific block (AJAX endpoint)
@app.route('/get_flats/<int:block_id>')
def get_flats(block_id):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get all flats for the selected block (both vacant and occupied)
    c.execute("SELECT flat_number, status FROM flats WHERE block_id = %s ORDER BY flat_number", (block_id,))
    flats = c.fetchall()

    conn.close()

    # Return list of flats with their status
    return jsonify([{'flat_number': flat[0], 'status': flat[1]} for flat in flats])

# Admin blocks management
@app.route('/admin/blocks')
def admin_blocks():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get all blocks
    c.execute("SELECT * FROM blocks ORDER BY block_name")
    blocks = c.fetchall()
    
    # Get flat count per block
    c.execute("""SELECT b.block_name, COUNT(f.id) as total_flats, 
                    SUM(CASE WHEN f.status = 'Vacant' THEN 1 ELSE 0 END) as vacant_flats
                    FROM blocks b 
                    LEFT JOIN flats f ON b.id = f.block_id 
                    GROUP BY b.id, b.block_name""")
    block_stats = c.fetchall()
    
    conn.close()
    
    return render_template('admin/blocks.html', blocks=blocks, block_stats=block_stats)

# Admin add block
@app.route('/admin/blocks/add', methods=['POST'])
def admin_add_block():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    block_name = request.form.get('block_name', '').strip().upper()
    
    if not block_name:
        return jsonify({'success': False, 'message': 'Block name is required'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO blocks (block_name) VALUES (%s)", (block_name,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Block added successfully'})
    except mysql.connector.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Block already exists'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to add block: ' + str(e)})

# Admin add flats to block
@app.route('/admin/flats/add', methods=['POST'])
def admin_add_flats():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    block_id = request.form.get('block_id', '').strip()
    from_flat = request.form.get('from_flat', '').strip()
    to_flat = request.form.get('to_flat', '').strip()
    
    if not all([block_id, from_flat, to_flat]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    try:
        from_flat_num = int(from_flat)
        to_flat_num = int(to_flat)
        
        if from_flat_num > to_flat_num:
            return jsonify({'success': False, 'message': 'From flat number should be less than To flat number'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Flat numbers must be valid integers'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get block name
    c.execute("SELECT block_name FROM blocks WHERE id = %s", (block_id,))
    block = c.fetchone()
    
    if not block:
        conn.close()
        return jsonify({'success': False, 'message': 'Block not found'})
    
    block_name = block[0]
    
    try:
        # Add flats in range with default status 'Vacant'
        for flat_num in range(from_flat_num, to_flat_num + 1):
            flat_number = f"{block_name}-{flat_num}"
            c.execute("INSERT INTO flats (block_id, flat_number, status) VALUES (%s, %s, %s)", (block_id, flat_number, 'Vacant'))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Flats {from_flat_num} to {to_flat_num} added successfully to Block {block_name}'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to add flats: ' + str(e)})

# Admin get all flats with status
@app.route('/admin/flats')
def admin_flats():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get all flats with block information
    c.execute("""SELECT f.id, b.block_name, f.flat_number, f.status, f.owner_name 
                    FROM flats f 
                    JOIN blocks b ON f.block_id = b.id 
                    ORDER BY b.block_name, f.flat_number""")
    flats = c.fetchall()
    
    conn.close()
    
    return render_template('admin/flats.html', flats=flats)

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    # Get quick stats for dashboard
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor(cursor_class=mysql.connector.cursor.MySQLCursorDict)

    # Get resident count
    c.execute("SELECT COUNT(*) as count FROM users WHERE role IN ('Owner', 'Tenant')")
    result = c.fetchone()
    residents_count = result['count'] if result else 0

    # Get payment stats
    c.execute("SELECT COUNT(*) as count FROM payments WHERE status = 'Paid'")
    result = c.fetchone()
    paid_payments = result['count'] if result else 0

    c.execute("SELECT COUNT(*) as count FROM payments WHERE status = 'Pending'")
    result = c.fetchone()
    pending_payments = result['count'] if result else 0

    c.execute("SELECT SUM(amount) as total FROM payments WHERE status = 'Paid'")
    result = c.fetchone()
    total_collection = result['total'] if result and result['total'] is not None else 0

    # Get event count
    c.execute("SELECT COUNT(*) as count FROM events")
    result = c.fetchone()
    event_count = result['count'] if result else 0

    conn.close()

    return render_template('admin/dashboard.html',
                          residents_count=residents_count,
                          paid_payments=paid_payments,
                          pending_payments=pending_payments,
                          total_collection=total_collection,
                          event_count=event_count)


# Resident Dashboard (for Owners)
@app.route('/resident')
def resident_dashboard():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get resident info
    c.execute("SELECT r.flat_number, r.resident_type FROM residents r WHERE r.user_id = %s", (session['user_id'],))
    resident = c.fetchone()

    conn.close()

    return render_template('resident/dashboard.html', resident=resident)


# Tenant Dashboard
@app.route('/tenant')
def tenant_dashboard():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get resident info
    c.execute("SELECT r.flat_number, r.resident_type FROM residents r WHERE r.user_id = %s", (session['user_id'],))
    resident = c.fetchone()

    conn.close()

    return render_template('tenant/dashboard.html', resident=resident)


# Security Dashboard
@app.route('/security')
def security_dashboard():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))

    return render_template('security/dashboard.html')


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user details
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("SELECT name, email, phone, profile_pic FROM users WHERE id = %s", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return redirect(url_for('login'))
    
    user_data = {
        'name': user[0],
        'email': user[1],
        'phone': user[2],
        'profile_pic': user[3] or 'default.png'
    }
    
    return render_template('profile.html', user=user_data)


@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Get form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    
    # Handle profile picture upload
    new_profile_pic = None
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and file.filename != '':
            # Validate file type
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
            ext = os.path.splitext(file.filename)[1].lower()
            if ext in allowed_extensions:
                # Generate unique filename
                unique_filename = str(uuid.uuid4()) + ext
                # Use app.root_path to ensure path is relative to app directory
                filepath = os.path.join(app.root_path, app.config['PROFILE_FOLDER'], unique_filename)
                file.save(filepath)
                new_profile_pic = unique_filename
            else:
                return jsonify({'success': False, 'message': 'Invalid file type. Only JPG, PNG, and GIF files are allowed.'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    try:
        if new_profile_pic:
            # Update with new profile picture
            c.execute("UPDATE users SET name = %s, email = %s, phone = %s, profile_pic = %s WHERE id = %s",
                      (name, email, phone, new_profile_pic, session['user_id']))
            session['profile_pic'] = new_profile_pic
        else:
            # Update without changing profile picture
            c.execute("UPDATE users SET name = %s, email = %s, phone = %s WHERE id = %s",
                      (name, email, phone, session['user_id']))
        
        conn.commit()
        conn.close()
        
        # Update session data
        session['name'] = name
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to update profile: ' + str(e)})


# Admin residents list
@app.route('/admin/residents')
def admin_residents():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""SELECT u.name, u.email, u.phone, r.flat_number, r.resident_type, u.id as user_id
                 FROM users u
                 JOIN residents r ON u.id = r.user_id""")
    residents = c.fetchall()
    conn.close()

    return render_template('admin/residents.html', residents=residents)

# Admin residents JSON endpoint for AJAX
@app.route('/admin/residents/json')
def admin_residents_json():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""SELECT r.id, u.name, r.flat_number
                 FROM residents r
                 JOIN users u ON r.user_id = u.id
                 ORDER BY u.name""")
    residents = c.fetchall()
    conn.close()

    # Convert to list of dicts
    residents_list = [{'id': r[0], 'name': r[1], 'flat_number': r[2]} for r in residents]

    return jsonify({'success': True, 'residents': residents_list})

# Admin complaints
@app.route('/admin/complaints')
def admin_complaints():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""SELECT c.id, u.name, r.flat_number, c.category, c.description, c.status, c.complaint_date, c.priority, c.ai_score
                 FROM complaints c 
                 JOIN residents r ON c.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY c.priority DESC, c.complaint_date DESC""")
    complaints = c.fetchall()
    conn.close()
    
    return render_template('admin/complaints.html', complaints=complaints)

# Admin assign complaint
@app.route('/admin/complaints/assign', methods=['POST'])
def admin_assign_complaint():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    complaint_id = request.form['complaint_id']
    assigned_to = request.form['assigned_to']
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("UPDATE complaints SET status = 'Assigned', assigned_to = %s WHERE id = %s",
              (assigned_to, complaint_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Complaint assigned successfully'})


# Admin add complaint (from admin UI)
@app.route('/admin/complaints/add', methods=['POST'])
def admin_add_complaint():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    # Gather input
    resident_input = request.form.get('resident', '').strip()
    flat_number = request.form.get('flat', '').strip()
    category = request.form.get('category', '').strip() or 'Other'
    description = request.form.get('description', '').strip()

    # Basic validation
    if not description:
        return jsonify({'success': False, 'message': 'Description is required'})

    # Normalize category
    allowed = ['Water', 'Electricity', 'Lift', 'Noise', 'Other']
    if category not in allowed:
        category = 'Other'

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Resolve resident_id using flat_number first, then resident name
    resident_id = None
    try:
        if flat_number:
            c.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
            row = c.fetchone()
            if row:
                resident_id = row[0]

        if not resident_id and resident_input:
            c.close()
            c = conn.cursor()
            # Try to match by exact (case-insensitive) user name
            c.execute("SELECT r.id FROM residents r JOIN users u ON r.user_id = u.id WHERE lower(u.name) = %s", (resident_input.lower(),))
            row = c.fetchone()
            if row:
                resident_id = row[0]

        if not resident_id:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found. Please provide a valid flat number or exact resident name.'})

        # AI Priority Classification
        from ai_priority import classify_priority
        priority, ai_score = classify_priority(description)
        
        # Insert complaint with priority
        c.execute("INSERT INTO complaints (resident_id, category, description, status, priority, ai_score) VALUES (%s, %s, %s, 'Open', %s, %s)",
                  (resident_id, category, description, priority, ai_score))
        conn.commit()
        complaint_id = c.lastrowid
        conn.close()

        return jsonify({'success': True, 'message': 'Complaint added successfully', 'complaint_id': complaint_id})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to add complaint: ' + str(e)})

# Admin resolve complaint
@app.route('/admin/complaints/resolve', methods=['POST'])
def admin_resolve_complaint():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    complaint_id = request.form['complaint_id']
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("UPDATE complaints SET status = 'Resolved', resolution_date = CURRENT_DATE WHERE id = %s",
              (complaint_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Complaint resolved successfully'})

# Admin maintenance bills
@app.route('/admin/maintenance-bills')
def admin_maintenance_bills():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    # Update late fines for all unpaid bills
    update_late_fines()
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""SELECT mb.id, u.name, mb.flat_number, mb.amount, mb.due_date, mb.status, mb.late_fine, mb.created_date
                 FROM maintenance_bills mb
                 JOIN residents r ON mb.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY mb.created_date DESC""")
    bills = c.fetchall()
    
    # Get all residents for the dropdown
    c.execute("""SELECT r.id, u.name, r.flat_number 
                 FROM residents r 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY u.name""")
    residents = c.fetchall()
    conn.close()
    
    return render_template('admin/maintenance_bills.html', bills=bills, residents=residents)


# Admin maintenance payments
@app.route('/admin/payments')
def admin_payments():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""SELECT p.id, u.name, r.flat_number, p.amount, p.payment_date, p.payment_method, p.receipt_number, p.status
                 FROM payments p
                 JOIN residents r ON p.resident_id = r.id
                 JOIN users u ON r.user_id = u.id
                 ORDER BY p.payment_date DESC""")
    payments = c.fetchall()

    # Get all residents for the dropdown
    c.execute("""SELECT r.id, u.name, r.flat_number
                 FROM residents r
                 JOIN users u ON r.user_id = u.id
                 ORDER BY u.name""")
    residents = c.fetchall()
    conn.close()

    return render_template('admin/payments.html', payments=payments, residents=residents)

# Admin generate maintenance bill
@app.route('/admin/payments/generate', methods=['POST'])
def admin_generate_bill():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Server-side validation
    resident_id = request.form.get('resident_id', '').strip()
    amount = request.form.get('amount', '').strip()
    due_date = request.form.get('due_date', '').strip()
    
    # Validate required fields
    if not resident_id or not amount or not due_date:
        return jsonify({'success': False, 'message': 'Resident, amount, and due date are required'})
    
    # Validate amount
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be a positive number'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Please enter a valid amount'})
    
    # Validate resident_id
    try:
        resident_id = int(resident_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid resident ID'})
    
    # Validate due date format (YYYY-MM-DD)
    from datetime import datetime
    try:
        datetime.strptime(due_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid due date format. Use YYYY-MM-DD'})
    
    # Get flat number for the resident
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("SELECT flat_number FROM residents WHERE id = %s", (resident_id,))
    resident = c.fetchone()
    
    if not resident:
        conn.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    flat_number = resident[0]
    
    try:
        # Insert maintenance bill (obligation)
        c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                  (resident_id, flat_number, amount, due_date, 'Unpaid'))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Maintenance bill generated successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to generate bill: ' + str(e)})


# Admin generate maintenance bill for specific resident
@app.route('/admin/maintenance-bills/generate', methods=['POST'])
def admin_generate_maintenance_bill():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Server-side validation
    resident_id = request.form.get('resident_id', '').strip()
    amount = request.form.get('amount', '').strip()
    due_date = request.form.get('due_date', '').strip()
    
    # Validate required fields
    if not resident_id or not amount or not due_date:
        return jsonify({'success': False, 'message': 'Resident, amount, and due date are required'})
    
    # Validate amount
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be a positive number'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Please enter a valid amount'})
    
    # Validate resident_id
    try:
        resident_id = int(resident_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid resident ID'})
    
    # Validate due date format (YYYY-MM-DD)
    from datetime import datetime
    try:
        datetime.strptime(due_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid due date format. Use YYYY-MM-DD'})
    
    # Get flat number for the resident
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("SELECT flat_number FROM residents WHERE id = %s", (resident_id,))
    resident = c.fetchone()
    
    if not resident:
        conn.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    flat_number = resident[0]
    
    try:
        # Insert maintenance bill
        c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                  (resident_id, flat_number, amount, due_date, 'Unpaid'))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Maintenance bill generated successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to generate bill: ' + str(e)})


# Admin generate monthly maintenance bills for all residents
@app.route('/admin/maintenance-bills/generate-monthly', methods=['POST'])
def admin_generate_monthly_bills():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Server-side validation
    amount = request.form.get('amount', '').strip()
    due_date = request.form.get('due_date', '').strip()
    
    if not amount or not due_date:
        return jsonify({'success': False, 'message': 'Amount and due date are required'})
    
    # Validate amount
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be a positive number'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Please enter a valid amount'})
    
    # Validate due date format (YYYY-MM-DD)
    from datetime import datetime
    try:
        datetime.strptime(due_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid due date format. Use YYYY-MM-DD'})
    
    # Get all residents
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("SELECT id, flat_number FROM residents")
    residents = c.fetchall()
    
    if not residents:
        conn.close()
        return jsonify({'success': False, 'message': 'No residents found'})
    
    success_count = 0
    try:
        for resident in residents:
            resident_id = resident[0]
            flat_number = resident[1]
            
            # Check if a bill already exists for this resident for this month
            from datetime import datetime
            current_month = datetime.now().strftime('%Y-%m')
            c.execute("SELECT id FROM maintenance_bills WHERE resident_id = %s AND substr(created_date, 1, 7) = %s", (resident_id, current_month))
            existing_bill = c.fetchone()
            
            if not existing_bill:
                # Insert maintenance bill for this resident
                c.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                          (resident_id, flat_number, amount, due_date, 'Unpaid'))
                success_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Monthly bills generated successfully for {success_count} residents'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to generate bills: ' + str(e)})


# Function to calculate late fine
from datetime import datetime, date

def calculate_late_fine(due_date_input, rate_per_day=50.0):
    """Calculate late fine based on days overdue"""
    try:
        if isinstance(due_date_input, str):
            due_date = datetime.strptime(due_date_input, '%Y-%m-%d').date()
        elif isinstance(due_date_input, (datetime, date)):
            due_date = due_date_input.date() if isinstance(due_date_input, datetime) else due_date_input
        else:
            return 0.0, 0

        today = date.today()

        if today > due_date:
            days_overdue = (today - due_date).days
            late_fine = days_overdue * rate_per_day
            return late_fine, days_overdue
        else:
            return 0.0, 0
    except (ValueError, AttributeError):
        return 0.0, 0


# Function to update late fines for all unpaid bills
def update_late_fines():
    """Update late fines for all unpaid bills"""
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    try:
        # Get all unpaid bills
        c.execute("SELECT id, due_date FROM maintenance_bills WHERE status = 'Unpaid'")
        unpaid_bills = c.fetchall()
        
        for bill in unpaid_bills:
            bill_id = bill[0]
            due_date = bill[1]
            
            late_fine, days_overdue = calculate_late_fine(due_date)
            
            # Update the late fine for this bill
            c.execute("UPDATE maintenance_bills SET late_fine = %s WHERE id = %s", (late_fine, bill_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f'Error updating late fines: {e}')
        return False


# Function to calculate days overdue
from datetime import datetime, date
def calculate_days_overdue(due_date_str):
    """Calculate number of days overdue"""
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = date.today()
        
        if today > due_date:
            days_overdue = (today - due_date).days
            return days_overdue
        else:
            return 0
    except ValueError:
        return 0


# Admin update maintenance bill status
@app.route('/admin/maintenance-bills/update-status', methods=['POST'])
def admin_update_bill_status():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    bill_id = request.form.get('bill_id', '').strip()
    status = request.form.get('status', '').strip()
    
    if not bill_id or not status:
        return jsonify({'success': False, 'message': 'Bill ID and status are required'})
    
    # Validate status
    if status not in ['Paid', 'Unpaid']:
        return jsonify({'success': False, 'message': 'Invalid status. Use Paid or Unpaid'})
    
    try:
        bill_id = int(bill_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid bill ID'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    try:
        # If marking as Paid, set late fine to 0
        if status == 'Paid':
            c.execute("UPDATE maintenance_bills SET status = %s, late_fine = 0 WHERE id = %s", (status, bill_id))
        else:
            # If marking as Unpaid, recalculate late fine
            c.execute("SELECT due_date FROM maintenance_bills WHERE id = %s", (bill_id,))
            result = c.fetchone()
            if result:
                due_date = result[0]
                late_fine, _ = calculate_late_fine(due_date)
                c.execute("UPDATE maintenance_bills SET status = %s, late_fine = %s WHERE id = %s", (status, late_fine, bill_id))
        
        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Bill not found'})
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Bill status updated to {status} successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to update bill status: ' + str(e)})

# Admin delete maintenance bill
@app.route('/admin/maintenance-bills/delete', methods=['POST'])
def admin_delete_bill():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    bill_id = request.form.get('bill_id', '').strip()
    
    if not bill_id:
        return jsonify({'success': False, 'message': 'Bill ID is required'})
    
    try:
        bill_id = int(bill_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid bill ID'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    try:
        c.execute("DELETE FROM maintenance_bills WHERE id = %s", (bill_id,))
        
        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Bill not found'})
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Bill deleted successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to delete bill: ' + str(e)})

# Admin mark payment as paid
@app.route('/admin/payments/mark-paid', methods=['POST'])
def admin_mark_paid():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    payment_id = request.form['payment_id']
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("UPDATE payments SET status = 'Paid', payment_date = CURRENT_DATE WHERE id = %s",
              (payment_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Payment marked as paid'})

# Admin download payment report (PDF)
@app.route('/admin/payments/report')
def admin_payments_report():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    # Import the report generation function
    from reports import generate_admin_payment_report_pdf
    
    # Generate PDF report
    pdf_buffer = generate_admin_payment_report_pdf()
    
    # Return PDF response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=admin_maintenance_payment_report.pdf'
    return response


# Admin download maintenance bills report (PDF)
@app.route('/admin/maintenance-bills/report')
def admin_maintenance_bills_report():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    # Import the report generation function
    from reports import generate_admin_maintenance_bills_report_pdf

    # Generate PDF report
    pdf_buffer = generate_admin_maintenance_bills_report_pdf()

    # Return PDF response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=admin_maintenance_bills_report.pdf'
    return response

# Admin comprehensive report (PDF)
@app.route('/admin/comprehensive-report')
def admin_comprehensive_report():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    # Import the report generation function
    from reports import generate_comprehensive_report_pdf

    # Generate comprehensive PDF report
    pdf_buffer = generate_comprehensive_report_pdf()

    # Return PDF response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=society_comprehensive_report.pdf'
    return response

# Resident maintenance report PDF (FIX for download button)
@app.route('/resident/maintenance/report')
def resident_maintenance_report():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return redirect(url_for('login'))

    from reports import generate_resident_payment_report_pdf
    pdf_buffer = generate_resident_payment_report_pdf(session['user_id'])

    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=payment_report.pdf'
    return response

# Individual payment receipt PDF (for per-payment download buttons)
@app.route('/resident/receipt/<payment_id>')
def resident_receipt(payment_id):
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.receipt_number, p.amount, p.payment_date, p.payment_method, p.status,
               u.name, r.flat_number
        FROM payments p 
        JOIN residents r ON p.resident_id = r.id 
        JOIN users u ON r.user_id = u.id 
        WHERE p.id = %s OR p.receipt_number = %s AND r.user_id = %s
    """, (payment_id, payment_id, session['user_id']))
    payment = c.fetchone()
    c.close()
    conn.close()
    
    if not payment:
        return "Receipt not found", 404
    
    # Get society settings
    society_settings = get_society_settings()
    
    receipt_data = {
        'id': payment[0],
        'receipt_number': payment[1] or f"REC-{payment_id}",
        'amount': payment[2],
        'payment_date': payment[3] or datetime.now().strftime('%Y-%m-%d'),
        'payment_method': payment[4] or 'Online',
        'status': payment[5],
        'name': payment[6],
        'flat_number': payment[7],
        'description': 'Maintenance Payment',
        # Society info
        'society_name': society_settings['society_name'],
        'society_address': society_settings['society_address'],
        'society_phone': society_settings['society_phone'],
        'society_email': society_settings['society_email']
    }
    
    from reports import generate_individual_receipt_pdf
    pdf_buffer = generate_individual_receipt_pdf(receipt_data)
    
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=receipt_{receipt_data["receipt_number"]}.pdf'
    return response

# Admin view payment receipt
@app.route('/admin/payments/receipt/<int:payment_id>')
def admin_view_receipt(payment_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""SELECT p.id, u.name, r.flat_number, p.amount, p.payment_date, p.payment_method, p.receipt_number, p.status 
                 FROM payments p 
                 JOIN residents r ON p.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 WHERE p.id = %s""", (payment_id,))
    payment = c.fetchone()
    conn.close()
    
    if not payment:
        return "Payment not found", 404
    
    # Get society settings
    society_settings = get_society_settings()
    
    # Create a dictionary for easier access in template
    receipt_data = {
        'id': payment[0],
        'name': payment[1],
        'flat_number': payment[2],
        'amount': payment[3],
        'payment_date': payment[4],
        'payment_method': payment[5],
        'receipt_number': payment[6],
        'status': payment[7],
        # Society information
        'society_name': society_settings['society_name'],
        'society_address': society_settings['society_address'],
        'society_phone': society_settings['society_phone'],
        'society_email': society_settings['society_email']
    }
    
    return render_template('admin/receipt.html', receipt=receipt_data)

# Admin settings
@app.route('/admin/settings')
def admin_settings():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    # Get current settings
    settings = get_society_settings()
    return render_template('admin/settings.html', settings=settings)

# Admin parking
@app.route('/admin/parking')
def admin_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""SELECT pk.slot_number, pk.slot_type, u.name, r.flat_number, pk.vehicle_number, pk.status 
                 FROM parking pk 
                 LEFT JOIN residents r ON pk.resident_id = r.id 
                 LEFT JOIN users u ON r.user_id = u.id 
                 ORDER BY pk.slot_number""")
    parking_slots = c.fetchall()
    c.close()

    # also fetch residents for the "Assign to" selector in the add modal
    c = conn.cursor()
    c.execute("""SELECT r.id, u.name, r.flat_number 
                 FROM residents r 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY r.flat_number""")
    residents = c.fetchall()
    c.close()
    conn.close()

    return render_template('admin/parking.html', parking_slots=parking_slots, residents=residents)


# Admin update settings
@app.route('/admin/settings/update', methods=['POST'])
def admin_update_settings():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Get form data
    society_name = request.form.get('society_name', '').strip()
    society_address = request.form.get('society_address', '').strip()
    society_phone = request.form.get('society_phone', '').strip()
    society_email = request.form.get('society_email', '').strip()
    
    # Validation
    if not society_name or not society_address:
        return jsonify({'success': False, 'message': 'Society name and address are required'})
    
    # Update settings
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO settings (id, society_name, society_address, society_phone, society_email) 
                  VALUES (1, %s, %s, %s, %s)""",
              (society_name, society_address, society_phone, society_email))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Settings updated successfully'})


# Admin add parking slot
@app.route('/admin/parking/add', methods=['POST'])
def admin_add_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    slot_number = request.form.get('slot_number', '').strip()
    slot_type = request.form.get('slot_type', '').strip()
    status = request.form.get('status', 'Available').strip()
    resident_id = request.form.get('resident_id', '').strip()
    flat_number = request.form.get('flat_number', '').strip()
    vehicle_number = request.form.get('vehicle_number', '').strip()

    if not slot_number or not slot_type:
        return jsonify({'success': False, 'message': 'Slot number and type are required'})

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    try:
        # determine resident_id if provided via resident_id or flat_number
        resolved_resident_id = None
        if resident_id:
            try:
                rid = int(resident_id)
                c.execute("SELECT id FROM residents WHERE id = %s", (rid,))
                if c.fetchone():
                    resolved_resident_id = rid
            except ValueError:
                resolved_resident_id = None

        if not resolved_resident_id and flat_number:
            c.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
            row = c.fetchone()
            if row:
                resolved_resident_id = row[0]

        # insert parking slot; resident_id may be NULL
        if resolved_resident_id:
            c.execute("INSERT INTO parking (resident_id, slot_number, slot_type, vehicle_number, status) VALUES (%s, %s, %s, %s, %s)",
                      (resolved_resident_id, slot_number, slot_type, vehicle_number.upper() if vehicle_number else None, status))
        else:
            c.execute("INSERT INTO parking (slot_number, slot_type, vehicle_number, status) VALUES (%s, %s, %s, %s)",
                      (slot_number, slot_type, vehicle_number.upper() if vehicle_number else None, status))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Parking slot added successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to add slot: ' + str(e)})


# Admin assign/unassign parking slot to resident
@app.route('/admin/parking/assign', methods=['POST'])
def admin_assign_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    slot_number = request.form.get('slot_number', '').strip()
    resident_id = request.form.get('resident_id', '').strip()

    if not slot_number or not resident_id:
        return jsonify({'success': False, 'message': 'Slot number and resident ID required'})

    try:
        resident_id = int(resident_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid resident ID'})

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    try:
        # find resident primary id
        c.execute("SELECT id FROM residents WHERE id = %s", (resident_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'})

        c.execute("UPDATE parking SET resident_id = %s, status = 'Occupied' WHERE slot_number = %s",
                  (resident_id, slot_number))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Slot assigned to resident'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to assign: ' + str(e)})


# Admin unassign parking slot
@app.route('/admin/parking/unassign', methods=['POST'])
def admin_unassign_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    slot_number = request.form.get('slot_number', '').strip()
    if not slot_number:
        return jsonify({'success': False, 'message': 'Slot number required'})

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    try:
        c.execute("UPDATE parking SET resident_id = NULL, vehicle_number = NULL, status = 'Available' WHERE slot_number = %s",
                  (slot_number,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Slot unassigned successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to unassign: ' + str(e)})


# Admin update parking vehicle or status
@app.route('/admin/parking/update', methods=['POST'])
def admin_update_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    slot_number = request.form.get('slot_number', '').strip()
    vehicle_number = request.form.get('vehicle_number', '').strip()
    status = request.form.get('status', '').strip()

    if not slot_number:
        return jsonify({'success': False, 'message': 'Slot number required'})

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    try:
        if vehicle_number and status:
            c.execute("UPDATE parking SET vehicle_number = %s, status = %s WHERE slot_number = %s",
                      (vehicle_number.upper(), status, slot_number))
        elif vehicle_number:
            c.execute("UPDATE parking SET vehicle_number = %s WHERE slot_number = %s",
                      (vehicle_number.upper(), slot_number))
        elif status:
            c.execute("UPDATE parking SET status = %s WHERE slot_number = %s",
                      (status, slot_number))
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'No update fields provided'})

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Slot updated successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to update: ' + str(e)})


# Admin edit parking slot (change slot number, type, resident, vehicle, status)
@app.route('/admin/parking/edit', methods=['POST'])
def admin_edit_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    slot_number = request.form.get('slot_number', '').strip()  # current identifier
    if not slot_number:
        return jsonify({'success': False, 'message': 'Current slot number is required'})

    new_slot_number = request.form.get('new_slot_number', '').strip()
    slot_type = request.form.get('slot_type', '').strip()
    status = request.form.get('status', '').strip()
    resident_id = request.form.get('resident_id', '').strip()
    flat_number = request.form.get('flat_number', '').strip()
    vehicle_number = request.form.get('vehicle_number', '').strip()
    unassign = request.form.get('unassign', '').strip()

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # verify slot exists
    c.execute("SELECT id FROM parking WHERE slot_number = %s", (slot_number,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Parking slot not found'})

    # resolve resident if provided
    resolved_resident_id = None
    if resident_id:
        try:
            rid = int(resident_id)
            c.execute("SELECT id FROM residents WHERE id = %s", (rid,))
            if c.fetchone():
                resolved_resident_id = rid
        except ValueError:
            resolved_resident_id = None

    if not resolved_resident_id and flat_number:
        c.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
        r = c.fetchone()
        if r:
            resolved_resident_id = r[0]

    try:
        set_parts = []
        params = []

        if new_slot_number:
            set_parts.append('slot_number = %s')
            params.append(new_slot_number)
        if slot_type:
            set_parts.append('slot_type = %s')
            params.append(slot_type)
        if vehicle_number:
            set_parts.append('vehicle_number = %s')
            params.append(vehicle_number.upper())
        if status:
            set_parts.append('status = %s')
            params.append(status)

        if unassign == '1':
            # explicit unassign request
            set_parts.append('resident_id = NULL')
            set_parts.append('vehicle_number = NULL')
            set_parts.append("status = 'Available'")
        elif resolved_resident_id:
            set_parts.append('resident_id = %s')
            params.append(resolved_resident_id)

        if not set_parts:
            conn.close()
            return jsonify({'success': False, 'message': 'No fields to update'})

        sql = f"UPDATE parking SET {', '.join(set_parts)} WHERE slot_number = %s"
        params.append(slot_number)
        c.execute(sql, tuple(params))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Parking slot updated successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to edit slot: ' + str(e)})


# Admin delete parking slot
@app.route('/admin/parking/delete', methods=['POST'])
def admin_delete_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    slot_number = request.form.get('slot_number', '').strip()
    if not slot_number:
        return jsonify({'success': False, 'message': 'Slot number is required'})

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM parking WHERE slot_number = %s", (slot_number,))
        if not c.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Parking slot not found'})

        c.execute("DELETE FROM parking WHERE slot_number = %s", (slot_number,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Parking slot deleted successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to delete slot: ' + str(e)})

# Admin charity
@app.route('/admin/charity')
def admin_charity():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("""SELECT ch.id, u.name, r.flat_number, ch.item_type, ch.quantity, ch.description, ch.status, ch.pickup_date 
                 FROM charity ch 
                 JOIN residents r ON ch.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY ch.pickup_date DESC""")
    charity_donations = c.fetchall()
    conn.close()
    
    return render_template('admin/charity.html', charity_donations=charity_donations)

# Admin approve charity donation
@app.route('/admin/charity/approve', methods=['POST'])
def admin_approve_charity():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    donation_id = request.form['donation_id']
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("UPDATE charity SET status = 'Approved' WHERE id = %s",
              (donation_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Donation approved successfully'})

# Admin mark charity donation as picked
@app.route('/admin/charity/pick', methods=['POST'])
def admin_pick_charity():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    donation_id = request.form['donation_id']
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("UPDATE charity SET status = 'Picked', pickup_date = CURRENT_DATE WHERE id = %s",
              (donation_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Donation marked as collected successfully'})

# Admin notices
@app.route('/admin/notices')
def admin_notices():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("SELECT * FROM notices ORDER BY notice_date DESC")
    notices = c.fetchall()
    conn.close()
    
    return render_template('admin/notices.html', notices=notices)

# Admin delete notice
@app.route('/admin/notices/delete', methods=['POST'])
def admin_delete_notice():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    notice_id = request.form['notice_id']
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("DELETE FROM notices WHERE id = %s", (notice_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Notice deleted successfully'})

# Admin edit notice
@app.route('/admin/notices/edit', methods=['POST'])
def admin_edit_notice():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Server-side validation
    notice_id = request.form.get('notice_id', '').strip()
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'Normal')
    
    # Validate required fields
    if not notice_id or not title or not content:
        return jsonify({'success': False, 'message': 'Notice ID, title and content are required'})
    
    # Validate title length
    if len(title) < 5:
        return jsonify({'success': False, 'message': 'Title must be at least 5 characters long'})
    
    # Validate content length
    if len(content) < 10:
        return jsonify({'success': False, 'message': 'Content must be at least 10 characters long'})
    
    # Validate priority
    if priority not in ['Normal', 'High', 'Urgent']:
        priority = 'Normal'
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("UPDATE notices SET title = %s, content = %s, priority = %s WHERE id = %s",
              (title, content, priority, notice_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Notice updated successfully'})

# Admin add notice
@app.route('/admin/notices/add', methods=['POST'])
def admin_add_notice():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Server-side validation
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'Normal')
    
    # Validate required fields
    if not title or not content:
        return jsonify({'success': False, 'message': 'Title and content are required'})
    
    # Validate title length
    if len(title) < 5:
        return jsonify({'success': False, 'message': 'Title must be at least 5 characters long'})
    
    # Validate content length
    if len(content) < 10:
        return jsonify({'success': False, 'message': 'Content must be at least 10 characters long'})
    
    # Validate priority
    if priority not in ['Normal', 'High', 'Urgent']:
        priority = 'Normal'
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    c.execute("INSERT INTO notices (admin_id, title, content, priority) VALUES (%s, %s, %s, %s)",
              (session['user_id'], title, content, priority))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Notice added successfully'})

# Admin reports
@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get daily visitor counts
    c.execute("""SELECT visit_date, COUNT(*) as visitor_count 
                 FROM visitors 
                 GROUP BY visit_date 
                 ORDER BY visit_date ASC 
                 LIMIT 30""")
    visitor_data = c.fetchall()
    c.close()
    
    # Get daily complaint counts
    c = conn.cursor()
    c.execute("""SELECT complaint_date, COUNT(*) as complaint_count 
                 FROM complaints 
                 GROUP BY complaint_date 
                 ORDER BY complaint_date ASC 
                 LIMIT 30""")
    complaint_data = c.fetchall()
    c.close()
    
    # Get daily delivery counts
    c = conn.cursor()
    c.execute("""SELECT DATE(arrival_time) as delivery_date, COUNT(*) as delivery_count 
                 FROM deliveries 
                 GROUP BY DATE(arrival_time) 
                 ORDER BY delivery_date ASC 
                 LIMIT 30""")
    delivery_data = c.fetchall()
    c.close()
    
    # Get monthly maintenance collection
    c = conn.cursor()
    c.execute("""SELECT DATE_FORMAT(payment_date, '%Y-%m') as payment_month, SUM(amount) as total_amount
                 FROM payments
                 WHERE status = 'Paid'
                 GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
                 ORDER BY payment_month ASC
                 LIMIT 12""")
    payment_data = c.fetchall()
    c.close()
    
    # Get per-resident totals (useful for per-resident charts)
    c = conn.cursor()
    c.execute("""SELECT r.id, u.name, r.flat_number, COALESCE(SUM(p.amount), 0) as total_paid
                 FROM residents r
                 JOIN users u ON r.user_id = u.id
                 LEFT JOIN payments p ON p.resident_id = r.id AND p.status = 'Paid'
                 GROUP BY r.id, u.name, r.flat_number
                 ORDER BY total_paid DESC
                 LIMIT 50""")
    payment_by_resident = c.fetchall()
    c.close()

    # Get payment status distribution for pie chart
    c = conn.cursor()
    c.execute("""SELECT status, COUNT(*) as count
                 FROM payments
                 GROUP BY status
                 ORDER BY status""")
    payment_status_data = c.fetchall()
    c.close()

    # Get complaint status distribution for pie chart
    c = conn.cursor()
    c.execute("""SELECT status, COUNT(*) as count
                 FROM complaints
                 GROUP BY status
                 ORDER BY status""")
    complaint_status_data = c.fetchall()

    conn.close()

    return render_template('admin/reports.html',
                          visitor_data=visitor_data,
                          complaint_data=complaint_data,
                          delivery_data=delivery_data,
                          payment_data=payment_data,
                          payment_by_resident=payment_by_resident,
                          payment_status_data=payment_status_data,
                          complaint_status_data=complaint_status_data)


@app.route('/admin/reports/resident/<int:resident_id>')
def admin_reports_resident(resident_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get totals per day for the last 30 days for this resident
    c.execute("""SELECT DATE(payment_date) as day, COALESCE(SUM(amount),0) as total
                 FROM payments
                 WHERE resident_id = %s AND status = 'Paid' AND DATE(payment_date) >= DATE('now', '-29 days')
                 GROUP BY day
                 ORDER BY day ASC""", (resident_id,))
    rows = c.fetchall()
    conn.close()

    # Build lookup and zero-fill the last 30 days
    totals_by_day = {r[0]: r[1] for r in rows}
    from datetime import date, timedelta
    result = []
    today = date.today()
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        key = d.strftime('%Y-%m-%d')
        result.append([key, float(totals_by_day.get(key, 0))])

    return jsonify(result)

# Admin add resident
@app.route('/admin/residents/add', methods=['POST'])
def admin_add_resident():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Server-side validation
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    flat_number = request.form.get('flat_number', '').strip()
    resident_type = request.form.get('resident_type', '').strip()
    password = request.form.get('password', '').strip()
    
    # Validate required fields
    if not all([name, email, flat_number, resident_type, password]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate email format
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address'})
    
    # Validate phone (should be 10 digits)
    phone_digits = ''.join(filter(str.isdigit, phone))
    if len(phone_digits) != 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit phone number'})
    
    # Validate resident type
    if resident_type not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Invalid resident type'})
    
    # Validate password length
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Check if email already exists
    c.execute("SELECT id FROM users WHERE email = %s", (email,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'A user with this email already exists'})
    
    # Check if flat number already exists
    c.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'A resident with this flat number already exists'})
    
    try:
        # Insert user
        c.execute("INSERT INTO users (name, email, password, role, phone) VALUES (%s, %s, %s, %s, %s)",
                  (name, email, password, resident_type, phone_digits))
        user_id = c.lastrowid
        
        # Insert resident
        c.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                  (user_id, flat_number, resident_type, datetime.now().strftime('%Y-%m-%d')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Resident added successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to add resident: ' + str(e)})

# Admin edit resident
@app.route('/admin/residents/edit', methods=['POST'])
def admin_edit_resident():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Server-side validation
    user_id = request.form.get('user_id', '').strip()
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    flat_number = request.form.get('flat_number', '').strip()
    resident_type = request.form.get('resident_type', '').strip()
    
    # Validate required fields
    if not all([user_id, name, email, flat_number, resident_type]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid user ID'})
    
    # Validate email format
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address'})
    
    # Phone is optional for update - only validate if provided
    phone_digits = ''
    if phone:
        phone_digits = ''.join(filter(str.isdigit, phone))
        if phone_digits and len(phone_digits) != 10:
            return jsonify({'success': False, 'message': 'Please enter a valid 10-digit phone number or leave empty'})
    
    # Validate resident type
    if resident_type not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Invalid resident type'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Check if email already exists for another user
    c.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
    if c.fetchone():
        c.close()
        conn.close()
        return jsonify({'success': False, 'message': 'A user with this email already exists'})
    
    # Check if flat number already exists for another resident
    c.close()
    c = conn.cursor()
    c.execute("SELECT r.id FROM residents r JOIN users u ON r.user_id = u.id WHERE r.flat_number = %s AND u.id != %s", 
              (flat_number, user_id))
    if c.fetchone():
        c.close()
        conn.close()
        return jsonify({'success': False, 'message': 'A resident with this flat number already exists'})
    
    try:
        # Update user - keep existing phone if not provided
        if phone_digits:
            c.execute("UPDATE users SET name = %s, email = %s, role = %s, phone = %s WHERE id = %s",
                      (name, email, resident_type, phone_digits, user_id))
        else:
            c.execute("UPDATE users SET name = %s, email = %s, role = %s WHERE id = %s",
                      (name, email, resident_type, user_id))
        
        # Update resident
        c.execute("UPDATE residents SET flat_number = %s, resident_type = %s WHERE user_id = %s",
                  (flat_number, resident_type, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Resident updated successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to update resident: ' + str(e)})

# Admin delete resident
@app.route('/admin/residents/delete', methods=['POST'])
def admin_delete_resident():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    user_id = request.form.get('user_id', '').strip()

    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'})

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid user ID'})

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    try:
        # Delete resident first (due to foreign key constraint)
        c.execute("DELETE FROM residents WHERE user_id = %s", (user_id,))
        c.close()

        # Delete user
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = %s", (user_id,))
        c.close()

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Resident deleted successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to delete resident: ' + str(e)})


@app.route('/emergency')
def emergency():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get emergency contacts
    c.execute("SELECT name, contact_type, phone_number FROM emergency_contacts WHERE is_active = TRUE ORDER BY priority ASC")
    emergency_contacts = c.fetchall()

    conn.close()

    return render_template('emergency.html', emergency_contacts=emergency_contacts)


# Emergency Log
@app.route('/emergency_log')
def emergency_log():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('emergency_log.html')


# Events
@app.route('/events')
def events():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor(cursor_class=mysql.connector.cursor.MySQLCursorDict)
    c.execute("SELECT id, title, event_type, event_date, event_time, venue, description, image, created_at FROM events ORDER BY event_date DESC")
    events = c.fetchall()
    conn.close()
    
    return render_template('events.html', events=events)


# Admin Events
@app.route('/admin/events')
def admin_events():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor(cursor_class=mysql.connector.cursor.MySQLCursorDict)
    c.execute("SELECT id, title, event_type, event_date, event_time, venue, description, image, created_at FROM events ORDER BY event_date DESC")
    events = c.fetchall()
    conn.close()
    
    return render_template('admin/events.html', events=events)


# Admin Add Event
@app.route('/admin/add_event')
def admin_add_event():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    return render_template('admin/add_event.html')


# Admin Save Event (POST - create new event)
@app.route('/admin/events/add', methods=['POST'])
def admin_save_event():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized access'})
    
    try:
        title = request.form.get('title', '').strip()
        event_type = request.form.get('event_type', '').strip()
        date = request.form.get('date', '').strip()
        time = request.form.get('time', '').strip()
        venue = request.form.get('venue', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate required fields
        if not title or not event_type or not date or not time or not venue or not description:
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                # Validate file type
                allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
                ext = os.path.splitext(file.filename)[1].lower()
                if ext in allowed_extensions:
                    # Generate unique filename
                    unique_filename = str(uuid.uuid4()) + ext
                    filepath = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(filepath)
                    image_path = f'/static/images/events/{unique_filename}'
                else:
                    return jsonify({'success': False, 'message': 'Invalid file type. Only JPG, PNG, and GIF files are allowed.'})
        
        conn = get_db()
        c = conn.cursor()
        
        # Insert new event
        c.execute("""INSERT INTO events (title, event_type, event_date, event_time, venue, description, image) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                  (title, event_type, date, time, venue, description, image_path))
        
        conn.commit()
        event_id = c.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Event added successfully', 'event_id': event_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding event: {str(e)}'})


# Admin Edit Event
@app.route('/admin/edit_event/<int:event_id>', methods=['POST'])
def admin_update_event(event_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized access'})
    
    try:
        title = request.form['title']
        event_type = request.form['event_type']
        date = request.form['date']
        time = request.form['time']
        venue = request.form['venue']
        description = request.form['description']
        
        conn = get_db()
        c = conn.cursor(cursor_class=mysql.connector.cursor.MySQLCursorDict)
        
        # Update event
        c.execute("""UPDATE events 
                     SET title = %s, event_type = %s, event_date = %s, event_time = %s, 
                         venue = %s, description = %s 
                     WHERE id = %s""",
                  (title, event_type, date, time, venue, description, event_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Event updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating event: {str(e)}'})


@app.route('/admin/edit_event/<int:event_id>')
def admin_edit_event(event_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor(cursor_class=mysql.connector.cursor.MySQLCursorDict)
    c.execute("SELECT id, title, event_type, event_date, event_time, venue, description, image FROM events WHERE id = %s", (event_id,))
    event = c.fetchone()
    conn.close()
    
    if not event:
        return redirect(url_for('admin_events'))
    
    return render_template('admin/edit_event.html', event=event)


# Resident Visitors
@app.route('/resident/visitors')
def resident_visitors():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident's flat number
    c.execute("SELECT flat_number FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    flat_number = resident[0] if resident else None
    c.close()
    
    # Get visitor entries for this flat
    visitors = []
    if flat_number:
        c = conn.cursor()
        c.execute("""SELECT id, visitor_name, mobile_number, purpose, DATE(entry_time) as visit_date, 
                     TIME(entry_time) as visit_time, status 
                     FROM visitor_entries 
                     WHERE flat_number = %s 
                     ORDER BY entry_time DESC""", (flat_number,))
        visitors = c.fetchall()
        c.close()
    
    conn.close()
    
    return render_template('resident/visitors.html', visitors=visitors)


# Add Resident Visitor
@app.route('/resident/visitors/add', methods=['POST'])
def add_resident_visitor():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    visitor_name = request.form.get('visitor_name', '').strip()
    contact = request.form.get('contact', '').strip()
    purpose = request.form.get('purpose', '').strip()
    
    if not all([visitor_name, contact, purpose]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate phone number (10 digits)
    phone_digits = ''.join(filter(str.isdigit, contact))
    if len(phone_digits) != 10:
        return jsonify({'success': False, 'message': 'Invalid phone number'})
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    try:
        # Get resident's flat number
        c.execute("SELECT flat_number FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        flat_number = resident[0] if resident else None
        c.close()
        
        if not flat_number:
            conn.close()
            return jsonify({'success': False, 'message': 'Could not find flat number'})
        
        # Insert visitor entry
        c = conn.cursor()
        c.execute("""INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status)
                     VALUES (%s, %s, %s, %s, %s)""",
                  (visitor_name, phone_digits, purpose, flat_number, 'In'))
        c.close()
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Visitor registered successfully'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to register visitor: ' + str(e)})


# Resident Deliveries
@app.route('/resident/deliveries')
def resident_deliveries():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None
    
    # Get deliveries for this resident
    deliveries = []
    if resident_id:
        c.execute("""SELECT id, delivery_company, delivery_item, 
                     DATE(arrival_time) as delivery_date, TIME(arrival_time) as arrival_time,
                     status, collected_time FROM deliveries 
                     WHERE resident_id = %s ORDER BY arrival_time DESC""", (resident_id,))
        deliveries = c.fetchall()
    
    conn.close()
    return render_template('resident/deliveries.html', deliveries=deliveries)


# Resident Deliveries Request
@app.route('/resident/deliveries/request', methods=['POST'])
def resident_deliveries_request():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        delivery_company = request.form.get('delivery_company', '')
        delivery_item = request.form.get('delivery_item', '')
        expected_time = request.form.get('expected_time', '')
        
        if not delivery_company or not delivery_item:
            return jsonify({'success': False, 'message': 'Company and item are required'}), 400
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        
        if not resident:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        resident_id = resident[0]
        
        # Insert delivery request
        c.execute("""INSERT INTO deliveries (resident_id, delivery_company, delivery_item, status) 
                     VALUES (%s, %s, %s, 'Pending')""", 
                  (resident_id, delivery_company, delivery_item))
        conn.commit()
        c.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Delivery request submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Resident Parking
@app.route('/resident/parking')
def resident_parking():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None
    
    # Get parking slots for this resident
    parking_slots = []
    if resident_id:
        c.execute("""SELECT id, slot_number, slot_type, vehicle_number, status 
                     FROM parking WHERE resident_id = %s""", (resident_id,))
        parking_slots = c.fetchall()
    
    conn.close()
    return render_template('resident/parking.html', parking_slots=parking_slots)


# Resident Complaints
@app.route('/resident/complaints')
def resident_complaints():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None
    
    # Get complaints for this resident
    complaints = []
    if resident_id:
        c.execute("""SELECT id, category, description, DATE(complaint_date) as complaint_date,
                     status, priority, COALESCE(ai_score, 0) as ai_score FROM complaints 
                     WHERE resident_id = %s ORDER BY complaint_date DESC""", (resident_id,))
        complaints = c.fetchall()
    
    c.close()
    conn.close()
    return render_template('resident/complaints.html', complaints=complaints)


# Resident Complaints Submit
@app.route('/resident/complaints/submit', methods=['POST'])
def resident_complaints_submit():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        
        if not category or not description:
            return jsonify({'success': False, 'message': 'Category and description are required'}), 400
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        
        if not resident:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        resident_id = resident[0]
        
        # Insert complaint
        c.execute("""INSERT INTO complaints (resident_id, category, description, status, priority) 
                     VALUES (%s, %s, %s, 'Open', 'Normal')""", 
                  (resident_id, category, description))
        conn.commit()
        c.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Complaint submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Resident Maintenance
@app.route('/resident/maintenance')
def resident_maintenance():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None

    # Get current unpaid maintenance bill (total of all unpaid bills)
    current_bill = 0
    unpaid_bills = []
    payment_history = []
    if resident_id:
        # Get all unpaid bills
        c.execute("""SELECT id, amount, due_date, status, created_date
                     FROM maintenance_bills
                     WHERE resident_id = %s AND status = 'Unpaid'
                     ORDER BY due_date DESC""", (resident_id,))
        unpaid_bills = c.fetchall()

        # Calculate total current bill
        current_bill = sum(bill[1] for bill in unpaid_bills) if unpaid_bills else 0

        # Get paid bills for history
        c.close()
        c = conn.cursor()
        c.execute("""SELECT id, amount, due_date, 'Paid' as status, created_date, 'Bill' as type
                     FROM maintenance_bills
                     WHERE resident_id = %s AND status = 'Paid'
                     ORDER BY due_date DESC""", (resident_id,))
        paid_bills = c.fetchall()

        # Get payment history
        c.close()
        c = conn.cursor()
        c.execute("""SELECT id, amount, payment_date, payment_method, receipt_number, status, 'Payment' as type
                     FROM payments
                     WHERE resident_id = %s ORDER BY payment_date DESC""", (resident_id,))
        payments = c.fetchall()

        # Combine paid bills and payments for history
        payment_history = []
        for bill in paid_bills:
            payment_history.append((bill[0], bill[1], bill[2], 'N/A', 'Paid', 'Bill'))
        for payment in payments:
            payment_history.append((payment[4], payment[1], payment[2], payment[3], payment[5], 'Payment'))
        # Sort by date (position 2)
        payment_history.sort(key=lambda x: str(x[2]), reverse=True)

    c.close()
    conn.close()
    return render_template('resident/maintenance.html',
                         current_bill=current_bill,
                         unpaid_bills=unpaid_bills,
                         payment_history=payment_history)


# Resident Maintenance Pay Current Bill
@app.route('/resident/maintenance/pay', methods=['POST'])
def resident_maintenance_pay():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        payment_method = request.form.get('payment_method', 'Online')

        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        resident_id = resident[0] if resident else None

        if not resident_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404

        # Get all unpaid bills for this resident
        c.execute("""SELECT id, amount FROM maintenance_bills
                     WHERE resident_id = %s AND status = 'Unpaid'""", (resident_id,))
        unpaid_bills = c.fetchall()

        if not unpaid_bills:
            conn.close()
            return jsonify({'success': False, 'message': 'No unpaid bills found'}), 400

        # Calculate total amount
        total_amount = sum(bill[1] for bill in unpaid_bills)

        # Generate receipt number
        import uuid
        receipt_number = f"REC-{uuid.uuid4().hex[:8].upper()}"

        # Insert payment record
        c.execute("""INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status)
                     VALUES (%s, %s, CURDATE(), %s, %s, 'Paid')""",
                  (resident_id, total_amount, payment_method, receipt_number))

        # Mark all unpaid bills as paid
        bill_ids = [bill[0] for bill in unpaid_bills]
        if bill_ids:
            placeholders = ','.join(['%s'] * len(bill_ids))
            c.execute(f"UPDATE maintenance_bills SET status = 'Paid' WHERE id IN ({placeholders})", bill_ids)

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'Payment of ₹{total_amount:.2f} successful. Receipt: {receipt_number}'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Payment failed: {str(e)}'}), 500


# Resident Maintenance Pay Pending Bill
@app.route('/resident/maintenance/pay_pending', methods=['POST'])
def resident_maintenance_pay_pending():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        bill_id = request.form.get('bill_id', '').strip()
        payment_method = request.form.get('payment_method', 'Online')

        if not bill_id:
            return jsonify({'success': False, 'message': 'Bill ID is required'}), 400

        try:
            bill_id = int(bill_id)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid bill ID'}), 400

        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        resident_id = resident[0] if resident else None

        if not resident_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404

        # Verify the bill belongs to this resident and is unpaid
        c.execute("""SELECT amount FROM maintenance_bills
                     WHERE id = %s AND resident_id = %s AND status = 'Unpaid'""", (bill_id, resident_id))
        bill = c.fetchone()

        if not bill:
            conn.close()
            return jsonify({'success': False, 'message': 'Bill not found or already paid'}), 404

        amount = bill[0]

        # Generate receipt number
        import uuid
        receipt_number = f"REC-{uuid.uuid4().hex[:8].upper()}"

        # Insert payment record
        c.execute("""INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status)
                     VALUES (%s, %s, CURDATE(), %s, %s, 'Paid')""",
                  (resident_id, amount, payment_method, receipt_number))

        # Mark the bill as paid
        c.execute("UPDATE maintenance_bills SET status = 'Paid' WHERE id = %s", (bill_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'Payment of ₹{amount:.2f} successful. Receipt: {receipt_number}'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Payment failed: {str(e)}'}), 500


# Resident Notices
@app.route('/resident/notices')
def resident_notices():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get all notices
    c.execute("""SELECT id, title, content, DATE(notice_date) as notice_date, priority 
                 FROM notices ORDER BY notice_date DESC""")
    notices = c.fetchall()
    
    conn.close()
    return render_template('resident/notices.html', notices=notices)


# Resident Charity
@app.route('/resident/charity')
def resident_charity():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None
    
    # Get donation history
    donations = []
    total_items = 0
    if resident_id:
        c.execute("""SELECT id, item_type, description, quantity, pickup_date, status 
                     FROM charity 
                     WHERE resident_id = %s ORDER BY pickup_date DESC""", (resident_id,))
        donations = c.fetchall()
        c.close()
        
        # Use new cursor for second query
        c = conn.cursor()
        c.execute("""SELECT COALESCE(COUNT(*), 0) FROM charity 
                     WHERE resident_id = %s AND status = 'Completed'""", (resident_id,))
        total_result = c.fetchone()
        total_items = total_result[0] if total_result else 0
    
    c.close()
    conn.close()
    return render_template('resident/charity.html', 
                         donations=donations, 
                         total_items=total_items)


# Resident Charity Submit
@app.route('/resident/charity/submit', methods=['POST'])
def resident_charity_submit():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        item_type = request.form.get('item_type', '')
        quantity = request.form.get('quantity', 1)
        description = request.form.get('description', '')
        
        if not item_type:
            return jsonify({'success': False, 'message': 'Item type is required'}), 400
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        
        if not resident:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        resident_id = resident[0]
        
        # Insert charity donation
        c.execute("""INSERT INTO charity (resident_id, item_type, quantity, description, status) 
                     VALUES (%s, %s, %s, %s, 'Pending')""", 
                  (resident_id, item_type, quantity, description))
        conn.commit()
        c.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Charity donation submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Tenant Visitors
@app.route('/tenant/visitors')
def tenant_visitors():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get tenant's flat number
    c.execute("SELECT flat_number FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    flat_number = resident[0] if resident else None
    c.close()
    
    # Get visitor entries for this flat
    visitors = []
    if flat_number:
        c = conn.cursor()
        c.execute("""SELECT id, visitor_name, mobile_number, purpose, DATE(entry_time) as visit_date, 
                     TIME(entry_time) as visit_time, status 
                     FROM visitor_entries 
                     WHERE flat_number = %s 
                     ORDER BY entry_time DESC""", (flat_number,))
        visitors = c.fetchall()
        c.close()
    
    conn.close()
    
    return render_template('tenant/visitors.html', visitors=visitors)


# Tenant Visitors Add
@app.route('/tenant/visitors/add', methods=['POST'])
def tenant_visitors_add():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        visitor_name = data.get('visitor_name', '')
        contact = data.get('contact', '')
        purpose = data.get('purpose', '')
        
        if not visitor_name or not contact or not purpose:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident info (tenant's flat number and ID)
        c.execute("SELECT flat_number, id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        
        if not resident:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        flat_number, resident_id = resident[0], resident[1]
        
        # Insert visitor entry - use visitor_entries table (used by security)
        c.execute("""INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, status) 
                     VALUES (%s, %s, %s, %s, 'In')""", 
                  (visitor_name, contact, purpose, flat_number))
        conn.commit()
        c.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Visitor registered successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Tenant Deliveries
@app.route('/tenant/deliveries')
def tenant_deliveries():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None
    
    # Get deliveries for this resident
    deliveries = []
    if resident_id:
        c.execute("""SELECT id, delivery_company, delivery_item, 
                     DATE(arrival_time) as delivery_date, TIME(arrival_time) as arrival_time,
                     status, collected_time FROM deliveries 
                     WHERE resident_id = %s ORDER BY arrival_time DESC""", (resident_id,))
        deliveries = c.fetchall()
    
    conn.close()
    return render_template('tenant/deliveries.html', deliveries=deliveries)


# Tenant Deliveries Request
@app.route('/tenant/deliveries/request', methods=['POST'])
def tenant_deliveries_request():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        delivery_company = request.form.get('delivery_company', '')
        delivery_item = request.form.get('delivery_item', '')
        expected_time = request.form.get('expected_time', '')
        
        if not delivery_company or not delivery_item:
            return jsonify({'success': False, 'message': 'Company and item are required'}), 400
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        
        if not resident:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        resident_id = resident[0]
        
        # Insert delivery request
        c.execute("""INSERT INTO deliveries (resident_id, delivery_company, delivery_item, status) 
                     VALUES (%s, %s, %s, 'Pending')""", 
                  (resident_id, delivery_company, delivery_item))
        conn.commit()
        c.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Delivery request submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Tenant Parking
@app.route('/tenant/parking')
def tenant_parking():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None
    
    # Get assigned parking slot for this resident
    parking = None
    if resident_id:
        c.execute("""SELECT id, resident_id, slot_number, slot_type, vehicle_number, status 
                     FROM parking WHERE resident_id = %s""", (resident_id,))
        parking = c.fetchone()
    
    # Get vehicle history for this tenant
    vehicle_history = []
    if resident_id:
        try:
            c.execute("""SELECT vehicle_number, vehicle_type, registration_date, status
                         FROM vehicles WHERE resident_id = %s ORDER BY registration_date DESC""", (resident_id,))
            vehicle_history = c.fetchall()
        except mysql.connector.errors.ProgrammingError:
            vehicle_history = []  # Table doesn't exist yet
    
    # Get all available parking slots
    parking_slots = []
    c.execute("""SELECT id, slot_number, slot_type, status FROM parking WHERE status = 'Available'""")
    parking_slots = c.fetchall()
    
    conn.close()
    return render_template('tenant/parking.html', parking=parking, vehicle_history=vehicle_history, parking_slots=parking_slots)


# Tenant Register Vehicle
@app.route('/tenant/parking/register', methods=['POST'])
def tenant_register_vehicle():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        vehicle_number = request.form.get('vehicle_number', '').strip().upper()
        vehicle_type = request.form.get('vehicle_type', '').strip()
        
        if not vehicle_number or not vehicle_type:
            return jsonify({'success': False, 'message': 'Vehicle number and type are required'}), 400
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        
        if not resident:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        resident_id = resident[0]
        
        # Check if vehicle already registered
        c.execute("SELECT id FROM vehicles WHERE vehicle_number = %s", (vehicle_number,))
        if c.fetchone():
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'This vehicle is already registered'}), 400
        
        # Insert vehicle
        c.execute("""INSERT INTO vehicles (resident_id, vehicle_number, vehicle_type, status) 
                     VALUES (%s, %s, %s, 'Registered')""", 
                  (resident_id, vehicle_number, vehicle_type))
        conn.commit()
        c.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Vehicle registered successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Tenant Complaints
@app.route('/tenant/complaints')
def tenant_complaints():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None

    # Get complaints for this resident
    complaints = []
    if resident_id:
        c.execute("""SELECT id, category, description, DATE(complaint_date) as complaint_date,
                     status, priority FROM complaints
                     WHERE resident_id = %s ORDER BY complaint_date DESC""", (resident_id,))
        complaints = c.fetchall()

    c.close()
    conn.close()
    return render_template('tenant/complaints.html', complaints=complaints)


# Tenant Complaints Submit
@app.route('/tenant/complaints/submit', methods=['POST'])
def tenant_complaints_submit():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        
        if not category or not description:
            return jsonify({'success': False, 'message': 'Category and description are required'}), 400
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        
        if not resident:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        resident_id = resident[0]
        
        # Insert complaint
        c.execute("""INSERT INTO complaints (resident_id, category, description, status, priority) 
                     VALUES (%s, %s, %s, 'Open', 'Normal')""", 
                  (resident_id, category, description))
        conn.commit()
        c.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Complaint submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Tenant Maintenance
@app.route('/tenant/maintenance')
def tenant_maintenance():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None
    
    # Get current month's maintenance bill
    current_bill = None
    maintenance_history = []
    if resident_id:
        c.execute("""SELECT id, amount, due_date, status, created_date 
                     FROM maintenance_bills 
                     WHERE resident_id = %s AND YEAR(due_date) = YEAR(CURDATE()) 
                     AND MONTH(due_date) = MONTH(CURDATE())""", (resident_id,))
        result = c.fetchall()
        # Extract amount (column 1) from the tuple
        current_bill = result[0][1] if result else None
        
        # Get maintenance history - use new cursor to avoid "Unread result found"
        c.close()
        c = conn.cursor()
        c.execute("""SELECT id, amount, due_date, status, created_date 
                     FROM maintenance_bills 
                     WHERE resident_id = %s ORDER BY due_date DESC LIMIT 12""", (resident_id,))
        maintenance_history = c.fetchall()
    
    c.close()
    conn.close()
    return render_template('tenant/maintenance.html', 
                         current_bill=current_bill, 
                         maintenance_history=maintenance_history)


# Tenant Notices
@app.route('/tenant/notices')
def tenant_notices():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get all notices
    c.execute("""SELECT id, title, content, DATE(notice_date) as notice_date, priority 
                 FROM notices ORDER BY notice_date DESC""")
    notices = c.fetchall()
    
    conn.close()
    return render_template('tenant/notices.html', notices=notices)


# Tenant Charity
@app.route('/tenant/charity')
def tenant_charity():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    resident_id = resident[0] if resident else None
    
    # Get donation history
    donations = []
    total_items = 0
    if resident_id:
        c.execute("""SELECT id, item_type, description, quantity, pickup_date, status 
                     FROM charity 
                     WHERE resident_id = %s ORDER BY pickup_date DESC""", (resident_id,))
        donations = c.fetchall()
        c.close()
        
        # Use new cursor for second query
        c = conn.cursor()
        c.execute("""SELECT COALESCE(COUNT(*), 0) FROM charity 
                     WHERE resident_id = %s AND status = 'Completed'""", (resident_id,))
        total_result = c.fetchone()
        total_items = total_result[0] if total_result else 0
    
    c.close()
    conn.close()
    return render_template('tenant/charity.html', 
                         donations=donations, 
                         total_items=total_items)


# Tenant Charity Submit
@app.route('/tenant/charity/submit', methods=['POST'])
def tenant_charity_submit():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        item_type = request.form.get('item_type', '')
        quantity = request.form.get('quantity', 1)
        description = request.form.get('description', '')
        condition = request.form.get('condition', '')
        
        if not item_type:
            return jsonify({'success': False, 'message': 'Item type is required'}), 400
        
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        
        if not resident:
            c.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        resident_id = resident[0]
        
        # Insert charity donation - append condition to description if provided
        full_description = f"{description} (Condition: {condition})" if condition else description
        c.execute("""INSERT INTO charity (resident_id, item_type, quantity, description, status) 
                     VALUES (%s, %s, %s, %s, 'Pending')""", 
                  (resident_id, item_type, quantity, full_description))
        conn.commit()
        c.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Charity donation submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Tenant Emergency
@app.route('/tenant/emergency')
def tenant_emergency():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get emergency contacts
    c.execute("""SELECT name, contact_type, phone_number FROM emergency_contacts 
                 WHERE is_active = TRUE ORDER BY priority ASC""")
    emergency_contacts = c.fetchall()
    
    conn.close()
    return render_template('tenant/emergency.html', emergency_contacts=emergency_contacts)


# Security Visitor Entries
@app.route('/security/visitor_entries')
def security_visitor_entries():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get all visitor entries
    c.execute("""SELECT id, visitor_name, mobile_number, purpose, flat_number, photo,
                 entry_time, exit_time, status
                 FROM visitor_entries
                 ORDER BY entry_time DESC""")
    visitor_entries = c.fetchall()

    conn.close()

    return render_template('security/visitor_entries.html', visitor_entries=visitor_entries)


# Add Visitor Entry (Security)
@app.route('/security/visitor_entries/add', methods=['POST'])
def security_add_visitor_entry():
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    try:
        # Get form data
        visitor_name = request.form.get('visitor_name', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        purpose = request.form.get('purpose', '').strip()
        flat_number = request.form.get('flat_number', '').strip()

        # Validate required fields
        if not all([visitor_name, mobile_number, purpose, flat_number]):
            return jsonify({'success': False, 'message': 'All fields are required'})

        # Validate mobile number (10 digits)
        if len(mobile_number) != 10 or not mobile_number.isdigit():
            return jsonify({'success': False, 'message': 'Please enter a valid 10-digit mobile number'})

        # Handle photo upload
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                # Validate file type
                allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
                ext = os.path.splitext(file.filename)[1].lower()
                if ext in allowed_extensions:
                    # Generate unique filename
                    unique_filename = str(uuid.uuid4()) + ext
                    filepath = os.path.join(app.root_path, 'static/images/visitor_photos', unique_filename)
                    file.save(filepath)
                    photo_path = f'/static/images/visitor_photos/{unique_filename}'
                else:
                    return jsonify({'success': False, 'message': 'Invalid file type. Only JPG, PNG, and GIF files are allowed.'})

        # Insert visitor entry
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        c.execute("""INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, photo, status)
                     VALUES (%s, %s, %s, %s, %s, %s)""",
                  (visitor_name, mobile_number, purpose, flat_number, photo_path, 'In'))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Visitor entry added successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to add visitor entry: {str(e)}'})


# Mark Visitor Exit
@app.route('/security/visitor_entries/mark_exit/<int:entry_id>', methods=['POST'])
def security_mark_exit(entry_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        # Update exit time and status
        c.execute("""UPDATE visitor_entries
                     SET exit_time = CURRENT_TIMESTAMP, status = 'Out'
                     WHERE id = %s""", (entry_id,))

        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Visitor entry not found'})

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Visitor exit marked successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to mark exit: {str(e)}'})


# Delete Visitor Entry
@app.route('/security/visitor_entries/delete/<int:entry_id>', methods=['POST'])
def security_delete_visitor_entry(entry_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        # Get photo path before deleting
        c.execute("SELECT photo FROM visitor_entries WHERE id = %s", (entry_id,))
        result = c.fetchone()

        if result and result[0]:
            # Delete photo file if it exists
            photo_path = result[0].replace('/static/images/visitor_photos/', '')
            full_path = os.path.join(app.root_path, 'static/images/visitor_photos', photo_path)
            if os.path.exists(full_path):
                os.remove(full_path)

        # Delete entry
        c.execute("DELETE FROM visitor_entries WHERE id = %s", (entry_id,))

        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Visitor entry not found'})

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Visitor entry deleted successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to delete visitor entry: {str(e)}'})


# Security Visitors
@app.route('/security/visitors')
def security_visitors():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get pending visitor entries only
    c.execute("""SELECT ve.id, u.name, r.flat_number, ve.visitor_name, ve.mobile_number, 
                 ve.purpose, ve.entry_time
                 FROM visitor_entries ve
                 LEFT JOIN residents r ON ve.flat_number = r.flat_number
                 LEFT JOIN users u ON r.user_id = u.id
                 WHERE ve.status = 'Pending'
                 ORDER BY ve.entry_time DESC""")
    visitors = c.fetchall()
    
    c.close()
    conn.close()
    
    return render_template('security/visitors.html', visitors=visitors)


# Security Deliveries
@app.route('/security/deliveries')
def security_deliveries():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()

    # Get pending deliveries (status = 'Pending')
    c.execute("""SELECT d.id, u.name as resident_name, r.flat_number, d.delivery_company,
                 d.delivery_item, DATE(d.arrival_time) as delivery_date,
                 TIME(d.arrival_time) as arrival_time, d.status, d.collected_time
                 FROM deliveries d
                 JOIN residents r ON d.resident_id = r.id
                 JOIN users u ON r.user_id = u.id
                 WHERE d.status = 'Pending'
                 ORDER BY d.arrival_time DESC""")
    pending_deliveries = c.fetchall()

    c.close()
    conn.close()
    return render_template('security/deliveries.html', pending_deliveries=pending_deliveries)


# Security Allow Delivery Entry
@app.route('/security/deliveries/allow/<int:delivery_id>', methods=['POST'])
def security_allow_delivery(delivery_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        # Update delivery status to 'Allowed'
        c.execute("UPDATE deliveries SET status = 'Allowed' WHERE id = %s AND status = 'Pending'",
                  (delivery_id,))

        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Delivery not found or already processed'})

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Delivery entry allowed successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to allow delivery: {str(e)}'})


# Security Mark Delivery as Collected
@app.route('/security/deliveries/collect/<int:delivery_id>', methods=['POST'])
def security_collect_delivery(delivery_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        # Update delivery status to 'Collected' and set collected_time
        c.execute("UPDATE deliveries SET status = 'Collected', collected_time = CURRENT_TIMESTAMP WHERE id = %s AND status = 'Pending'",
                  (delivery_id,))

        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Delivery not found or already processed'})

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Delivery marked as collected successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to collect delivery: {str(e)}'})


# Security Mark Delivery as Delivered
@app.route('/security/deliveries/deliver/<int:delivery_id>', methods=['POST'])
def security_deliver_delivery(delivery_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()

        # Update delivery status to 'Delivered' and set collected_time
        c.execute("UPDATE deliveries SET status = 'Delivered', collected_time = CURRENT_TIMESTAMP WHERE id = %s AND status = 'Pending'",
                  (delivery_id,))

        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Delivery not found or already processed'})

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Delivery marked as delivered successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to deliver package: {str(e)}'})


# Security Parking
@app.route('/security/parking')
def security_parking():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get all parking slots
    c.execute("""SELECT p.id, u.name as resident_name, r.flat_number, p.slot_number, 
                 p.slot_type, p.vehicle_number, p.status
                 FROM parking p
                 JOIN residents r ON p.resident_id = r.id
                 JOIN users u ON r.user_id = u.id
                 ORDER BY p.slot_number""")
    parking_slots = c.fetchall()
    
    conn.close()
    return render_template('security/parking.html', parking_slots=parking_slots)


# Security Emergency
@app.route('/security/emergency')
def security_emergency():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    c = conn.cursor()
    
    # Get emergency logs
    c.execute("""SELECT el.id, u.name as resident_name, r.flat_number, el.emergency_type,
                 el.description, DATE(el.log_time) as log_date, TIME(el.log_time) as log_time,
                 el.action_taken, el.resolved
                 FROM emergency_logs el
                 JOIN residents r ON el.resident_id = r.id
                 JOIN users u ON r.user_id = u.id
                 ORDER BY el.log_time DESC""")
    emergency_logs = c.fetchall()
    
    c.close()
    conn.close()
    return render_template('security/emergency.html', emergency_logs=emergency_logs)


# POST endpoint for resident to submit complaint
@app.route('/resident/complaints/submit', methods=['POST'])
def resident_complaint_submit():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        resident_id = resident[0] if resident else None
        
        if not resident_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        
        # Insert complaint
        c.execute("""INSERT INTO complaints (resident_id, category, description, status, priority)
                     VALUES (%s, %s, %s, 'Open', 'Normal')""",
                  (resident_id, category, description))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Complaint submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# POST endpoint for tenant to submit complaint
@app.route('/tenant/complaints/submit', methods=['POST'])
def tenant_complaint_submit():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        resident_id = resident[0] if resident else None
        
        if not resident_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        priority = request.form.get('priority', 'Normal')
        
        # Insert complaint
        c.execute("""INSERT INTO complaints (resident_id, category, description, status, priority)
                     VALUES (%s, %s, %s, 'Open', %s)""",
                  (resident_id, category, description, priority))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Complaint submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# POST endpoint for tenant to update complaint
@app.route('/tenant/complaints/update/<int:complaint_id>', methods=['POST'])
def tenant_complaint_update(complaint_id):
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        resident_id = resident[0] if resident else None
        
        if not resident_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        priority = request.form.get('priority', 'Normal')
        
        # Update complaint (only if it belongs to this resident)
        c.execute("""UPDATE complaints 
                     SET category = %s, description = %s, priority = %s
                     WHERE id = %s AND resident_id = %s""",
                  (category, description, priority, complaint_id, resident_id))
        conn.commit()
        
        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': 'Complaint updated successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# POST endpoint for tenant to delete complaint
@app.route('/tenant/complaints/delete/<int:complaint_id>', methods=['POST'])
def tenant_complaint_delete(complaint_id):
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        resident_id = resident[0] if resident else None
        
        if not resident_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        # Delete complaint (only if it belongs to this resident)
        c.execute("""DELETE FROM complaints 
                     WHERE id = %s AND resident_id = %s""",
                  (complaint_id, resident_id))
        conn.commit()
        
        if c.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': 'Complaint deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# POST endpoint for resident to submit delivery request
@app.route('/resident/deliveries/request', methods=['POST'])
def resident_delivery_request():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        resident_id = resident[0] if resident else None
        
        if not resident_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        delivery_company = request.form.get('delivery_company', '')
        delivery_item = request.form.get('delivery_item', '')
        expected_time = request.form.get('expected_time', '')
        
        # Insert delivery request
        c.execute("""INSERT INTO deliveries (resident_id, delivery_company, delivery_item, arrival_time, status)
                     VALUES (%s, %s, %s, NOW(), 'Pending')""",
                  (resident_id, delivery_company, delivery_item))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Delivery request submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# POST endpoint for tenant to submit delivery request
@app.route('/tenant/deliveries/request', methods=['POST'])
def tenant_delivery_request():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society'
        )
        c = conn.cursor()
        
        # Get resident ID (for tenant, we get resident they're associated with)
        c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
        resident = c.fetchone()
        resident_id = resident[0] if resident else None
        
        if not resident_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Resident not found'}), 404
        
        delivery_company = request.form.get('delivery_company', '')
        delivery_item = request.form.get('delivery_item', '')
        expected_time = request.form.get('expected_time', '')
        
        # Insert delivery request
        c.execute("""INSERT INTO deliveries (resident_id, delivery_company, delivery_item, arrival_time, status)
                     VALUES (%s, %s, %s, NOW(), 'Pending')""",
                  (resident_id, delivery_company, delivery_item))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Delivery request submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 4000)))
