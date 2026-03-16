"""
===============================================
HOW DUE PAYMENT CHECKING WORKS - EXAMPLE CODE
===============================================

This file explains how due payments are checked in the SMS system.
"""

# ============================================
# EXAMPLE 1: How Admin Checks All Due Payments
# ============================================

"""
Admin route: /admin/maintenance-bills
This shows ALL residents' due payments to the admin.
"""

def admin_maintenance_bills_example():
    """
    Admin sees this output:
    
    ┌─────────────────────────────────────────────────────────────┐
    │  MAINTENANCE BILLS - ADMIN VIEW                            │
    ├─────┬───────────────┬────────┬─────────┬───────────┬──────┤
    │ ID  │ Resident Name │ Flat   │ Amount  │ Due Date  │Status│
    ├─────┼───────────────┼────────┼─────────┼───────────┼──────┤
    │ 1   │ John Owner   │ A-101  │ ₹2500   │ 2024-01-15│Unpaid│
    │ 2   │ Jane Tenant  │ B-202  │ ₹2500   │ 2024-01-15│Unpaid│
    │ 3   │ John Owner   │ A-101  │ ₹2500   │ 2024-02-15│ Paid │
    └─────┴───────────────┴────────┴─────────┴───────────┴──────┘
    
    Database Query Used:
    """
    
    # This is the actual query from app.py
    query = """
    SELECT mb.id, u.name, mb.flat_number, mb.amount, mb.due_date, 
           mb.status, mb.late_fine, mb.created_date
    FROM maintenance_bills mb
    JOIN residents r ON mb.resident_id = r.id 
    JOIN users u ON r.user_id = u.id 
    ORDER BY mb.created_date DESC
    """
    
    # Result: List of all bills with status
    bills = [
        (1, "John Owner", "A-101", 2500.00, "2024-01-15", "Unpaid", 50.00, "2024-01-01"),
        (2, "Jane Tenant", "B-202", 2500.00, "2024-01-15", "Unpaid", 50.00, "2024-01-01"),
        (3, "John Owner", "A-101", 2500.00, "2024-02-15", "Paid", 0.00, "2024-02-01"),
    ]
    
    return bills


# ============================================
# EXAMPLE 2: How Resident Checks Their Due Payments
# ============================================

"""
Resident route: /resident/maintenance
This shows ONLY that resident's due payments.
"""

def resident_maintenance_example(user_id):
    """
    When John Owner (A-101) logs in, he sees:
    
    ┌─────────────────────────────────────────────────────────────┐
    │  YOUR MAINTENANCE BILLS                                     │
    ├─────────────────────────────────────────────────────────────┤
    │  Flat: A-101 | Total Due: ₹2500                           │
    ├─────────────────────────────────────────────────────────────┤
    │  Bill #1: ₹2500 - Due: 2024-01-15 - UNPAID - Late: ₹50   │
    │  Bill #2: ₹2500 - Due: 2024-02-15 - PAID                  │
    └─────────────────────────────────────────────────────────────┘
    
    Database Query Used:
    """
    
    # Get resident's ID from user_id
    resident_id = 1  # John's resident ID
    
    # Query to get unpaid bills for THIS resident
    query_unpaid = """
    SELECT id, amount, due_date, status, created_date
    FROM maintenance_bills
    WHERE resident_id = %s AND status = 'Unpaid'
    ORDER BY due_date DESC
    """
    
    # Result: Only John's unpaid bills
    unpaid_bills = [
        (1, 2500.00, "2024-01-15", "Unpaid", "2024-01-01"),
    ]
    
    # Calculate total due
    current_bill = sum(bill[1] for bill in unpaid_bills)  # = 2500
    
    return {
        "unpaid_bills": unpaid_bills,
        "total_due": current_bill
    }


# ============================================
# EXAMPLE 3: Late Fine Calculation
# ============================================

from datetime import datetime, date

def calculate_late_fine(due_date_str, rate_per_day=50.0):
    """
    Calculate late fine if payment is overdue.
    
    Example:
    - Due Date: 2024-01-15
    - Today: 2024-01-20
    - Days Overdue: 5 days
    - Late Fine: 5 × ₹50 = ₹250
    """
    
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    today = date.today()
    
    if today > due_date:
        days_overdue = (today - due_date).days
        late_fine = days_overdue * rate_per_day
        return late_fine, days_overdue
    else:
        return 0.0, 0


# Test the function
fine, days = calculate_late_fine("2024-01-15")
print(f"Days overdue: {days}, Late Fine: ₹{fine}")


# ============================================
# EXAMPLE 4: How to Check Due Payments (Summary)
# ============================================

def check_due_payments_summary():
    """
    Complete picture of how due payments work:
    
    1. Admin checks ALL due payments:
       → Go to /admin/maintenance-bills
       → See table with all residents' bills
    
    2. Resident checks THEIR due payments:
       → Go to /resident/maintenance (for Owner)
       → Go to /tenant/maintenance (for Tenant)
       → See only their own unpaid bills
    
    3. Due payment status:
       → "Unpaid" = Due payment (needs to be paid)
       → "Paid" = Already paid
    
    4. Late fine:
       →自动 added if due date passed
       → ₹50 per day overdue
    """
    
    return "See above explanations!"


# ============================================
# FLOW DIAGRAM: How Due Payment Checking Works
# ============================================

"""
USER LOGIN
    │
    ▼
┌─────────────────────────────────────┐
│  Is user Admin?                     │
└─────────────────────────────────────┘
    │
    ├── YES ──► /admin/maintenance-bills
    │              │
    │              ▼
    │         Show ALL bills from database
    │         (Everyone's due payments)
    │
    ▼
    NO
    │
    ▼
┌─────────────────────────────────────┐
│  Is user Owner?                     │
└─────────────────────────────────────┘
    │
    ├── YES ──► /resident/maintenance
    │              │
    │              ▼
    │         Get resident_id from session
    │         Query: WHERE resident_id = ?
    │         Show ONLY this user's bills
    │
    ▼
    NO
    │
    ▼
┌─────────────────────────────────────┐
│  Is user Tenant?                    │
└─────────────────────────────────────┘
    │
    ├── YES ──► /tenant/maintenance
    │              │
    │              ▼
    │         Get resident_id from session
    │         Query: WHERE resident_id = ?
    │         Show ONLY this user's bills
    │
    ▼
    NO ──► ACCESS DENIED
"""


if __name__ == "__main__":
    # Run examples
    print("=" * 50)
    print("HOW DUE PAYMENT CHECKING WORKS")
    print("=" * 50)
    
    # Example 1: Admin view
    print("\n📊 ADMIN VIEW - All Due Payments:")
    bills = admin_maintenance_bills_example()
    for bill in bills:
        print(f"  Bill #{bill[0]}: {bill[1]} ({bill[2]}) - ₹{bill[3]} - {bill[5]}")
    
    # Example 2: Resident view
    print("\n👤 RESIDENT VIEW - My Due Payments:")
    result = resident_maintenance_example(user_id=1)
    print(f"  Total Due: ₹{result['total_due']}")
    for bill in result['unpaid_bills']:
        print(f"  Bill #{bill[0]}: ₹{bill[1]} - Due: {bill[2]} - {bill[3]}")
    
    # Example 3: Late fine
    print("\n⏰ LATE FINE CALCULATION:")
    fine, days = calculate_late_fine("2024-01-15")
    print(f"  Due Date: 2024-01-15, Today: {date.today()}")
    print(f"  Days Overdue: {days}, Late Fine: ₹{fine}")
