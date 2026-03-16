-- Create database
CREATE DATABASE IF NOT EXISTS society;

-- Use database
USE society;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profile_pic VARCHAR(255)
);

-- Create blocks table
CREATE TABLE IF NOT EXISTS blocks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    block_name VARCHAR(100) UNIQUE NOT NULL
);

-- Create flats table
CREATE TABLE IF NOT EXISTS flats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    block_id INT NOT NULL,
    flat_number VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    owner_name VARCHAR(255),
    FOREIGN KEY (block_id) REFERENCES blocks(id)
);

-- Create residents table
CREATE TABLE IF NOT EXISTS residents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    flat_number VARCHAR(50),
    resident_type VARCHAR(50),
    occupancy_start DATE,
    occupancy_end DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create visitor_entries table
CREATE TABLE IF NOT EXISTS visitor_entries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    visitor_name VARCHAR(255) NOT NULL,
    mobile_number VARCHAR(20),
    purpose TEXT,
    flat_number VARCHAR(50),
    photo VARCHAR(255),
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP NULL,
    status VARCHAR(10) NOT NULL
);

-- Create deliveries table
CREATE TABLE IF NOT EXISTS deliveries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resident_id INT NOT NULL,
    delivery_company VARCHAR(255),
    delivery_item TEXT,
    arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    collected_time TIMESTAMP NULL,
    FOREIGN KEY (resident_id) REFERENCES residents(id)
);

-- Create parking table
CREATE TABLE IF NOT EXISTS parking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resident_id INT,
    slot_number VARCHAR(50) NOT NULL,
    slot_type VARCHAR(50),
    vehicle_number VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (resident_id) REFERENCES residents(id)
);

-- Create vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resident_id INT NOT NULL,
    vehicle_number VARCHAR(50) NOT NULL,
    vehicle_type VARCHAR(50),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (resident_id) REFERENCES residents(id)
);

-- Create complaints table
CREATE TABLE IF NOT EXISTS complaints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resident_id INT NOT NULL,
    category VARCHAR(100),
    description TEXT,
    complaint_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    assigned_to VARCHAR(255),
    resolution_date DATE,
    priority VARCHAR(20),
    ai_score DECIMAL(3,2),
    FOREIGN KEY (resident_id) REFERENCES residents(id)
);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resident_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    receipt_number VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL,
    description TEXT,
    FOREIGN KEY (resident_id) REFERENCES residents(id)
);

-- Create charity table
CREATE TABLE IF NOT EXISTS charity (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resident_id INT NOT NULL,
    item_type VARCHAR(100),
    quantity INT,
    description TEXT,
    status VARCHAR(20) NOT NULL,
    pickup_date DATE,
    FOREIGN KEY (resident_id) REFERENCES residents(id)
);

-- Create maintenance_bills table
CREATE TABLE IF NOT EXISTS maintenance_bills (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resident_id INT NOT NULL,
    flat_number VARCHAR(50),
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    late_fine DECIMAL(10,2) DEFAULT 0.00,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id)
);

-- Create notices table
CREATE TABLE IF NOT EXISTS notices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    notice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority VARCHAR(20),
    FOREIGN KEY (admin_id) REFERENCES users(id)
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    event_type VARCHAR(50),
    event_date DATE NOT NULL,
    event_time TIME,
    venue VARCHAR(255),
    description TEXT,
    image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create emergency_logs table
CREATE TABLE IF NOT EXISTS emergency_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resident_id INT NOT NULL,
    emergency_type VARCHAR(100),
    description TEXT,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_taken TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (resident_id) REFERENCES residents(id)
);

-- Create emergency_contacts table
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    contact_type VARCHAR(50),
    phone_number VARCHAR(20),
    priority INT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create settings table (single row with id=1)
CREATE TABLE IF NOT EXISTS settings (
    id INT PRIMARY KEY CHECK (id = 1),
    society_name VARCHAR(255),
    society_address TEXT,
    society_phone VARCHAR(20),
    society_email VARCHAR(255),
    society_website VARCHAR(255)
);

-- Insert default settings
INSERT IGNORE INTO settings (id, society_name, society_address, society_phone, society_email, society_website) 
VALUES (1, 'Society Management System', '123 Main Street, City', '+1234567890', 'admin@society.com', 'www.society.com');

-- Insert sample admin user (password: admin123)
INSERT IGNORE INTO users (name, email, password, role, phone) 
VALUES ('Admin User', 'admin@society.com', 'admin123', 'admin', '+1234567890');

-- Insert sample resident user (password: resident123)
INSERT IGNORE INTO users (name, email, password, role, phone) 
VALUES ('Resident User', 'resident@society.com', 'resident123', 'resident', '+1234567891');

-- Insert sample tenant user (password: tenant123)
INSERT IGNORE INTO users (name, email, password, role, phone) 
VALUES ('Tenant User', 'tenant@society.com', 'tenant123', 'tenant', '+1234567892');

-- Insert sample security user (password: security123)
INSERT IGNORE INTO users (name, email, password, role, phone) 
VALUES ('Security User', 'security@society.com', 'security123', 'security', '+1234567893');