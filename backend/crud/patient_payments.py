from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from ..models.patient_payments import PatientPayment, Expense, Invoice, InsuranceClaim
from ..models.patients import Patient
from ..models.doctors import Doctor
from ..models.patient_visits import PatientVisit
from ..models.billing_categories import BillingCategory
from ..schemas.patient_payments import (
    PatientPaymentCreate, PatientPaymentUpdate, ExpenseCreate, ExpenseUpdate,
    InvoiceCreate, InvoiceUpdate, InsuranceClaimCreate, InsuranceClaimUpdate,
    PatientPaymentSearch, ExpenseSearch, InvoiceSearch, InsuranceClaimSearch
)

logger = logging.getLogger(__name__)

# Patient Payment CRUD operations
def generate_payment_code(db: Session):
    """Generate unique payment code"""
    from datetime import datetime
    prefix = "PAY"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(PatientPayment).filter(
        PatientPayment.payment_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.payment_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_patient_payments(db: Session, skip: int = 0, limit: int = 100):
    """Get all patient payments"""
    return db.query(PatientPayment).filter(PatientPayment.deleted_at == None)\
        .order_by(PatientPayment.payment_date.desc())\
        .offset(skip).limit(limit).all()

def get_patient_payment_by_id(db: Session, payment_id: int):
    """Get patient payment by ID"""
    return db.query(PatientPayment).filter(
        PatientPayment.id == payment_id,
        PatientPayment.deleted_at == None
    ).first()

def get_patient_payment_by_code(db: Session, payment_code: str):
    """Get patient payment by code"""
    return db.query(PatientPayment).filter(
        PatientPayment.payment_code == payment_code,
        PatientPayment.deleted_at == None
    ).first()

def get_payments_by_patient(db: Session, patient_id: int):
    """Get all payments for a specific patient"""
    return db.query(PatientPayment).join(PatientVisit).filter(
        PatientVisit.patient_id == patient_id,
        PatientPayment.deleted_at == None
    ).order_by(PatientPayment.payment_date.desc()).all()

def get_payments_by_visit(db: Session, visit_id: int):
    """Get all payments for a specific visit"""
    return db.query(PatientPayment).filter(
        PatientPayment.visit_id == visit_id,
        PatientPayment.deleted_at == None
    ).order_by(PatientPayment.payment_date.asc()).all()

def get_payments_by_date_range(db: Session, start_date: date, end_date: date):
    """Get payments within a date range"""
    return db.query(PatientPayment).filter(
        PatientPayment.payment_date >= start_date,
        PatientPayment.payment_date <= end_date,
        PatientPayment.deleted_at == None
    ).order_by(PatientPayment.payment_date.asc()).all()

def search_patient_payments(db: Session, search: PatientPaymentSearch, skip: int = 0, limit: int = 100):
    """Search patient payments with filters"""
    query = db.query(PatientPayment).filter(PatientPayment.deleted_at == None)
    
    if search.patient_name:
        query = query.join(PatientVisit).join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.date_from:
        query = query.filter(PatientPayment.payment_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(PatientPayment.payment_date <= search.date_to)
    
    if search.payment_method:
        query = query.filter(PatientPayment.payment_method == search.payment_method)
    
    if search.status:
        query = query.filter(PatientPayment.status == search.status)
    
    if search.min_amount:
        query = query.filter(PatientPayment.amount >= search.min_amount)
    
    if search.max_amount:
        query = query.filter(PatientPayment.amount <= search.max_amount)
    
    return query.order_by(PatientPayment.payment_date.desc())\
        .offset(skip).limit(limit).all()

def create_patient_payment(db: Session, payment: PatientPaymentCreate, user_id: int):
    """Create new patient payment"""
    payment_code = generate_payment_code(db)
    db_payment = PatientPayment(**payment.dict(), payment_code=payment_code, created_by=user_id)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def create_bulk_patient_payments(db: Session, payments: List[PatientPaymentCreate], user_id: int):
    """Create multiple patient payments"""
    created_payments = []
    
    for payment_data in payments:
        payment = PatientPaymentCreate(**payment_data.dict())
        try:
            db_payment = create_patient_payment(db, payment, user_id)
            created_payments.append(db_payment)
        except Exception as e:
            logger.error(f"Failed to create payment: {e}")
            continue
    
    return created_payments

def update_patient_payment(db: Session, payment_id: int, payment: PatientPaymentUpdate, user_id: int):
    """Update patient payment"""
    db_payment = db.query(PatientPayment).filter(
        PatientPayment.id == payment_id,
        PatientPayment.deleted_at == None
    ).first()
    
    if not db_payment:
        return None
    
    for key, value in payment.dict(exclude_unset=True).items():
        setattr(db_payment, key, value)
    
    db_payment.updated_by = user_id
    db.commit()
    db.refresh(db_payment)
    return db_payment

def delete_patient_payment(db: Session, payment_id: int, user_id: int):
    """Soft delete patient payment"""
    db_payment = db.query(PatientPayment).filter(
        PatientPayment.id == payment_id,
        PatientPayment.deleted_at == None
    ).first()
    
    if not db_payment:
        return None
    
    db_payment.deleted_at = func.now()
    db_payment.deleted_by = user_id
    db.commit()
    return db_payment

def process_refund(db: Session, payment_id: int, refund_reason: str, user_id: int):
    """Process a payment refund"""
    db_payment = db.query(PatientPayment).filter(
        PatientPayment.id == payment_id,
        PatientPayment.deleted_at == None
    ).first()
    
    if not db_payment:
        return None
    
    if db_payment.is_refund:
        raise ValueError("Payment is already a refund")
    
    # Create refund payment
    refund_payment = PatientPayment(
        visit_id=db_payment.visit_id,
        payment_date=date.today(),
        amount=db_payment.amount,
        payment_method=db_payment.payment_method,
        bank_name=db_payment.bank_name,
        check_number=db_payment.check_number,
        status='completed',
        is_refund=True,
        refund_reason=refund_reason,
        created_by=user_id
    )
    
    # Update original payment status
    db_payment.status = 'refunded'
    db_payment.updated_by = user_id
    
    db.add(refund_payment)
    db.commit()
    db.refresh(refund_payment)
    return refund_payment

# Expense CRUD operations
def generate_expense_code(db: Session):
    """Generate unique expense code"""
    from datetime import datetime
    prefix = "EXP"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(Expense).filter(
        Expense.expense_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.expense_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_expenses(db: Session, skip: int = 0, limit: int = 100):
    """Get all expenses"""
    return db.query(Expense).filter(Expense.deleted_at == None)\
        .order_by(Expense.expense_date.desc())\
        .offset(skip).limit(limit).all()

def get_expense_by_id(db: Session, expense_id: int):
    """Get expense by ID"""
    return db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.deleted_at == None
    ).first()

def get_expenses_by_date_range(db: Session, start_date: date, end_date: date):
    """Get expenses within a date range"""
    return db.query(Expense).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
        Expense.deleted_at == None
    ).order_by(Expense.expense_date.asc()).all()

def search_expenses(db: Session, search: ExpenseSearch, skip: int = 0, limit: int = 100):
    """Search expenses with filters"""
    query = db.query(Expense).filter(Expense.deleted_at == None)
    
    if search.date_from:
        query = query.filter(Expense.expense_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(Expense.expense_date <= search.date_to)
    
    if search.category_id:
        query = query.filter(Expense.category_id == search.category_id)
    
    if search.vendor_name:
        query = query.filter(Expense.vendor_name.ilike(f"%{search.vendor_name}%"))
    
    if search.payment_method:
        query = query.filter(Expense.payment_method == search.payment_method)
    
    if search.min_amount:
        query = query.filter(Expense.amount >= search.min_amount)
    
    if search.max_amount:
        query = query.filter(Expense.amount <= search.max_amount)
    
    return query.order_by(Expense.expense_date.desc())\
        .offset(skip).limit(limit).all()

def create_expense(db: Session, expense: ExpenseCreate, user_id: int):
    """Create new expense"""
    expense_code = generate_expense_code(db)
    db_expense = Expense(**expense.dict(), expense_code=expense_code, created_by=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def update_expense(db: Session, expense_id: int, expense: ExpenseUpdate, user_id: int):
    """Update expense"""
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.deleted_at == None
    ).first()
    
    if not db_expense:
        return None
    
    for key, value in expense.dict(exclude_unset=True).items():
        setattr(db_expense, key, value)
    
    db_expense.updated_by = user_id
    db.commit()
    db.refresh(db_expense)
    return db_expense

def delete_expense(db: Session, expense_id: int, user_id: int):
    """Soft delete expense"""
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.deleted_at == None
    ).first()
    
    if not db_expense:
        return None
    
    db_expense.deleted_at = func.now()
    db_expense.deleted_by = user_id
    db.commit()
    return db_expense

# Invoice CRUD operations
def generate_invoice_code(db: Session):
    """Generate unique invoice code"""
    from datetime import datetime
    prefix = "INV"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(Invoice).filter(
        Invoice.invoice_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.invoice_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_invoices(db: Session, skip: int = 0, limit: int = 100):
    """Get all invoices"""
    return db.query(Invoice).filter(Invoice.deleted_at == None)\
        .order_by(Invoice.invoice_date.desc())\
        .offset(skip).limit(limit).all()

def get_invoice_by_id(db: Session, invoice_id: int):
    """Get invoice by ID"""
    return db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.deleted_at == None
    ).first()

def get_invoices_by_patient(db: Session, patient_id: int):
    """Get all invoices for a specific patient"""
    return db.query(Invoice).join(PatientVisit).filter(
        PatientVisit.patient_id == patient_id,
        Invoice.deleted_at == None
    ).order_by(Invoice.invoice_date.desc()).all()

def get_invoices_by_visit(db: Session, visit_id: int):
    """Get all invoices for a specific visit"""
    return db.query(Invoice).filter(
        Invoice.visit_id == visit_id,
        Invoice.deleted_at == None
    ).order_by(Invoice.invoice_date.desc()).all()

def search_invoices(db: Session, search: InvoiceSearch, skip: int = 0, limit: int = 100):
    """Search invoices with filters"""
    query = db.query(Invoice).filter(Invoice.deleted_at == None)
    
    if search.patient_name:
        query = query.join(PatientVisit).join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.date_from:
        query = query.filter(Invoice.invoice_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(Invoice.invoice_date <= search.date_to)
    
    if search.status:
        query = query.filter(Invoice.status == search.status)
    
    if search.min_amount:
        query = query.filter(Invoice.total_amount >= search.min_amount)
    
    if search.max_amount:
        query = query.filter(Invoice.total_amount <= search.max_amount)
    
    return query.order_by(Invoice.invoice_date.desc())\
        .offset(skip).limit(limit).all()

def create_invoice(db: Session, invoice: InvoiceCreate, user_id: int):
    """Create new invoice"""
    invoice_code = generate_invoice_code(db)
    db_invoice = Invoice(**invoice.dict(), invoice_code=invoice_code, created_by=user_id)
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def update_invoice(db: Session, invoice_id: int, invoice: InvoiceUpdate, user_id: int):
    """Update invoice"""
    db_invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.deleted_at == None
    ).first()
    
    if not db_invoice:
        return None
    
    for key, value in invoice.dict(exclude_unset=True).items():
        setattr(db_invoice, key, value)
    
    db_invoice.updated_by = user_id
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def delete_invoice(db: Session, invoice_id: int, user_id: int):
    """Soft delete invoice"""
    db_invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.deleted_at == None
    ).first()
    
    if not db_invoice:
        return None
    
    db_invoice.deleted_at = func.now()
    db_invoice.deleted_by = user_id
    db.commit()
    return db_invoice

def mark_invoice_as_paid(db: Session, invoice_id: int, user_id: int):
    """Mark invoice as paid"""
    db_invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.deleted_at == None
    ).first()
    
    if not db_invoice:
        return None
    
    db_invoice.status = 'paid'
    db_invoice.paid_amount = db_invoice.total_amount
    db_invoice.balance_amount = 0
    db_invoice.updated_by = user_id
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

# Insurance Claim CRUD operations
def generate_claim_code(db: Session):
    """Generate unique insurance claim code"""
    from datetime import datetime
    prefix = "CLM"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(InsuranceClaim).filter(
        InsuranceClaim.claim_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.claim_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_insurance_claims(db: Session, skip: int = 0, limit: int = 100):
    """Get all insurance claims"""
    return db.query(InsuranceClaim).filter(InsuranceClaim.deleted_at == None)\
        .order_by(InsuranceClaim.claim_date.desc())\
        .offset(skip).limit(limit).all()

def get_insurance_claim_by_id(db: Session, claim_id: int):
    """Get insurance claim by ID"""
    return db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.deleted_at == None
    ).first()

def get_claims_by_patient(db: Session, patient_id: int):
    """Get all insurance claims for a specific patient"""
    return db.query(InsuranceClaim).join(PatientVisit).filter(
        PatientVisit.patient_id == patient_id,
        InsuranceClaim.deleted_at == None
    ).order_by(InsuranceClaim.claim_date.desc()).all()

def search_insurance_claims(db: Session, search: InsuranceClaimSearch, skip: int = 0, limit: int = 100):
    """Search insurance claims with filters"""
    query = db.query(InsuranceClaim).filter(InsuranceClaim.deleted_at == None)
    
    if search.patient_name:
        query = query.join(PatientVisit).join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.insurance_company:
        query = query.filter(InsuranceClaim.insurance_company.ilike(f"%{search.insurance_company}%"))
    
    if search.date_from:
        query = query.filter(InsuranceClaim.claim_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(InsuranceClaim.claim_date <= search.date_to)
    
    if search.status:
        query = query.filter(InsuranceClaim.status == search.status)
    
    return query.order_by(InsuranceClaim.claim_date.desc())\
        .offset(skip).limit(limit).all()

def create_insurance_claim(db: Session, claim: InsuranceClaimCreate, user_id: int):
    """Create new insurance claim"""
    claim_code = generate_claim_code(db)
    db_claim = InsuranceClaim(**claim.dict(), claim_code=claim_code, created_by=user_id)
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim

def update_insurance_claim(db: Session, claim_id: int, claim: InsuranceClaimUpdate, user_id: int):
    """Update insurance claim"""
    db_claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.deleted_at == None
    ).first()
    
    if not db_claim:
        return None
    
    for key, value in claim.dict(exclude_unset=True).items():
        setattr(db_claim, key, value)
    
    db_claim.updated_by = user_id
    db.commit()
    db.refresh(db_claim)
    return db_claim

def delete_insurance_claim(db: Session, claim_id: int, user_id: int):
    """Soft delete insurance claim"""
    db_claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.deleted_at == None
    ).first()
    
    if not db_claim:
        return None
    
    db_claim.deleted_at = func.now()
    db_claim.deleted_by = user_id
    db.commit()
    return db_claim

def submit_insurance_claim(db: Session, claim_id: int, user_id: int):
    """Submit insurance claim for processing"""
    db_claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.deleted_at == None
    ).first()
    
    if not db_claim:
        return None
    
    if db_claim.status != 'draft':
        raise ValueError("Only draft claims can be submitted")
    
    db_claim.status = 'submitted'
    db_claim.submission_date = date.today()
    db_claim.updated_by = user_id
    
    db.commit()
    db.refresh(db_claim)
    return db_claim

# Statistics and Reports
def get_payment_stats(db: Session, start_date: date = None, end_date: date = None):
    """Get payment statistics"""
    query = db.query(PatientPayment).filter(
        PatientPayment.deleted_at == None,
        PatientPayment.is_refund == False
    )
    
    if start_date:
        query = query.filter(PatientPayment.payment_date >= start_date)
    if end_date:
        query = query.filter(PatientPayment.payment_date <= end_date)
    
    total_payments = query.count()
    total_revenue = query.with_entities(func.sum(PatientPayment.amount)).scalar() or 0
    
    # Payment method breakdown
    cash_payments = query.filter(PatientPayment.payment_method == 'cash').with_entities(func.sum(PatientPayment.amount)).scalar() or 0
    card_payments = query.filter(PatientPayment.payment_method == 'card').with_entities(func.sum(PatientPayment.amount)).scalar() or 0
    check_payments = query.filter(PatientPayment.payment_method == 'check').with_entities(func.sum(PatientPayment.amount)).scalar() or 0
    transfer_payments = query.filter(PatientPayment.payment_method == 'transfer').with_entities(func.sum(PatientPayment.amount)).scalar() or 0
    
    # Pending payments
    pending_payments = query.filter(PatientPayment.status == 'pending').count()
    
    # Refunded amount
    refunded_amount = db.query(func.sum(PatientPayment.amount)).filter(
        PatientPayment.deleted_at == None,
        PatientPayment.is_refund == True
    ).scalar() or 0
    
    return {
        "total_payments": total_payments,
        "total_revenue": total_revenue,
        "cash_payments": cash_payments,
        "card_payments": card_payments,
        "check_payments": check_payments,
        "transfer_payments": transfer_payments,
        "pending_payments": pending_payments,
        "refunded_amount": refunded_amount
    }

def get_expense_stats(db: Session, start_date: date = None, end_date: date = None):
    """Get expense statistics"""
    query = db.query(Expense).filter(Expense.deleted_at == None)
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    total_expenses = query.count()
    total_amount = query.with_entities(func.sum(Expense.amount)).scalar() or 0
    
    # Expenses by category
    by_category = db.query(
        BillingCategory.category_name,
        func.sum(Expense.amount).label('amount')
    ).join(Expense).filter(
        Expense.deleted_at == None
    ).group_by(BillingCategory.category_name).all()
    
    # Recurring expenses
    recurring_expenses = query.filter(Expense.is_recurring == True).count()
    
    return {
        "total_expenses": total_expenses,
        "total_amount": total_amount,
        "by_category": [{"category": cat.category_name, "amount": float(amount)} for cat, amount in by_category],
        "recurring_expenses": recurring_expenses
    }

def get_revenue_report(db: Session, start_date: date, end_date: date):
    """Get comprehensive revenue report"""
    # Total revenue
    total_revenue = db.query(func.sum(PatientPayment.amount)).filter(
        PatientPayment.deleted_at == None,
        PatientPayment.is_refund == False,
        PatientPayment.payment_date >= start_date,
        PatientPayment.payment_date <= end_date
    ).scalar() or 0
    
    # Total expenses
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.deleted_at == None,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).scalar() or 0
    
    net_income = total_revenue - total_expenses
    
    # Revenue by payment method
    by_payment_method = db.query(
        PatientPayment.payment_method,
        func.sum(PatientPayment.amount).label('amount')
    ).filter(
        PatientPayment.deleted_at == None,
        PatientPayment.is_refund == False,
        PatientPayment.payment_date >= start_date,
        PatientPayment.payment_date <= end_date
    ).group_by(PatientPayment.payment_method).all()
    
    # Revenue by service category (simplified)
    by_category = db.query(
        func.sum(PatientPayment.amount).label('amount')
    ).filter(
        PatientPayment.deleted_at == None,
        PatientPayment.is_refund == False,
        PatientPayment.payment_date >= start_date,
        PatientPayment.payment_date <= end_date
    ).scalar() or 0
    
    return {
        "period": f"{start_date} to {end_date}",
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "by_payment_method": [{"method": method, "amount": float(amount)} for method, amount in by_payment_method],
        "by_category": [{"category": "Medical Services", "amount": float(by_category)}]
    }

def get_aging_report(db: Session):
    """Get accounts receivable aging report"""
    today = date.today()
    
    # Current (0-30 days)
    current_date = today - timedelta(days=30)
    current = db.query(func.sum(Invoice.balance_amount)).filter(
        Invoice.deleted_at == None,
        Invoice.due_date >= current_date,
        Invoice.status.in_(['sent', 'overdue'])
    ).scalar() or 0
    
    # 31-60 days
    days_30_date = today - timedelta(days=60)
    days_30 = db.query(func.sum(Invoice.balance_amount)).filter(
        Invoice.deleted_at == None,
        Invoice.due_date >= days_30_date,
        Invoice.due_date < current_date,
        Invoice.status.in_(['sent', 'overdue'])
    ).scalar() or 0
    
    # 61-90 days
    days_60_date = today - timedelta(days=90)
    days_60 = db.query(func.sum(Invoice.balance_amount)).filter(
        Invoice.deleted_at == None,
        Invoice.due_date >= days_60_date,
        Invoice.due_date < days_30_date,
        Invoice.status.in_(['sent', 'overdue'])
    ).scalar() or 0
    
    # 91+ days
    days_90 = db.query(func.sum(Invoice.balance_amount)).filter(
        Invoice.deleted_at == None,
        Invoice.due_date < days_60_date,
        Invoice.status.in_(['sent', 'overdue'])
    ).scalar() or 0
    
    total_outstanding = current + days_30 + days_60 + days_90
    
    return {
        "period": f"As of {today}",
        "current": current,
        "days_30": days_30,
        "days_60": days_60,
        "days_90": days_90,
        "over_90": days_90,
        "total_outstanding": total_outstanding
    }