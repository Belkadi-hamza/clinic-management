from sqlalchemy import Column, Integer, Text, Date, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PatientAllergy(Base):
    __tablename__ = "patient_allergies"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    allergy_id = Column(Integer, ForeignKey("allergies.id", ondelete="CASCADE"), nullable=False)
    severity = Column(Enum("mild", "moderate", "severe", "life_threatening", name="allergy_severity"), nullable=True)
    reaction_description = Column(Text, nullable=True)
    diagnosed_date = Column(Date, nullable=True)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)