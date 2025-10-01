from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
    vaccine = relationship("Vaccine")
    administering_doctor = relationship("Doctor")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])