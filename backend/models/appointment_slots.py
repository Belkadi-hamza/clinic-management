from sqlalchemy import Column, Integer, Boolean, Time, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id = Column(Integer, primary_key=True, index=True)
    slot_index = Column(Integer, nullable=False)
    slot_time = Column(Time, nullable=False)
    is_available = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("system_users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("system_users.id"), nullable=True)