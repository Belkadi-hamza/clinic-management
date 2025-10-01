from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Date, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LabOrder(Base):
    __tablename__ = "lab_orders"

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("patient_visits.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("lab_tests.id", ondelete="CASCADE"), nullable=False)
    ordering_doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    order_date = Column(Date, nullable=False)
    laboratory_name = Column(String(255), nullable=True)
    clinical_notes = Column(Text, nullable=True)
    results = Column(Text, nullable=True)
    result_date = Column(Date, nullable=True)
    is_abnormal = Column(Boolean, nullable=True)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)