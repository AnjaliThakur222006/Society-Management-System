import sqlite3
from datetime import datetime
import os

DB = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'society.db'))
print('Using DB:', DB)
conn = sqlite3.connect(DB)
c = conn.cursor()

# List residents
c.execute('SELECT id, user_id, flat_number FROM residents')
res = c.fetchall()
print('Residents:')
for r in res:
    import sqlite3
    from datetime import datetime
    import os

    DB = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'society.db'))
    print('Using DB:', DB)
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # List residents
    c.execute('SELECT id, user_id, flat_number FROM residents')
    res = c.fetchall()
    print('Residents:')
    for r in res:
        print(r)

    if not res:
        print('No residents found. Exiting.')
        conn.close()
        exit(1)

    # Prefer flat A-101 if exists
    resident_id = None
    for r in res:
        if r[2] == 'A-101':
            resident_id = r[0]
            break

    if resident_id is None:
        resident_id = res[0][0]

    print('Selected resident_id:', resident_id)

    # Show payments count before
    c.execute('SELECT COUNT(*) FROM payments WHERE resident_id = ?', (resident_id,))
    count_before = c.fetchone()[0]
    print('Payments before:', count_before)

    # Insert pending payment
    amount = 5000.00
    receipt = 'BATCH-' + datetime.utcnow().strftime('%Y%m%d%H%M%S')
    try:
        c.execute(
            "INSERT INTO payments (resident_id, amount, receipt_number, status) VALUES (?, ?, ?, ?)",
            (resident_id, amount, receipt, 'Pending')
        )
        conn.commit()
        print('Inserted payment with receipt:', receipt)
    except Exception as e:
        print('Insert failed:', e)
        conn.rollback()

    # Show payments count after and last row
    c.execute('SELECT COUNT(*) FROM payments WHERE resident_id = ?', (resident_id,))
    count_after = c.fetchone()[0]
    print('Payments after:', count_after)

    c.execute('SELECT id, resident_id, amount, payment_date, payment_method, receipt_number, status FROM payments WHERE resident_id = ? ORDER BY id DESC LIMIT 5', (resident_id,))
    rows = c.fetchall()
    print('Recent payments:')
    for row in rows:
        print(row)

    conn.close()
    print('Done')
