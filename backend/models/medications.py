from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    medication_code = Column(String(20), unique=True, nullable=False)
    generic_name = Column(String(255), nullable=False)
    brand_name = Column(String(255), nullable=True)
    pharmaceutical_form = Column(String(100), nullable=True)
    dosage_strength = Column(String(100), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    unit_price = Column(DECIMAL(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)