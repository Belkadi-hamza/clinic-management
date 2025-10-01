from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal

from ..db import get_db
from ..schemas.expenses import (
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse, ExpenseCategoryTree,
    ExpenseCategorySearch, ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseWithDetails,
    ExpenseSearch, ExpenseBudgetCreate, ExpenseBudgetUpdate, ExpenseBudgetResponse,
    ExpenseBudgetSearch, VendorCreate, VendorUpdate, VendorResponse, VendorSearch,
    ExpenseStats, MonthlyBudgetReport, VendorSummary, ExpenseTrend,
    BulkExpenseCreate, BulkBudgetCreate, ExpenseApproval
)
from ..crud.expenses import (
    get_expense_categories, get_expense_category_by_id, get_expense_category_by_code,
    get_root_categories, get_sub_categories, get_category_tree, search_expense_categories,
    create_expense_category, update_expense_category, delete_expense_category,
    get_expenses, get_expense_by_id, get_expense_by_code, get_expenses_by_category,
    get_expenses_by_date_range, get_pending_approval_expenses, get_recurring_expenses,
    search_expenses, create_expense, create_bulk_expenses, update_expense, delete_expense,
    submit_expense_for_approval, approve_expense, mark_expense_as_paid, process_recurring_expenses,
    get_expense_budgets, get_expense_budget_by_id, get_budget_by_category_and_period,
    get_budgets_by_period, search_expense_budgets, create_expense_budget,
    create_bulk_expense_budgets, update_expense_budget, delete_expense_budget,
    get_vendors, get_vendor_by_id, get_vendor_by_code, search_vendors,
    create_vendor, update_vendor, delete_vendor,
    get_expense_stats, get_budget_vs_actual, get_vendor_summary, get_expense_trends
)
from ..deps import get_current_user, require_permission
from ..models.system_users import SystemUser

router = APIRouter()

# Expense Category Endpoints
@router.get("/categories/", response_model=List[ExpenseCategoryResponse])
def read_expense_categories(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all expense categories"""
    require_permission(current_user, "billing", "read")
    categories = get_expense_categories(db, skip=skip, limit=limit)
    
    enhanced_categories = []
    for category in categories:
        enhanced_data = ExpenseCategoryResponse.from_orm(category)
        
        # Add parent category name
        if category.parent_category:
            enhanced_data.parent_category_name = category.parent_category.category_name
        
        # Count sub-categories
        sub_categories = get_sub_categories(db, category.id)
        enhanced_data.sub_category_count = len(sub_categories)
        
        # Count expenses
        expenses = get_expenses_by_category(db, category.id)
        enhanced_data.expense_count = len(expenses)
        
        # Calculate current month spent
        today = date.today()
        current_month_expenses = db.query(func.sum(Expense.amount)).filter(
            Expense.category_id == category.id,
            Expense.deleted_at == None,
            Expense.expense_date >= date(today.year, today.month, 1),
            Expense.expense_date <= today
        ).scalar() or 0
        enhanced_data.current_month_spent = current_month_expenses
        
        enhanced_categories.append(enhanced_data)
    
    return enhanced_categories

@router.get("/categories/root", response_model=List[ExpenseCategoryResponse])
def read_root_categories(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all root categories (no parent)"""
    require_permission(current_user, "billing", "read")
    categories = get_root_categories(db)
    
    enhanced_categories = []
    for category in categories:
        enhanced_data = ExpenseCategoryResponse.from_orm(category)
        
        # Count sub-categories
        sub_categories = get_sub_categories(db, category.id)
        enhanced_data.sub_category_count = len(sub_categories)
        
        # Count expenses
        expenses = get_expenses_by_category(db, category.id)
        enhanced_data.expense_count = len(expenses)
        
        enhanced_categories.append(enhanced_data)
    
    return enhanced_categories

@router.get("/categories/{category_id}", response_model=ExpenseCategoryResponse)
def read_expense_category(
    category_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense category by ID"""
    require_permission(current_user, "billing", "read")
    category = get_expense_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Expense category not found")
    
    enhanced_data = ExpenseCategoryResponse.from_orm(category)
    
    # Add parent category name
    if category.parent_category:
        enhanced_data.parent_category_name = category.parent_category.category_name
    
    # Count sub-categories
    sub_categories = get_sub_categories(db, category_id)
    enhanced_data.sub_category_count = len(sub_categories)
    
    # Count expenses
    expenses = get_expenses_by_category(db, category_id)
    enhanced_data.expense_count = len(expenses)
    
    # Calculate current month spent
    today = date.today()
    current_month_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.category_id == category_id,
        Expense.deleted_at == None,
        Expense.expense_date >= date(today.year, today.month, 1),
        Expense.expense_date <= today
    ).scalar() or 0
    enhanced_data.current_month_spent = current_month_expenses
    
    return enhanced_data

@router.get("/categories/tree/hierarchy", response_model=List[ExpenseCategoryTree])
def read_category_tree(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete category hierarchy tree"""
    require_permission(current_user, "billing", "read")
    tree = get_category_tree(db)
    return tree

@router.post("/categories/", response_model=ExpenseCategoryResponse)
def create_expense_category_endpoint(
    category: ExpenseCategoryCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new expense category"""
    require_permission(current_user, "billing", "create")
    
    # Validate parent category if provided
    if category.parent_category_id:
        parent_category = get_expense_category_by_id(db, category.parent_category_id)
        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")
    
    db_category = create_expense_category(db, category, current_user.id)
    
    enhanced_data = ExpenseCategoryResponse.from_orm(db_category)
    
    # Add parent category name
    if db_category.parent_category:
        enhanced_data.parent_category_name = db_category.parent_category.category_name
    
    return enhanced_data

@router.put("/categories/{category_id}", response_model=ExpenseCategoryResponse)
def update_expense_category_endpoint(
    category_id: int,
    category: ExpenseCategoryUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update expense category"""
    require_permission(current_user, "billing", "update")
    try:
        db_category = update_expense_category(db, category_id, category, current_user.id)
        if not db_category:
            raise HTTPException(status_code=404, detail="Expense category not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = ExpenseCategoryResponse.from_orm(db_category)
    
    # Add parent category name
    if db_category.parent_category:
        enhanced_data.parent_category_name = db_category.parent_category.category_name
    
    # Count sub-categories
    sub_categories = get_sub_categories(db, category_id)
    enhanced_data.sub_category_count = len(sub_categories)
    
    # Count expenses
    expenses = get_expenses_by_category(db, category_id)
    enhanced_data.expense_count = len(expenses)
    
    return enhanced_data

@router.delete("/categories/{category_id}")
def delete_expense_category_endpoint(
    category_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete expense category"""
    require_permission(current_user, "billing", "delete")
    try:
        db_category = delete_expense_category(db, category_id, current_user.id)
        if not db_category:
            raise HTTPException(status_code=404, detail="Expense category not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Expense category deleted successfully"}

@router.post("/categories/search/", response_model=List[ExpenseCategoryResponse])
def search_expense_categories_endpoint(
    search: ExpenseCategorySearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search expense categories with filters"""
    require_permission(current_user, "billing", "read")
    categories = search_expense_categories(db, search, skip=skip, limit=limit)
    
    enhanced_categories = []
    for category in categories:
        enhanced_data = ExpenseCategoryResponse.from_orm(category)
        
        # Add parent category name
        if category.parent_category:
            enhanced_data.parent_category_name = category.parent_category.category_name
        
        # Count sub-categories
        sub_categories = get_sub_categories(db, category.id)
        enhanced_data.sub_category_count = len(sub_categories)
        
        # Count expenses
        expenses = get_expenses_by_category(db, category.id)
        enhanced_data.expense_count = len(expenses)
        
        enhanced_categories.append(enhanced_data)
    
    return enhanced_categories

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
            enhanced_data.category_code = expense.category.category_code
        
        if expense.recorded_by_doctor:
            enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
        
        if expense.approver:
            enhanced_data.approver_name = expense.approver.username
        
        if expense.creator:
            enhanced_data.creator_name = expense.creator.username
        
        enhanced_expenses.append(enhanced_data)
    
    return enhanced_expenses

@router.get("/expenses/{expense_id}", response_model=ExpenseWithDetails)
def read_expense(
    expense_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense by ID with details"""
    require_permission(current_user, "billing", "read")
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    enhanced_data = ExpenseWithDetails.from_orm(expense)
    
    # Add related information
    if expense.category:
        enhanced_data.category_name = expense.category.category_name
        enhanced_data.category_code = expense.category.category_code
        enhanced_data.category_details = {
            "id": expense.category.id,
            "code": expense.category.category_code,
            "name": expense.category.category_name,
            "description": expense.category.description,
            "budget_amount": float(expense.category.budget_amount) if expense.category.budget_amount else None
        }
    
    if expense.recorded_by_doctor:
        enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
        enhanced_data.doctor_details = {
            "id": expense.recorded_by_doctor.id,
            "name": f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}",
            "specialization": expense.recorded_by_doctor.specialization
        }
    
    if expense.approver:
        enhanced_data.approver_name = expense.approver.username
    
    if expense.creator:
        enhanced_data.creator_name = expense.creator.username
    
    return enhanced_data

@router.get("/expenses/pending-approval", response_model=List[ExpenseResponse])
def read_pending_approval_expenses(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expenses pending approval"""
    require_permission(current_user, "billing", "read")
    expenses = get_pending_approval_expenses(db)
    
    enhanced_expenses = []
    for expense in expenses:
        enhanced_data = ExpenseResponse.from_orm(expense)
        
        # Add related information
        if expense.category:
            enhanced_data.category_name = expense.category.category_name
            enhanced_data.category_code = expense.category.category_code
        
        if expense.recorded_by_doctor:
            enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
        
        if expense.creator:
            enhanced_data.creator_name = expense.creator.username
        
        enhanced_expenses.append(enhanced_data)
    
    return enhanced_expenses

@router.get("/expenses/recurring", response_model=List[ExpenseResponse])
def read_recurring_expenses(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all recurring expenses"""
    require_permission(current_user, "billing", "read")
    expenses = get_recurring_expenses(db)
    
    enhanced_expenses = []
    for expense in expenses:
        enhanced_data = ExpenseResponse.from_orm(expense)
        
        # Add related information
        if expense.category:
            enhanced_data.category_name = expense.category.category_name
            enhanced_data.category_code = expense.category.category_code
        
        if expense.recorded_by_doctor:
            enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
        
        enhanced_expenses.append(enhanced_data)
    
    return enhanced_expenses

@router.post("/expenses/", response_model=ExpenseResponse)
def create_expense_endpoint(
    expense: ExpenseCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new expense"""
    require_permission(current_user, "billing", "create")
    
    # Validate category exists
    category = get_expense_category_by_id(db, expense.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Expense category not found")
    
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
        enhanced_data.category_code = db_expense.category.category_code
    
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
    expenses = create_bulk_expenses(db, bulk_expense.expenses, current_user.id)
    
    enhanced_expenses = []
    for expense in expenses:
        enhanced_data = ExpenseResponse.from_orm(expense)
        
        # Add related information
        if expense.category:
            enhanced_data.category_name = expense.category.category_name
            enhanced_data.category_code = expense.category.category_code
        
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
        enhanced_data.category_code = db_expense.category.category_code
    
    if db_expense.recorded_by_doctor:
        enhanced_data.doctor_name = f"{db_expense.recorded_by_doctor.first_name} {db_expense.recorded_by_doctor.last_name}"
    
    if db_expense.approver:
        enhanced_data.approver_name = db_expense.approver.username
    
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

@router.post("/expenses/{expense_id}/submit")
def submit_expense_for_approval_endpoint(
    expense_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit expense for approval"""
    require_permission(current_user, "billing", "update")
    try:
        db_expense = submit_expense_for_approval(db, expense_id, current_user.id)
        if not db_expense:
            raise HTTPException(status_code=404, detail="Expense not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Expense submitted for approval"}

@router.post("/expenses/{expense_id}/approve")
def approve_expense_endpoint(
    expense_id: int,
    approval: ExpenseApproval,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve or reject expense"""
    require_permission(current_user, "billing", "update")
    try:
        db_expense = approve_expense(db, expense_id, approval, current_user.id)
        if not db_expense:
            raise HTTPException(status_code=404, detail="Expense not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    action = "approved" if approval.status.value == "approved" else "rejected"
    return {"message": f"Expense {action} successfully"}

@router.post("/expenses/{expense_id}/mark-paid")
def mark_expense_as_paid_endpoint(
    expense_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark expense as paid"""
    require_permission(current_user, "billing", "update")
    try:
        db_expense = mark_expense_as_paid(db, expense_id, current_user.id)
        if not db_expense:
            raise HTTPException(status_code=404, detail="Expense not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Expense marked as paid"}

@router.post("/expenses/process-recurring")
def process_recurring_expenses_endpoint(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process recurring expenses"""
    require_permission(current_user, "billing", "create")
    created_expenses = process_recurring_expenses(db, current_user.id)
    
    return {
        "message": f"Processed {len(created_expenses)} recurring expenses",
        "created_expenses": [exp.expense_code for exp in created_expenses]
    }

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
            enhanced_data.category_code = expense.category.category_code
        
        if expense.recorded_by_doctor:
            enhanced_data.doctor_name = f"{expense.recorded_by_doctor.first_name} {expense.recorded_by_doctor.last_name}"
        
        if expense.approver:
            enhanced_data.approver_name = expense.approver.username
        
        enhanced_expenses.append(enhanced_data)
    
    return enhanced_expenses

# Statistics and Reports
@router.get("/stats/overview", response_model=ExpenseStats)
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

@router.get("/reports/budget-vs-actual")
def get_budget_vs_actual_report(
    year: int,
    month: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get budget vs actual report"""
    require_permission(current_user, "billing", "read")
    report = get_budget_vs_actual(db, year, month)
    return report

@router.get("/reports/vendor-summary", response_model=List[VendorSummary])
def get_vendor_summary_report(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vendor spending summary"""
    require_permission(current_user, "billing", "read")
    summary = get_vendor_summary(db)
    return summary

@router.get("/reports/expense-trends", response_model=List[ExpenseTrend])
def get_expense_trends_report(
    months: int = Query(12, ge=1, le=36),
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense trends report"""
    require_permission(current_user, "billing", "read")
    trends = get_expense_trends(db, months)
    return trends

@router.get("/reports/monthly-summary")
def get_monthly_expense_summary(
    year: int,
    month: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly expense summary"""
    require_permission(current_user, "billing", "read")
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    expenses = get_expenses_by_date_range(db, start_date, end_date)
    total_amount = sum(exp.amount for exp in expenses)
    
    # Group by category
    by_category = {}
    for expense in expenses:
        category_name = expense.category.category_name if expense.category else "Uncategorized"
        if category_name not in by_category:
            by_category[category_name] = 0
        by_category[category_name] += expense.amount
    
    # Group by payment method
    by_payment_method = {}
    for expense in expenses:
        method = expense.payment_method
        if method not in by_payment_method:
            by_payment_method[method] = 0
        by_payment_method[method] += expense.amount
    
    return {
        "period": f"{year}-{month:02d}",
        "total_expenses": len(expenses),
        "total_amount": float(total_amount),
        "by_category": [{"category": cat, "amount": float(amount)} for cat, amount in by_category.items()],
        "by_payment_method": [{"method": method, "amount": float(amount)} for method, amount in by_payment_method.items()],
        "average_expense": float(total_amount / len(expenses)) if expenses else 0
    }