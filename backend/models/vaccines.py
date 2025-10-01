from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Vaccine(Base):
    __tablename__ = "vaccines"
    
    id = Column(Integer, primary_key=True, index=True)
    vaccine_code = Column(String(20), unique=True, nullable=False, index=True)
    vaccine_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    recommended_age_months = Column(Integer, nullable=True)  # Recommended age in months
    booster_required = Column(Boolean, default=False)
    booster_interval_months = Column(Integer, nullable=True)  # Months between doses
    total_doses_required = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
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
    schedules = relationship("VaccinationSchedule", back_populates="vaccine")

class VaccinationSchedule(Base):
    __tablename__ = "vaccination_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_code = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    vaccine_id = Column(Integer, ForeignKey('vaccines.id'), nullable=False, index=True)
    dose_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    scheduled_date = Column(Date, nullable=False, index=True)
    administered_date = Column(Date, nullable=True, index=True)
    is_administered = Column(Boolean, default=False)
    administering_doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=True)
    lot_number = Column(String(100), nullable=True)
    batch_number = Column(String(100), nullable=True)
    expiration_date = Column(Date, nullable=True)
    administration_site = Column(String(100), nullable=True)  # e.g., 'Left Arm', 'Right Thigh'
    route = Column(String(50), nullable=True)  # e.g., 'Intramuscular', 'Oral'
    adverse_reactions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    vaccine = relationship("Vaccine", back_populates="schedules")
    administering_doctor = relationship("Doctor")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class VaccineInventory(Base):
    __tablename__ = "vaccine_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    vaccine_id = Column(Integer, ForeignKey('vaccines.id'), nullable=False, index=True)
    lot_number = Column(String(100), nullable=False)
    batch_number = Column(String(100), nullable=True)
    expiration_date = Column(Date, nullable=False, index=True)
    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_used = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=10)
    unit_cost = Column(Integer, nullable=True)  # Cost per dose in cents
    supplier = Column(String(255), nullable=True)
    received_date = Column(Date, nullable=False)
    storage_temperature = Column(String(50), nullable=True)  # e.g., '2-8°C'
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    vaccine = relationship("Vaccine")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])