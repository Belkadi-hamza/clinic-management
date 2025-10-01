from sqlalchemy import Column, Integer, Text, DECIMAL, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class VisitService(Base):
    __tablename__ = "visit_services"

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("patient_visits.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("medical_services.id", ondelete="CASCADE"), nullable=False)
    actual_price = Column(DECIMAL(10,2), nullable=True)
    performed_by_doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)