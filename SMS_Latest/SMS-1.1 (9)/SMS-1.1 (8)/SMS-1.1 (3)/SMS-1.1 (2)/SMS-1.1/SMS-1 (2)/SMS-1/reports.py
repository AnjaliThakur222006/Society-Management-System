import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import base64

def get_payment_data():
    """Get payment data from database"""
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    query = """
    SELECT p.id, u.name, r.flat_number, p.amount, p.payment_date, p.payment_method, p.receipt_number, p.status
    FROM payments p
    JOIN residents r ON p.resident_id = r.id
    JOIN users u ON r.user_id = u.id
    ORDER BY p.payment_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_resident_payment_summary():
    """Get payment summary by resident"""
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    query = """
    SELECT r.id, u.name, r.flat_number, COALESCE(SUM(p.amount), 0) as total_paid
    FROM residents r
    JOIN users u ON r.user_id = u.id
    LEFT JOIN payments p ON p.resident_id = r.id AND p.status = 'Paid'
    GROUP BY r.id, u.name, r.flat_number
    ORDER BY total_paid DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def create_payment_trend_chart(df):
    """Create payment trend chart"""
    # Convert payment_date to datetime
    df['payment_date'] = pd.to_datetime(df['payment_date'])
    
    # Group by month and sum amounts
    monthly_payments = df.groupby(df['payment_date'].dt.to_period('M'))['amount'].sum()
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    monthly_payments.plot(kind='bar', color='skyblue')
    plt.title('Monthly Payment Trends')
    plt.xlabel('Month')
    plt.ylabel('Total Amount (₹)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save to bytes
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def create_payment_status_chart(df):
    """Create payment status distribution chart"""
    status_counts = df['status'].value_counts()
    
    # Create the plot
    plt.figure(figsize=(8, 6))
    colors_list = ['#4CAF50', '#FFC107', '#F44336'][:len(status_counts)]
    status_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors_list)
    plt.title('Payment Status Distribution')
    plt.ylabel('')
    plt.tight_layout()
    
    # Save to bytes
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def create_top_payers_chart(df_summary):
    """Create top payers chart"""
    top_payers = df_summary.head(10)
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(top_payers)), top_payers['total_paid'], color='lightgreen')
    plt.title('Top 10 Paying Residents')
    plt.xlabel('Residents')
    plt.ylabel('Total Amount Paid (₹)')
    plt.xticks(range(len(top_payers)), [f"{row['name']} ({row['flat_number']})" for _, row in top_payers.iterrows()], rotation=45, ha='right')
    plt.tight_layout()
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}',
                ha='center', va='bottom')
    
    # Save to bytes
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def generate_admin_payment_report_pdf():
    """Generate comprehensive PDF report for admin"""
    # Get data
    df = get_payment_data()
    df_summary = get_resident_payment_summary()
    
    # Create charts
    trend_chart = create_payment_trend_chart(df)
    status_chart = create_payment_status_chart(df)
    top_payers_chart = create_top_payers_chart(df_summary)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Society Maintenance Payment Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report date
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary statistics
    total_payments = len(df)
    total_amount = df['amount'].sum()
    paid_count = len(df[df['status'] == 'Paid'])
    pending_count = len(df[df['status'] == 'Pending'])
    
    summary_data = [
        ['Total Payments', str(total_payments)],
        ['Total Amount', f"₹{total_amount:,.2f}"],
        ['Paid Payments', str(paid_count)],
        ['Pending Payments', str(pending_count)],
        ['Average Payment', f"₹{total_amount/total_payments if total_payments > 0 else 0:,.2f}"]
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("Summary Statistics", styles['Heading2']))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Charts
    story.append(Paragraph("Payment Trends", styles['Heading2']))
    trend_img = Image(trend_chart, width=6*inch, height=3.6*inch)
    story.append(trend_img)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Payment Status Distribution", styles['Heading2']))
    status_img = Image(status_chart, width=5*inch, height=3.75*inch)
    story.append(status_img)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Top Paying Residents", styles['Heading2']))
    top_payers_img = Image(top_payers_chart, width=6*inch, height=3.6*inch)
    story.append(top_payers_img)
    story.append(Spacer(1, 20))
    
    # Payment details table
    story.append(Paragraph("Payment Details", styles['Heading2']))
    
    # Prepare data for table
    table_data = [['ID', 'Resident', 'Flat', 'Amount', 'Date', 'Method', 'Receipt', 'Status']]
    for _, row in df.iterrows():
        table_data.append([
            str(row['id']),
            row['name'],
            row['flat_number'],
            f"₹{row['amount']:,.2f}",
            row['payment_date'] if row['payment_date'] else '',
            row['payment_method'] if row['payment_method'] else '',
            row['receipt_number'] if row['receipt_number'] else '',
            row['status']
        ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer


def generate_individual_receipt_pdf(receipt_data):
    """Generate PDF receipt for a specific payment"""
    # Create PDF with centered margins
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.5*inch, rightMargin=1.5*inch)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        alignment=1  # Center alignment
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=6,
        alignment=0  # Left alignment
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        alignment=1  # Center alignment for amount and other centered content
    )

    # Society header - centered
    story.append(Paragraph(receipt_data['society_name'], title_style))
    story.append(Paragraph(receipt_data['society_address'], normal_style))
    story.append(Paragraph(f"Phone: {receipt_data['society_phone']}", normal_style))
    story.append(Paragraph(f"Email: {receipt_data['society_email']}", normal_style))
    story.append(Spacer(1, 20))

    # Receipt title - centered
    story.append(Paragraph("PAYMENT RECEIPT", title_style))
    story.append(Spacer(1, 10))

    # Receipt details table - centered on page
    receipt_content = []
    receipt_content.append([Paragraph("Receipt Number:", heading_style), Paragraph(str(receipt_data['receipt_number']), normal_style)])
    receipt_content.append([Paragraph("Date:", heading_style), Paragraph(str(receipt_data['payment_date']), normal_style)])
    receipt_content.append([Paragraph("Resident Name:", heading_style), Paragraph(receipt_data['name'], normal_style)])
    receipt_content.append([Paragraph("Flat Number:", heading_style), Paragraph(receipt_data['flat_number'], normal_style)])
    receipt_content.append([Paragraph("Description:", heading_style), Paragraph(str(receipt_data['description']) if receipt_data['description'] else 'Maintenance Payment', normal_style)])
    receipt_content.append([Paragraph("Amount:", heading_style), Paragraph(f"₹{receipt_data['amount']:,.2f}", normal_style)])
    receipt_content.append([Paragraph("Payment Method:", heading_style), Paragraph(str(receipt_data['payment_method']), normal_style)])
    receipt_content.append([Paragraph("Status:", heading_style), Paragraph(str(receipt_data['status']), normal_style)])

    receipt_table = Table(receipt_content, colWidths=[2.5*inch, 4*inch], hAlign='CENTER')
    receipt_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0, colors.white),
    ]))

    story.append(receipt_table)
    story.append(Spacer(1, 20))

    # Amount in words - centered
    amount = receipt_data['amount']
    amount_in_words = number_to_words(amount)
    story.append(Paragraph(f"Amount in Words: {amount_in_words} Only", normal_style))
    story.append(Spacer(1, 20))

    # Thank you message - centered
    story.append(Paragraph("Thank you for your payment.", normal_style))
    story.append(Spacer(1, 30))

    # Signature area - centered
    signature_info = [
        ['', 'Manager Signature'],
        ['', ''],
        ['', ''],
        ['', 'Date: _____________'],
    ]

    signature_table = Table(signature_info, colWidths=[4*inch, 2*inch], hAlign='CENTER')
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0, colors.white),
    ]))

    story.append(signature_table)

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return buffer


def number_to_words(num):
    """Convert number to words"""
    # Simple implementation for now
    # In a real system, you would want a more comprehensive function
    try:
        num = float(num)
        # Convert to integer for basic word conversion
        n = int(num)
        if n == 0:
            return "Zero"
        
        # Basic implementation - you might want to enhance this
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        def convert_hundreds(n):
            result = ""
            if n >= 100:
                result += ones[n // 100] + " Hundred "
                n %= 100
            if n >= 20:
                result += tens[n // 10] + " "
                n %= 10
                if n > 0:
                    result += ones[n] + " "
            elif n > 0:
                result += ones[n] + " "
            return result.strip()
        
        if n >= 10000000:  # Crores
            crore = n // 10000000
            n %= 10000000
            result = convert_hundreds(crore) + " Crore "
            if n > 0:
                result += convert_hundreds(n)
        elif n >= 100000:  # Lakhs
            lakh = n // 100000
            n %= 100000
            result = convert_hundreds(lakh) + " Lakh "
            if n > 0:
                result += convert_hundreds(n)
        elif n >= 1000:  # Thousands
            thousand = n // 1000
            n %= 1000
            result = convert_hundreds(thousand) + " Thousand "
            if n > 0:
                result += convert_hundreds(n)
        else:
            result = convert_hundreds(n)
        
        # Add decimal part if exists
        decimal_part = int((num - int(num)) * 100)
        if decimal_part > 0:
            result += f" and Paise {convert_hundreds(decimal_part)}"
        
        return result.strip() + f" Rupees"
    except:
        return str(num) + " Rupees"


def get_maintenance_bill_data():
    """Get maintenance bill data from database"""
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    query = """
    SELECT mb.id, u.name, mb.flat_number, mb.amount, mb.due_date, mb.status, mb.late_fine, mb.created_date
    FROM maintenance_bills mb
    JOIN residents r ON mb.resident_id = r.id
    JOIN users u ON r.user_id = u.id
    ORDER BY mb.created_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_resident_bill_summary():
    """Get maintenance bill summary by resident"""
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    query = """
    SELECT r.id, u.name, r.flat_number,
           COUNT(mb.id) as total_bills,
           SUM(mb.amount) as total_amount,
           SUM(CASE WHEN mb.status = 'Unpaid' THEN mb.amount ELSE 0 END) as total_unpaid,
           SUM(mb.late_fine) as total_late_fine
    FROM residents r
    JOIN users u ON r.user_id = u.id
    LEFT JOIN maintenance_bills mb ON mb.resident_id = r.id
    GROUP BY r.id, u.name, r.flat_number
    ORDER BY total_unpaid DESC, total_amount DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def generate_admin_maintenance_bills_report_pdf():
    """Generate comprehensive PDF report for maintenance bills"""
    # Get data
    df = get_maintenance_bill_data()
    df_summary = get_resident_bill_summary()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Society Maintenance Bills Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report date
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary statistics
    total_bills = len(df)
    total_amount = df['amount'].sum() if not df.empty else 0
    total_late_fine = df['late_fine'].sum() if not df.empty else 0
    paid_count = len(df[df['status'] == 'Paid']) if not df.empty else 0
    unpaid_count = len(df[df['status'] == 'Unpaid']) if not df.empty else 0
    total_outstanding = df[df['status'] == 'Unpaid']['amount'].sum() + df['late_fine'].sum() if not df.empty else 0
    
    summary_data = [
        ['Total Bills', str(total_bills)],
        ['Total Amount', f"₹{total_amount:,.2f}"],
        ['Total Late Fine', f"₹{total_late_fine:,.2f}"],
        ['Paid Bills', str(paid_count)],
        ['Unpaid Bills', str(unpaid_count)],
        ['Total Outstanding', f"₹{total_outstanding:,.2f}"]
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("Summary Statistics", styles['Heading2']))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Status distribution
    if not df.empty:
        status_counts = df['status'].value_counts()
        status_data = [['Status', 'Count', 'Percentage']]
        for status, count in status_counts.items():
            percentage = (count / total_bills) * 100
            status_data.append([status, str(count), f"{percentage:.1f}%"])
        
        status_table = Table(status_data)
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Bill Status Distribution", styles['Heading2']))
        story.append(status_table)
        story.append(Spacer(1, 20))
    
    # Top residents with unpaid bills
    if not df_summary.empty:
        top_unpaid_residents = df_summary.head(10)[['name', 'flat_number', 'total_bills', 'total_amount', 'total_unpaid']].values.tolist()
        top_unpaid_data = [['Name', 'Flat Number', 'Total Bills', 'Total Amount', 'Total Unpaid']]
        top_unpaid_data.extend(top_unpaid_residents)
        
        top_unpaid_table = Table(top_unpaid_data)
        top_unpaid_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(Paragraph("Top Residents with Unpaid Bills", styles['Heading2']))
        story.append(top_unpaid_table)
        story.append(Spacer(1, 20))
    
    # Bill details table
    story.append(Paragraph("Bill Details", styles['Heading2']))
    
    # Prepare data for table
    if not df.empty:
        table_data = [['ID', 'Resident', 'Flat', 'Amount', 'Due Date', 'Status', 'Late Fine', 'Created Date']]
        for _, row in df.iterrows():
            table_data.append([
                str(row['id']),
                row['name'],
                row['flat_number'],
                f"₹{row['amount']:,.2f}",
                row['due_date'] if row['due_date'] else '',
                row['status'],
                f"₹{row['late_fine']:,.2f}" if row['late_fine'] else '₹0.00',
                row['created_date'] if row['created_date'] else ''
            ])
    else:
        table_data = [['No bills found']]
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer

def generate_resident_payment_report_pdf(user_id):
    """Generate PDF report for a specific resident"""
    # Get resident payment data
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    query = """
    SELECT p.id, u.name, r.flat_number, p.amount, p.payment_date, p.payment_method, p.receipt_number, p.status
    FROM payments p
    JOIN residents r ON p.resident_id = r.id
    JOIN users u ON r.user_id = u.id
    WHERE r.user_id = %s
    ORDER BY p.payment_date DESC
    """
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()

    if df.empty:
        # Create simple PDF with no data message
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("Resident Payment Report", styles['Title']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("No payment history found for this resident.", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer

    # Create payment trend chart for resident
    df['payment_date'] = pd.to_datetime(df['payment_date'])
    monthly_payments = df.groupby(df['payment_date'].dt.to_period('M'))['amount'].sum()

    plt.figure(figsize=(10, 6))
    monthly_payments.plot(kind='bar', color='lightcoral')
    plt.title('Your Monthly Payment History')
    plt.xlabel('Month')
    plt.ylabel('Amount (₹)')
    plt.xticks(rotation=45)
    plt.tight_layout()

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Resident Payment Report", styles['Title']))
    story.append(Spacer(1, 20))

    # Resident info
    resident_name = df.iloc[0]['name']
    flat_number = df.iloc[0]['flat_number']
    story.append(Paragraph(f"Resident: {resident_name}", styles['Heading2']))
    story.append(Paragraph(f"Flat Number: {flat_number}", styles['Heading2']))
    story.append(Spacer(1, 20))

    # Summary
    total_paid = df[df['status'] == 'Paid']['amount'].sum()
    total_pending = df[df['status'] == 'Pending']['amount'].sum()
    payment_count = len(df)

    summary_data = [
        ['Total Payments', str(payment_count)],
        ['Total Amount Paid', f"₹{total_paid:,.2f}"],
        ['Pending Amount', f"₹{total_pending:,.2f}"]
    ]

    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(Paragraph("Payment Summary", styles['Heading2']))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Chart
    story.append(Paragraph("Your Payment History", styles['Heading2']))
    payment_chart = Image(img_buffer, width=6*inch, height=3.6*inch)
    story.append(payment_chart)
    story.append(Spacer(1, 20))

    # Payment details
    story.append(Paragraph("Payment Details", styles['Heading2']))

    table_data = [['ID', 'Amount', 'Date', 'Method', 'Receipt', 'Status']]
    for _, row in df.iterrows():
        table_data.append([
            str(row['id']),
            f"₹{row['amount']:,.2f}",
            row['payment_date'] if row['payment_date'] else '',
            row['payment_method'] if row['payment_method'] else '',
            row['receipt_number'] if row['receipt_number'] else '',
            row['status']
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))

    story.append(table)

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return buffer


def generate_comprehensive_report_pdf():
    """Generate comprehensive PDF report for the entire society management system"""
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Society Management System - Comprehensive Report", title_style))
    story.append(Spacer(1, 20))

    # Report date
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Get society settings
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='anjali@2',
        database='society'
    )
    settings_query = "SELECT society_name, society_address, society_phone, society_email FROM settings WHERE id = 1"
    settings = pd.read_sql_query(settings_query, conn).iloc[0] if not pd.read_sql_query(settings_query, conn).empty else None

    if settings is not None:
        story.append(Paragraph("Society Information", styles['Heading2']))
        society_info = [
            ['Society Name', settings['society_name']],
            ['Address', settings['society_address']],
            ['Phone', settings['society_phone']],
            ['Email', settings['society_email']]
        ]
        society_table = Table(society_info)
        society_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(society_table)
        story.append(Spacer(1, 20))

    # 1. RESIDENTS OVERVIEW
    residents_query = """
    SELECT COUNT(*) as total_residents,
           SUM(CASE WHEN role = 'Owner' THEN 1 ELSE 0 END) as owners,
           SUM(CASE WHEN role = 'Tenant' THEN 1 ELSE 0 END) as tenants
    FROM users WHERE role IN ('Owner', 'Tenant')
    """
    residents_stats = pd.read_sql_query(residents_query, conn)

    blocks_query = "SELECT COUNT(*) as total_blocks FROM blocks"
    blocks_count = pd.read_sql_query(blocks_query, conn).iloc[0]['total_blocks']

    flats_query = """
    SELECT COUNT(*) as total_flats,
           SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied_flats,
           SUM(CASE WHEN status = 'Vacant' THEN 1 ELSE 0 END) as vacant_flats
    FROM flats
    """
    flats_stats = pd.read_sql_query(flats_query, conn)

    story.append(Paragraph("1. Residents & Property Overview", styles['Heading2']))

    overview_data = [
        ['Total Residents', str(residents_stats.iloc[0]['total_residents'])],
        ['Owners', str(residents_stats.iloc[0]['owners'])],
        ['Tenants', str(residents_stats.iloc[0]['tenants'])],
        ['Total Blocks', str(blocks_count)],
        ['Total Flats', str(flats_stats.iloc[0]['total_flats'])],
        ['Occupied Flats', str(flats_stats.iloc[0]['occupied_flats'])],
        ['Vacant Flats', str(flats_stats.iloc[0]['vacant_flats'])]
    ]

    overview_table = Table(overview_data)
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(overview_table)
    story.append(Spacer(1, 20))

    # 2. FINANCIAL OVERVIEW
    payments_query = """
    SELECT COUNT(*) as total_payments,
           SUM(amount) as total_amount,
           SUM(CASE WHEN status = 'Paid' THEN amount ELSE 0 END) as paid_amount,
           SUM(CASE WHEN status = 'Pending' THEN amount ELSE 0 END) as pending_amount
    FROM payments
    """
    payments_stats = pd.read_sql_query(payments_query, conn)

    bills_query = """
    SELECT COUNT(*) as total_bills,
           SUM(amount) as total_bill_amount,
           SUM(CASE WHEN status = 'Paid' THEN amount ELSE 0 END) as paid_bills,
           SUM(CASE WHEN status = 'Unpaid' THEN amount ELSE 0 END) as unpaid_bills,
           SUM(late_fine) as total_late_fines
    FROM maintenance_bills
    """
    bills_stats = pd.read_sql_query(bills_query, conn)

    story.append(Paragraph("2. Financial Overview", styles['Heading2']))

    financial_data = [
        ['Total Payments', str(payments_stats.iloc[0]['total_payments'])],
        ['Total Payment Amount', f"₹{payments_stats.iloc[0]['total_amount'] or 0:,.2f}"],
        ['Paid Amount', f"₹{payments_stats.iloc[0]['paid_amount'] or 0:,.2f}"],
        ['Pending Amount', f"₹{payments_stats.iloc[0]['pending_amount'] or 0:,.2f}"],
        ['Total Maintenance Bills', str(bills_stats.iloc[0]['total_bills'])],
        ['Total Bill Amount', f"₹{bills_stats.iloc[0]['total_bill_amount'] or 0:,.2f}"],
        ['Paid Bills', f"₹{bills_stats.iloc[0]['paid_bills'] or 0:,.2f}"],
        ['Unpaid Bills', f"₹{bills_stats.iloc[0]['unpaid_bills'] or 0:,.2f}"],
        ['Total Late Fines', f"₹{bills_stats.iloc[0]['total_late_fines'] or 0:,.2f}"]
    ]

    financial_table = Table(financial_data)
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(financial_table)
    story.append(Spacer(1, 20))

    # 3. ACTIVITY OVERVIEW
    complaints_query = """
    SELECT COUNT(*) as total_complaints,
           SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved_complaints,
           SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_complaints
    FROM complaints
    """
    complaints_stats = pd.read_sql_query(complaints_query, conn)

    visitors_query = "SELECT COUNT(*) as total_visitors FROM visitors"
    visitors_count = pd.read_sql_query(visitors_query, conn).iloc[0]['total_visitors']

    deliveries_query = "SELECT COUNT(*) as total_deliveries FROM deliveries"
    deliveries_count = pd.read_sql_query(deliveries_query, conn).iloc[0]['total_deliveries']

    parking_query = """
    SELECT COUNT(*) as total_slots,
           SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied_slots,
           SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available_slots
    FROM parking
    """
    parking_stats = pd.read_sql_query(parking_query, conn)

    charity_query = "SELECT COUNT(*) as total_donations FROM charity"
    charity_count = pd.read_sql_query(charity_query, conn).iloc[0]['total_donations']

    events_query = "SELECT COUNT(*) as total_events FROM events"
    events_count = pd.read_sql_query(events_query, conn).iloc[0]['total_events']

    emergency_query = "SELECT COUNT(*) as total_emergencies FROM emergency_logs"
    emergency_count = pd.read_sql_query(emergency_query, conn).iloc[0]['total_emergencies']

    notices_query = "SELECT COUNT(*) as total_notices FROM notices"
    notices_count = pd.read_sql_query(notices_query, conn).iloc[0]['total_notices']

    story.append(Paragraph("3. Activity Overview", styles['Heading2']))

    activity_data = [
        ['Total Complaints', str(complaints_stats.iloc[0]['total_complaints'])],
        ['Resolved Complaints', str(complaints_stats.iloc[0]['resolved_complaints'])],
        ['Open Complaints', str(complaints_stats.iloc[0]['open_complaints'])],
        ['Total Visitors', str(visitors_count)],
        ['Total Deliveries', str(deliveries_count)],
        ['Total Parking Slots', str(parking_stats.iloc[0]['total_slots'])],
        ['Occupied Parking', str(parking_stats.iloc[0]['occupied_slots'])],
        ['Available Parking', str(parking_stats.iloc[0]['available_slots'])],
        ['Total Charity Donations', str(charity_count)],
        ['Total Events', str(events_count)],
        ['Total Emergency Logs', str(emergency_count)],
        ['Total Notices', str(notices_count)]
    ]

    activity_table = Table(activity_data)
    activity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(activity_table)
    story.append(Spacer(1, 20))

    # 4. CHARTS SECTION
    story.append(Paragraph("4. Analytics Charts", styles['Heading2']))

    # Payment status chart
    payments_df = get_payment_data()
    if not payments_df.empty:
        plt.figure(figsize=(8, 6))
        status_counts = payments_df['status'].value_counts()
        colors_list = ['#4CAF50', '#FFC107', '#F44336'][:len(status_counts)]
        status_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors_list)
        plt.title('Payment Status Distribution')
        plt.ylabel('')
        plt.tight_layout()

        chart_buffer = BytesIO()
        plt.savefig(chart_buffer, format='png', dpi=300, bbox_inches='tight')
        chart_buffer.seek(0)
        plt.close()

        story.append(Paragraph("Payment Status Distribution", styles['Heading3']))
        payment_chart = Image(chart_buffer, width=5*inch, height=3.75*inch)
        story.append(payment_chart)
        story.append(Spacer(1, 20))

    # Monthly payment trends
    if not payments_df.empty:
        payments_df['payment_date'] = pd.to_datetime(payments_df['payment_date'], errors='coerce')
        payments_df = payments_df.dropna(subset=['payment_date'])
        if not payments_df.empty:
            monthly_payments = payments_df.groupby(payments_df['payment_date'].dt.to_period('M'))['amount'].sum()

            plt.figure(figsize=(10, 6))
            monthly_payments.plot(kind='bar', color='skyblue')
            plt.title('Monthly Payment Trends')
            plt.xlabel('Month')
            plt.ylabel('Total Amount (₹)')
            plt.xticks(rotation=45)
            plt.tight_layout()

            trend_buffer = BytesIO()
            plt.savefig(trend_buffer, format='png', dpi=300, bbox_inches='tight')
            trend_buffer.seek(0)
            plt.close()

            story.append(Paragraph("Monthly Payment Trends", styles['Heading3']))
            trend_chart = Image(trend_buffer, width=6*inch, height=3.6*inch)
            story.append(trend_chart)
            story.append(Spacer(1, 20))

    # Top payers chart
    if not payments_df.empty:
        top_payers_df = get_resident_payment_summary()
        if not top_payers_df.empty:
            top_payers = top_payers_df.head(5)

            plt.figure(figsize=(10, 6))
            bars = plt.bar(range(len(top_payers)), top_payers['total_paid'], color='lightgreen')
            plt.title('Top 5 Paying Residents')
            plt.xlabel('Residents')
            plt.ylabel('Total Amount Paid (₹)')
            plt.xticks(range(len(top_payers)), [f"{row['name']} ({row['flat_number']})" for _, row in top_payers.iterrows()], rotation=45, ha='right')
            plt.tight_layout()

            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}',
                        ha='center', va='bottom')

            top_payers_buffer = BytesIO()
            plt.savefig(top_payers_buffer, format='png', dpi=300, bbox_inches='tight')
            top_payers_buffer.seek(0)
            plt.close()

            story.append(Paragraph("Top Paying Residents", styles['Heading3']))
            top_payers_chart = Image(top_payers_buffer, width=6*inch, height=3.6*inch)
            story.append(top_payers_chart)
            story.append(Spacer(1, 20))

    conn.close()

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return buffer
