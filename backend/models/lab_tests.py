from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LabTest(Base):
    __tablename__ = "lab_tests"

    id = Column(Integer, primary_key=True, index=True)
    test_code = Column(String(20), unique=True, nullable=False)
    test_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    specimen_type = Column(String(100), nullable=True)
    reference_range_min = Column(DECIMAL(10, 2), nullable=True)
    reference_range_max = Column(DECIMAL(10, 2), nullable=True)
    measurement_unit = Column(String(50), nullable=True)
    is_favorite = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)