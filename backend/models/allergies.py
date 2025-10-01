from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, index=True)
    allergy_name = Column(String(255), nullable=False)
    allergy_type = Column(Enum('food', 'drug', 'environmental', 'other', name='allergy_type'), nullable=False)
    description = Column(Text)
    
    # Audit fields
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
    patient_allergies = relationship("PatientAllergy", back_populates="allergy")

class PatientAllergy(Base):
    __tablename__ = "patient_allergies"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    allergy_id = Column(Integer, ForeignKey('allergies.id'), nullable=False)
    severity = Column(Enum('mild', 'moderate', 'severe', 'life_threatening', name='allergy_severity'))
    reaction_description = Column(Text)
    diagnosed_date = Column(Date)
    
    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="patient_allergies")
    allergy = relationship("Allergy", back_populates="patient_allergies")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])