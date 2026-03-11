

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import os
import time
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from database import get_db as get_database_db, get_cursor, init_db as init_mysql_db

app = Flask(__name__)
app.secret_key = 'society_management_secret_key'

# Configure upload folders
UPLOAD_FOLDER = 'static/images/events'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure profile picture upload folder
PROFILE_FOLDER = 'static/uploads/profiles'
app.config['PROFILE_FOLDER'] = PROFILE_FOLDER

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/images/visitor_photos', exist_ok=True)
os.makedirs(app.config['PROFILE_FOLDER'], exist_ok=True)

# Get society settings
# Database connection helper function
def get_db():
    # Using the database module's get_db function
    return get_database_db()

def get_society_settings():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT society_name, society_address, society_phone, society_email FROM settings WHERE id = 1")
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        return {
            'society_name': result['society_name'],
            'society_address': result['society_address'],
            'society_phone': result['society_phone'],
            'society_email': result['society_email']
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
    # Using the database module's init_db function
    init_mysql_db()

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
    
    db = get_db()
    cursor = db.cursor()
    
    # First, try to authenticate with email
    cursor.execute("SELECT * FROM users WHERE email=%s AND password= %s", (username, password))
    user = cursor.fetchone()
    
    # If not found with email, try to authenticate with flat number
    if not user:
        # Find user by flat number
        cursor.execute("""SELECT u.* FROM users u 
                    JOIN residents r ON u.id = r.user_id 
                    WHERE r.flat_number=%s AND u.password= %s""", (username, password))
        user = cursor.fetchone()
    
    cursor.close()
    
    if user:
        session['user_id'] = user['id']
        session['name'] = user['name']
        # Get user role from the users table
        session['role'] = user['role']
        # Get user profile picture
        # Handle case where profile_pic column might not exist in some rows
        if 'profile_pic' in user and user['profile_pic']:
            session['profile_pic'] = user['profile_pic']
        else:
            session['profile_pic'] = 'default.png'
        
        if user['role'] == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif user['role'] == 'Owner':
            return redirect(url_for('resident_dashboard'))
        elif user['role'] == 'Tenant':
            return redirect(url_for('tenant_dashboard'))
        elif user['role'] == 'Security':
            return redirect(url_for('security_dashboard'))
    else:
        # Check if user exists but password is wrong
        db = get_db()
        cursor = db.cursor()
        
        # First, try to find user with email
        cursor.execute("SELECT * FROM users WHERE email=%s", (username,))
        user_exists = cursor.fetchone()
        
        # If not found with email, try to find via flat number
        if not user_exists:
            cursor.execute("SELECT u.* FROM users u \n                        JOIN residents r ON u.id = r.user_id \n                        WHERE r.flat_number=%s", (username,))
            user_exists = cursor.fetchone()
        
        cursor.close()
        
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
    db = get_db()
    cursor = db.cursor()
    
    # Get all blocks for dropdown
    cursor.execute("SELECT * FROM blocks")
    blocks = cursor.fetchall()
    
    cursor.close()
    
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
                filepath = os.path.join(app.config['PROFILE_FOLDER'], unique_filename)
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
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'success': False, 'message': 'A user with this email already exists'})
    
    # Check if flat exists in flats table - flat_number from form is already complete (e.g., A-1, A-2)
    cursor.execute("SELECT id, status FROM flats WHERE flat_number = %s", (flat_number,))
    flat_result = cursor.fetchone()
    if not flat_result:
        cursor.close()
        return jsonify({'success': False, 'message': 'Flat number does not exist in the society records'})
    
    # Check if flat is vacant before allowing registration
    flat_id, flat_status = flat_result
    if flat_status != 'Vacant':
        cursor.close()
        return jsonify({'success': False, 'message': 'Selected flat is not available for registration. Please select a vacant flat.'})
    
    # Double-check if flat is already registered in residents table
    cursor.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'success': False, 'message': 'This flat is already registered'})
    
    try:
        # Insert user
        cursor.execute("INSERT INTO users (name, email, password, role, phone, profile_pic) VALUES (%s, %s, %s, %s, %s, %s)",
                  (name, email, password, user_type, mobile_digits, profile_pic))
        cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = cursor.fetchone()['LAST_INSERT_ID()']
        
        # Insert resident
        cursor.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                  (user_id, flat_number, user_type, datetime.now().strftime('%Y-%m-%d')))
        
        # Update flat status to Occupied
        cursor.execute("UPDATE flats SET status = 'Occupied', owner_name = %s WHERE flat_number = %s",
                  (name, flat_number))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Registration successful. You can now login.'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to register: ' + str(e)})

# Get flats for a specific block (AJAX endpoint)
@app.route('/get_flats/<int:block_id>')
def get_flats(block_id):
    db = get_db()
    cursor = db.cursor()
    
    # Get vacant flats for the selected block
    cursor.execute("SELECT flat_number FROM flats WHERE block_id = %s AND status = 'Vacant'", (block_id,))
    flats = cursor.fetchall()
    
    cursor.close()
    
    return jsonify([flat['flat_number'] for flat in flats])

# Admin blocks management
@app.route('/admin/blocks')
def admin_blocks():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get all blocks
    cursor.execute("SELECT * FROM blocks ORDER BY block_name")
    blocks = cursor.fetchall()
    
    # Get flat count per block
    cursor.execute("""SELECT b.block_name, COUNT(f.id) as total_flats, 
                    SUM(CASE WHEN f.status = 'Vacant' THEN 1 ELSE 0 END) as vacant_flats
                    FROM blocks b 
                    LEFT JOIN flats f ON b.id = f.block_id 
                    GROUP BY b.id, b.block_name""")
    block_stats = cursor.fetchall()
    
    cursor.close()
    
    return render_template('admin/blocks.html', blocks=blocks, block_stats=block_stats)

# Admin add block
@app.route('/admin/blocks/add', methods=['POST'])
def admin_add_block():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    block_name = request.form.get('block_name', '').strip().upper()
    
    if not block_name:
        return jsonify({'success': False, 'message': 'Block name is required'})
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("INSERT INTO blocks (block_name) VALUES (%s)", (block_name,))
        db.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Block added successfully'})
    except Exception:
        cursor.close()
        return jsonify({'success': False, 'message': 'Block already exists'})
    except Exception as e:
        cursor.close()
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
    
    db = get_db()
    cursor = db.cursor()
    
    # Get block name
    cursor.execute("SELECT block_name FROM blocks WHERE id = %s", (block_id,))
    block = cursor.fetchone()
    
    if not block:
        cursor.close()
        return jsonify({'success': False, 'message': 'Block not found'})
    
    block_name = block['block_name']
    
    try:
        # Add flats in range
        for flat_num in range(from_flat_num, to_flat_num + 1):
            flat_number = f"{block_name}-{flat_num}"
            cursor.execute("INSERT INTO flats (block_id, flat_number) VALUES (%s, %s)", (block_id, flat_number))
        
        db.commit()
        cursor.close()
        return jsonify({'success': True, 'message': f'Flats {from_flat_num} to {to_flat_num} added successfully to Block {block_name}'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to add flats: ' + str(e)})

# Admin get all flats with status
@app.route('/admin/flats')
def admin_flats():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get all flats with block information
    cursor.execute("""SELECT f.id, b.block_name, f.flat_number, f.status, f.owner_name 
                    FROM flats f 
                    JOIN blocks b ON f.block_id = b.id 
                    ORDER BY b.block_name, f.flat_number""")
    flats = cursor.fetchall()
    
    cursor.close()
    
    return render_template('admin/flats.html', flats=flats)

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user details
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name, email, phone, profile_pic FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    
    if not user:
        return redirect(url_for('login'))
    
    user_data = {
        'name': user['name'],
        'email': user['email'],
        'phone': user['phone'],
        'profile_pic': user['profile_pic'] or 'default.png'
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
                filepath = os.path.join(app.config['PROFILE_FOLDER'], unique_filename)
                file.save(filepath)
                new_profile_pic = unique_filename
            else:
                return jsonify({'success': False, 'message': 'Invalid file type. Only JPG, PNG, and GIF files are allowed.'})
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        if new_profile_pic:
            # Update with new profile picture
            cursor.execute("UPDATE users SET name = %s, email = %s, phone = %s, profile_pic = %s WHERE id = %s",
                      (name, email, phone, new_profile_pic, session['user_id']))
            session['profile_pic'] = new_profile_pic
        else:
            # Update without changing profile picture
            cursor.execute("UPDATE users SET name = %s, email = %s, phone = %s WHERE id = %s",
                      (name, email, phone, session['user_id']))
        
        db.commit()
        cursor.close()
        
        # Update session data
        session['name'] = name
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to update profile: ' + str(e)})


# Admin residents list
@app.route('/admin/residents')
def admin_residents():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""SELECT u.name, u.email, u.phone, r.flat_number, r.resident_type 
                 FROM users u 
                 JOIN residents r ON u.id = r.user_id""")
    residents = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/residents.html', residents=residents)

# Admin complaints
@app.route('/admin/complaints')
def admin_complaints():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""SELECT c.id, u.name, r.flat_number, c.category, c.description, c.status, c.complaint_date, c.priority, c.ai_score
                 FROM complaints c 
                 JOIN residents r ON c.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY c.priority DESC, c.complaint_date DESC""")
    complaints = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/complaints.html', complaints=complaints)

# Admin assign complaint
@app.route('/admin/complaints/assign', methods=['POST'])
def admin_assign_complaint():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    complaint_id = request.form['complaint_id']
    assigned_to = request.form['assigned_to']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE complaints SET status = 'Assigned', assigned_to = %s WHERE id = %s",
              (assigned_to, complaint_id))
    db.commit()
    cursor.close()
    
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

    db = get_db()
    cursor = db.cursor()

    # Resolve resident_id using flat_number first, then resident name
    resident_id = None
    try:
        if flat_number:
            cursor.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
            row = cursor.fetchone()
            if row:
                resident_id = row['id']

        if not resident_id and resident_input:
            # Try to match by exact (case-insensitive) user name
            cursor.execute("SELECT r.id FROM residents r JOIN users u ON r.user_id = u.id WHERE lower(u.name) = %s", (resident_input.lower(),))
            row = cursor.fetchone()
            if row:
                resident_id = row['id']

        if not resident_id:
            cursor.close()
            return jsonify({'success': False, 'message': 'Resident not found. Please provide a valid flat number or exact resident name.'})

        # AI Priority Classification
        from ai_priority import classify_priority
        priority, ai_score = classify_priority(description)
        
        # Insert complaint with priority
        cursor.execute("INSERT INTO complaints (resident_id, category, description, status, priority, ai_score) VALUES (%s, %s, %s, 'Open', %s, %s)",
                  (resident_id, category, description, priority, ai_score))
        db.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        complaint_id = cursor.fetchone()['LAST_INSERT_ID()']
        cursor.close()

        return jsonify({'success': True, 'message': 'Complaint added successfully', 'complaint_id': complaint_id})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to add complaint: ' + str(e)})

# Admin resolve complaint
@app.route('/admin/complaints/resolve', methods=['POST'])
def admin_resolve_complaint():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    complaint_id = request.form['complaint_id']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE complaints SET status = 'Resolved', resolution_date = CURRENT_DATE WHERE id = %s",
              (complaint_id,))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Complaint resolved successfully'})

# Admin maintenance bills
@app.route('/admin/maintenance-bills')
def admin_maintenance_bills():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    # Update late fines for all unpaid bills
    update_late_fines()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""SELECT mb.id, u.name, mb.flat_number, mb.amount, mb.due_date, mb.status, mb.late_fine, mb.created_date
                 FROM maintenance_bills mb
                 JOIN residents r ON mb.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY mb.created_date DESC""")
    bills = cursor.fetchall()
    
    # Get all residents for the dropdown
    cursor.execute("""SELECT r.id, u.name, r.flat_number 
                 FROM residents r 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY u.name""")
    residents = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/maintenance_bills.html', bills=bills, residents=residents)


# Admin maintenance payments
@app.route('/admin/payments')
def admin_payments():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""SELECT p.id, u.name, r.flat_number, p.amount, p.payment_date, p.payment_method, p.receipt_number, p.status 
                 FROM payments p 
                 JOIN residents r ON p.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY p.payment_date DESC""")
    payments = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/payments.html', payments=payments)

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
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT flat_number FROM residents WHERE id = %s", (resident_id,))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    flat_number = resident['flat_number']
    
    try:
        # Insert maintenance bill (obligation)
        cursor.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                  (resident_id, flat_number, amount, due_date, 'Unpaid'))
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Maintenance bill generated successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
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
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT flat_number FROM residents WHERE id = %s", (resident_id,))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    flat_number = resident['flat_number']
    
    try:
        # Insert maintenance bill
        cursor.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                  (resident_id, flat_number, amount, due_date, 'Unpaid'))
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Maintenance bill generated successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
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
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, flat_number FROM residents")
    residents = cursor.fetchall()
    
    if not residents:
        cursor.close()
        return jsonify({'success': False, 'message': 'No residents found'})
    
    success_count = 0
    try:
        for resident in residents:
            resident_id = resident['id']
            flat_number = resident['flat_number']
            
            # Check if a bill already exists for this resident for this month
            from datetime import datetime
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute("SELECT id FROM maintenance_bills WHERE resident_id = %s AND DATE_FORMAT(created_date, '%%Y-%%m') = %s", (resident_id, current_month))
            existing_bill = cursor.fetchone()
            
            if not existing_bill:
                # Insert maintenance bill for this resident
                cursor.execute("INSERT INTO maintenance_bills (resident_id, flat_number, amount, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                          (resident_id, flat_number, amount, due_date, 'Unpaid'))
                success_count += 1
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': f'Monthly bills generated successfully for {success_count} residents'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to generate bills: ' + str(e)})


# Function to calculate late fine
from datetime import datetime, date

def calculate_late_fine(due_date_str, rate_per_day=50.0):
    """Calculate late fine based on days overdue"""
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = date.today()
        
        if today > due_date:
            days_overdue = (today - due_date).days
            late_fine = days_overdue * rate_per_day
            return late_fine, days_overdue
        else:
            return 0.0, 0
    except ValueError:
        return 0.0, 0


# Function to update late fines for all unpaid bills
def update_late_fines():
    """Update late fines for all unpaid bills"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get all unpaid bills
        cursor.execute("SELECT id, due_date FROM maintenance_bills WHERE status = 'Unpaid'")
        unpaid_bills = cursor.fetchall()
        
        for bill in unpaid_bills:
            bill_id = bill['id']
            due_date = bill['due_date']
            
            late_fine, days_overdue = calculate_late_fine(due_date)
            
            # Update the late fine for this bill
            cursor.execute("UPDATE maintenance_bills SET late_fine = %s WHERE id = %s", (late_fine, bill_id))
        
        db.commit()
        cursor.close()
        return True
    except Exception as e:
        db.rollback()
        cursor.close()
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
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # If marking as Paid, set late fine to 0
        if status == 'Paid':
            cursor.execute("UPDATE maintenance_bills SET status = %s, late_fine = 0 WHERE id = %s", (status, bill_id))
        else:
            # If marking as Unpaid, recalculate late fine
            cursor.execute("SELECT due_date FROM maintenance_bills WHERE id = %s", (bill_id,))
            result = cursor.fetchone()
            if result:
                due_date = result['due_date']
                late_fine, _ = calculate_late_fine(due_date)
                cursor.execute("UPDATE maintenance_bills SET status = %s, late_fine = %s WHERE id = %s", (status, late_fine, bill_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({'success': False, 'message': 'Bill not found'})
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': f'Bill status updated to {status} successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to update bill status: ' + str(e)})

# Admin mark payment as paid
@app.route('/admin/payments/mark-paid', methods=['POST'])
def admin_mark_paid():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    payment_id = request.form['payment_id']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE payments SET status = 'Paid', payment_date = CURRENT_DATE WHERE id = %s",
              (payment_id,))
    db.commit()
    cursor.close()
    
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

# Admin view payment receipt
@app.route('/admin/payments/receipt/<int:payment_id>')
def admin_view_receipt(payment_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""SELECT p.id, u.name, r.flat_number, p.amount, p.payment_date, p.payment_method, p.receipt_number, p.status 
                 FROM payments p 
                 JOIN residents r ON p.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 WHERE p.id = %s""", (payment_id,))
    payment = cursor.fetchone()
    cursor.close()
    
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
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""SELECT pk.slot_number, pk.slot_type, u.name, r.flat_number, pk.vehicle_number, pk.status 
                 FROM parking pk 
                 LEFT JOIN residents r ON pk.resident_id = r.id 
                 LEFT JOIN users u ON r.user_id = u.id 
                 ORDER BY pk.slot_number""")
    parking_slots = cursor.fetchall()

    # also fetch residents for the "Assign to" selector in the add modal
    cursor.execute("""SELECT r.id, u.name, r.flat_number 
                 FROM residents r 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY r.flat_number""")
    residents = cursor.fetchall()
    cursor.close()

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
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""INSERT INTO settings (id, society_name, society_address, society_phone, society_email) 
                  VALUES (1, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE 
                  society_name = VALUES(society_name), 
                  society_address = VALUES(society_address), 
                  society_phone = VALUES(society_phone), 
                  society_email = VALUES(society_email)""",
              (society_name, society_address, society_phone, society_email))
    db.commit()
    cursor.close()
    
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

    db = get_db()
    cursor = db.cursor()
    try:
        # determine resident_id if provided via resident_id or flat_number
        resolved_resident_id = None
        if resident_id:
            try:
                rid = int(resident_id)
                cursor.execute("SELECT id FROM residents WHERE id = %s", (rid,))
                if cursor.fetchone():
                    resolved_resident_id = rid
            except ValueError:
                resolved_resident_id = None

        if not resolved_resident_id and flat_number:
            cursor.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
            row = cursor.fetchone()
            if row:
                resolved_resident_id = row['id']

        # insert parking slot; resident_id may be NULL
        if resolved_resident_id:
            cursor.execute("INSERT INTO parking (resident_id, slot_number, slot_type, vehicle_number, status) VALUES (%s, %s, %s, %s, %s)",
                      (resolved_resident_id, slot_number, slot_type, vehicle_number.upper() if vehicle_number else None, status))
        else:
            cursor.execute("INSERT INTO parking (slot_number, slot_type, vehicle_number, status) VALUES (%s, %s, %s, %s)",
                      (slot_number, slot_type, vehicle_number.upper() if vehicle_number else None, status))

        db.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Parking slot added successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
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

    db = get_db()
    cursor = db.cursor()
    try:
        # find resident primary id
        cursor.execute("SELECT id FROM residents WHERE id = %s", (resident_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'success': False, 'message': 'Resident not found'})

        cursor.execute("UPDATE parking SET resident_id = %s, status = 'Occupied' WHERE slot_number = %s",
                  (resident_id, slot_number))
        db.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Slot assigned to resident'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to assign: ' + str(e)})


# Admin unassign parking slot
@app.route('/admin/parking/unassign', methods=['POST'])
def admin_unassign_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    slot_number = request.form.get('slot_number', '').strip()
    if not slot_number:
        return jsonify({'success': False, 'message': 'Slot number required'})

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE parking SET resident_id = NULL, vehicle_number = NULL, status = 'Available' WHERE slot_number = %s",
                  (slot_number,))
        db.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Slot unassigned successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
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

    db = get_db()
    cursor = db.cursor()
    try:
        if vehicle_number and status:
            cursor.execute("UPDATE parking SET vehicle_number = %s, status = %s WHERE slot_number = %s",
                      (vehicle_number.upper(), status, slot_number))
        elif vehicle_number:
            cursor.execute("UPDATE parking SET vehicle_number = %s WHERE slot_number = %s",
                      (vehicle_number.upper(), slot_number))
        elif status:
            cursor.execute("UPDATE parking SET status = %s WHERE slot_number = %s",
                      (status, slot_number))
        else:
            cursor.close()
            return jsonify({'success': False, 'message': 'No update fields provided'})

        db.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Slot updated successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
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

    db = get_db()
    cursor = db.cursor()

    # verify slot exists
    cursor.execute("SELECT id FROM parking WHERE slot_number = %s", (slot_number,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        return jsonify({'success': False, 'message': 'Parking slot not found'})

    # resolve resident if provided
    resolved_resident_id = None
    if resident_id:
        try:
            rid = int(resident_id)
            cursor.execute("SELECT id FROM residents WHERE id = %s", (rid,))
            if cursor.fetchone():
                resolved_resident_id = rid
        except ValueError:
            resolved_resident_id = None

    if not resolved_resident_id and flat_number:
        cursor.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
        r = cursor.fetchone()
        if r:
            resolved_resident_id = r['id']

    try:
        set_parts = []
        params = []

        if new_slot_number:
            set_parts.append('slot_number = ?')
            params.append(new_slot_number)
        if slot_type:
            set_parts.append('slot_type = ?')
            params.append(slot_type)
        if vehicle_number:
            set_parts.append('vehicle_number = ?')
            params.append(vehicle_number.upper())
        if status:
            set_parts.append('status = ?')
            params.append(status)

        if unassign == '1':
            # explicit unassign request
            set_parts.append('resident_id = NULL')
            set_parts.append('vehicle_number = NULL')
            set_parts.append("status = 'Available'")
        elif resolved_resident_id:
            set_parts.append('resident_id = ?')
            params.append(resolved_resident_id)

        if not set_parts:
            cursor.close()
            return jsonify({'success': False, 'message': 'No fields to update'})

        sql = f"UPDATE parking SET {', '.join(set_parts)} WHERE slot_number = %s"
        params.append(slot_number)
        cursor.execute(sql, tuple(params))
        db.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Parking slot updated successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to edit slot: ' + str(e)})


# Admin delete parking slot
@app.route('/admin/parking/delete', methods=['POST'])
def admin_delete_parking():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    slot_number = request.form.get('slot_number', '').strip()
    if not slot_number:
        return jsonify({'success': False, 'message': 'Slot number is required'})

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM parking WHERE slot_number = %s", (slot_number,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'success': False, 'message': 'Parking slot not found'})

        cursor.execute("DELETE FROM parking WHERE slot_number = %s", (slot_number,))
        db.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Parking slot deleted successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to delete slot: ' + str(e)})

# Admin charity
@app.route('/admin/charity')
def admin_charity():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""SELECT ch.id, u.name, r.flat_number, ch.item_type, ch.quantity, ch.description, ch.status, ch.pickup_date 
                 FROM charity ch 
                 JOIN residents r ON ch.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY ch.pickup_date DESC""")
    charity_donations = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/charity.html', charity_donations=charity_donations)

# Admin approve charity donation
@app.route('/admin/charity/approve', methods=['POST'])
def admin_approve_charity():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    donation_id = request.form['donation_id']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE charity SET status = 'Approved' WHERE id = %s",
              (donation_id,))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Donation approved successfully'})

# Admin mark charity donation as picked
@app.route('/admin/charity/pick', methods=['POST'])
def admin_pick_charity():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    donation_id = request.form['donation_id']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE charity SET status = 'Picked', pickup_date = CURRENT_DATE WHERE id = %s",
              (donation_id,))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Donation marked as collected successfully'})

# Admin notices
@app.route('/admin/notices')
def admin_notices():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM notices ORDER BY notice_date DESC")
    notices = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/notices.html', notices=notices)

# Admin delete notice
@app.route('/admin/notices/delete', methods=['POST'])
def admin_delete_notice():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    notice_id = request.form['notice_id']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM notices WHERE id = %s", (notice_id,))
    db.commit()
    cursor.close()
    
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
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE notices SET title = %s, content = %s, priority = %s WHERE id = %s",
              (title, content, priority, notice_id))
    db.commit()
    cursor.close()
    
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
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO notices (admin_id, title, content, priority) VALUES (%s, %s, %s, %s)",
              (session['user_id'], title, content, priority))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Notice added successfully'})

# Admin reports
@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get daily visitor counts
    cursor.execute("""SELECT visit_date, COUNT(*) as visitor_count 
                 FROM visitors 
                 GROUP BY visit_date 
                 ORDER BY visit_date ASC 
                 LIMIT 30""")
    visitor_data = cursor.fetchall()
    
    # Get daily complaint counts
    cursor.execute("""SELECT complaint_date, COUNT(*) as complaint_count 
                 FROM complaints 
                 GROUP BY complaint_date 
                 ORDER BY complaint_date ASC 
                 LIMIT 30""")
    complaint_data = cursor.fetchall()
    
    # Get daily delivery counts
    cursor.execute("""SELECT DATE(arrival_time) as delivery_date, COUNT(*) as delivery_count 
                 FROM deliveries 
                 GROUP BY DATE(arrival_time) 
                 ORDER BY delivery_date ASC 
                 LIMIT 30""")
    delivery_data = cursor.fetchall()
    
    # Get monthly maintenance collection
    cursor.execute("""SELECT DATE_FORMAT(payment_date, '%Y-%m') as payment_month, SUM(amount) as total_amount 
                 FROM payments 
                 WHERE status = 'Paid' 
                 GROUP BY DATE_FORMAT(payment_date, '%Y-%m') 
                 ORDER BY payment_month ASC 
                 LIMIT 12""")
    payment_data = cursor.fetchall()
    
    # Get per-resident totals (useful for per-resident charts)
    cursor.execute("""SELECT r.id, u.name, r.flat_number, COALESCE(SUM(p.amount), 0) as total_paid
                 FROM residents r
                 JOIN users u ON r.user_id = u.id
                 LEFT JOIN payments p ON p.resident_id = r.id AND p.status = 'Paid'
                 GROUP BY r.id, u.name, r.flat_number
                 ORDER BY total_paid DESC
                 LIMIT 50""")
    payment_by_resident = cursor.fetchall()

    cursor.close()

    return render_template('admin/reports.html', 
                          visitor_data=visitor_data, 
                          complaint_data=complaint_data, 
                          delivery_data=delivery_data, 
                          payment_data=payment_data,
                          payment_by_resident=payment_by_resident)


@app.route('/admin/reports/resident/<int:resident_id>')
def admin_reports_resident(resident_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    db = get_db()
    cursor = db.cursor()

    # Get totals per day for the last 30 days for this resident
    cursor.execute("""SELECT DATE(payment_date) as day, COALESCE(SUM(amount),0) as total
                 FROM payments
                 WHERE resident_id = %s AND status = 'Paid' AND DATE(payment_date) >= DATE_SUB(CURDATE(), INTERVAL 29 DAY)
                 GROUP BY day
                 ORDER BY day ASC""", (resident_id,))
    rows = cursor.fetchall()
    cursor.close()

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
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'success': False, 'message': 'A user with this email already exists'})
    
    # Check if flat number already exists
    cursor.execute("SELECT id FROM residents WHERE flat_number = %s", (flat_number,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'success': False, 'message': 'A resident with this flat number already exists'})
    
    try:
        # Insert user
        cursor.execute("INSERT INTO users (name, email, password, role, phone) VALUES (%s, %s, %s, %s, %s)",
                  (name, email, password, resident_type, phone_digits))
        cursor.execute("SELECT LAST_INSERT_ID()")
        result = cursor.fetchone()
        user_id = result['LAST_INSERT_ID()']
        
        # Insert resident
        cursor.execute("INSERT INTO residents (user_id, flat_number, resident_type, occupancy_start) VALUES (%s, %s, %s, %s)",
                  (user_id, flat_number, resident_type, datetime.now().strftime('%Y-%m-%d')))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Resident added successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
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
    
    # Validate phone (should be 10 digits)
    phone_digits = ''.join(filter(str.isdigit, phone))
    if len(phone_digits) != 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit phone number'})
    
    # Validate resident type
    if resident_type not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Invalid resident type'})
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if email already exists for another user
    cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'success': False, 'message': 'A user with this email already exists'})
    
    # Check if flat number already exists for another resident
    cursor.execute("SELECT r.id FROM residents r JOIN users u ON r.user_id = u.id WHERE r.flat_number = %s AND u.id != %s", 
              (flat_number, user_id))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'success': False, 'message': 'A resident with this flat number already exists'})
    
    try:
        # Update user
        cursor.execute("UPDATE users SET name = %s, email = %s, role = %s, phone = %s WHERE id = %s",
                  (name, email, resident_type, phone_digits, user_id))
        
        # Update resident
        cursor.execute("UPDATE residents SET flat_number = %s, resident_type = %s WHERE user_id = %s",
                  (flat_number, resident_type, user_id))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Resident updated successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to update resident: ' + str(e)})

# Admin delete resident
@app.route('/admin/residents/delete', methods=['POST'])
def admin_delete_resident():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Server-side validation
    user_id = request.form.get('user_id', '').strip()
    
    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid user ID'})
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Delete related records first (foreign key constraints)
        cursor.execute("DELETE FROM visitors WHERE resident_id IN (SELECT id FROM residents WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM deliveries WHERE resident_id IN (SELECT id FROM residents WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM parking WHERE resident_id IN (SELECT id FROM residents WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM complaints WHERE resident_id IN (SELECT id FROM residents WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM payments WHERE resident_id IN (SELECT id FROM residents WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM charity WHERE resident_id IN (SELECT id FROM residents WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM emergency_logs WHERE resident_id IN (SELECT id FROM residents WHERE user_id = %s)", (user_id,))
        
        # Delete resident record
        cursor.execute("DELETE FROM residents WHERE user_id = %s", (user_id,))
        
        # Delete user record
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Resident deleted successfully'})
    except Exception as e:
        db.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': 'Failed to delete resident: ' + str(e)})

# Resident dashboard
@app.route('/resident')
def resident_dashboard():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    return render_template('resident/dashboard.html')


# Tenant dashboard
@app.route('/tenant')
def tenant_dashboard():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    return render_template('tenant/dashboard.html')

# Resident visitor registration
@app.route('/resident/visitors')
def resident_visitors():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        # Debug information
        print(f"Resident not found for user_id: {session['user_id']}")
        cursor.execute("SELECT id, user_id FROM residents")
        all_residents = cursor.fetchall()
        print(f"All residents: {all_residents}")
        return redirect(url_for('resident_dashboard'))
    
    resident_id = resident['id']
    
    # Get visitor history
    cursor.execute("SELECT * FROM visitors WHERE resident_id = %s ORDER BY visit_date DESC", (resident_id,))
    visitors = cursor.fetchall()
    cursor.close()
    
    return render_template('resident/visitors.html', visitors=visitors)


# Tenant visitor registration
@app.route('/tenant/visitors')
def tenant_visitors():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return redirect(url_for('tenant_dashboard'))
    
    resident_id = resident['id']
    
    # Get visitor history
    cursor.execute("SELECT * FROM visitors WHERE resident_id = %s ORDER BY visit_date DESC", (resident_id,))
    visitors = cursor.fetchall()
    cursor.close()
    
    return render_template('tenant/visitors.html', visitors=visitors)

# Resident add visitor
@app.route('/resident/visitors/add', methods=['POST'])
def resident_add_visitor():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    visitor_name = request.json.get('visitor_name', '').strip() if request.is_json else request.form.get('visitor_name', '').strip()
    contact = request.json.get('contact', '').strip() if request.is_json else request.form.get('contact', '').strip()
    purpose = request.json.get('purpose', '').strip() if request.is_json else request.form.get('purpose', '').strip()
    
    # Validate required fields
    if not visitor_name or not contact or not purpose:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate contact (should be 10 digits)
    contact_digits = ''.join(filter(str.isdigit, contact))
    if len(contact_digits) != 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit phone number'})
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    cursor.execute("INSERT INTO visitors (resident_id, visitor_name, contact, visit_purpose, status) VALUES (%s, %s, %s, %s, %s)",
              (resident_id, visitor_name, contact_digits, purpose, 'Pending'))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Visitor registered successfully'})


# Tenant add visitor
@app.route('/tenant/visitors/add', methods=['POST'])
def tenant_add_visitor():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    visitor_name = request.json.get('visitor_name', '').strip() if request.is_json else request.form.get('visitor_name', '').strip()
    contact = request.json.get('contact', '').strip() if request.is_json else request.form.get('contact', '').strip()
    purpose = request.json.get('purpose', '').strip() if request.is_json else request.form.get('purpose', '').strip()
    
    # Validate required fields
    if not visitor_name or not contact or not purpose:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate contact (should be 10 digits)
    contact_digits = ''.join(filter(str.isdigit, contact))
    if len(contact_digits) != 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit phone number'})
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    cursor.execute("INSERT INTO visitors (resident_id, visitor_name, contact, visit_purpose, status) VALUES (%s, %s, %s, %s, %s)",
              (resident_id, visitor_name, contact_digits, purpose, 'Pending'))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Visitor registered successfully'})

# Tenant update visitor
@app.route('/tenant/visitors/update/<int:visitor_id>', methods=['POST'])
def tenant_update_visitor(visitor_id):
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    visitor_name = request.json.get('visitor_name', '').strip() if request.is_json else request.form.get('visitor_name', '').strip()
    contact = request.json.get('contact', '').strip() if request.is_json else request.form.get('contact', '').strip()
    purpose = request.json.get('purpose', '').strip() if request.is_json else request.form.get('purpose', '').strip()
    status = request.json.get('status', '').strip() if request.is_json else request.form.get('status', '').strip()
    
    # Validate required fields
    if not visitor_name or not contact or not purpose or not status:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate contact (should be 10 digits)
    contact_digits = ''.join(filter(str.isdigit, contact))
    if len(contact_digits) != 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit phone number'})
    
    # Validate status
    allowed_statuses = ['Pending', 'Approved', 'Rejected', 'Exited']
    if status not in allowed_statuses:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Check if the visitor belongs to this resident
    cursor.execute("SELECT * FROM visitors WHERE id = %s AND resident_id = %s", (visitor_id, resident_id))
    visitor = cursor.fetchone()
    
    if not visitor:
        cursor.close()
        return jsonify({'success': False, 'message': 'Visitor not found or does not belong to you'})
    
    # Update the visitor
    cursor.execute("""UPDATE visitors 
                SET visitor_name = %s, contact = %s, visit_purpose = %s, status = %s 
                WHERE id = %s AND resident_id = %s""",
              (visitor_name, contact_digits, purpose, status, visitor_id, resident_id))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Visitor updated successfully'})

# Tenant delete visitor
@app.route('/tenant/visitors/delete/<int:visitor_id>', methods=['POST'])
def tenant_delete_visitor(visitor_id):
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Check if the visitor belongs to this resident
    cursor.execute("SELECT * FROM visitors WHERE id = %s AND resident_id = %s", (visitor_id, resident_id))
    visitor = cursor.fetchone()
    
    if not visitor:
        cursor.close()
        return jsonify({'success': False, 'message': 'Visitor not found or does not belong to you'})
    
    # Delete the visitor
    cursor.execute("DELETE FROM visitors WHERE id = %s AND resident_id = %s", (visitor_id, resident_id))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Visitor deleted successfully'})

# Resident request delivery
@app.route('/resident/deliveries/request', methods=['POST'])
def resident_request_delivery():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    delivery_company = request.form.get('delivery_company', '').strip()
    delivery_item = request.form.get('delivery_item', '').strip()
    expected_time = request.form.get('expected_time', '').strip()
    
    # Validate required fields
    if not delivery_company or not delivery_item:
        return jsonify({'success': False, 'message': 'Company name and item description are required'})
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    cursor.execute("INSERT INTO deliveries (resident_id, delivery_company, delivery_item) VALUES (%s, %s, %s)",
              (resident_id, delivery_company, delivery_item))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Delivery request submitted successfully'})


# Tenant request delivery
@app.route('/tenant/deliveries/request', methods=['POST'])
def tenant_request_delivery():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    delivery_company = request.form.get('delivery_company', '').strip()
    delivery_item = request.form.get('delivery_item', '').strip()
    expected_time = request.form.get('expected_time', '').strip()
    
    # Validate required fields
    if not delivery_company or not delivery_item:
        return jsonify({'success': False, 'message': 'Company name and item description are required'})
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    cursor.execute("INSERT INTO deliveries (resident_id, delivery_company, delivery_item) VALUES (%s, %s, %s)",
              (resident_id, delivery_company, delivery_item))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Delivery request submitted successfully'})

# Resident deliveries
@app.route('/resident/deliveries')
def resident_deliveries():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return redirect(url_for('resident_dashboard'))
    
    resident_id = resident['id']
    
    # Get delivery history
    cursor.execute("SELECT * FROM deliveries WHERE resident_id = %s ORDER BY arrival_time DESC", (resident_id,))
    deliveries = cursor.fetchall()
    cursor.close()
    
    return render_template('resident/deliveries.html', deliveries=deliveries)


# Tenant deliveries
@app.route('/tenant/deliveries')
def tenant_deliveries():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return redirect(url_for('tenant_dashboard'))
    
    resident_id = resident['id']
    
    # Get delivery history
    cursor.execute("SELECT * FROM deliveries WHERE resident_id = %s ORDER BY arrival_time DESC", (resident_id,))
    deliveries = cursor.fetchall()
    cursor.close()
    
    return render_template('tenant/deliveries.html', deliveries=deliveries)

# Resident complaints
@app.route('/resident/complaints')
def resident_complaints():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return redirect(url_for('resident_dashboard'))
    
    resident_id = resident['id']
    
    # Get complaint history with priority
    cursor.execute("SELECT id, category, description, complaint_date, status, priority, ai_score FROM complaints WHERE resident_id = %s ORDER BY complaint_date DESC", (resident_id,))
    complaints = cursor.fetchall()
    cursor.close()
    
    return render_template('resident/complaints.html', complaints=complaints)


# Tenant complaints
@app.route('/tenant/complaints')
def tenant_complaints():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = cursor.fetchone()
    
    if not resident:
        cursor.close()
        return redirect(url_for('tenant_dashboard'))
    
    resident_id = resident['id']
    
    # Get complaint history with priority
    cursor.execute("SELECT id, category, description, complaint_date, status, priority, ai_score FROM complaints WHERE resident_id = %s ORDER BY complaint_date DESC", (resident_id,))
    complaints = cursor.fetchall()
    cursor.close()
    
    return render_template('tenant/complaints.html', complaints=complaints)

# Tenant submit complaint
@app.route('/tenant/complaints/submit', methods=['POST'])
def tenant_submit_complaint():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    category = request.form.get('category', '').strip()
    description = request.form.get('description', '').strip()
    
    # Validate required fields
    if not category or not description:
        return jsonify({'success': False, 'message': 'Category and description are required'})
    
    # Validate description length
    if len(description) < 10:
        return jsonify({'success': False, 'message': 'Description must be at least 10 characters long'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # AI Priority Classification
    from ai_priority import classify_priority
    priority, ai_score = classify_priority(description)
    
    c.execute("INSERT INTO complaints (resident_id, category, description, priority, ai_score) VALUES (%s, %s, %s, %s, %s)",
              (resident_id, category, description, priority, ai_score))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Complaint submitted successfully'})

# Tenant update complaint
@app.route('/tenant/complaints/update/<int:complaint_id>', methods=['POST'])
def tenant_update_complaint(complaint_id):
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    category = request.form.get('category', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', '').strip()
    
    # Validate required fields
    if not category or not description or not priority:
        return jsonify({'success': False, 'message': 'Category, description, and priority are required'})
    
    # Validate description length
    if len(description) < 10:
        return jsonify({'success': False, 'message': 'Description must be at least 10 characters long'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Check if complaint belongs to this resident
    c.execute("SELECT * FROM complaints WHERE id = %s AND resident_id = %s", (complaint_id, resident_id))
    complaint = c.fetchone()
    
    if not complaint:
        c.close()
        return jsonify({'success': False, 'message': 'Complaint not found or does not belong to you'})
    
    # AI Priority Classification
    from ai_priority import classify_priority
    priority, ai_score = classify_priority(description)
    
    # Update the complaint
    c.execute("UPDATE complaints SET category = %s, description = %s, priority = %s, ai_score = %s WHERE id = %s AND resident_id = %s",
              (category, description, priority, ai_score, complaint_id, resident_id))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Complaint updated successfully'})

# Tenant delete complaint
@app.route('/tenant/complaints/delete/<int:complaint_id>', methods=['POST'])
def tenant_delete_complaint(complaint_id):
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Check if complaint belongs to this resident
    c.execute("SELECT * FROM complaints WHERE id = %s AND resident_id = %s", (complaint_id, resident_id))
    complaint = c.fetchone()
    
    if not complaint:
        c.close()
        return jsonify({'success': False, 'message': 'Complaint not found or does not belong to you'})
    
    # Delete the complaint
    c.execute("DELETE FROM complaints WHERE id = %s AND resident_id = %s", (complaint_id, resident_id))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Complaint deleted successfully'})

# Resident submit complaint
@app.route('/resident/complaints/submit', methods=['POST'])
def resident_submit_complaint():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    category = request.form.get('category', '').strip()
    description = request.form.get('description', '').strip()
    
    # Validate required fields
    if not category or not description:
        return jsonify({'success': False, 'message': 'Category and description are required'})
    
    # Validate description length
    if len(description) < 10:
        return jsonify({'success': False, 'message': 'Description must be at least 10 characters long'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # AI Priority Classification
    from ai_priority import classify_priority
    priority, ai_score = classify_priority(description)
    
    c.execute("INSERT INTO complaints (resident_id, category, description, priority, ai_score) VALUES (%s, %s, %s, %s, %s)",
              (resident_id, category, description, priority, ai_score))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Complaint submitted successfully'})

# Resident maintenance
@app.route('/resident/maintenance')
def resident_maintenance():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return redirect(url_for('resident_dashboard'))
    
    resident_id = resident['id']
    
    # Get payment history
    c.execute("SELECT * FROM payments WHERE resident_id = %s ORDER BY payment_date DESC", (resident_id,))
    payments = c.fetchall()
    
    # Get current bill (simplified)
    c.execute("SELECT SUM(amount) FROM payments WHERE resident_id = %s AND status = 'Paid'", (resident_id,))
    result = c.fetchone()
    total_paid = result['SUM(amount)'] if result and result['SUM(amount)'] else 0
    
    # Simplified current bill calculation
    current_bill = 5000 - total_paid if total_paid < 5000 else 0
    
    c.close()
    
    return render_template('resident/maintenance.html', payments=payments, current_bill=current_bill)


# Tenant maintenance
@app.route('/tenant/maintenance')
def tenant_maintenance():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    # Redirect to the same maintenance bills page as residents
    return redirect(url_for('tenant_maintenance_bills'))


# Resident pay a specific pending invoice
@app.route('/resident/maintenance/pay_pending', methods=['POST'])
def resident_pay_pending():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Not logged in'})

    payment_id = request.form.get('payment_id', '').strip()
    payment_method = request.form.get('payment_method', 'Online').strip()

    if not payment_id:
        return jsonify({'success': False, 'message': 'Payment ID is required'})

    try:
        payment_id = int(payment_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid payment ID'})

    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    # Verify the payment belongs to this resident
    c.execute("SELECT p.resident_id, p.amount FROM payments p JOIN residents r ON p.resident_id = r.id WHERE p.id = %s AND r.user_id = %s",
              (payment_id, session['user_id']))
    row = c.fetchone()
    if not row:
        c.close()
        return jsonify({'success': False, 'message': 'Payment not found'})

    try:
        c.execute("UPDATE payments SET status = 'Paid', payment_method = %s, payment_date = CURDATE() WHERE id = %s",
                  (payment_method, payment_id))
        db.commit()
        c.close()
        return jsonify({'success': True, 'message': 'Payment recorded as paid'})
    except Exception as e:
        db.rollback()
        c.close()
        return jsonify({'success': False, 'message': 'Failed to update payment: ' + str(e)})


# Tenant pay a specific pending invoice
@app.route('/tenant/maintenance/pay_pending', methods=['POST'])
def tenant_pay_pending():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})

    payment_id = request.form.get('payment_id', '').strip()
    payment_method = request.form.get('payment_method', 'Online').strip()

    if not payment_id:
        return jsonify({'success': False, 'message': 'Payment ID is required'})

    try:
        payment_id = int(payment_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid payment ID'})

    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    # Verify the payment belongs to this resident
    c.execute("SELECT p.resident_id, p.amount FROM payments p JOIN residents r ON p.resident_id = r.id WHERE p.id = %s AND r.user_id = %s",
              (payment_id, session['user_id']))
    row = c.fetchone()
    if not row:
        c.close()
        return jsonify({'success': False, 'message': 'Payment not found'})

    try:
        c.execute("UPDATE payments SET status = 'Paid', payment_method = %s, payment_date = CURDATE() WHERE id = %s",
                  (payment_method, payment_id))
        db.commit()
        c.close()
        return jsonify({'success': True, 'message': 'Payment recorded as paid'})
    except Exception as e:
        db.rollback()
        c.close()
        return jsonify({'success': False, 'message': 'Failed to update payment: ' + str(e)})


# Resident download payment report (PDF)
@app.route('/resident/maintenance/report')
def resident_maintenance_report():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))

    # Import the report generation function
    from reports import generate_resident_payment_report_pdf
    
    # Generate PDF report
    pdf_buffer = generate_resident_payment_report_pdf(session['user_id'])
    
    # Return PDF response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=resident_maintenance_payment_report.pdf'
    return response


# Tenant download payment report (PDF)
@app.route('/tenant/maintenance/report')
def tenant_maintenance_report():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))

    # Import the report generation function
    from reports import generate_resident_payment_report_pdf
    
    # Generate PDF report
    pdf_buffer = generate_resident_payment_report_pdf(session['user_id'])
    
    # Return PDF response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=tenant_maintenance_payment_report.pdf'
    return response


# Resident generate bill (resident can request a bill to be created as Pending)
@app.route('/resident/maintenance/generate', methods=['POST'])
def resident_generate_bill():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})

    resident_id = resident['id']

    # Calculate current outstanding bill (same logic as resident_maintenance)
    c.execute("SELECT SUM(amount) FROM payments WHERE resident_id = %s AND status = 'Paid'", (resident_id,))
    result = c.fetchone()
    total_paid = result['SUM(amount)'] if result and result['SUM(amount)'] else 0
    current_bill = 5000 - total_paid if total_paid < 5000 else 0

    if current_bill <= 0:
        c.close()
        return jsonify({'success': False, 'message': 'No dues to generate'})

    # Generate unique receipt/reference for pending bill with realistic format
    from datetime import datetime
    timestamp = int(time.time())
    receipt_number = f"{datetime.now().strftime('%Y%m')}-{timestamp % 10000:04d}"

    try:
        c.execute("INSERT INTO payments (resident_id, amount, receipt_number, status) VALUES (%s, %s, %s, %s)",
                  (resident_id, current_bill, receipt_number, 'Pending'))
        db.commit()
        c.close()
        return jsonify({'success': True, 'message': 'Bill generated successfully', 'receipt_number': receipt_number, 'amount': current_bill})
    except Exception as e:
        db.rollback()
        c.close()
        return jsonify({'success': False, 'message': 'Failed to generate bill: ' + str(e)})


# Tenant generate bill (tenant can request a bill to be created as Pending)
@app.route('/tenant/maintenance/generate', methods=['POST'])
def tenant_generate_bill():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})

    resident_id = resident['id']

    # Calculate current outstanding bill (same logic as tenant_maintenance)
    c.execute("SELECT SUM(amount) FROM payments WHERE resident_id = %s AND status = 'Paid'", (resident_id,))
    result = c.fetchone()
    total_paid = result['SUM(amount)'] if result and result['SUM(amount)'] else 0
    current_bill = 5000 - total_paid if total_paid < 5000 else 0

    if current_bill <= 0:
        c.close()
        return jsonify({'success': False, 'message': 'No dues to generate'})

    # Generate unique receipt/reference for pending bill with realistic format
    from datetime import datetime
    timestamp = int(time.time())
    receipt_number = f"{datetime.now().strftime('%Y%m')}-{timestamp % 10000:04d}"

    try:
        c.execute("INSERT INTO payments (resident_id, amount, receipt_number, status) VALUES (%s, %s, %s, %s)",
                  (resident_id, current_bill, receipt_number, 'Pending'))
        db.commit()
        c.close()
        return jsonify({'success': True, 'message': 'Bill generated successfully', 'receipt_number': receipt_number, 'amount': current_bill})
    except Exception as e:
        db.rollback()
        c.close()
        return jsonify({'success': False, 'message': 'Failed to generate bill: ' + str(e)})

# Resident make payment
@app.route('/resident/maintenance/pay', methods=['POST'])
def resident_make_payment():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    payment_method = request.form.get('payment_method', '').strip()
    
    # Validate required fields
    if not payment_method:
        return jsonify({'success': False, 'message': 'Payment method is required'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Get current bill amount (this should be improved in a real system)
    c.execute("SELECT SUM(amount) FROM payments WHERE resident_id = %s AND status = 'Paid'", (resident_id,))
    result = c.fetchone()
    total_paid = result['SUM(amount)'] if result and result['SUM(amount)'] else 0
    current_bill = 5000 - total_paid if total_paid < 5000 else 0
    
    if current_bill <= 0:
        c.close()
        return jsonify({'success': False, 'message': 'No dues to pay'})
    
    # Generate unique receipt number with realistic format (YYYY-MM-XXXX)
    from datetime import datetime
    timestamp = int(time.time())
    receipt_number = f"{datetime.now().strftime('%Y%m')}-{timestamp % 10000:04d}"
    
    # Insert payment record with "Paid" status since this is a demo
    c.execute("INSERT INTO payments (resident_id, amount, payment_method, receipt_number, status) VALUES (%s, %s, %s, %s, %s)",
              (resident_id, current_bill, payment_method, receipt_number, 'Paid'))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Payment successful', 'receipt_number': receipt_number})


# Tenant make payment
@app.route('/tenant/maintenance/pay', methods=['POST'])
def tenant_make_payment():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    payment_method = request.form.get('payment_method', '').strip()
    
    # Validate required fields
    if not payment_method:
        return jsonify({'success': False, 'message': 'Payment method is required'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Get current bill amount (this should be improved in a real system)
    c.execute("SELECT SUM(amount) FROM payments WHERE resident_id = %s AND status = 'Paid'", (resident_id,))
    result = c.fetchone()
    total_paid = result['SUM(amount)'] if result and result['SUM(amount)'] else 0
    current_bill = 5000 - total_paid if total_paid < 5000 else 0
    
    if current_bill <= 0:
        c.close()
        return jsonify({'success': False, 'message': 'No dues to pay'})
    
    # Generate unique receipt number with realistic format (YYYY-MM-XXXX)
    from datetime import datetime
    timestamp = int(time.time())
    receipt_number = f"{datetime.now().strftime('%Y%m')}-{timestamp % 10000:04d}"
    
    # Insert payment record with "Paid" status since this is a demo
    c.execute("INSERT INTO payments (resident_id, amount, payment_method, receipt_number, status) VALUES (%s, %s, %s, %s, %s)",
              (resident_id, current_bill, payment_method, receipt_number, 'Paid'))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Payment successful', 'receipt_number': receipt_number})

# Tenant update payment
@app.route('/tenant/maintenance/payments/update/<int:payment_id>', methods=['POST'])
def tenant_update_payment(payment_id):
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    amount = request.form.get('amount', '').strip()
    payment_method = request.form.get('payment_method', '').strip()
    payment_date = request.form.get('payment_date', '').strip()
    description = request.form.get('description', '').strip()
    
    # Validate required fields
    if not amount or not payment_method:
        return jsonify({'success': False, 'message': 'Amount and payment method are required'})
    
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than zero'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Check if the payment belongs to this resident
    c.execute("SELECT id FROM payments WHERE id = %s AND resident_id = %s", (payment_id, resident_id))
    payment = c.fetchone()
    
    if not payment:
        c.close()
        return jsonify({'success': False, 'message': 'Payment not found or access denied'})
    
    # Update payment record
    c.execute("UPDATE payments SET amount = %s, payment_method = %s, payment_date = %s, status = 'Paid' WHERE id = %s AND resident_id = %s",
              (amount, payment_method, payment_date, payment_id, resident_id))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Payment updated successfully'})

# Tenant delete payment
@app.route('/tenant/maintenance/payments/delete/<int:payment_id>', methods=['POST'])
def tenant_delete_payment(payment_id):
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Check if the payment belongs to this resident
    c.execute("SELECT id FROM payments WHERE id = %s AND resident_id = %s", (payment_id, resident_id))
    payment = c.fetchone()
    
    if not payment:
        c.close()
        return jsonify({'success': False, 'message': 'Payment not found or access denied'})
    
    # Delete payment record
    c.execute("DELETE FROM payments WHERE id = %s AND resident_id = %s", (payment_id, resident_id))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Payment deleted successfully'})


# Tenant download specific payment receipt (PDF)
@app.route('/tenant/maintenance/receipt/<int:payment_id>')
def tenant_download_receipt(payment_id):
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return redirect(url_for('tenant_dashboard'))
    
    resident_id = resident['id']
    
    # Get payment details
    c.execute("""SELECT p.id, u.name, r.flat_number, p.amount, p.payment_date, p.payment_method, p.receipt_number, p.status, p.description 
                 FROM payments p 
                 JOIN residents r ON p.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 WHERE p.id = %s AND r.user_id = %s""", (payment_id, session['user_id']))
    payment = c.fetchone()
    
    if not payment:
        c.close()
        return "Payment not found", 404
    
    # Get society settings
    c.execute("SELECT society_name, society_address, society_phone, society_email FROM settings WHERE id = 1")
    settings = c.fetchone()
    c.close()
    
    # Create a dictionary for easier access in template
    receipt_data = {
        'id': payment['id'],
        'name': payment['name'],
        'flat_number': payment['flat_number'],
        'amount': payment['amount'],
        'payment_date': payment['payment_date'],
        'payment_method': payment['payment_method'],
        'receipt_number': payment['receipt_number'],
        'status': payment['status'],
        'description': payment['description'],
        # Society information
        'society_name': settings['society_name'] if settings else 'SOCIETY MANAGEMENT SYSTEM',
        'society_address': settings['society_address'] if settings else '123 Society Address, City, State - 123456',
        'society_phone': settings['society_phone'] if settings else '+91 9876543210',
        'society_email': settings['society_email'] if settings else 'info@society.com'
    }
    
    # Import the report generation function
    from reports import generate_individual_receipt_pdf
    
    # Generate PDF receipt
    pdf_buffer = generate_individual_receipt_pdf(receipt_data)
    
    # Return PDF response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=payment_receipt_{payment[6]}.pdf'
    return response

# Resident parking
@app.route('/resident/parking')
def resident_parking():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return redirect(url_for('resident_dashboard'))
    
    resident_id = resident['id']
    
    # Get parking information
    c.execute("SELECT * FROM parking WHERE resident_id = %s", (resident_id,))
    parking = c.fetchone()
    c.close()
    
    return render_template('resident/parking.html', parking=parking)


# Tenant parking
@app.route('/tenant/parking')
def tenant_parking():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return redirect(url_for('tenant_dashboard'))
    
    resident_id = resident['id']
    
    # Get parking information
    c.execute("SELECT * FROM parking WHERE resident_id = %s", (resident_id,))
    parking = c.fetchone()
    
    # Get parking history (all parking records for this resident)
    c.execute("SELECT vehicle_number, slot_type, status FROM parking WHERE resident_id = %s ORDER BY id DESC", (resident_id,))
    parking_history = c.fetchall()
    c.close()
    
    # Format the history data for display
    vehicle_history = []
    for record in parking_history:
        if record['vehicle_number']:  # If vehicle number exists
            vehicle_history.append([record['vehicle_number'], record['slot_type'], "Current" if record['status'] == 'Occupied' else record['status']])
    
    return render_template('tenant/parking.html', parking=parking, vehicle_history=vehicle_history)

# Resident register vehicle
@app.route('/resident/parking/register', methods=['POST'])
def resident_register_vehicle():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    vehicle_number = request.form.get('vehicle_number', '').strip().upper()
    vehicle_type = request.form.get('vehicle_type', '').strip()
    
    # Validate required fields
    if not vehicle_number or not vehicle_type:
        return jsonify({'success': False, 'message': 'Vehicle number and type are required'})
    
    # Validate vehicle number format (e.g., MH12AB1234)
    import re
    vehicle_regex = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$')
    if not vehicle_regex.match(vehicle_number):
        return jsonify({'success': False, 'message': 'Please enter a valid vehicle number (e.g., MH12AB1234)'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Update parking record with vehicle information
    c.execute("UPDATE parking SET vehicle_number = %s, status = 'Occupied' WHERE resident_id = %s",
              (vehicle_number, resident_id))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Vehicle registered successfully'})


# Tenant register vehicle
@app.route('/tenant/parking/register', methods=['POST'])
def tenant_register_vehicle():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    vehicle_number = request.form.get('vehicle_number', '').strip().upper()
    vehicle_type = request.form.get('vehicle_type', '').strip()
    
    # Validate required fields
    if not vehicle_number or not vehicle_type:
        return jsonify({'success': False, 'message': 'Vehicle number and type are required'})
    
    # Validate vehicle number format (e.g., MH12AB1234)
    import re
    vehicle_regex = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$')
    if not vehicle_regex.match(vehicle_number):
        return jsonify({'success': False, 'message': 'Please enter a valid vehicle number (e.g., MH12AB1234)'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Update parking record with vehicle information
    c.execute("UPDATE parking SET vehicle_number = %s, status = 'Occupied' WHERE resident_id = %s",
              (vehicle_number, resident_id))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Vehicle registered successfully'})

# Resident charity
@app.route('/resident/charity')
def resident_charity():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return redirect(url_for('login'))
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return redirect(url_for('resident_dashboard'))
    
    resident_id = resident['id']
    
    # Get charity history
    c.execute("SELECT * FROM charity WHERE resident_id = %s ORDER BY pickup_date DESC", (resident_id,))
    donations = c.fetchall()
    c.close()
    
    return render_template('resident/charity.html', donations=donations)


# Owner charity (same as resident)
@app.route('/owner/charity')
def owner_charity():
    # Just redirect to the same function since both owners and tenants can access charity
    return resident_charity()


# Tenant charity
@app.route('/tenant/charity')
def tenant_charity():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return redirect(url_for('login'))
    
    # Just redirect to the same function since both tenants and owners can access charity
    return resident_charity()

# Resident submit charity
@app.route('/resident/charity/submit', methods=['POST'])
def resident_submit_charity():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    item_type = request.form.get('item_type', '').strip()
    quantity = request.form.get('quantity', '').strip()
    description = request.form.get('description', '').strip()
    condition = request.form.get('condition', '').strip()
    
    # Validate required fields
    if not item_type or not quantity or not description:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive number'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Please enter a valid quantity'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Combine description with condition if provided
    description_with_condition = f"{description} - Condition: {condition}" if condition else description
    
    c.execute("INSERT INTO charity (resident_id, item_type, quantity, description) VALUES (%s, %s, %s, %s)",
              (resident_id, item_type, quantity, description_with_condition))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Charity donation submitted successfully'})


# Owner submit charity (same as resident)
@app.route('/owner/charity/submit', methods=['POST'])
def owner_submit_charity():
    # Just redirect to the same function since both owners and tenants can submit donations
    return resident_submit_charity()


# Tenant submit charity
@app.route('/tenant/charity/submit', methods=['POST'])
def tenant_submit_charity():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Server-side validation
    item_type = request.form.get('item_type', '').strip()
    quantity = request.form.get('quantity', '').strip()
    description = request.form.get('description', '').strip()
    condition = request.form.get('condition', '').strip()
    
    # Validate required fields
    if not item_type or not quantity or not description:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive number'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Please enter a valid quantity'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Combine description with condition if provided
    description_with_condition = f"{description} - Condition: {condition}" if condition else description
    
    c.execute("INSERT INTO charity (resident_id, item_type, quantity, description) VALUES (%s, %s, %s, %s)",
              (resident_id, item_type, quantity, description_with_condition))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Charity donation submitted successfully'})

# Resident maintenance bills
@app.route('/resident/maintenance-bills')
def resident_maintenance_bills():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return redirect(url_for('login'))
    
    # Update late fines for all unpaid bills
    update_late_fines()
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    
    # Get resident ID
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return redirect(url_for('login'))
    
    resident_id = resident['id']
    
    # Get maintenance bills for this resident
    c.execute("""SELECT mb.id, mb.flat_number, mb.amount, mb.due_date, mb.status, mb.late_fine, mb.created_date
                 FROM maintenance_bills mb
                 WHERE mb.resident_id = %s
                 ORDER BY mb.created_date DESC""", (resident_id,))
    raw_bills = c.fetchall()
    
    # Process bills to add days overdue calculation
    bills = []
    for bill in raw_bills:
        bill_id = bill['id']
        flat_number = bill['flat_number']
        amount = bill['amount']
        due_date = bill['due_date']
        status = bill['status']
        late_fine = bill['late_fine']
        created_date = bill['created_date']
        
        # Calculate days overdue if bill is unpaid
        days_overdue = 0
        if status == 'Unpaid':
            days_overdue = calculate_days_overdue(due_date)
        
        bills.append((bill_id, flat_number, amount, due_date, status, late_fine, created_date, days_overdue))
    
    c.close()
    
    return render_template('resident/maintenance_bills.html', bills=bills)


# Owner maintenance bills (separate route for owners)
@app.route('/owner/maintenance-bills')
def owner_maintenance_bills():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return redirect(url_for('login'))
    
    # Just redirect to the same function since both owners and tenants should see their bills
    return resident_maintenance_bills()


# Tenant maintenance bills (same as resident)
@app.route('/tenant/maintenance-bills')
def tenant_maintenance_bills():
    # Just redirect to the same function since both owners and tenants should see their bills
    return resident_maintenance_bills()


# Resident pay maintenance bill
@app.route('/resident/maintenance-bills/pay', methods=['POST'])
def resident_pay_maintenance_bill():
    if 'user_id' not in session or session['role'] not in ['Owner', 'Tenant']:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    bill_id = request.form.get('bill_id', '').strip()
    payment_method = request.form.get('payment_method', 'Cash').strip()
    
    if not bill_id:
        return jsonify({'success': False, 'message': 'Bill ID is required'})
    
    # Validate bill_id
    try:
        bill_id = int(bill_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid bill ID'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Verify that the bill belongs to this resident
    c.execute("SELECT status FROM maintenance_bills WHERE id = %s AND resident_id = %s", (bill_id, resident_id))
    bill = c.fetchone()
    
    if not bill:
        c.close()
        return jsonify({'success': False, 'message': 'Bill not found or does not belong to you'})
    
    bill_status = bill['status']
    
    if bill_status == 'Paid':
        c.close()
        return jsonify({'success': False, 'message': 'This bill is already paid'})
    
    # Mark the bill as paid
    c.execute("UPDATE maintenance_bills SET status = 'Paid', late_fine = 0 WHERE id = %s", (bill_id,))
    
    # Generate a receipt number for the payment
    from datetime import datetime
    timestamp = int(time.time())
    receipt_number = f"MB-{datetime.now().strftime('%Y%m')}-{timestamp % 10000:04d}"
    
    # Record the payment in the payments table
    c.execute("""INSERT INTO payments (resident_id, amount, payment_date, payment_method, receipt_number, status) 
                 SELECT %s, mb.amount + mb.late_fine, CURDATE(), %s, %s, 'Paid'
                 FROM maintenance_bills mb WHERE mb.id = %s""", (resident_id, payment_method, receipt_number, bill_id))
    
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Bill paid successfully', 'receipt_number': receipt_number})


# Tenant pay maintenance bill (same as resident)
@app.route('/tenant/maintenance-bills/pay', methods=['POST'])
def tenant_pay_maintenance_bill():
    # Just redirect to the same function since both tenants and owners can pay bills
    return resident_pay_maintenance_bill()


# Resident notices
@app.route('/resident/notices')
def resident_notices():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT * FROM notices ORDER BY notice_date DESC")
    notices = c.fetchall()
    c.close()
    
    return render_template('resident/notices.html', notices=notices)


# Tenant notices
@app.route('/tenant/notices')
def tenant_notices():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT * FROM notices ORDER BY notice_date DESC")
    notices = c.fetchall()
    c.close()
    
    return render_template('tenant/notices.html', notices=notices)

# Resident emergency
@app.route('/resident/emergency')
def resident_emergency():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    return render_template('resident/emergency.html')


# Tenant emergency
@app.route('/tenant/emergency')
def tenant_emergency():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    return render_template('tenant/emergency.html')

# Resident emergency call
@app.route('/resident/emergency/call', methods=['POST'])
def resident_emergency_call():
    if 'user_id' not in session or session['role'] != 'Owner':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Get emergency type from form
    emergency_type = request.form.get('emergency_type', '').strip()
    
    # Validate emergency type
    if emergency_type not in ['Medical', 'Police', 'Fire']:
        c.close()
        return jsonify({'success': False, 'message': 'Invalid emergency type'})
    
    # Log emergency
    c.execute("INSERT INTO emergency_logs (resident_id, emergency_type, description) VALUES (%s, %s, %s)",
              (resident_id, emergency_type, f"Emergency call for {emergency_type}"))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': f'{emergency_type} emergency logged successfully'})


# Tenant emergency call
@app.route('/tenant/emergency/call', methods=['POST'])
def tenant_emergency_call():
    if 'user_id' not in session or session['role'] != 'Tenant':
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Get emergency type from form
    emergency_type = request.form.get('emergency_type', '').strip()
    
    # Validate emergency type
    if emergency_type not in ['Medical', 'Police', 'Fire']:
        c.close()
        return jsonify({'success': False, 'message': 'Invalid emergency type'})
    
    # Log emergency
    c.execute("INSERT INTO emergency_logs (resident_id, emergency_type, description) VALUES (%s, %s, %s)",
              (resident_id, emergency_type, f"Emergency call for {emergency_type}"))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': f'{emergency_type} emergency logged successfully'})

# Security dashboard
@app.route('/security')
def security_dashboard():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    return render_template('security/dashboard.html')

# Security visitors
@app.route('/security/visitors')
def security_visitors():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""SELECT v.id, u.name, r.flat_number, v.visitor_name, v.contact, v.visit_purpose, v.visit_date, v.visit_time, v.status 
                 FROM visitors v
                 JOIN residents r ON v.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 WHERE v.status = 'Pending'
                 ORDER BY v.visit_date DESC, v.visit_time DESC""")
    pending_visitors = c.fetchall()
    c.close()
    
    return render_template('security/visitors.html', pending_visitors=pending_visitors)

# Security deliveries
@app.route('/security/deliveries')
def security_deliveries():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""SELECT d.id, u.name, r.flat_number, d.delivery_company, d.delivery_item, d.arrival_time, d.status 
                 FROM deliveries d
                 JOIN residents r ON d.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 WHERE d.status = 'Pending'
                 ORDER BY d.arrival_time DESC""")
    pending_deliveries = c.fetchall()
    c.close()
    
    return render_template('security/deliveries.html', pending_deliveries=pending_deliveries)

# Security parking
@app.route('/security/parking')
def security_parking():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""SELECT pk.slot_number, pk.slot_type, u.name, r.flat_number, pk.vehicle_number, pk.status 
                 FROM parking pk 
                 LEFT JOIN residents r ON pk.resident_id = r.id 
                 LEFT JOIN users u ON r.user_id = u.id 
                 ORDER BY pk.slot_number""")
    parking_slots = c.fetchall()
    c.close()
    
    return render_template('security/parking.html', parking_slots=parking_slots)

# Security allow delivery
@app.route('/security/deliveries/allow/<int:delivery_id>', methods=['POST'])
def security_allow_delivery(delivery_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("UPDATE deliveries SET status = 'Allowed' WHERE id = %s", (delivery_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Delivery allowed successfully'})

# Security collect delivery
@app.route('/security/deliveries/collect/<int:delivery_id>', methods=['POST'])
def security_collect_delivery(delivery_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("UPDATE deliveries SET status = 'Collected', collected_time = NOW() WHERE id = %s", (delivery_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Delivery collected successfully'})

# Security deliver delivery
@app.route('/security/deliveries/deliver/<int:delivery_id>', methods=['POST'])
def security_deliver_delivery(delivery_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("UPDATE deliveries SET status = 'Delivered' WHERE id = %s", (delivery_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Delivery marked as delivered successfully'})

# Security emergency alerts
@app.route('/security/emergency')
def security_emergency():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""SELECT e.id, u.name, r.flat_number, e.emergency_type, e.description, e.log_time, e.resolved
                 FROM emergency_logs e
                 JOIN residents r ON e.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY e.log_time DESC""")
    emergency_logs = c.fetchall()
    c.close()
    
    return render_template('security/emergency.html', emergency_logs=emergency_logs)

# Visitor management
@app.route('/visitor/add', methods=['POST'])
def add_visitor():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    resident_id = request.form['resident_id']
    visitor_name = request.form['visitor_name']
    contact = request.form['contact']
    purpose = request.form['purpose']
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("INSERT INTO visitors (resident_id, visitor_name, contact, visit_purpose) VALUES (%s, %s, %s, %s)",
              (resident_id, visitor_name, contact, purpose))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Visitor added successfully'})

# Get pending visitors for security
@app.route('/security/visitors/pending')
def pending_visitors():
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""SELECT v.id, v.visitor_name, v.contact, v.visit_purpose, r.flat_number 
                 FROM visitors v 
                 JOIN residents r ON v.resident_id = r.id 
                 WHERE v.status = 'Pending'""")
    visitors = c.fetchall()
    c.close()
    
    return jsonify(visitors)

# Approve visitor
@app.route('/security/visitor/approve/<int:visitor_id>')
def approve_visitor(visitor_id):
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("UPDATE visitors SET status = 'Approved' WHERE id = %s", (visitor_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Visitor approved'})

# Reject visitor
@app.route('/security/visitor/reject/<int:visitor_id>')
def reject_visitor(visitor_id):
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("UPDATE visitors SET status = 'Rejected' WHERE id = %s", (visitor_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Visitor rejected'})

# Mark visitor exit
@app.route('/security/visitor/exit/<int:visitor_id>')
def exit_visitor(visitor_id):
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("UPDATE visitors SET status = 'Exited', exit_time = NOW() WHERE id = %s", (visitor_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Visitor exit marked'})

# Security emergency mark as resolved
@app.route('/security/emergency/resolve/<int:emergency_id>', methods=['POST'])
def security_resolve_emergency(emergency_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})

# Security visitor entries dashboard
@app.route('/security/visitor_entries')
def security_visitor_entries():
    if 'user_id' not in session or session['role'] != 'Security':
        return redirect(url_for('login'))
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""SELECT ve.id, ve.visitor_name, ve.mobile_number, ve.purpose, ve.flat_number, ve.photo, ve.entry_time, ve.exit_time, ve.status
                 FROM visitor_entries ve
                 ORDER BY ve.entry_time DESC""")
    visitor_entries = c.fetchall()
    c.close()
    
    return render_template('security/visitor_entries.html', visitor_entries=visitor_entries)

# Security add visitor entry
@app.route('/security/visitor_entries/add', methods=['POST'])
def security_add_visitor_entry():
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    visitor_name = request.form.get('visitor_name', '').strip()
    mobile_number = request.form.get('mobile_number', '').strip()
    purpose = request.form.get('purpose', '').strip()
    flat_number = request.form.get('flat_number', '').strip()
    
    # Server-side validation
    if not visitor_name or not mobile_number or not purpose or not flat_number:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate mobile number format
    import re
    mobile_regex = re.compile(r'^\d{10}$')
    if not mobile_regex.match(mobile_number):
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit mobile number'})
    
    # Handle photo upload
    photo_url = None
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo and photo.filename != '':
            # Validate file type
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(photo.filename)[1].lower()
            if ext in allowed_extensions:
                # Generate unique filename using UUID
                unique_filename = str(uuid.uuid4()) + ext
                filepath = os.path.join('static', 'images', 'visitor_photos', unique_filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                photo.save(filepath)
                photo_url = f'/static/images/visitor_photos/{unique_filename}'
            else:
                return jsonify({'success': False, 'message': 'Invalid file type. Only JPG, PNG, and GIF files are allowed.'})
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""INSERT INTO visitor_entries (visitor_name, mobile_number, purpose, flat_number, photo)
                 VALUES (%s, %s, %s, %s, %s)""",
              (visitor_name, mobile_number, purpose, flat_number, photo_url))
    db.commit()
    visitor_id = c.lastrowid
    c.close()
    
    return jsonify({'success': True, 'message': 'Visitor entry added successfully', 'id': visitor_id})

# Security mark visitor exit
@app.route('/security/visitor_entries/mark_exit/<int:entry_id>', methods=['POST'])
def security_mark_visitor_exit(entry_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""UPDATE visitor_entries 
                 SET exit_time = NOW(), status = 'Out'
                 WHERE id = %s""", (entry_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Visitor marked as exited'})

# Security delete visitor entry
@app.route('/security/visitor_entries/delete/<int:entry_id>', methods=['POST'])
def security_delete_visitor_entry(entry_id):
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # First, get the photo path to clean up the file
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT photo FROM visitor_entries WHERE id = %s", (entry_id,))
    result = c.fetchone()
    
    if result and result['photo']:
        # Delete the photo file
        import os
        photo_path = os.getcwd() + '/SMS-1 (2)/SMS-1' + result['photo']
        if os.path.exists(photo_path):
            os.remove(photo_path)
    
    # Delete the visitor entry
    c.execute("DELETE FROM visitor_entries WHERE id = %s", (entry_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Visitor entry deleted successfully'})

# Auto-delete records older than 30 days (should be run periodically)
@app.route('/security/visitor_entries/cleanup')
def security_cleanup_visitor_entries():
    if 'user_id' not in session or session['role'] != 'Security':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    
    # Get old records before deletion to clean up photos
    c.execute("SELECT photo FROM visitor_entries WHERE entry_time < DATE_SUB(NOW(), INTERVAL 30 DAY)")
    old_records = c.fetchall()
    
    # Delete photos associated with old records
    for record in old_records:
        if record['photo']:
            import os
            photo_path = os.getcwd() + '/SMS-1 (2)/SMS-1' + record['photo']
            if os.path.exists(photo_path):
                os.remove(photo_path)
    
    # Delete old records
    c.execute("DELETE FROM visitor_entries WHERE entry_time < DATE_SUB(NOW(), INTERVAL 30 DAY)")
    deleted_count = c.rowcount
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': f'{deleted_count} old visitor entries cleaned up'})


# Periodic cleanup function that can be called automatically
from threading import Timer
import time

def schedule_periodic_cleanup():
    def run_cleanup():
        print("Running periodic cleanup...")
        try:
            db = get_db()
            c = db.cursor(MySQLdb.cursors.DictCursor)
            
            # Get old records before deletion to clean up photos
            c.execute("SELECT photo FROM visitor_entries WHERE entry_time < DATE_SUB(NOW(), INTERVAL 30 DAY)")
            old_records = c.fetchall()
            
            # Delete photos associated with old records
            for record in old_records:
                if record['photo']:
                    import os
                    photo_path = os.getcwd() + '/SMS-1 (2)/SMS-1' + record['photo']
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
            
            # Delete old records
            c.execute("DELETE FROM visitor_entries WHERE entry_time < DATE_SUB(NOW(), INTERVAL 30 DAY)")
            deleted_count = c.rowcount
            db.commit()
            c.close()
            
            print(f"Cleaned up {deleted_count} old visitor entries")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
        
        # Schedule the next cleanup (every 24 hours)
        timer = Timer(24 * 60 * 60, run_cleanup)  # 24 hours in seconds
        timer.daemon = True
        timer.start()
    
    # Run cleanup after 1 minute initially
    initial_timer = Timer(60, run_cleanup)
    initial_timer.daemon = True
    initial_timer.start()

# Start the periodic cleanup when the app starts
schedule_periodic_cleanup()



# General emergency page (accessible to all logged-in users)
@app.route('/emergency')
def emergency():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get emergency contacts from the emergency_contacts table
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    
    # Get all active emergency contacts ordered by priority
    c.execute("SELECT name, contact_type, phone_number FROM emergency_contacts WHERE is_active = 1 ORDER BY priority ASC")
    emergency_contacts = c.fetchall()
    
    # Separate contacts by type for easier access in template
    contacts_by_type = {}
    for contact in emergency_contacts:
        name = contact['name']
        contact_type = contact['contact_type']
        phone_number = contact['phone_number']
        contacts_by_type[contact_type.lower()] = phone_number
    
    c.close()
    
    # Get specific contacts, fallback to defaults if not in emergency_contacts table
    admin_contact = contacts_by_type.get('admin', '9876543210')
    security_contact = contacts_by_type.get('security', '9876543211')
    maintenance_contact = contacts_by_type.get('maintenance', '9876543212')
    doctor_contact = contacts_by_type.get('doctor', '9876543213')
    
    return render_template('emergency.html', 
                          admin_contact=admin_contact,
                          security_contact=security_contact,
                          maintenance_contact=maintenance_contact,
                          doctor_contact=doctor_contact,
                          emergency_contacts=emergency_contacts)

# Emergency log page - allows users to log emergency incidents
@app.route('/emergency/log')
def emergency_log():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    c.close()
    
    if not resident:
        return redirect(url_for('home'))
    
    return render_template('emergency_log.html')

# Submit emergency log
@app.route('/emergency/log/submit', methods=['POST'])
def submit_emergency_log():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Get form data
    emergency_type = request.form.get('emergency_type', '').strip()
    description = request.form.get('description', '').strip()
    action_taken = request.form.get('action_taken', '').strip()
    
    # Validate required fields
    if not emergency_type or not description:
        return jsonify({'success': False, 'message': 'Emergency type and description are required'})
    
    # Get resident ID
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT id FROM residents WHERE user_id = %s", (session['user_id'],))
    resident = c.fetchone()
    
    if not resident:
        c.close()
        return jsonify({'success': False, 'message': 'Resident not found'})
    
    resident_id = resident['id']
    
    # Insert emergency log
    c.execute("INSERT INTO emergency_logs (resident_id, emergency_type, description, action_taken) VALUES (%s, %s, %s, %s)",
              (resident_id, emergency_type, description, action_taken))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Emergency logged successfully'})

# Admin emergency management
@app.route('/admin/emergency')
def admin_emergency():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("""SELECT e.id, u.name, r.flat_number, e.emergency_type, e.description, e.log_time, e.resolved, e.action_taken
                 FROM emergency_logs e
                 JOIN residents r ON e.resident_id = r.id 
                 JOIN users u ON r.user_id = u.id 
                 ORDER BY e.log_time DESC""")
    emergency_logs = c.fetchall()
    c.close()
    
    return render_template('admin/emergency.html', emergency_logs=emergency_logs)

# Admin emergency resolve
@app.route('/admin/emergency/resolve/<int:emergency_id>', methods=['POST'])
def admin_resolve_emergency(emergency_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db = get_db()
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute("UPDATE emergency_logs SET resolved = 1 WHERE id = %s", (emergency_id,))
    db.commit()
    c.close()
    
    return jsonify({'success': True, 'message': 'Emergency marked as resolved'})

# Admin emergency add action
@app.route('/admin/emergency/action/<int:emergency_id>', methods=['POST'])
def admin_emergency_action(emergency_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    action_taken = request.form.get('action_taken', '').strip()
    
    if not action_taken:
        return jsonify({'success': False, 'message': 'Action taken is required'})
    
    conn = sqlite3.connect('society.db')
    c = conn.cursor()
    c.execute("UPDATE emergency_logs SET action_taken = ? WHERE id = ?", (action_taken, emergency_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Action recorded successfully'})

# Admin emergency contacts management
@app.route('/admin/emergency-contacts')
def admin_emergency_contacts():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('society.db')
    c = conn.cursor()
    c.execute("SELECT * FROM emergency_contacts ORDER BY priority ASC")
    contacts = c.fetchall()
    conn.close()
    
    return render_template('admin/emergency_contacts.html', contacts=contacts)

# Admin add emergency contact
@app.route('/admin/emergency-contacts/add', methods=['POST'])
def admin_add_emergency_contact():
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    name = request.form.get('name', '').strip()
    contact_type = request.form.get('contact_type', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    priority = request.form.get('priority', '10')
    
    # Validate required fields
    if not name or not contact_type or not phone_number:
        return jsonify({'success': False, 'message': 'Name, contact type, and phone number are required'})
    
    # Validate priority
    try:
        priority = int(priority)
    except ValueError:
        priority = 10
    
    conn = sqlite3.connect('society.db')
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO emergency_contacts (name, contact_type, phone_number, priority, is_active) VALUES (?, ?, ?, ?, 1)",
                  (name, contact_type, phone_number, priority))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Emergency contact added successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to add contact: ' + str(e)})

# Admin update emergency contact
@app.route('/admin/emergency-contacts/update/<int:contact_id>', methods=['POST'])
def admin_update_emergency_contact(contact_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    name = request.form.get('name', '').strip()
    contact_type = request.form.get('contact_type', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    priority = request.form.get('priority', '10')
    is_active = request.form.get('is_active', '0') == '1'
    
    # Validate required fields
    if not name or not contact_type or not phone_number:
        return jsonify({'success': False, 'message': 'Name, contact type, and phone number are required'})
    
    # Validate priority
    try:
        priority = int(priority)
    except ValueError:
        priority = 10
    
    conn = sqlite3.connect('society.db')
    c = conn.cursor()
    
    try:
        c.execute("UPDATE emergency_contacts SET name=?, contact_type=?, phone_number=?, priority=?, is_active=? WHERE id=?",
                  (name, contact_type, phone_number, priority, is_active, contact_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Emergency contact updated successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to update contact: ' + str(e)})

# Admin delete emergency contact
@app.route('/admin/emergency-contacts/delete/<int:contact_id>', methods=['POST'])
def admin_delete_emergency_contact(contact_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = sqlite3.connect('society.db')
    c = conn.cursor()
    
    try:
        c.execute("DELETE FROM emergency_contacts WHERE id = ?", (contact_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Emergency contact deleted successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed to delete contact: ' + str(e)})

# Admin events management
@app.route('/admin/events')
def admin_events():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    events = conn.execute("SELECT * FROM events ORDER BY created_at DESC").fetchall()
    conn.close()
    
    return render_template('admin/events.html', events=events)

@app.route('/admin/events/add', methods=['GET', 'POST'])
def admin_add_event():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        event_type = request.form['event_type'].strip()
        date = request.form['date'].strip()
        time = request.form['time'].strip()
        venue = request.form['venue'].strip()
        description = request.form['description'].strip()
        image = request.files['image']
        
        # Validate required fields
        if not title or not date or not time or not venue or not description:
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        filename = None
        
        if image and image.filename != '':
            # Get file extension
            ext = os.path.splitext(image.filename)[1]
            
            # Generate unique name using UUID
            unique_name = str(uuid.uuid4()) + ext
            
            # Secure the filename
            filename = secure_filename(unique_name)
            
            # Save image
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events 
            (title, event_type, event_date, event_time, venue, description, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, event_type, date, time, venue, description, filename))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Event added successfully'})
    
    return render_template('admin/add_event.html')

@app.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
def admin_edit_event(event_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        event_type = request.form['event_type'].strip()
        date = request.form['date'].strip()
        time = request.form['time'].strip()
        venue = request.form['venue'].strip()
        description = request.form['description'].strip()
        image = request.files.get('image')
        
        # Validate required fields
        if not title or not date or not time or not venue or not description:
            cursor.close()
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Get current event data
        cursor.execute("SELECT image FROM events WHERE id = %s", (event_id,))
        current_event = cursor.fetchone()
        
        filename = current_event['image'] if current_event and current_event['image'] else None
        
        # Handle new image upload
        if image and image.filename != '':
            # Delete old image if exists
            if filename:
                old_img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(old_img_path):
                    os.remove(old_img_path)
            
            # Get file extension
            ext = os.path.splitext(image.filename)[1]
            
            # Generate unique name using UUID
            unique_name = str(uuid.uuid4()) + ext
            
            # Secure the filename
            filename = secure_filename(unique_name)
            
            # Save new image
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Update event
        cursor.execute("""UPDATE events SET 
            title=%s, event_type=%s, event_date=%s, event_time=%s, 
            venue=%s, description=%s, image=%s WHERE id=%s""",
            (title, event_type, date, time, venue, description, filename, event_id))
        
        db.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Event updated successfully'})
    
    # GET request - show edit form
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    cursor.close()
    
    if not event:
        return redirect(url_for('admin_events'))
    
    return render_template('admin/edit_event.html', event=event)

@app.route('/admin/events/delete/<int:event_id>')
def admin_delete_event(event_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT image FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    
    if event and event['image']:
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], event['image'])
        if os.path.exists(img_path):
            os.remove(img_path)
    
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Event deleted successfully'})

# Public events page for residents
@app.route('/events')
def events():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM events ORDER BY event_date DESC")
    events = cursor.fetchall()
    cursor.close()
    
    return render_template('events.html', events=events)

if __name__ == '__main__':
    try:
        init_db()
    except Exception as e:
        print(f"MySQL not available: {e}")
        print("Please install and start MySQL server, or use a SQLite fallback.")
    app.run(debug=True)