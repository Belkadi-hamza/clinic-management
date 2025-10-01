from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, Boolean, Numeric, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    category_code = Column(String(20), unique=True, nullable=False, index=True)
    category_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_category_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    budget_amount = Column(Numeric(10, 2), nullable=True)  # Monthly budget for this category
    color_code = Column(String(7), nullable=True)  # Hex color for UI (e.g., #FF5733)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    parent_category = relationship("ExpenseCategory", remote_side=[id], backref="sub_categories")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])
    expenses = relationship("Expense", back_populates="category")

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_code = Column(String(20), unique=True, nullable=False, index=True)
    expense_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=False, index=True)
    description = Column(Text, nullable=False)
    payment_method = Column(Enum('cash', 'check', 'card', 'transfer', 'other', name='payment_method'), nullable=False)
    bank_name = Column(String(100), nullable=True)
    check_number = Column(String(50), nullable=True)
    card_last_four = Column(String(4), nullable=True)
    card_type = Column(String(50), nullable=True)
    reference_number = Column(String(100), nullable=True)
    vendor_name = Column(String(255), nullable=True)
    vendor_contact = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    invoice_date = Column(Date, nullable=True)
    recorded_by_doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=True)
    approved_by_id = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_interval = Column(String(50), nullable=True)  # daily, weekly, monthly, quarterly, yearly
    recurrence_end_date = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=True)
    status = Column(Enum('draft', 'submitted', 'approved', 'rejected', 'paid', name='expense_status'), default='draft')
    rejection_reason = Column(Text, nullable=True)
    attachment_url = Column(String(500), nullable=True)  # URL to uploaded receipt/document
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    category = relationship("ExpenseCategory", back_populates="expenses")
    recorded_by_doctor = relationship("Doctor")
    approver = relationship("SystemUser", foreign_keys=[approved_by_id])
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class ExpenseBudget(Base):
    __tablename__ = "expense_budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=False, index=True)
    budget_year = Column(Integer, nullable=False, index=True)
    budget_month = Column(Integer, nullable=False, index=True)  # 1-12
    allocated_amount = Column(Numeric(10, 2), nullable=False)
    actual_amount = Column(Numeric(10, 2), default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    category = relationship("ExpenseCategory")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_code = Column(String(20), unique=True, nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(100), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])
    expenses = relationship("Expense", backref="vendor_relation")