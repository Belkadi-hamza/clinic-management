from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

class PaymentMethod(str, Enum):
    cash = "cash"
    check = "check"
    card = "card"
    transfer = "transfer"

class PaymentStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"

class InvoiceStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"

class ClaimStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    paid = "paid"

# Patient Payment Schemas
class PatientPaymentBase(BaseModel):
    visit_id: int
    payment_date: date
    amount: Decimal
    payment_method: PaymentMethod
    bank_name: Optional[str] = None
    check_number: Optional[str] = None
    card_last_four: Optional[str] = None
    card_type: Optional[str] = None
    reference_number: Optional[str] = None
    transaction_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.completed
    is_refund: bool = False
    refund_reason: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('amount')
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @field_validator('payment_date')
    def payment_date_not_future(cls, v):
        if v > date.today():
            raise ValueError('Payment date cannot be in the future')
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

class PatientPaymentCreate(PatientPaymentBase):
    pass

class PatientPaymentUpdate(BaseModel):
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = None
    payment_method: Optional[PaymentMethod] = None
    bank_name: Optional[str] = None
    check_number: Optional[str] = None
    card_last_four: Optional[str] = None
    card_type: Optional[str] = None
    reference_number: Optional[str] = None
    transaction_id: Optional[str] = None
    status: Optional[PaymentStatus] = None
    is_refund: Optional[bool] = None
    refund_reason: Optional[str] = None
    notes: Optional[str] = None

class PatientPaymentResponse(PatientPaymentBase):
    id: int
    payment_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    visit_date: Optional[date] = None
    doctor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Expense Schemas
class ExpenseBase(BaseModel):
    expense_date: date
    amount: Decimal
    category_id: Optional[int] = None
    description: str
    payment_method: PaymentMethod
    bank_name: Optional[str] = None
    check_number: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    recorded_by_doctor_id: Optional[int] = None
    is_recurring: bool = False
    recurrence_interval: Optional[str] = None
    next_due_date: Optional[date] = None
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
        if v and v not in ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']:
            raise ValueError('Recurrence interval must be one of: daily, weekly, monthly, quarterly, yearly')
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
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    recorded_by_doctor_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    recurrence_interval: Optional[str] = None
    next_due_date: Optional[date] = None
    notes: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: int
    expense_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    category_name: Optional[str] = None
    doctor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Invoice Schemas
class InvoiceBase(BaseModel):
    visit_id: int
    invoice_date: date
    due_date: date
    total_amount: Decimal
    tax_amount: Decimal = Decimal('0.0')
    discount_amount: Decimal = Decimal('0.0')
    paid_amount: Decimal = Decimal('0.0')
    balance_amount: Decimal
    status: InvoiceStatus = InvoiceStatus.draft
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None

    @field_validator('total_amount')
    def total_amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Total amount must be positive')
        return v

    @field_validator('due_date')
    def due_date_after_invoice_date(cls, v, values):
        if 'invoice_date' in values and v < values['invoice_date']:
            raise ValueError('Due date cannot be before invoice date')
        return v

    @field_validator('balance_amount')
    def validate_balance_amount(cls, v, values):
        total = values.get('total_amount', 0)
        paid = values.get('paid_amount', 0)
        tax = values.get('tax_amount', 0)
        discount = values.get('discount_amount', 0)
        
        expected_balance = total + tax - discount - paid
        if v != expected_balance:
            raise ValueError('Balance amount does not match calculated value')
        return v

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    balance_amount: Optional[Decimal] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: int
    invoice_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    visit_date: Optional[date] = None
    doctor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class InvoiceWithPayments(InvoiceResponse):
    payments: List[PatientPaymentResponse] = []

# Insurance Claim Schemas
class InsuranceClaimBase(BaseModel):
    visit_id: int
    insurance_company: str
    policy_number: str
    subscriber_name: str
    relationship_to_patient: str
    total_claim_amount: Decimal
    approved_amount: Optional[Decimal] = None
    patient_responsibility: Optional[Decimal] = None
    claim_date: date
    submission_date: Optional[date] = None
    approval_date: Optional[date] = None
    status: ClaimStatus = ClaimStatus.draft
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('total_claim_amount')
    def claim_amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Claim amount must be positive')
        return v

    @field_validator('submission_date')
    def submission_date_after_claim_date(cls, v, values):
        if v and 'claim_date' in values and v < values['claim_date']:
            raise ValueError('Submission date cannot be before claim date')
        return v

    @field_validator('approval_date')
    def approval_date_after_submission(cls, v, values):
        if v and 'submission_date' in values and values['submission_date'] and v < values['submission_date']:
            raise ValueError('Approval date cannot be before submission date')
        return v

class InsuranceClaimCreate(InsuranceClaimBase):
    pass

class InsuranceClaimUpdate(BaseModel):
    insurance_company: Optional[str] = None
    policy_number: Optional[str] = None
    subscriber_name: Optional[str] = None
    relationship_to_patient: Optional[str] = None
    total_claim_amount: Optional[Decimal] = None
    approved_amount: Optional[Decimal] = None
    patient_responsibility: Optional[Decimal] = None
    claim_date: Optional[date] = None
    submission_date: Optional[date] = None
    approval_date: Optional[date] = None
    status: Optional[ClaimStatus] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class InsuranceClaimResponse(InsuranceClaimBase):
    id: int
    claim_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    visit_date: Optional[date] = None
    
    class Config:
        from_attributes = True

# Search and Filter Schemas
class PatientPaymentSearch(BaseModel):
    patient_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

class ExpenseSearch(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    category_id: Optional[int] = None
    vendor_name: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

class InvoiceSearch(BaseModel):
    patient_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[InvoiceStatus] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

class InsuranceClaimSearch(BaseModel):
    patient_name: Optional[str] = None
    insurance_company: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[ClaimStatus] = None

# Statistics and Reports
class PaymentStats(BaseModel):
    total_payments: int
    total_revenue: Decimal
    cash_payments: Decimal
    card_payments: Decimal
    check_payments: Decimal
    transfer_payments: Decimal
    pending_payments: int
    refunded_amount: Decimal

class ExpenseStats(BaseModel):
    total_expenses: int
    total_amount: Decimal
    by_category: List[dict]
    recurring_expenses: int

class RevenueReport(BaseModel):
    period: str
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal
    by_payment_method: List[dict]
    by_category: List[dict]

class AgingReport(BaseModel):
    period: str
    current: Decimal
    days_30: Decimal
    days_60: Decimal
    days_90: Decimal
    over_90: Decimal
    total_outstanding: Decimal

# Bulk Operations
class BulkPaymentCreate(BaseModel):
    payments: List[PatientPaymentCreate]

class BulkExpenseCreate(BaseModel):
    expenses: List[ExpenseCreate]