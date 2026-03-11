import pymysql
from flask import g
import os


def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = pymysql.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            database='society_management',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    return g.db


def get_cursor():
    """Get database cursor"""
    db = get_db()
    return db.cursor()


def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    """Initialize app with database functions"""
    app.teardown_appcontext(close_db)


def init_db():
    """Initialize database tables for MySQL"""
    try:
        db = pymysql.connect(
            host='localhost',
            user='root',
            password='anjali@2',
            charset='utf8mb4'
        )
    except Exception as e:
        print(f"Error connecting to MySQL for initialization: {e}")
        print("Please ensure MySQL server is running with:")
        print("  - Host: localhost")
        print("  - User: root")
        print("  - Password: anjali@2")
        raise
    
    cursor = db.cursor()
    
    # Create database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS society_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cursor.execute("USE society_management;")
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('Admin', 'Resident', 'Security', 'Tenant') NOT NULL,
            phone VARCHAR(15),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            profile_pic VARCHAR(255) DEFAULT 'default.png'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INT CHECK (id = 1) PRIMARY KEY,
            society_name VARCHAR(255) NOT NULL,
            society_address TEXT NOT NULL,
            society_phone VARCHAR(15),
            society_email VARCHAR(100),
            society_website VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create blocks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            block_name VARCHAR(50) UNIQUE NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create flats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            block_id INT,
            flat_number VARCHAR(20) NOT NULL,
            status ENUM('Vacant', 'Occupied') DEFAULT 'Vacant',
            owner_name VARCHAR(100),
            FOREIGN KEY (block_id) REFERENCES blocks(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create residents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS residents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            flat_number VARCHAR(20) NOT NULL,
            block_id INT,
            vehicle_numbers TEXT,
            family_members TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (block_id) REFERENCES blocks(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create visitors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            resident_id INT,
            visitor_name VARCHAR(100) NOT NULL,
            contact VARCHAR(15) NOT NULL,
            visit_purpose TEXT NOT NULL,
            visit_date DATE NOT NULL,
            visit_time TIME NOT NULL,
            status ENUM('Pending', 'Approved', 'Rejected', 'Completed') DEFAULT 'Pending',
            approved_by INT,
            approved_at TIMESTAMP NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (resident_id) REFERENCES residents(id),
            FOREIGN KEY (approved_by) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create visitor_entries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitor_entries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            visitor_id INT,
            visitor_name VARCHAR(100) NOT NULL,
            contact VARCHAR(15) NOT NULL,
            visit_purpose TEXT NOT NULL,
            visit_date DATE NOT NULL,
            visit_time TIME NOT NULL,
            entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_time TIMESTAMP NULL,
            photo VARCHAR(500),
            status ENUM('Active', 'Exited') DEFAULT 'Active',
            FOREIGN KEY (visitor_id) REFERENCES visitors(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create notices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            posted_by INT NOT NULL,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expiry_date DATE,
            is_important BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (posted_by) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create complaints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            subject VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            complaint_date DATE NOT NULL,
            status ENUM('Open', 'In Progress', 'Resolved', 'Closed') DEFAULT 'Open',
            priority ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
            assigned_to INT,
            resolved_at TIMESTAMP NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create maintenance_bills table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            resident_id INT,
            flat_number VARCHAR(20),
            amount DECIMAL(10,2) NOT NULL,
            due_date DATE NOT NULL,
            status ENUM('Pending', 'Paid', 'Overdue') DEFAULT 'Pending',
            late_fine DECIMAL(10,2) DEFAULT 0.00,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resident_id) REFERENCES residents(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bill_id INT,
            resident_id INT,
            amount DECIMAL(10,2) NOT NULL,
            payment_date DATE NOT NULL,
            payment_method VARCHAR(50),
            transaction_id VARCHAR(100),
            status ENUM('Pending', 'Completed', 'Failed', 'Refunded') DEFAULT 'Pending',
            notes TEXT,
            FOREIGN KEY (bill_id) REFERENCES maintenance_bills(id),
            FOREIGN KEY (resident_id) REFERENCES residents(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            event_date DATE NOT NULL,
            event_time TIME NOT NULL,
            venue VARCHAR(100) NOT NULL,
            organizer VARCHAR(100),
            max_attendees INT,
            registration_required BOOLEAN DEFAULT FALSE,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_path VARCHAR(500),
            FOREIGN KEY (created_by) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create event_registrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_registrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_id INT,
            user_id INT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('Registered', 'Attended', 'Cancelled') DEFAULT 'Registered',
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create deliveries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            recipient_name VARCHAR(100) NOT NULL,
            recipient_flat VARCHAR(20) NOT NULL,
            delivery_type VARCHAR(50) NOT NULL,
            item_description TEXT,
            sender_name VARCHAR(100),
            arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivery_status ENUM('Pending', 'Received', 'Delivered') DEFAULT 'Pending',
            received_by VARCHAR(100),
            delivery_person_signature TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create parking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking (
            id INT AUTO_INCREMENT PRIMARY KEY,
            flat_number VARCHAR(20) NOT NULL,
            vehicle_type ENUM('Two Wheeler', 'Four Wheeler') NOT NULL,
            vehicle_number VARCHAR(20) NOT NULL,
            owner_name VARCHAR(100) NOT NULL,
            parking_slot VARCHAR(20),
            allocated_date DATE,
            status ENUM('Active', 'Inactive') DEFAULT 'Active'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create emergency_contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            contact_type ENUM('Admin', 'Security', 'Fire', 'Police', 'Ambulance', 'Maintenance', 'Doctor', 'Other') NOT NULL,
            phone_number VARCHAR(15) NOT NULL,
            priority INT DEFAULT 10,
            is_active BOOLEAN DEFAULT TRUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create charity table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            target_amount DECIMAL(10,2),
            collected_amount DECIMAL(10,2) DEFAULT 0.00,
            start_date DATE,
            end_date DATE,
            organizer VARCHAR(100),
            status ENUM('Active', 'Completed', 'Cancelled') DEFAULT 'Active',
            image_path VARCHAR(500)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create charity_donations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charity_donations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            charity_id INT,
            donor_name VARCHAR(100) NOT NULL,
            donor_flat VARCHAR(20),
            amount DECIMAL(10,2) NOT NULL,
            donation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            payment_method VARCHAR(50),
            status ENUM('Pending', 'Completed', 'Failed') DEFAULT 'Pending',
            FOREIGN KEY (charity_id) REFERENCES charity(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create maintenance_requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            flat_number VARCHAR(20) NOT NULL,
            issue_type VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            priority ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
            status ENUM('Reported', 'In Progress', 'Completed', 'Cancelled') DEFAULT 'Reported',
            reported_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_to INT,
            completed_date TIMESTAMP NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # Create visitor_status_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitor_status_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            visitor_id INT NOT NULL,
            status_from ENUM('Pending', 'Approved', 'Rejected', 'Completed'),
            status_to ENUM('Pending', 'Approved', 'Rejected', 'Completed'),
            changed_by INT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (visitor_id) REFERENCES visitors(id),
            FOREIGN KEY (changed_by) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    db.commit()
    cursor.close()
    db.close()


