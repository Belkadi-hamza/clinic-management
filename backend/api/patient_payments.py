from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal

from ..db import get_db
from ..schemas.patient_payments import (
    PatientPaymentCreate, PatientPaymentUpdate, PatientPaymentResponse, PatientPaymentSearch,
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseSearch,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceWithPayments, InvoiceSearch,
    InsuranceClaimCreate, InsuranceClaimUpdate, InsuranceClaimResponse, InsuranceClaimSearch,
    PaymentStats, ExpenseStats, RevenueReport, AgingReport,
    BulkPaymentCreate, BulkExpenseCreate
)
from ..crud.patient_payments import (
    get_patient_payments, get_patient_payment_by_id, get_patient_payment_by_code,
    get_payments_by_patient, get_payments_by_visit, get_payments_by_date_range,
    search_patient_payments, create_patient_payment, create_bulk_patient_payments,
    update_patient_payment, delete_patient_payment, process_refund,
    get_expenses, get_expense_by_id, get_expenses_by_date_range, search_expenses,
    create_expense, update_expense, delete_expense,
    get_invoices, get_invoice_by_id, get_invoices_by_patient, get_invoices_by_visit,
    search_invoices, create_invoice, update_invoice, delete_invoice, mark_invoice_as_paid,
    get_insurance_claims, get_insurance_claim_by_id, get_claims_by_patient,
    search_insurance_claims, create_insurance_claim, update_insurance_claim,
    delete_insurance_claim, submit_insurance_claim,
    get_payment_stats, get_expense_stats, get_revenue_report, get_aging_report
)
from ..deps import get_current_user, require_permission
from ..models.system_users import SystemUser

router = APIRouter()

# Patient Payment Endpoints
@router.get("/payments/", response_model=List[PatientPaymentResponse])
def read_patient_payments(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all patient payments"""
    require_permission(current_user, "billing", "read")
    payments = get_patient_payments(db, skip=skip, limit=limit)
    
    enhanced_payments = []
    for payment in payments:
        enhanced_data = PatientPaymentResponse.from_orm(payment)
        
        # Add related information
        if payment.visit and payment.visit.patient:
            enhanced_data.patient_name = f"{payment.visit.patient.first_name} {payment.visit.patient.last_name}"
            enhanced_data.patient_code = payment.visit.patient.patient_code
        
        if payment.visit:
            enhanced_data.visit_date = payment.visit.visit_date
        
        if payment.visit and payment.visit.doctor:
            enhanced_data.doctor_name = f"{payment.visit.doctor.first_name} {payment.visit.doctor.last_name}"
        
        enhanced_payments.append(enhanced_data)
    
    return enhanced_payments

@router.get("/payments/{payment_id}", response_model=PatientPaymentResponse)
def read_patient_payment(
    payment_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get patient payment by ID"""
    require_permission(current_user, "billing", "read")
    payment = get_patient_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Patient payment not found")
    
    enhanced_data = PatientPaymentResponse.from_orm(payment)
    
    # Add related information
    if payment.visit and payment.visit.patient:
        enhanced_data.patient_name = f"{payment.visit.patient.first_name} {payment.visit.patient.last_name}"
        enhanced_data.patient_code = payment.visit.patient.patient_code
    
    if payment.visit:
        enhanced_data.visit_date = payment.visit.visit_date
    
    if payment.visit and payment.visit.doctor:
        enhanced_data.doctor_name = f"{payment.visit.doctor.first_name} {payment.visit.doctor.last_name}"
    
    return enhanced_data

@router.get("/patients/{patient_id}/payments", response_model=List[PatientPaymentResponse])
def read_patient_payments_by_patient(
    patient_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all payments for a specific patient"""
    require_permission(current_user, "billing", "read")
    payments = get_payments_by_patient(db, patient_id)
    
    enhanced_payments = []
    for payment in payments:
        enhanced_data = PatientPaymentResponse.from_orm(payment)
        
        # Add related information
        if payment.visit and payment.visit.patient:
            enhanced_data.patient_name = f"{payment.visit.patient.first_name} {payment.visit.patient.last_name}"
            enhanced_data.patient_code = payment.visit.patient.patient_code
        
        if payment.visit:
            enhanced_data.visit_date = payment.visit.visit_date
        
        if payment.visit and payment.visit.doctor:
            enhanced_data.doctor_name = f"{payment.visit.doctor.first_name} {payment.visit.doctor.last_name}"
        
        enhanced_payments.append(enhanced_data)
    
    return enhanced_payments

@router.get("/visits/{visit_id}/payments", response_model=List[PatientPaymentResponse])
def read_patient_payments_by_visit(
    visit_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all payments for a specific visit"""
    require_permission(current_user, "billing", "read")
    payments = get_payments_by_visit(db, visit_id)
    
    enhanced_payments = []
    for payment in payments:
        enhanced_data = PatientPaymentResponse.from_orm(payment)
        
        # Add related information
        if payment.visit and payment.visit.patient:
            enhanced_data.patient_name = f"{payment.visit.patient.first_name} {payment.visit.patient.last_name}"
            enhanced_data.patient_code = payment.visit.patient.patient_code
        
        if payment.visit:
            enhanced_data.visit_date = payment.visit.visit_date
        
        if payment.visit and payment.visit.doctor:
            enhanced_data.doctor_name = f"{payment.visit.doctor.first_name} {payment.visit.doctor.last_name}"
        
        enhanced_payments.append(enhanced_data)
    
    return enhanced_payments

@router.post("/payments/", response_model=PatientPaymentResponse)
def create_patient_payment_endpoint(
    payment: PatientPaymentCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new patient payment"""
    require_permission(current_user, "billing", "create")
    
    # Validate visit exists
    from ..crud.patients import get_patient_visit_by_id
    visit = get_patient_visit_by_id(db, payment.visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Patient visit not found")
    
    db_payment = create_patient_payment(db, payment, current_user.id)
    
    enhanced_data = PatientPaymentResponse.from_orm(db_payment)
    
    # Add related information
    if db_payment.visit and db_payment.visit.patient:
        enhanced_data.patient_name = f"{db_payment.visit.patient.first_name} {db_payment.visit.patient.last_name}"
        enhanced_data.patient_code = db_payment.visit.patient.patient_code
    
    if db_payment.visit:
        enhanced_data.visit_date = db_payment.visit.visit_date
    
    if db_payment.visit and db_payment.visit.doctor:
        enhanced_data.doctor_name = f"{db_payment.visit.doctor.first_name} {db_payment.visit.doctor.last_name}"
    
    return enhanced_data

@router.post("/payments/bulk", response_model=List[PatientPaymentResponse])
def create_bulk_patient_payments_endpoint(
    bulk_payment: BulkPaymentCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple patient payments"""
    require_permission(current_user, "billing", "create")
    payments = create_bulk_patient_payments(db, bulk_payment.payments, current_user.id)
    
    enhanced_payments = []
    for payment in payments:
        enhanced_data = PatientPaymentResponse.from_orm(payment)
        
        # Add related information
        if payment.visit and payment.visit.patient:
            enhanced_data.patient_name = f"{payment.visit.patient.first_name} {payment.visit.patient.last_name}"
            enhanced_data.patient_code = payment.visit.patient.patient_code
        
        if payment.visit:
            enhanced_data.visit_date = payment.visit.visit_date
        
        if payment.visit and payment.visit.doctor:
            enhanced_data.doctor_name = f"{payment.visit.doctor.first_name} {payment.visit.doctor.last_name}"
        
        enhanced_payments.append(enhanced_data)
    
    return enhanced_payments

@router.put("/payments/{payment_id}", response_model=PatientPaymentResponse)
def update_patient_payment_endpoint(
    payment_id: int,
    payment: PatientPaymentUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update patient payment"""
    require_permission(current_user, "billing", "update")
    db_payment = update_patient_payment(db, payment_id, payment, current_user.id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Patient payment not found")
    
    enhanced_data = PatientPaymentResponse.from_orm(db_payment)
    
    # Add related information
    if db_payment.visit and db_payment.visit.patient:
        enhanced_data.patient_name = f"{db_payment.visit.patient.first_name} {db_payment.visit.patient.last_name}"
        enhanced_data.patient_code = db_payment.visit.patient.patient_code
    
    if db_payment.visit:
        enhanced_data.visit_date = db_payment.visit.visit_date
    
    if db_payment.visit and db_payment.visit.doctor:
        enhanced_data.doctor_name = f"{db_payment.visit.doctor.first_name} {db_payment.visit.doctor.last_name}"
    
    return enhanced_data

@router.delete("/payments/{payment_id}")
def delete_patient_payment_endpoint(
    payment_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete patient payment"""
    require_permission(current_user, "billing", "delete")
    db_payment = delete_patient_payment(db, payment_id, current_user.id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Patient payment not found")
    return {"message": "Patient payment deleted successfully"}

@router.post("/payments/{payment_id}/refund")
def refund_patient_payment_endpoint(
    payment_id: int,
    refund_reason: str,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process payment refund"""
    require_permission(current_user, "billing", "update")
    try:
        refund_payment = process_refund(db, payment_id, refund_reason, current_user.id)
        if not refund_payment:
            raise HTTPException(status_code=404, detail="Patient payment not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Payment refund processed successfully", "refund_code": refund_payment.payment_code}

@router.post("/payments/search/", response_model=List[PatientPaymentResponse])
def search_patient_payments_endpoint(
    search: PatientPaymentSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search patient payments with filters"""
    require_permission(current_user, "billing", "read")
    payments = search_patient_payments(db, search, skip=skip, limit=limit)
    
    enhanced_payments = []
    for payment in payments:
        enhanced_data = PatientPaymentResponse.from_orm(payment)
        
        # Add related information
        if payment.visit and payment.visit.patient:
            enhanced_data.patient_name = f"{payment.visit.patient.first_name} {payment.visit.patient.last_name}"
            enhanced_data.patient_code = payment.visit.patient.patient_code
        
        if payment.visit:
            enhanced_data.visit_date = payment.visit.visit_date
        
        if payment.visit and payment.visit.doctor:
            enhanced_data.doctor_name = f"{payment.visit.doctor.first_name} {payment.visit.doctor.last_name}"
        
        enhanced_payments.append(enhanced_data)
    
    return enhanced_payments

# Expense Endpoints
@router.get("/expenses/", response_model=List[ExpenseResponse])
def read_expenses(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all expenses"""
    require_permission(current_user, "billing", "read")
    expenses = get_expenses(db, skip=skip, limit=limit)
    
    enhanced_expenses = []
    for expense in expenses:
        enhanced_data = ExpenseResponse.from_orm(expense)
        
        # Add related information
        if expense.category:
            enhanced_data.category_name = expense.category.category_name
        
        if expense.recorded_by_doctor:
            enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
        
        enhanced_expenses.append(enhanced_data)
    
    return enhanced_expenses

@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def read_expense(
    expense_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense by ID"""
    require_permission(current_user, "billing", "read")
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    enhanced_data = ExpenseResponse.from_orm(expense)
    
    # Add related information
    if expense.category:
        enhanced_data.category_name = expense.category.category_name
    
    if expense.recorded_by_doctor:
        enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
    
    return enhanced_data

@router.post("/expenses/", response_model=ExpenseResponse)
def create_expense_endpoint(
    expense: ExpenseCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new expense"""
    require_permission(current_user, "billing", "create")
    
    # Validate category if provided
    if expense.category_id:
        from ..crud.billing_categories import get_billing_category_by_id
        category = get_billing_category_by_id(db, expense.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Billing category not found")
    
    # Validate doctor if provided
    if expense.recorded_by_doctor_id:
        from ..crud.doctors import get_doctor_by_id
        doctor = get_doctor_by_id(db, expense.recorded_by_doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
    
    db_expense = create_expense(db, expense, current_user.id)
    
    enhanced_data = ExpenseResponse.from_orm(db_expense)
    
    # Add related information
    if db_expense.category:
        enhanced_data.category_name = db_expense.category.category_name
    
    if db_expense.recorded_by_doctor:
        enhanced_data.doctor_name = f"{db_expense.recorded_by_doctor.first_name} {db_expense.recorded_by_doctor.last_name}"
    
    return enhanced_data

@router.post("/expenses/bulk", response_model=List[ExpenseResponse])
def create_bulk_expenses_endpoint(
    bulk_expense: BulkExpenseCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple expenses"""
    require_permission(current_user, "billing", "create")
    expenses = []
    for expense_data in bulk_expense.expenses:
        expense = ExpenseCreate(**expense_data)
        db_expense = create_expense(db, expense, current_user.id)
        expenses.append(db_expense)
    
    enhanced_expenses = []
    for expense in expenses:
        enhanced_data = ExpenseResponse.from_orm(expense)
        
        # Add related information
        if expense.category:
            enhanced_data.category_name = expense.category.category_name
        
        if expense.recorded_by_doctor:
            enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
        
        enhanced_expenses.append(enhanced_data)
    
    return enhanced_expenses

@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense_endpoint(
    expense_id: int,
    expense: ExpenseUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update expense"""
    require_permission(current_user, "billing", "update")
    db_expense = update_expense(db, expense_id, expense, current_user.id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    enhanced_data = ExpenseResponse.from_orm(db_expense)
    
    # Add related information
    if db_expense.category:
        enhanced_data.category_name = db_expense.category.category_name
    
    if db_expense.recorded_by_doctor:
        enhanced_data.doctor_name = f"{db_expense.recorded_by_doctor.first_name} {db_expense.recorded_by_doctor.last_name}"
    
    return enhanced_data

@router.delete("/expenses/{expense_id}")
def delete_expense_endpoint(
    expense_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete expense"""
    require_permission(current_user, "billing", "delete")
    db_expense = delete_expense(db, expense_id, current_user.id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}

@router.post("/expenses/search/", response_model=List[ExpenseResponse])
def search_expenses_endpoint(
    search: ExpenseSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search expenses with filters"""
    require_permission(current_user, "billing", "read")
    expenses = search_expenses(db, search, skip=skip, limit=limit)
    
    enhanced_expenses = []
    for expense in expenses:
        enhanced_data = ExpenseResponse.from_orm(expense)
        
        # Add related information
        if expense.category:
            enhanced_data.category_name = expense.category.category_name
        
        if expense.recorded_by_doctor:
            enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
        
        enhanced_expenses.append(enhanced_data)
    
    return enhanced_expenses

# Statistics and Reports
@router.get("/stats/payments", response_model=PaymentStats)
def get_payment_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment statistics"""
    require_permission(current_user, "billing", "read")
    stats = get_payment_stats(db, start_date, end_date)
    return PaymentStats(**stats)

@router.get("/stats/expenses", response_model=ExpenseStats)
def get_expense_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense statistics"""
    require_permission(current_user, "billing", "read")
    stats = get_expense_stats(db, start_date, end_date)
    return ExpenseStats(**stats)

@router.get("/reports/revenue")
def get_revenue_report_endpoint(
    start_date: date,
    end_date: date,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive revenue report"""
    require_permission(current_user, "billing", "read")
    report = get_revenue_report(db, start_date, end_date)
    return report

@router.get("/reports/aging")
def get_aging_report_endpoint(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get accounts receivable aging report"""
    require_permission(current_user, "billing", "read")
    report = get_aging_report(db)
    return report

@router.get("/reports/daily-summary")
def get_daily_summary_report(
    report_date: date = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily financial summary"""
    require_permission(current_user, "billing", "read")
    
    if not report_date:
        report_date = date.today()
    
    # Daily payments
    daily_payments = get_payments_by_date_range(db, report_date, report_date)
    total_daily_revenue = sum(p.amount for p in daily_payments if not p.is_refund)
    
    # Daily expenses
    daily_expenses = get_expenses_by_date_range(db, report_date, report_date)
    total_daily_expenses = sum(e.amount for e in daily_expenses)
    
    # Payment method breakdown
    payment_methods = {}
    for payment in daily_payments:
        if not payment.is_refund:
            method = payment.payment_method
            payment_methods[method] = payment_methods.get(method, 0) + payment.amount
    
    return {
        "date": report_date,
        "total_revenue": total_daily_revenue,
        "total_expenses": total_daily_expenses,
        "net_income": total_daily_revenue - total_daily_expenses,
        "payment_count": len(daily_payments),
        "expense_count": len(daily_expenses),
        "payment_methods": payment_methods
    }