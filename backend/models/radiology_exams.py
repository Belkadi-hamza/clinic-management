from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class RadiologyExam(Base):
    __tablename__ = "radiology_exams"

    id = Column(Integer, primary_key=True, index=True)
    exam_code = Column(String(20), unique=True, nullable=False)
    exam_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    exam_type = Column(String(50), nullable=True)
    is_favorite = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)