# Society Management System - Data Dictionary

## Overview
This data dictionary provides detailed specifications for all database tables, columns, data types, constraints, and relationships in the Society Management System.

## Database Schema Summary
- **Database Name**: society_management
- **Character Set**: utf8mb4
- **Collation**: utf8mb4_unicode_ci
- **Engine**: InnoDB

---

## 1. users Table

### Description
Stores user account information for all system users including administrators, residents, and security personnel.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each user |
| name | VARCHAR(100) | NOT NULL | Full name of the user |
| email | VARCHAR(100) | UNIQUE, NOT NULL | Email address (used for login) |
| password | VARCHAR(255) | NOT NULL | Hashed password |
| role | ENUM('Admin', 'Resident', 'Security', 'Tenant') | NOT NULL | User role in the system |
| phone | VARCHAR(15) | NULL | Contact phone number |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |
| profile_pic | VARCHAR(255) | DEFAULT 'default.png' | Profile picture filename |

### Indexes
- PRIMARY KEY on `id`
- UNIQUE KEY on `email`
- INDEX on `role` (for role-based queries)

### Relationships
- Referenced by: residents.user_id (1:1)
- References: complaints.user_id (1:many)
- References: payments.user_id (1:many)
- References: events.created_by (1:many)
- References: notices.posted_by (1:many)

---

## 2. settings Table

### Description
Stores society-wide configuration settings and information.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, CHECK (id = 1) | Single row constraint |
| society_name | VARCHAR(255) | NOT NULL | Name of the society |
| society_address | TEXT | NOT NULL | Complete address of the society |
| society_phone | VARCHAR(15) | NULL | Society contact phone |
| society_email | VARCHAR(100) | NULL | Society contact email |
| society_website | VARCHAR(255) | NULL | Society website URL |

### Indexes
- PRIMARY KEY on `id`

### Notes
- Contains only one row (id = 1) for global settings
- Used throughout the application for society information display

---

## 3. blocks Table

### Description
Represents building blocks within the society complex.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique block identifier |
| block_name | VARCHAR(50) | UNIQUE, NOT NULL | Block name (e.g., A, B, C) |

### Indexes
- PRIMARY KEY on `id`
- UNIQUE KEY on `block_name`

### Relationships
- Referenced by: flats.block_id (1:many)
- Referenced by: residents.block_id (1:many)

---

## 4. flats Table

### Description
Represents individual housing units within blocks.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique flat identifier |
| block_id | INT | FOREIGN KEY | Reference to blocks table |
| flat_number | VARCHAR(20) | NOT NULL | Flat number (e.g., A-101) |
| status | ENUM('Vacant', 'Occupied') | DEFAULT 'Vacant' | Current occupancy status |
| owner_name | VARCHAR(100) | NULL | Name of the flat owner |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `block_id`
- UNIQUE KEY on `flat_number`
- INDEX on `status`

### Relationships
- References: blocks.id
- Referenced by: residents.flat_number (1:1)

---

## 5. residents Table

### Description
Extends user information with resident-specific details.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique resident identifier |
| user_id | INT | FOREIGN KEY, NOT NULL | Reference to users table |
| flat_number | VARCHAR(20) | NOT NULL | Resident's flat number |
| block_id | INT | FOREIGN KEY | Reference to blocks table |
| resident_type | VARCHAR(20) | NULL | Owner or Tenant |
| occupancy_start | DATE | NULL | When resident moved in |
| vehicle_numbers | TEXT | NULL | JSON array of vehicle numbers |
| family_members | TEXT | NULL | JSON array of family member details |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id`
- FOREIGN KEY on `block_id`
- UNIQUE KEY on `flat_number`
- INDEX on `user_id`

### Relationships
- References: users.id
- References: blocks.id
- Referenced by: visitors.resident_id (1:many)
- Referenced by: complaints.resident_id (1:many)
- Referenced by: maintenance_bills.resident_id (1:many)
- Referenced by: payments.resident_id (1:many)
- Referenced by: parking.resident_id (1:many)
- Referenced by: deliveries.resident_id (1:many)
- Referenced by: emergency_logs.resident_id (1:many)

---

## 6. visitors Table

### Description
Manages visitor information and access requests.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique visitor entry identifier |
| user_id | INT | FOREIGN KEY, NOT NULL | User who registered the visitor |
| resident_id | INT | FOREIGN KEY | Resident being visited |
| visitor_name | VARCHAR(100) | NOT NULL | Name of the visitor |
| contact | VARCHAR(15) | NOT NULL | Visitor contact number |
| visit_purpose | TEXT | NOT NULL | Purpose of visit |
| visit_date | DATE | NOT NULL | Scheduled visit date |
| visit_time | TIME | NOT NULL | Scheduled visit time |
| status | ENUM('Pending', 'Approved', 'Rejected', 'Completed') | DEFAULT 'Pending' | Approval status |
| approved_by | INT | FOREIGN KEY | User who approved/rejected |
| approved_at | TIMESTAMP | NULL | Approval timestamp |
| exit_time | TIMESTAMP | NULL | Visitor exit timestamp |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id`
- FOREIGN KEY on `resident_id`
- FOREIGN KEY on `approved_by`
- INDEX on `status`
- INDEX on `visit_date`

### Relationships
- References: users.id (user_id)
- References: residents.id (resident_id)
- References: users.id (approved_by)

---

## 7. visitor_entries Table

### Description
Tracks actual visitor entries and exits with photo evidence.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique entry identifier |
| visitor_id | INT | FOREIGN KEY | Reference to visitors table |
| visitor_name | VARCHAR(100) | NOT NULL | Visitor name |
| mobile_number | VARCHAR(15) | NOT NULL | Visitor contact |
| purpose | TEXT | NOT NULL | Visit purpose |
| flat_number | VARCHAR(20) | NOT NULL | Flat being visited |
| photo | VARCHAR(500) | NULL | Photo filename |
| entry_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Entry timestamp |
| exit_time | TIMESTAMP | NULL | Exit timestamp |
| status | ENUM('Active', 'Exited') | DEFAULT 'Active' | Current status |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `visitor_id`
- INDEX on `entry_time`
- INDEX on `status`

### Relationships
- References: visitors.id

---

## 8. notices Table

### Description
Stores society notices and announcements.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique notice identifier |
| title | VARCHAR(200) | NOT NULL | Notice title |
| content | TEXT | NOT NULL | Notice content |
| posted_by | INT | FOREIGN KEY, NOT NULL | User who posted the notice |
| posted_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Posting timestamp |
| expiry_date | DATE | NULL | Notice expiry date |
| is_important | BOOLEAN | DEFAULT FALSE | Importance flag |
| priority | ENUM('Normal', 'High', 'Urgent') | DEFAULT 'Normal' | Notice priority |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `posted_by`
- INDEX on `posted_at`
- INDEX on `is_important`
- INDEX on `priority`

### Relationships
- References: users.id (posted_by)

---

## 9. complaints Table

### Description
Manages resident complaints and maintenance requests.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique complaint identifier |
| user_id | INT | FOREIGN KEY, NOT NULL | User who filed complaint |
| resident_id | INT | FOREIGN KEY | Resident details |
| subject | VARCHAR(200) | NOT NULL | Complaint subject |
| category | VARCHAR(50) | NOT NULL | Complaint category |
| description | TEXT | NOT NULL | Detailed description |
| complaint_date | DATE | NOT NULL | Date complaint was filed |
| status | ENUM('Open', 'In Progress', 'Resolved', 'Closed') | DEFAULT 'Open' | Current status |
| priority | ENUM('Low', 'Medium', 'High', 'Critical') | DEFAULT 'Medium' | Priority level |
| ai_score | FLOAT | NULL | AI-generated priority score |
| assigned_to | INT | FOREIGN KEY | Assigned staff member |
| resolved_at | TIMESTAMP | NULL | Resolution timestamp |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id`
- FOREIGN KEY on `resident_id`
- FOREIGN KEY on `assigned_to`
- INDEX on `status`
- INDEX on `priority`
- INDEX on `complaint_date`

### Relationships
- References: users.id (user_id)
- References: residents.id (resident_id)
- References: users.id (assigned_to)

---

## 10. maintenance_bills Table

### Description
Stores maintenance bill information and payment tracking.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique bill identifier |
| resident_id | INT | FOREIGN KEY | Resident being billed |
| flat_number | VARCHAR(20) | NULL | Flat number for reference |
| amount | DECIMAL(10,2) | NOT NULL | Bill amount |
| due_date | DATE | NOT NULL | Payment due date |
| status | ENUM('Pending', 'Paid', 'Overdue') | DEFAULT 'Pending' | Payment status |
| late_fine | DECIMAL(10,2) | DEFAULT 0.00 | Accumulated late fees |
| created_date | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Bill creation date |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `resident_id`
- INDEX on `status`
- INDEX on `due_date`
- INDEX on `created_date`

### Relationships
- References: residents.id
- Referenced by: payments.bill_id (1:many)

---

## 11. payments Table

### Description
Records all payment transactions for maintenance bills.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique payment identifier |
| bill_id | INT | FOREIGN KEY | Reference to maintenance bill |
| resident_id | INT | FOREIGN KEY | Paying resident |
| amount | DECIMAL(10,2) | NOT NULL | Payment amount |
| payment_date | DATE | NOT NULL | Payment date |
| payment_method | VARCHAR(50) | NULL | Payment method used |
| transaction_id | VARCHAR(100) | NULL | External transaction ID |
| receipt_number | VARCHAR(50) | NULL | Generated receipt number |
| status | ENUM('Pending', 'Completed', 'Failed', 'Refunded') | DEFAULT 'Pending' | Payment status |
| notes | TEXT | NULL | Additional payment notes |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `bill_id`
- FOREIGN KEY on `resident_id`
- INDEX on `payment_date`
- INDEX on `status`
- INDEX on `receipt_number`

### Relationships
- References: maintenance_bills.id
- References: residents.id

---

## 12. events Table

### Description
Manages society events and activities.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique event identifier |
| title | VARCHAR(200) | NOT NULL | Event title |
| description | TEXT | NOT NULL | Event description |
| event_date | DATE | NOT NULL | Event date |
| event_time | TIME | NOT NULL | Event time |
| venue | VARCHAR(100) | NOT NULL | Event venue |
| organizer | VARCHAR(100) | NULL | Event organizer |
| max_attendees | INT | NULL | Maximum attendees |
| registration_required | BOOLEAN | DEFAULT FALSE | Registration requirement |
| created_by | INT | FOREIGN KEY | User who created event |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| image_path | VARCHAR(500) | NULL | Event image filename |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `created_by`
- INDEX on `event_date`
- INDEX on `created_at`

### Relationships
- References: users.id (created_by)
- Referenced by: event_registrations.event_id (1:many)

---

## 13. event_registrations Table

### Description
Tracks event registrations by residents.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique registration identifier |
| event_id | INT | FOREIGN KEY | Reference to events table |
| user_id | INT | FOREIGN KEY | Registered user |
| registration_date | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |
| status | ENUM('Registered', 'Attended', 'Cancelled') | DEFAULT 'Registered' | Registration status |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `event_id`
- FOREIGN KEY on `user_id`
- INDEX on `registration_date`
- INDEX on `status`

### Relationships
- References: events.id
- References: users.id

---

## 14. deliveries Table

### Description
Manages package and delivery tracking.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique delivery identifier |
| resident_id | INT | FOREIGN KEY | Receiving resident |
| delivery_company | VARCHAR(100) | NOT NULL | Delivery company name |
| delivery_item | TEXT | NULL | Item description |
| arrival_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Arrival timestamp |
| status | ENUM('Pending', 'Received', 'Delivered') | DEFAULT 'Pending' | Delivery status |
| received_by | VARCHAR(100) | NULL | Person who received |
| delivery_person_signature | TEXT | NULL | Digital signature |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `resident_id`
- INDEX on `arrival_time`
- INDEX on `status`

### Relationships
- References: residents.id

---

## 15. parking Table

### Description
Manages parking slot allocations and vehicle information.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique parking record identifier |
| resident_id | INT | FOREIGN KEY | Assigned resident |
| slot_number | VARCHAR(20) | NOT NULL | Parking slot identifier |
| slot_type | ENUM('Two Wheeler', 'Four Wheeler') | NOT NULL | Vehicle type |
| vehicle_number | VARCHAR(20) | NOT NULL | Vehicle registration number |
| owner_name | VARCHAR(100) | NOT NULL | Vehicle owner name |
| parking_slot | VARCHAR(20) | NULL | Specific slot assignment |
| allocated_date | DATE | NULL | Allocation date |
| status | ENUM('Active', 'Inactive') | DEFAULT 'Active' | Allocation status |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `resident_id`
- UNIQUE KEY on `vehicle_number`
- INDEX on `slot_number`
- INDEX on `status`

### Relationships
- References: residents.id

---

## 16. emergency_contacts Table

### Description
Stores emergency contact information for the society.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique contact identifier |
| name | VARCHAR(100) | NOT NULL | Contact person/organization name |
| contact_type | ENUM('Admin', 'Security', 'Fire', 'Police', 'Ambulance', 'Maintenance', 'Doctor', 'Other') | NOT NULL | Type of emergency contact |
| phone_number | VARCHAR(15) | NOT NULL | Contact phone number |
| priority | INT | DEFAULT 10 | Contact priority (lower = higher priority) |
| is_active | BOOLEAN | DEFAULT TRUE | Contact active status |

### Indexes
- PRIMARY KEY on `id`
- INDEX on `contact_type`
- INDEX on `priority`
- INDEX on `is_active`

---

## 17. emergency_logs Table

### Description
Records emergency incidents and responses.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique log identifier |
| resident_id | INT | FOREIGN KEY | Resident who reported emergency |
| emergency_type | VARCHAR(50) | NOT NULL | Type of emergency |
| description | TEXT | NOT NULL | Emergency description |
| log_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Incident timestamp |
| resolved | BOOLEAN | DEFAULT FALSE | Resolution status |
| action_taken | TEXT | NULL | Actions taken to resolve |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `resident_id`
- INDEX on `log_time`
- INDEX on `resolved`
- INDEX on `emergency_type`

### Relationships
- References: residents.id

---

## 18. charity Table

### Description
Manages charity campaigns and fundraising activities.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique charity identifier |
| title | VARCHAR(200) | NOT NULL | Charity campaign title |
| description | TEXT | NOT NULL | Campaign description |
| target_amount | DECIMAL(10,2) | NULL | Fundraising target |
| collected_amount | DECIMAL(10,2) | DEFAULT 0.00 | Amount collected |
| start_date | DATE | NULL | Campaign start date |
| end_date | DATE | NULL | Campaign end date |
| organizer | VARCHAR(100) | NULL | Campaign organizer |
| status | ENUM('Active', 'Completed', 'Cancelled') | DEFAULT 'Active' | Campaign status |
| image_path | VARCHAR(500) | NULL | Campaign image |

### Indexes
- PRIMARY KEY on `id`
- INDEX on `status`
- INDEX on `start_date`
- INDEX on `end_date`

### Relationships
- Referenced by: charity_donations.charity_id (1:many)

---

## 19. charity_donations Table

### Description
Records individual donations to charity campaigns.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique donation identifier |
| charity_id | INT | FOREIGN KEY | Reference to charity campaign |
| donor_name | VARCHAR(100) | NOT NULL | Donor name |
| donor_flat | VARCHAR(20) | NULL | Donor flat number |
| amount | DECIMAL(10,2) | NOT NULL | Donation amount |
| donation_date | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Donation timestamp |
| payment_method | VARCHAR(50) | NULL | Payment method used |
| status | ENUM('Pending', 'Completed', 'Failed') | DEFAULT 'Pending' | Donation status |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `charity_id`
- INDEX on `donation_date`
- INDEX on `status`

### Relationships
- References: charity.id

---

## 20. maintenance_requests Table

### Description
Tracks maintenance requests separate from complaints.

### Columns

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique request identifier |
| user_id | INT | FOREIGN KEY, NOT NULL | User who made request |
| flat_number | VARCHAR(20) | NOT NULL | Affected flat |
| issue_type | VARCHAR(100) | NOT NULL | Type of maintenance issue |
| description | TEXT | NOT NULL | Detailed description |
| priority | ENUM('Low', 'Medium', 'High', 'Critical') | DEFAULT 'Medium' | Request priority |
| status | ENUM('Reported', 'In Progress', 'Completed', 'Cancelled') | DEFAULT 'Reported' | Request status |
| reported_date | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Report timestamp |
| assigned_to | INT | FOREIGN KEY | Assigned maintenance staff |
| completed_date | TIMESTAMP | NULL | Completion timestamp |

### Indexes
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id`
- FOREIGN KEY on `assigned_to`
- INDEX on `status`
- INDEX on `priority`
- INDEX on `reported_date`

### Relationships
- References: users.id (user_id)
- References: users.id (assigned_to)

---

## Data Types Legend

| MySQL Type | Description | Range/Format |
|------------|-------------|--------------|
| INT | Integer | -2,147,483,648 to 2,147,483,647 |
| VARCHAR(n) | Variable character string | Up to n characters |
| TEXT | Long text | Up to 65,535 characters |
| DECIMAL(p,s) | Fixed-point number | p digits, s decimal places |
| DATE | Date | YYYY-MM-DD |
| TIME | Time | HH:MM:SS |
| TIMESTAMP | Date and time | YYYY-MM-DD HH:MM:SS |
| BOOLEAN | True/false | 0 or 1 |
| ENUM | Enumeration | Predefined values |

## Constraints Legend

| Constraint | Description |
|------------|-------------|
| PRIMARY KEY | Unique identifier for table |
| FOREIGN KEY | References primary key in another table |
| NOT NULL | Field cannot be empty |
| UNIQUE | Values must be unique across table |
| DEFAULT | Default value if none provided |
| AUTO_INCREMENT | Automatically incrementing integer |
| CHECK | Custom validation rule |

## Naming Conventions

- **Tables**: snake_case, plural nouns (e.g., users, complaints)
- **Columns**: snake_case, singular nouns (e.g., user_id, flat_number)
- **Primary Keys**: id (integer, auto-increment)
- **Foreign Keys**: [referenced_table]_id (e.g., user_id, resident_id)
- **Indexes**: Automatically created for foreign keys and unique constraints

This data dictionary serves as the authoritative reference for all database structures in the Society Management System.
