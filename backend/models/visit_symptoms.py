from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class VisitSymptom(Base):
    __tablename__ = "visit_symptoms"

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey('patient_visits.id'), nullable=False)
    symptom_id = Column(Integer, ForeignKey('symptoms.id'), nullable=False)
    severity = Column(String(50))  # mild, moderate, severe, etc.
    duration_days = Column(Integer)
    notes = Column(Text)
    
    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    symptom = relationship("Symptom", back_populates="visit_symptoms")
    visit = relationship("PatientVisit", back_populates="visit_symptoms")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])