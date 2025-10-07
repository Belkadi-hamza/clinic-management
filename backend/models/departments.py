from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from .base import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    head_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    created_by = Column(Integer, ForeignKey("system_users.id", ondelete="SET NULL"))
    updated_by = Column(Integer, ForeignKey("system_users.id", ondelete="SET NULL"))
    deleted_by = Column(Integer, ForeignKey("system_users.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
