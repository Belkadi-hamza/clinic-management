from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MedicalCondition(Base):
    __tablename__ = "medical_conditions"

    id = Column(Integer, primary_key=True, index=True)
    condition_code = Column(String(20), unique=True, nullable=False)
    condition_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    icd_code = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    general_information = Column(Text, nullable=True)
    diagnostic_criteria = Column(Text, nullable=True)
    treatment_guidelines = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)