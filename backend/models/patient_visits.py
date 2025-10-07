from sqlalchemy import Column, Integer, String, Text, Date, Time, DECIMAL, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class PatientVisit(Base):
    __tablename__ = "patient_visits"

    id = Column(Integer, primary_key=True, index=True)
    visit_code = Column(String(20), unique=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    visit_date = Column(Date, nullable=False)
    visit_time = Column(Time, nullable=True)
    visit_type = Column(ENUM("consultation", "follow_up", "emergency", "routine_checkup", name="visit_type"), nullable=True)
    chief_complaint = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    weight = Column(DECIMAL(5,2), nullable=True)
    height = Column(DECIMAL(5,2), nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    blood_glucose = Column(DECIMAL(5,2), nullable=True)
    temperature = Column(DECIMAL(4,2), nullable=True)
    status = Column(String(50), default="completed")
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="patient_visits")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])