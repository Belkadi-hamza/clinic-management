from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Boolean, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BillingCategory(Base):
    __tablename__ = "billing_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    category_code = Column(String(20), unique=True, nullable=False, index=True)
    category_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_category_id = Column(Integer, ForeignKey('billing_categories.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    default_price = Column(Numeric(10, 2), nullable=True)  # Default price for this category
    tax_rate = Column(Numeric(5, 2), default=0.0)  # Tax rate percentage
    requires_doctor_approval = Column(Boolean, default=False)
    is_insurance_claimable = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    parent_category = relationship("BillingCategory", remote_side=[id], backref="sub_categories")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])
    
    # Relationship with medical services
    medical_services = relationship("MedicalService", back_populates="billing_category")

class MedicalService(Base):
    __tablename__ = "medical_services"
    
    id = Column(Integer, primary_key=True, index=True)
    service_code = Column(String(20), unique=True, nullable=False, index=True)
    service_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    standard_price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey('billing_categories.id'), nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Estimated duration in minutes
    is_active = Column(Boolean, default=True)
    requires_specialist = Column(Boolean, default=False)
    is_lab_service = Column(Boolean, default=False)
    is_radiology_service = Column(Boolean, default=False)
    is_procedure = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    billing_category = relationship("BillingCategory", back_populates="medical_services")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])
    
    # Relationship with visit services
    visit_services = relationship("VisitService", back_populates="medical_service")

class VisitService(Base):
    __tablename__ = "visit_services"
    
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey('patient_visits.id'), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey('medical_services.id'), nullable=False, index=True)
    actual_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, default=1)
    discount_amount = Column(Numeric(10, 2), default=0.0)
    discount_percentage = Column(Numeric(5, 2), default=0.0)
    tax_amount = Column(Numeric(10, 2), default=0.0)
    final_price = Column(Numeric(10, 2), nullable=False)
    performed_by_doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=True)
    notes = Column(Text, nullable=True)
    service_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    visit = relationship("PatientVisit")
    medical_service = relationship("MedicalService", back_populates="visit_services")
    performed_by_doctor = relationship("Doctor")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])