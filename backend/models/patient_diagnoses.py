from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PatientDiagnosis(Base):
    __tablename__ = "patient_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("patient_visits.id", ondelete="CASCADE"), nullable=False)
    condition_id = Column(Integer, ForeignKey("medical_conditions.id", ondelete="CASCADE"), nullable=False)
    diagnosis_date = Column(Date, nullable=False)
    diagnosing_doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    certainty_level = Column(Enum("confirmed", "probable", "suspected", "ruled_out", name="diagnosis_certainty"), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)