from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(ENUM("male", "female", name="gender_type"), nullable=True)
    marital_status = Column(ENUM("single", "married", "divorced", "widowed", name="marital_status"), nullable=True)
    blood_type = Column(ENUM("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="blood_type"), nullable=True)
    place_of_birth = Column(String(255), nullable=True)
    medical_history = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    
    # Relationships
    patient_allergies = relationship("PatientAllergy", back_populates="patient")
    patient_visits = relationship("PatientVisit", back_populates="patient")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])