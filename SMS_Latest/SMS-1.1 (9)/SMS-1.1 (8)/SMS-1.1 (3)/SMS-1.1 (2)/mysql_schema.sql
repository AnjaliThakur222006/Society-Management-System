-- MySQL Schema for Society Management System

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profile_pic VARCHAR(255) DEFAULT 'default.png'
);

CREATE TABLE residents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    flat_number VARCHAR(50) NOT NULL,
    resident_type VARCHAR(50) NOT NULL, -- Owner or Tenant
    occupancy_start DATE,
    occupancy_end DATE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT,
    visitor_name VARCHAR(255) NOT NULL,
    contact VARCHAR(20),
    visit_purpose TEXT,
    visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    visit_time TIME,
    status VARCHAR(20) DEFAULT 'Pending', -- Pending, Approved, Rejected, Exited
    exit_time TIME,
    FOREIGN KEY (resident_id) REFERENCES residents (id)
);

CREATE TABLE deliveries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT,
    delivery_company VARCHAR(255) NOT NULL,
    delivery_item TEXT,
    arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Pending', -- Pending, Allowed, Collected, Delivered
    collected_time TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents (id)
);

CREATE TABLE parking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT,
    slot_number VARCHAR(50) NOT NULL,
    slot_type VARCHAR(50) NOT NULL, -- Fixed, Shared, Temporary
    vehicle_number VARCHAR(50),
    status VARCHAR(20) DEFAULT 'Available', -- Available, Occupied
    FOREIGN KEY (resident_id) REFERENCES residents (id)
);

CREATE TABLE complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    complaint_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Open', -- Open, Assigned, Resolved
    assigned_to VARCHAR(255),
    resolution_date DATE,
    priority VARCHAR(20) DEFAULT 'Normal', -- Urgent, Medium, Normal
    ai_score DECIMAL(3,2) DEFAULT 0.0,
    FOREIGN KEY (resident_id) REFERENCES residents (id)
);

CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT,
    amount DECIMAL(10,2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    receipt_number VARCHAR(100) UNIQUE,
    status VARCHAR(20) DEFAULT 'Paid',
    description TEXT,
    FOREIGN KEY (resident_id) REFERENCES residents (id)
);

CREATE TABLE charity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT,
    item_type VARCHAR(100) NOT NULL,
    quantity INT,
    description TEXT,
    status VARCHAR(20) DEFAULT 'Pending', -- Pending, Approved, Picked
    pickup_date DATE,
    FOREIGN KEY (resident_id) REFERENCES residents (id)
);

CREATE TABLE maintenance_bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT,
    flat_number VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Unpaid', -- Unpaid, Paid
    late_fine DECIMAL(10,2) DEFAULT 0.0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents (id)
);

CREATE TABLE notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    notice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority VARCHAR(20) DEFAULT 'Normal', -- Normal, High, Urgent
    FOREIGN KEY (admin_id) REFERENCES users (id)
);

CREATE TABLE emergency_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT,
    emergency_type VARCHAR(100) NOT NULL,
    description TEXT,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_taken TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (resident_id) REFERENCES residents (id)
);

CREATE TABLE emergency_contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_type VARCHAR(50) NOT NULL, -- Admin, Security, Fire, Police, Ambulance, Maintenance, Doctor, Other
    phone_number VARCHAR(20) NOT NULL,
    priority INT DEFAULT 10, -- Lower number means higher priority
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE settings (
    id INT PRIMARY KEY CHECK (id = 1),
    society_name VARCHAR(255) NOT NULL,
    society_address TEXT NOT NULL,
    society_phone VARCHAR(20),
    society_email VARCHAR(255),
    society_website VARCHAR(255)
);

CREATE TABLE blocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    block_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE flats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    block_id INT,
    flat_number VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'Vacant', -- Vacant, Occupied
    owner_name VARCHAR(255),
    FOREIGN KEY (block_id) REFERENCES blocks (id)
);

CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    event_type VARCHAR(50),
    event_date DATE,
    event_time TIME,
    venue VARCHAR(255),
    description TEXT,
    image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE visitor_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_name VARCHAR(255) NOT NULL,
    mobile_number VARCHAR(20) NOT NULL,
    purpose TEXT NOT NULL,
    flat_number VARCHAR(50) NOT NULL,
    photo VARCHAR(255),
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP,
    status VARCHAR(10) DEFAULT 'In'  -- In or Out
);
