from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, extract, case
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from ..models.expenses import ExpenseCategory, Expense, ExpenseBudget, Vendor
from ..models.doctors import Doctor
from ..models.system_users import SystemUser
from ..schemas.expenses import (
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCreate, ExpenseUpdate,
    ExpenseBudgetCreate, ExpenseBudgetUpdate, VendorCreate, VendorUpdate,
    ExpenseCategorySearch, ExpenseSearch, ExpenseBudgetSearch, VendorSearch,
    ExpenseApproval
)

logger = logging.getLogger(__name__)

# Expense Category CRUD operations
def generate_category_code(db: Session):
    """Generate unique expense category code"""
    prefix = "ECAT"
    
    # Find the highest number
    max_category = db.query(ExpenseCategory).order_by(ExpenseCategory.id.desc()).first()
    next_num = (max_category.id + 1) if max_category else 1
    
    return f"{prefix}{next_num:04d}"

def get_expense_categories(db: Session, skip: int = 0, limit: int = 100):
    """Get all expense categories"""
    return db.query(ExpenseCategory).filter(ExpenseCategory.deleted_at == None)\
        .order_by(ExpenseCategory.category_name.asc())\
        .offset(skip).limit(limit).all()

def get_expense_category_by_id(db: Session, category_id: int):
    """Get expense category by ID"""
    return db.query(ExpenseCategory).filter(
        ExpenseCategory.id == category_id,
        ExpenseCategory.deleted_at == None
    ).first()

def get_expense_category_by_code(db: Session, category_code: str):
    """Get expense category by code"""
    return db.query(ExpenseCategory).filter(
        ExpenseCategory.category_code == category_code,
        ExpenseCategory.deleted_at == None
    ).first()

def get_root_categories(db: Session):
    """Get all root categories (no parent)"""
    return db.query(ExpenseCategory).filter(
        ExpenseCategory.parent_category_id == None,
        ExpenseCategory.deleted_at == None
    ).order_by(ExpenseCategory.category_name.asc()).all()

def get_sub_categories(db: Session, parent_category_id: int):
    """Get all sub-categories for a parent category"""
    return db.query(ExpenseCategory).filter(
        ExpenseCategory.parent_category_id == parent_category_id,
        ExpenseCategory.deleted_at == None
    ).order_by(ExpenseCategory.category_name.asc()).all()

def get_category_tree(db: Session):
    """Get complete category hierarchy"""
    root_categories = get_root_categories(db)
    tree = []
    
    for category in root_categories:
        tree.append(_build_category_tree(db, category))
    
    return tree

def _build_category_tree(db: Session, category: ExpenseCategory):
    """Recursively build category tree"""
    sub_categories = get_sub_categories(db, category.id)
    
    # Get current month expenses for this category
    today = date.today()
    current_month_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.category_id == category.id,
        Expense.deleted_at == None,
        Expense.expense_date >= date(today.year, today.month, 1),
        Expense.expense_date <= today
    ).scalar() or 0
    
    tree_node = {
        'category': category,
        'current_month_spent': current_month_expenses,
        'sub_categories': []
    }
    
    for sub_category in sub_categories:
        tree_node['sub_categories'].append(_build_category_tree(db, sub_category))
    
    return tree_node

def search_expense_categories(db: Session, search: ExpenseCategorySearch, skip: int = 0, limit: int = 100):
    """Search expense categories with filters"""
    query = db.query(ExpenseCategory).filter(ExpenseCategory.deleted_at == None)
    
    if search.category_name:
        query = query.filter(ExpenseCategory.category_name.ilike(f"%{search.category_name}%"))
    
    if search.parent_category_id is not None:
        if search.parent_category_id == 0:  # Special case for root categories
            query = query.filter(ExpenseCategory.parent_category_id == None)
        else:
            query = query.filter(ExpenseCategory.parent_category_id == search.parent_category_id)
    
    if search.is_active is not None:
        query = query.filter(ExpenseCategory.is_active == search.is_active)
    
    return query.order_by(ExpenseCategory.category_name.asc())\
        .offset(skip).limit(limit).all()

def create_expense_category(db: Session, category: ExpenseCategoryCreate, user_id: int):
    """Create new expense category"""
    category_code = generate_category_code(db)
    db_category = ExpenseCategory(**category.dict(), category_code=category_code, created_by=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_expense_category(db: Session, category_id: int, category: ExpenseCategoryUpdate, user_id: int):
    """Update expense category"""
    db_category = db.query(ExpenseCategory).filter(
        ExpenseCategory.id == category_id,
        ExpenseCategory.deleted_at == None
    ).first()
    
    if not db_category:
        return None
    
    # Prevent circular reference
    if category.parent_category_id == category_id:
        raise ValueError("Category cannot be its own parent")
    
    for key, value in category.dict(exclude_unset=True).items():
        setattr(db_category, key, value)
    
    db_category.updated_by = user_id
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_expense_category(db: Session, category_id: int, user_id: int):
    """Soft delete expense category"""
    db_category = db.query(ExpenseCategory).filter(
        ExpenseCategory.id == category_id,
        ExpenseCategory.deleted_at == None
    ).first()
    
    if not db_category:
        return None
    
    # Check if category has sub-categories
    sub_categories = get_sub_categories(db, category_id)
    if sub_categories:
        raise ValueError("Cannot delete category with sub-categories")
    
    # Check if category has expenses
    expenses = db.query(Expense).filter(
        Expense.category_id == category_id,
        Expense.deleted_at == None
    ).first()
    
    if expenses:
        raise ValueError("Cannot delete category with associated expenses")
    
    db_category.deleted_at = func.now()
    db_category.deleted_by = user_id
    db.commit()
    return db_category

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

def get_expense_by_code(db: Session, expense_code: str):
    """Get expense by code"""
    return db.query(Expense).filter(
        Expense.expense_code == expense_code,
        Expense.deleted_at == None
    ).first()

def get_expenses_by_category(db: Session, category_id: int):
    """Get all expenses for a specific category"""
    return db.query(Expense).filter(
        Expense.category_id == category_id,
        Expense.deleted_at == None
    ).order_by(Expense.expense_date.desc()).all()

def get_expenses_by_date_range(db: Session, start_date: date, end_date: date):
    """Get expenses within a date range"""
    return db.query(Expense).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
        Expense.deleted_at == None
    ).order_by(Expense.expense_date.asc()).all()

def get_pending_approval_expenses(db: Session):
    """Get expenses pending approval"""
    return db.query(Expense).filter(
        Expense.status == 'submitted',
        Expense.deleted_at == None
    ).order_by(Expense.expense_date.desc()).all()

def get_recurring_expenses(db: Session):
    """Get all recurring expenses"""
    return db.query(Expense).filter(
        Expense.is_recurring == True,
        Expense.deleted_at == None
    ).order_by(Expense.next_due_date.asc()).all()

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
    
    if search.status:
        query = query.filter(Expense.status == search.status)
    
    if search.min_amount:
        query = query.filter(Expense.amount >= search.min_amount)
    
    if search.max_amount:
        query = query.filter(Expense.amount <= search.max_amount)
    
    if search.is_recurring is not None:
        query = query.filter(Expense.is_recurring == search.is_recurring)
    
    if search.recorded_by_doctor_id:
        query = query.filter(Expense.recorded_by_doctor_id == search.recorded_by_doctor_id)
    
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

def create_bulk_expenses(db: Session, expenses: List[ExpenseCreate], user_id: int):
    """Create multiple expenses"""
    created_expenses = []
    
    for expense_data in expenses:
        expense = ExpenseCreate(**expense_data.dict())
        try:
            db_expense = create_expense(db, expense, user_id)
            created_expenses.append(db_expense)
        except Exception as e:
            logger.error(f"Failed to create expense: {e}")
            continue
    
    return created_expenses

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

def submit_expense_for_approval(db: Session, expense_id: int, user_id: int):
    """Submit expense for approval"""
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.deleted_at == None
    ).first()
    
    if not db_expense:
        return None
    
    if db_expense.status != 'draft':
        raise ValueError("Only draft expenses can be submitted for approval")
    
    db_expense.status = 'submitted'
    db_expense.updated_by = user_id
    db.commit()
    db.refresh(db_expense)
    return db_expense

def approve_expense(db: Session, expense_id: int, approval: ExpenseApproval, user_id: int):
    """Approve or reject expense"""
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.deleted_at == None
    ).first()
    
    if not db_expense:
        return None
    
    if db_expense.status != 'submitted':
        raise ValueError("Only submitted expenses can be approved/rejected")
    
    db_expense.status = approval.status
    db_expense.approved_by_id = user_id
    
    if approval.status == 'rejected':
        db_expense.rejection_reason = approval.rejection_reason
    
    db_expense.updated_by = user_id
    db.commit()
    db.refresh(db_expense)
    return db_expense

def mark_expense_as_paid(db: Session, expense_id: int, user_id: int):
    """Mark expense as paid"""
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.deleted_at == None
    ).first()
    
    if not db_expense:
        return None
    
    if db_expense.status != 'approved':
        raise ValueError("Only approved expenses can be marked as paid")
    
    db_expense.status = 'paid'
    db_expense.updated_by = user_id
    db.commit()
    db.refresh(db_expense)
    return db_expense

def process_recurring_expenses(db: Session, user_id: int):
    """Process recurring expenses and create new instances"""
    today = date.today()
    recurring_expenses = get_recurring_expenses(db)
    created_expenses = []
    
    for expense in recurring_expenses:
        if expense.next_due_date and expense.next_due_date <= today:
            # Create new expense instance
            new_expense_data = ExpenseCreate(
                expense_date=expense.next_due_date,
                amount=expense.amount,
                category_id=expense.category_id,
                description=f"Recurring: {expense.description}",
                payment_method=expense.payment_method,
                bank_name=expense.bank_name,
                check_number=expense.check_number,
                card_last_four=expense.card_last_four,
                card_type=expense.card_type,
                reference_number=expense.reference_number,
                vendor_name=expense.vendor_name,
                vendor_contact=expense.vendor_contact,
                recorded_by_doctor_id=expense.recorded_by_doctor_id,
                is_recurring=True,
                recurrence_interval=expense.recurrence_interval,
                recurrence_end_date=expense.recurrence_end_date,
                status='draft',
                notes=expense.notes
            )
            
            # Calculate next due date
            next_due_date = _calculate_next_due_date(
                expense.next_due_date, 
                expense.recurrence_interval
            )
            
            # Check if recurrence has ended
            if expense.recurrence_end_date and next_due_date > expense.recurrence_end_date:
                expense.is_recurring = False
                expense.next_due_date = None
            else:
                expense.next_due_date = next_due_date
            
            # Create new expense
            new_expense = create_expense(db, new_expense_data, user_id)
            created_expenses.append(new_expense)
    
    db.commit()
    return created_expenses

def _calculate_next_due_date(current_date: date, interval: str) -> date:
    """Calculate next due date based on recurrence interval"""
    if interval == 'daily':
        return current_date + timedelta(days=1)
    elif interval == 'weekly':
        return current_date + timedelta(weeks=1)
    elif interval == 'monthly':
        # Add one month
        if current_date.month == 12:
            return date(current_date.year + 1, 1, current_date.day)
        else:
            return date(current_date.year, current_date.month + 1, current_date.day)
    elif interval == 'quarterly':
        return current_date + timedelta(days=90)
    elif interval == 'yearly':
        return date(current_date.year + 1, current_date.month, current_date.day)
    else:
        return current_date

# Expense Budget CRUD operations
def get_expense_budgets(db: Session, skip: int = 0, limit: int = 100):
    """Get all expense budgets"""
    return db.query(ExpenseBudget).filter(ExpenseBudget.deleted_at == None)\
        .order_by(ExpenseBudget.budget_year.desc(), ExpenseBudget.budget_month.desc())\
        .offset(skip).limit(limit).all()

def get_expense_budget_by_id(db: Session, budget_id: int):
    """Get expense budget by ID"""
    return db.query(ExpenseBudget).filter(
        ExpenseBudget.id == budget_id,
        ExpenseBudget.deleted_at == None
    ).first()

def get_budget_by_category_and_period(db: Session, category_id: int, year: int, month: int):
    """Get budget for a specific category and period"""
    return db.query(ExpenseBudget).filter(
        ExpenseBudget.category_id == category_id,
        ExpenseBudget.budget_year == year,
        ExpenseBudget.budget_month == month,
        ExpenseBudget.deleted_at == None
    ).first()

def get_budgets_by_period(db: Session, year: int, month: int):
    """Get all budgets for a specific period"""
    return db.query(ExpenseBudget).filter(
        ExpenseBudget.budget_year == year,
        ExpenseBudget.budget_month == month,
        ExpenseBudget.deleted_at == None
    ).order_by(ExpenseBudget.category_id).all()

def search_expense_budgets(db: Session, search: ExpenseBudgetSearch, skip: int = 0, limit: int = 100):
    """Search expense budgets with filters"""
    query = db.query(ExpenseBudget).filter(ExpenseBudget.deleted_at == None)
    
    if search.budget_year:
        query = query.filter(ExpenseBudget.budget_year == search.budget_year)
    
    if search.budget_month:
        query = query.filter(ExpenseBudget.budget_month == search.budget_month)
    
    if search.category_id:
        query = query.filter(ExpenseBudget.category_id == search.category_id)
    
    return query.order_by(ExpenseBudget.budget_year.desc(), ExpenseBudget.budget_month.desc())\
        .offset(skip).limit(limit).all()

def create_expense_budget(db: Session, budget: ExpenseBudgetCreate, user_id: int):
    """Create new expense budget"""
    # Check if budget already exists for this category and period
    existing_budget = get_budget_by_category_and_period(
        db, budget.category_id, budget.budget_year, budget.budget_month
    )
    
    if existing_budget:
        raise ValueError("Budget already exists for this category and period")
    
    db_budget = ExpenseBudget(**budget.dict(), created_by=user_id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

def create_bulk_expense_budgets(db: Session, budgets: List[ExpenseBudgetCreate], user_id: int):
    """Create multiple expense budgets"""
    created_budgets = []
    
    for budget_data in budgets:
        budget = ExpenseBudgetCreate(**budget_data.dict())
        try:
            db_budget = create_expense_budget(db, budget, user_id)
            created_budgets.append(db_budget)
        except ValueError as e:
            logger.warning(f"Budget already exists: {e}")
            continue
        except Exception as e:
            logger.error(f"Failed to create budget: {e}")
            continue
    
    return created_budgets

def update_expense_budget(db: Session, budget_id: int, budget: ExpenseBudgetUpdate, user_id: int):
    """Update expense budget"""
    db_budget = db.query(ExpenseBudget).filter(
        ExpenseBudget.id == budget_id,
        ExpenseBudget.deleted_at == None
    ).first()
    
    if not db_budget:
        return None
    
    for key, value in budget.dict(exclude_unset=True).items():
        setattr(db_budget, key, value)
    
    db_budget.updated_by = user_id
    db.commit()
    db.refresh(db_budget)
    return db_budget

def delete_expense_budget(db: Session, budget_id: int, user_id: int):
    """Soft delete expense budget"""
    db_budget = db.query(ExpenseBudget).filter(
        ExpenseBudget.id == budget_id,
        ExpenseBudget.deleted_at == None
    ).first()
    
    if not db_budget:
        return None
    
    db_budget.deleted_at = func.now()
    db_budget.deleted_by = user_id
    db.commit()
    return db_budget

# Vendor CRUD operations
def generate_vendor_code(db: Session):
    """Generate unique vendor code"""
    prefix = "VEND"
    
    # Find the highest number
    max_vendor = db.query(Vendor).order_by(Vendor.id.desc()).first()
    next_num = (max_vendor.id + 1) if max_vendor else 1
    
    return f"{prefix}{next_num:04d}"

def get_vendors(db: Session, skip: int = 0, limit: int = 100):
    """Get all vendors"""
    return db.query(Vendor).filter(Vendor.deleted_at == None)\
        .order_by(Vendor.vendor_name.asc())\
        .offset(skip).limit(limit).all()

def get_vendor_by_id(db: Session, vendor_id: int):
    """Get vendor by ID"""
    return db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.deleted_at == None
    ).first()

def get_vendor_by_code(db: Session, vendor_code: str):
    """Get vendor by code"""
    return db.query(Vendor).filter(
        Vendor.vendor_code == vendor_code,
        Vendor.deleted_at == None
    ).first()

def search_vendors(db: Session, search: VendorSearch, skip: int = 0, limit: int = 100):
    """Search vendors with filters"""
    query = db.query(Vendor).filter(Vendor.deleted_at == None)
    
    if search.vendor_name:
        query = query.filter(Vendor.vendor_name.ilike(f"%{search.vendor_name}%"))
    
    if search.is_active is not None:
        query = query.filter(Vendor.is_active == search.is_active)
    
    return query.order_by(Vendor.vendor_name.asc())\
        .offset(skip).limit(limit).all()

def create_vendor(db: Session, vendor: VendorCreate, user_id: int):
    """Create new vendor"""
    vendor_code = generate_vendor_code(db)
    db_vendor = Vendor(**vendor.dict(), vendor_code=vendor_code, created_by=user_id)
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

def update_vendor(db: Session, vendor_id: int, vendor: VendorUpdate, user_id: int):
    """Update vendor"""
    db_vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.deleted_at == None
    ).first()
    
    if not db_vendor:
        return None
    
    for key, value in vendor.dict(exclude_unset=True).items():
        setattr(db_vendor, key, value)
    
    db_vendor.updated_by = user_id
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

def delete_vendor(db: Session, vendor_id: int, user_id: int):
    """Soft delete vendor"""
    db_vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.deleted_at == None
    ).first()
    
    if not db_vendor:
        return None
    
    # Check if vendor has expenses
    expenses = db.query(Expense).filter(
        Expense.vendor_name == db_vendor.vendor_name,
        Expense.deleted_at == None
    ).first()
    
    if expenses:
        raise ValueError("Cannot delete vendor with associated expenses")
    
    db_vendor.deleted_at = func.now()
    db_vendor.deleted_by = user_id
    db.commit()
    return db_vendor

# Statistics and Reports
def get_expense_stats(db: Session, start_date: date = None, end_date: date = None):
    """Get expense statistics"""
    query = db.query(Expense).filter(Expense.deleted_at == None)
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    total_expenses = query.count()
    total_amount = query.with_entities(func.sum(Expense.amount)).scalar() or 0
    average_expense = total_amount / total_expenses if total_expenses > 0 else 0
    
    # Expenses by category
    by_category = db.query(
        ExpenseCategory.category_name,
        func.sum(Expense.amount).label('amount')
    ).join(Expense).filter(
        Expense.deleted_at == None
    ).group_by(ExpenseCategory.category_name).all()
    
    # Expenses by payment method
    by_payment_method = db.query(
        Expense.payment_method,
        func.sum(Expense.amount).label('amount')
    ).filter(
        Expense.deleted_at == None
    ).group_by(Expense.payment_method).all()
    
    # Expenses by status
    by_status = db.query(
        Expense.status,
        func.count(Expense.id).label('count')
    ).filter(
        Expense.deleted_at == None
    ).group_by(Expense.status).all()
    
    # Recurring expenses count
    recurring_expenses_count = query.filter(Expense.is_recurring == True).count()
    
    # Pending approval count
    pending_approval_count = query.filter(Expense.status == 'submitted').count()
    
    return {
        "total_expenses": total_expenses,
        "total_amount": float(total_amount),
        "average_expense": float(average_expense),
        "by_category": [{"category": cat.category_name, "amount": float(amount)} for cat, amount in by_category],
        "by_payment_method": [{"method": method, "amount": float(amount)} for method, amount in by_payment_method],
        "by_status": [{"status": status, "count": count} for status, count in by_status],
        "recurring_expenses_count": recurring_expenses_count,
        "pending_approval_count": pending_approval_count
    }

def get_budget_vs_actual(db: Session, year: int, month: int):
    """Get budget vs actual report for a specific period"""
    budgets = get_budgets_by_period(db, year, month)
    
    report = {
        "year": year,
        "month": month,
        "total_allocated": 0,
        "total_actual": 0,
        "total_remaining": 0,
        "categories": []
    }
    
    for budget in budgets:
        # Calculate actual expenses for this category and period
        actual_amount = db.query(func.sum(Expense.amount)).filter(
            Expense.category_id == budget.category_id,
            Expense.deleted_at == None,
            Expense.expense_date >= date(year, month, 1),
            Expense.expense_date <= date(year, month, 1) + timedelta(days=32)  # Cover entire month
        ).scalar() or 0
        
        utilization_percentage = (actual_amount / budget.allocated_amount * 100) if budget.allocated_amount > 0 else 0
        remaining_amount = budget.allocated_amount - actual_amount
        
        report["total_allocated"] += budget.allocated_amount
        report["total_actual"] += actual_amount
        
        report["categories"].append({
            "category_id": budget.category_id,
            "category_name": budget.category.category_name,
            "allocated_amount": float(budget.allocated_amount),
            "actual_amount": float(actual_amount),
            "utilization_percentage": round(utilization_percentage, 2),
            "remaining_amount": float(remaining_amount)
        })
    
    report["total_remaining"] = report["total_allocated"] - report["total_actual"]
    
    return report

def get_vendor_summary(db: Session):
    """Get vendor spending summary"""
    vendors = get_vendors(db)
    summary = []
    
    for vendor in vendors:
        # Get vendor expenses
        vendor_expenses = db.query(Expense).filter(
            Expense.vendor_name == vendor.vendor_name,
            Expense.deleted_at == None
        ).all()
        
        total_spent = sum(exp.amount for exp in vendor_expenses)
        expense_count = len(vendor_expenses)
        
        # Get last transaction date
        last_transaction = db.query(Expense.expense_date).filter(
            Expense.vendor_name == vendor.vendor_name,
            Expense.deleted_at == None
        ).order_by(Expense.expense_date.desc()).first()
        
        summary.append({
            "vendor_id": vendor.id,
            "vendor_name": vendor.vendor_name,
            "total_spent": float(total_spent),
            "expense_count": expense_count,
            "last_transaction_date": last_transaction[0] if last_transaction else None
        })
    
    return summary

def get_expense_trends(db: Session, months: int = 12):
    """Get expense trends over time"""
    end_date = date.today()
    start_date = end_date - timedelta(days=months*30)
    
    trends = db.query(
        extract('year', Expense.expense_date).label('year'),
        extract('month', Expense.expense_date).label('month'),
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('expense_count')
    ).filter(
        Expense.deleted_at == None,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    return [
        {
            "period": f"{int(t.year)}-{int(t.month):02d}",
            "total_amount": float(t.total_amount or 0),
            "expense_count": t.expense_count
        }
        for t in trends
    ]