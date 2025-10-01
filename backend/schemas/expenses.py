from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

class PaymentMethod(str, Enum):
    cash = "cash"
    check = "check"
    card = "card"
    transfer = "transfer"
    other = "other"

class ExpenseStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    paid = "paid"

class RecurrenceInterval(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

# Expense Category Schemas
class ExpenseCategoryBase(BaseModel):
    category_name: str
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: bool = True
    budget_amount: Optional[Decimal] = None
    color_code: Optional[str] = None

    @field_validator('category_name')
    def category_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()

    @field_validator('budget_amount')
    def budget_amount_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Budget amount must be positive')
        return v

    @field_validator('color_code')
    def validate_color_code(cls, v):
        if v and not v.startswith('#'):
            raise ValueError('Color code must start with #')
        if v and len(v) != 7:
            raise ValueError('Color code must be 7 characters long (including #)')
        return v

class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass

class ExpenseCategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: Optional[bool] = None
    budget_amount: Optional[Decimal] = None
    color_code: Optional[str] = None

class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    category_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    parent_category_name: Optional[str] = None
    sub_category_count: int = 0
    expense_count: int = 0
    current_month_spent: Decimal = Decimal('0.0')
    
    class Config:
        from_attributes = True

class ExpenseCategoryTree(ExpenseCategoryResponse):
    sub_categories: List['ExpenseCategoryTree'] = []

# Expense Schemas
class ExpenseBase(BaseModel):
    expense_date: date
    amount: Decimal
    category_id: int
    description: str
    payment_method: PaymentMethod
    bank_name: Optional[str] = None
    check_number: Optional[str] = None
    card_last_four: Optional[str] = None
    card_type: Optional[str] = None
    reference_number: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_contact: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    recorded_by_doctor_id: Optional[int] = None
    is_recurring: bool = False
    recurrence_interval: Optional[RecurrenceInterval] = None
    recurrence_end_date: Optional[date] = None
    next_due_date: Optional[date] = None
    status: ExpenseStatus = ExpenseStatus.draft
    attachment_url: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('amount')
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @field_validator('expense_date')
    def expense_date_not_future(cls, v):
        if v > date.today():
            raise ValueError('Expense date cannot be in the future')
        return v

    @field_validator('recurrence_interval')
    def validate_recurrence_interval(cls, v, values):
        if values.get('is_recurring') and not v:
            raise ValueError('Recurrence interval is required for recurring expenses')
        return v

    @field_validator('recurrence_end_date')
    def validate_recurrence_end_date(cls, v, values):
        if v and 'expense_date' in values and v < values['expense_date']:
            raise ValueError('Recurrence end date cannot be before expense date')
        return v

    @field_validator('next_due_date')
    def validate_next_due_date(cls, v, values):
        if v and 'expense_date' in values and v < values['expense_date']:
            raise ValueError('Next due date cannot be before expense date')
        return v

    @field_validator('card_last_four')
    def validate_card_last_four(cls, v, values):
        if values.get('payment_method') == 'card' and not v:
            raise ValueError('Card last four digits required for card payments')
        if v and len(v) != 4:
            raise ValueError('Card last four must be exactly 4 digits')
        if v and not v.isdigit():
            raise ValueError('Card last four must be digits only')
        return v

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None
    amount: Optional[Decimal] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    bank_name: Optional[str] = None
    check_number: Optional[str] = None
    card_last_four: Optional[str] = None
    card_type: Optional[str] = None
    reference_number: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_contact: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    recorded_by_doctor_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    recurrence_interval: Optional[RecurrenceInterval] = None
    recurrence_end_date: Optional[date] = None
    next_due_date: Optional[date] = None
    status: Optional[ExpenseStatus] = None
    attachment_url: Optional[str] = None
    notes: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: int
    expense_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    doctor_name: Optional[str] = None
    approver_name: Optional[str] = None
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class ExpenseWithDetails(ExpenseResponse):
    category_details: Optional[dict] = None
    doctor_details: Optional[dict] = None

# Expense Budget Schemas
class ExpenseBudgetBase(BaseModel):
    category_id: int
    budget_year: int
    budget_month: int
    allocated_amount: Decimal
    notes: Optional[str] = None

    @field_validator('allocated_amount')
    def allocated_amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Allocated amount must be positive')
        return v

    @field_validator('budget_year')
    def budget_year_valid(cls, v):
        current_year = date.today().year
        if v < current_year - 1 or v > current_year + 5:
            raise ValueError('Budget year must be reasonable')
        return v

    @field_validator('budget_month')
    def budget_month_valid(cls, v):
        if v < 1 or v > 12:
            raise ValueError('Budget month must be between 1 and 12')
        return v

class ExpenseBudgetCreate(ExpenseBudgetBase):
    pass

class ExpenseBudgetUpdate(BaseModel):
    allocated_amount: Optional[Decimal] = None
    notes: Optional[str] = None

class ExpenseBudgetResponse(ExpenseBudgetBase):
    id: int
    actual_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    utilization_percentage: float = 0.0
    remaining_amount: Decimal = Decimal('0.0')
    
    class Config:
        from_attributes = True

# Vendor Schemas
class VendorBase(BaseModel):
    vendor_name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator('vendor_name')
    def vendor_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Vendor name cannot be empty')
        return v.strip()

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class VendorResponse(VendorBase):
    id: int
    vendor_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    total_expenses: Decimal = Decimal('0.0')
    expense_count: int = 0
    
    class Config:
        from_attributes = True

# Search and Filter Schemas
class ExpenseCategorySearch(BaseModel):
    category_name: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: Optional[bool] = None

class ExpenseSearch(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    category_id: Optional[int] = None
    vendor_name: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    status: Optional[ExpenseStatus] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    is_recurring: Optional[bool] = None
    recorded_by_doctor_id: Optional[int] = None

class ExpenseBudgetSearch(BaseModel):
    budget_year: Optional[int] = None
    budget_month: Optional[int] = None
    category_id: Optional[int] = None

class VendorSearch(BaseModel):
    vendor_name: Optional[str] = None
    is_active: Optional[bool] = None

# Statistics and Reports
class ExpenseStats(BaseModel):
    total_expenses: int
    total_amount: Decimal
    average_expense: Decimal
    by_category: List[dict]
    by_payment_method: List[dict]
    by_status: List[dict]
    recurring_expenses_count: int
    pending_approval_count: int

class BudgetVsActual(BaseModel):
    category_id: int
    category_name: str
    allocated_amount: Decimal
    actual_amount: Decimal
    utilization_percentage: float
    remaining_amount: Decimal

class MonthlyBudgetReport(BaseModel):
    year: int
    month: int
    total_allocated: Decimal
    total_actual: Decimal
    total_remaining: Decimal
    categories: List[BudgetVsActual]

class VendorSummary(BaseModel):
    vendor_id: int
    vendor_name: str
    total_spent: Decimal
    expense_count: int
    last_transaction_date: Optional[date]

class ExpenseTrend(BaseModel):
    period: str
    total_amount: Decimal
    expense_count: int

# Bulk Operations
class BulkExpenseCreate(BaseModel):
    expenses: List[ExpenseCreate]

class BulkBudgetCreate(BaseModel):
    budgets: List[ExpenseBudgetCreate]

# Approval Schemas
class ExpenseApproval(BaseModel):
    status: ExpenseStatus
    rejection_reason: Optional[str] = None

    @field_validator('rejection_reason')
    def rejection_reason_required(cls, v, values):
        if values.get('status') == ExpenseStatus.rejected and not v:
            raise ValueError('Rejection reason is required when rejecting an expense')
        return v
        