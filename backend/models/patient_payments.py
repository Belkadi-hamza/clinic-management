from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, Boolean, Numeric, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PatientPayment(Base):
    __tablename__ = "patient_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_code = Column(String(20), unique=True, nullable=False, index=True)
    visit_id = Column(Integer, ForeignKey('patient_visits.id'), nullable=False, index=True)
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum('cash', 'check', 'card', 'transfer', name='payment_method'), nullable=False)
    bank_name = Column(String(100), nullable=True)
    check_number = Column(String(50), nullable=True)
    card_last_four = Column(String(4), nullable=True)  # Last 4 digits of card
    card_type = Column(String(50), nullable=True)  # visa, mastercard, etc.
    reference_number = Column(String(100), nullable=True)  # For transfers or other references
    transaction_id = Column(String(100), nullable=True)  # Gateway transaction ID
    status = Column(Enum('pending', 'completed', 'failed', 'refunded', name='payment_status'), default='completed')
    is_refund = Column(Boolean, default=False)  # Whether this is a refund payment
    refund_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    visit = relationship("PatientVisit")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_code = Column(String(20), unique=True, nullable=False, index=True)
    expense_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey('billing_categories.id'), nullable=True)
    description = Column(Text, nullable=False)
    payment_method = Column(Enum('cash', 'check', 'card', 'transfer', name='payment_method'), nullable=False)
    bank_name = Column(String(100), nullable=True)
    check_number = Column(String(50), nullable=True)
    vendor_name = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    recorded_by_doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_interval = Column(String(50), nullable=True)  # monthly, quarterly, etc.
    next_due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    category = relationship("BillingCategory")
    recorded_by_doctor = relationship("Doctor")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_code = Column(String(20), unique=True, nullable=False, index=True)
    visit_id = Column(Integer, ForeignKey('patient_visits.id'), nullable=False, index=True)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.0)
    discount_amount = Column(Numeric(10, 2), default=0.0)
    paid_amount = Column(Numeric(10, 2), default=0.0)
    balance_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum('draft', 'sent', 'paid', 'overdue', 'cancelled', name='invoice_status'), default='draft')
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    visit = relationship("PatientVisit")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])
    payments = relationship("PatientPayment", backref="invoice")

class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_code = Column(String(20), unique=True, nullable=False, index=True)
    visit_id = Column(Integer, ForeignKey('patient_visits.id'), nullable=False, index=True)
    insurance_company = Column(String(255), nullable=False)
    policy_number = Column(String(100), nullable=False)
    subscriber_name = Column(String(255), nullable=False)
    relationship_to_patient = Column(String(50), nullable=False)  # self, spouse, child, etc.
    total_claim_amount = Column(Numeric(10, 2), nullable=False)
    approved_amount = Column(Numeric(10, 2), nullable=True)
    patient_responsibility = Column(Numeric(10, 2), nullable=True)
    claim_date = Column(Date, nullable=False)
    submission_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    status = Column(Enum('draft', 'submitted', 'approved', 'rejected', 'paid', name='claim_status'), default='draft')
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    visit = relationship("PatientVisit")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])