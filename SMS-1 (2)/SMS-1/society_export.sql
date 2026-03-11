-- Exported from SQLite database
-- Generated on 2026-01-16 14:16:33.913455

-- Create table users
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `name` TEXT NOT NULL,
  `email` TEXT NOT NULL,
  `password` TEXT NOT NULL,
  `role` TEXT NOT NULL,
  `phone` TEXT,
  `created_at` TIMESTAMP
);

-- Insert data into users
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (1, 'Admin User', 'admin@society.com', 'admin123', 'Admin', '9876543210', '2025-12-19 16:13:43');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (2, 'John Owner', 'john.owner@gmail.com', 'owner123', 'Owner', '9876543211', '2025-12-19 16:13:43');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (3, 'Jane Tenant', 'jane.tenant@gmail.com', 'tenant123', 'Tenant', '9876543212', '2025-12-19 16:13:43');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (4, 'Security Guard', 'security@society.com', 'security123', 'Security', '9876543213', '2025-12-19 16:13:43');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (5, 'desai gunjan', 'gunajn@gmail.com', 'tenant123', 'Tenant', '9876543210', '2025-12-28 06:52:29');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (6, 'Anjali Thakur', 'anjali@society.com', 'admin123', 'Owner', '8754641452', '2026-01-01 11:09:45');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (7, 'Anjali Thakur', 'unj@society.com', 'admin123', 'Owner', '9857458675', '2026-01-03 06:58:15');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (8, 'Anjali Thakur', 'thakuranjali222006@gmail.com', '123456', 'Owner', '9696325846', '2026-01-03 08:26:04');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (9, 'Venisha', 'avniisha@gmail.com', '123456', 'Owner', '1234567890', '2026-01-03 08:50:25');
INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `phone`, `created_at`) VALUES (10, 'Avniisha', 'venisha@gmail.com', '123456', 'Tenant', '1234567890', '2026-01-03 09:02:51');

-- Create table residents
DROP TABLE IF EXISTS `residents`;
CREATE TABLE `residents` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `user_id` INTEGER,
  `flat_number` TEXT NOT NULL,
  `resident_type` TEXT NOT NULL,
  `occupancy_start` DATE,
  `occupancy_end` DATE
);

-- Insert data into residents
INSERT INTO `residents` (`id`, `user_id`, `flat_number`, `resident_type`, `occupancy_start`, `occupancy_end`) VALUES (1, 2, 'A-101', 'Owner', '2023-01-01', NULL);
INSERT INTO `residents` (`id`, `user_id`, `flat_number`, `resident_type`, `occupancy_start`, `occupancy_end`) VALUES (2, 3, 'B-202', 'Tenant', '2023-06-01', NULL);
INSERT INTO `residents` (`id`, `user_id`, `flat_number`, `resident_type`, `occupancy_start`, `occupancy_end`) VALUES (3, 5, 'F3-101', 'Tenant', '2025-12-28', NULL);
INSERT INTO `residents` (`id`, `user_id`, `flat_number`, `resident_type`, `occupancy_start`, `occupancy_end`) VALUES (4, 6, 'B-221', 'Owner', '2026-01-01', NULL);
INSERT INTO `residents` (`id`, `user_id`, `flat_number`, `resident_type`, `occupancy_start`, `occupancy_end`) VALUES (5, 7, 'B-203', 'Owner', '2026-01-03', NULL);
INSERT INTO `residents` (`id`, `user_id`, `flat_number`, `resident_type`, `occupancy_start`, `occupancy_end`) VALUES (6, 8, 'A-3', 'Owner', '2026-01-03', NULL);
INSERT INTO `residents` (`id`, `user_id`, `flat_number`, `resident_type`, `occupancy_start`, `occupancy_end`) VALUES (7, 9, 'B-14', 'Owner', '2026-01-03', NULL);
INSERT INTO `residents` (`id`, `user_id`, `flat_number`, `resident_type`, `occupancy_start`, `occupancy_end`) VALUES (8, 10, 'A-5', 'Tenant', '2026-01-03', NULL);

-- Create table visitors
DROP TABLE IF EXISTS `visitors`;
CREATE TABLE `visitors` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `resident_id` INTEGER,
  `visitor_name` TEXT NOT NULL,
  `contact` TEXT,
  `visit_purpose` TEXT,
  `visit_date` DATE,
  `visit_time` TIME,
  `status` TEXT,
  `exit_time` TIME
);

-- Insert data into visitors
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (1, 1, 'Venisha', '1234567890', 'Personal', '2025-12-19', '16:16:30', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (2, 2, 'Johan', '5678943210', 'Business', '2025-12-27', '04:59:44', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (3, 2, 'Johan', '5678943210', 'Personal', '2025-12-27', '05:09:27', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (4, 2, 'Johan', '5678943210', 'Personal', '2025-12-27', '05:59:14', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (5, 2, 'Johan', '5678943210', 'Personal', '2025-12-27', '06:03:25', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (6, 2, 'Johan', '9876543210', 'Business', '2025-12-27', '06:17:34', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (7, 2, 'Johan', '5678943210', 'Delivery', '2025-12-27', '11:36:45', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (8, 2, 'Johan', '5678943210', 'Delivery', '2025-12-27', '11:36:45', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (9, 2, 'Desai gunjan', '9876543210', 'Delivery', '2025-12-27', '12:09:38', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (10, 2, 'xyz', '5678943210', 'Delivery', '2025-12-31', '12:25:02', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (11, 6, 'abv', '8796456457', 'Delivery', '2026-01-03', '08:32:45', 'Pending', NULL);
INSERT INTO `visitors` (`id`, `resident_id`, `visitor_name`, `contact`, `visit_purpose`, `visit_date`, `visit_time`, `status`, `exit_time`) VALUES (12, 1, 'ram', '8958878964', 'Service', '2026-01-16', '08:38:47', 'Pending', NULL);

-- Create table deliveries
DROP TABLE IF EXISTS `deliveries`;
CREATE TABLE `deliveries` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `resident_id` INTEGER,
  `delivery_company` TEXT NOT NULL,
  `delivery_item` TEXT,
  `arrival_time` TIMESTAMP,
  `status` TEXT,
  `collected_time` TIMESTAMP
);

-- Insert data into deliveries
INSERT INTO `deliveries` (`id`, `resident_id`, `delivery_company`, `delivery_item`, `arrival_time`, `status`, `collected_time`) VALUES (1, 1, 'Amazon', 'Books', '2025-12-19 16:33:16', 'Pending', NULL);
INSERT INTO `deliveries` (`id`, `resident_id`, `delivery_company`, `delivery_item`, `arrival_time`, `status`, `collected_time`) VALUES (2, 2, 'Flipcard', 'Books', '2025-12-27 05:00:23', 'Pending', NULL);
INSERT INTO `deliveries` (`id`, `resident_id`, `delivery_company`, `delivery_item`, `arrival_time`, `status`, `collected_time`) VALUES (3, 2, 'Amazon', 'Mobile', '2025-12-27 12:10:18', 'Pending', NULL);
INSERT INTO `deliveries` (`id`, `resident_id`, `delivery_company`, `delivery_item`, `arrival_time`, `status`, `collected_time`) VALUES (4, 2, 'amazon', 'book', '2026-01-01 11:01:47', 'Pending', NULL);

-- Create table parking
DROP TABLE IF EXISTS `parking`;
CREATE TABLE `parking` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `resident_id` INTEGER,
  `slot_number` TEXT NOT NULL,
  `slot_type` TEXT NOT NULL,
  `vehicle_number` TEXT,
  `status` TEXT
);

-- Insert data into parking
INSERT INTO `parking` (`id`, `resident_id`, `slot_number`, `slot_type`, `vehicle_number`, `status`) VALUES (1, 2, 'P-101', 'Fixed', 'TN09GH3456', 'Occupied');
INSERT INTO `parking` (`id`, `resident_id`, `slot_number`, `slot_type`, `vehicle_number`, `status`) VALUES (2, 3, 'P-202', 'Shared', NULL, 'Available');

-- Create table complaints
DROP TABLE IF EXISTS `complaints`;
CREATE TABLE `complaints` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `resident_id` INTEGER,
  `category` TEXT NOT NULL,
  `description` TEXT NOT NULL,
  `complaint_date` DATE,
  `status` TEXT,
  `assigned_to` TEXT,
  `resolution_date` DATE,
  `priority` TEXT,
  `ai_score` REAL
);

-- Insert data into complaints
INSERT INTO `complaints` (`id`, `resident_id`, `category`, `description`, `complaint_date`, `status`, `assigned_to`, `resolution_date`, `priority`, `ai_score`) VALUES (2, 2, 'Noise', 'society noise to very distrabing', '2025-12-27', 'Open', NULL, NULL, 'Medium', 14.0);

-- Create table payments
DROP TABLE IF EXISTS `payments`;
CREATE TABLE `payments` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `resident_id` INTEGER,
  `amount` REAL NOT NULL,
  `payment_date` DATE,
  `payment_method` TEXT,
  `receipt_number` TEXT,
  `status` TEXT,
  `description` TEXT
);

-- Insert data into payments
INSERT INTO `payments` (`id`, `resident_id`, `amount`, `payment_date`, `payment_method`, `receipt_number`, `status`, `description`) VALUES (1, 1, 5000.0, '2025-12-19', NULL, '202512-3496', 'Pending', NULL);
INSERT INTO `payments` (`id`, `resident_id`, `amount`, `payment_date`, `payment_method`, `receipt_number`, `status`, `description`) VALUES (2, 1, 5000.0, '2025-12-19', NULL, '202512-4289', 'Paid', NULL);
INSERT INTO `payments` (`id`, `resident_id`, `amount`, `payment_date`, `payment_method`, `receipt_number`, `status`, `description`) VALUES (3, 1, 5000.0, '2025-12-19', 'Credit Card', '202512-4570', 'Paid', NULL);
INSERT INTO `payments` (`id`, `resident_id`, `amount`, `payment_date`, `payment_method`, `receipt_number`, `status`, `description`) VALUES (5, 2, 5000.0, '2025-12-27', NULL, '202512-5548', 'Pending', NULL);
INSERT INTO `payments` (`id`, `resident_id`, `amount`, `payment_date`, `payment_method`, `receipt_number`, `status`, `description`) VALUES (7, 2, 5000.0, '2025-12-27', NULL, '202512-5784', 'Pending', NULL);
INSERT INTO `payments` (`id`, `resident_id`, `amount`, `payment_date`, `payment_method`, `receipt_number`, `status`, `description`) VALUES (8, 2, 5000.0, '2025-12-27', 'Net Banking', '202512-5824', 'Paid', NULL);

-- Create table charity
DROP TABLE IF EXISTS `charity`;
CREATE TABLE `charity` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `resident_id` INTEGER,
  `item_type` TEXT NOT NULL,
  `quantity` INTEGER,
  `description` TEXT,
  `status` TEXT,
  `pickup_date` DATE
);

-- Insert data into charity
INSERT INTO `charity` (`id`, `resident_id`, `item_type`, `quantity`, `description`, `status`, `pickup_date`) VALUES (1, 2, 'Clothes', 10, 'old clothes charity', 'Pending', NULL);

-- Create table notices
DROP TABLE IF EXISTS `notices`;
CREATE TABLE `notices` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `admin_id` INTEGER,
  `title` TEXT NOT NULL,
  `content` TEXT NOT NULL,
  `notice_date` DATE,
  `priority` TEXT
);

-- Create table emergency_logs
DROP TABLE IF EXISTS `emergency_logs`;
CREATE TABLE `emergency_logs` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `resident_id` INTEGER,
  `emergency_type` TEXT NOT NULL,
  `description` TEXT,
  `log_time` TIMESTAMP,
  `action_taken` TEXT,
  `resolved` BOOLEAN
);

-- Insert data into emergency_logs
INSERT INTO `emergency_logs` (`id`, `resident_id`, `emergency_type`, `description`, `log_time`, `action_taken`, `resolved`) VALUES (1, 2, 'Medical', 'Emergency call for Medical', '2025-12-27 13:12:49', NULL, 0);
INSERT INTO `emergency_logs` (`id`, `resident_id`, `emergency_type`, `description`, `log_time`, `action_taken`, `resolved`) VALUES (2, 2, 'Medical', 'Emergency call for Medical', '2025-12-27 17:51:42', NULL, 0);

-- Create table settings
DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `society_name` TEXT NOT NULL,
  `society_address` TEXT NOT NULL,
  `society_phone` TEXT,
  `society_email` TEXT,
  `society_website` TEXT
);

-- Insert data into settings
INSERT INTO `settings` (`id`, `society_name`, `society_address`, `society_phone`, `society_email`, `society_website`) VALUES (1, 'SOCIETY MANAGEMENT SYSTEM', '123 Society Address, City, State - 123456', '+91 9876543210', 'info@society.com', NULL);

-- Create table blocks
DROP TABLE IF EXISTS `blocks`;
CREATE TABLE `blocks` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `block_name` TEXT NOT NULL
);

-- Insert data into blocks
INSERT INTO `blocks` (`id`, `block_name`) VALUES (1, 'A');
INSERT INTO `blocks` (`id`, `block_name`) VALUES (2, 'B');

-- Create table flats
DROP TABLE IF EXISTS `flats`;
CREATE TABLE `flats` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `block_id` INTEGER,
  `flat_number` TEXT NOT NULL,
  `status` TEXT,
  `owner_name` TEXT
);

-- Insert data into flats
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (1, 1, 'A-1', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (2, 1, 'A-2', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (3, 1, 'A-3', 'Occupied', 'Anjali Thakur');
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (4, 1, 'A-4', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (5, 1, 'A-5', 'Occupied', 'Avniisha');
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (6, 1, 'A-6', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (7, 1, 'A-7', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (8, 1, 'A-8', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (9, 1, 'A-9', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (10, 1, 'A-10', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (11, 1, 'A-11', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (12, 1, 'A-12', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (13, 2, 'B-11', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (14, 2, 'B-12', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (15, 2, 'B-13', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (16, 2, 'B-14', 'Occupied', 'Venisha');
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (17, 2, 'B-15', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (18, 2, 'B-16', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (19, 2, 'B-17', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (20, 2, 'B-18', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (21, 2, 'B-19', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (22, 2, 'B-20', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (23, 2, 'B-21', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (24, 2, 'B-22', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (25, 2, 'B-23', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (26, 2, 'B-24', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (27, 2, 'B-25', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (28, 2, 'B-12', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (29, 2, 'B-13', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (30, 2, 'B-14', 'Occupied', 'Venisha');
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (31, 2, 'B-15', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (32, 2, 'B-16', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (33, 2, 'B-17', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (34, 2, 'B-18', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (35, 2, 'B-19', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (36, 2, 'B-20', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (37, 2, 'B-21', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (38, 2, 'B-22', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (39, 2, 'B-23', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (40, 2, 'B-24', 'Vacant', NULL);
INSERT INTO `flats` (`id`, `block_id`, `flat_number`, `status`, `owner_name`) VALUES (41, 2, 'B-25', 'Vacant', NULL);

-- Create table emergency_contacts
DROP TABLE IF EXISTS `emergency_contacts`;
CREATE TABLE `emergency_contacts` (
  `id` INT AUTO_INCREMENT  PRIMARY KEY,
  `name` TEXT NOT NULL,
  `contact_type` TEXT NOT NULL,
  `phone_number` TEXT NOT NULL,
  `priority` INTEGER,
  `is_active` BOOLEAN
);

-- Insert data into emergency_contacts
INSERT INTO `emergency_contacts` (`id`, `name`, `contact_type`, `phone_number`, `priority`, `is_active`) VALUES (1, 'Admin Emergency', 'Admin', '9876543210', 1, 1);
INSERT INTO `emergency_contacts` (`id`, `name`, `contact_type`, `phone_number`, `priority`, `is_active`) VALUES (2, 'Security Guard', 'Security', '9876543211', 2, 1);
INSERT INTO `emergency_contacts` (`id`, `name`, `contact_type`, `phone_number`, `priority`, `is_active`) VALUES (3, 'Ambulance Service', 'Ambulance', '108', 3, 1);
INSERT INTO `emergency_contacts` (`id`, `name`, `contact_type`, `phone_number`, `priority`, `is_active`) VALUES (4, 'Fire Department', 'Fire', '101', 4, 1);
INSERT INTO `emergency_contacts` (`id`, `name`, `contact_type`, `phone_number`, `priority`, `is_active`) VALUES (5, 'Police Department', 'Police', '100', 5, 1);
INSERT INTO `emergency_contacts` (`id`, `name`, `contact_type`, `phone_number`, `priority`, `is_active`) VALUES (6, 'Maintenance', 'Maintenance', '9876543212', 6, 1);
INSERT INTO `emergency_contacts` (`id`, `name`, `contact_type`, `phone_number`, `priority`, `is_active`) VALUES (7, 'Nearby Doctor', 'Doctor', '9876543213', 7, 1);

