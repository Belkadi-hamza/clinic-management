from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(Enum('M', 'F', 'O', name='staff_gender'))
    marital_status = Column(String(50))
    mobile_phone = Column(String(20))
    home_phone = Column(String(20))
    fax = Column(String(20))
    email = Column(String(150))
    country = Column(String(100))
    region = Column(String(100))
    city = Column(String(100))
    profile_image = Column(Text)
    position = Column(String(100))
    hire_date = Column(Date)
    department = Column(String(100))
    
    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])
    system_user = relationship("SystemUser", back_populates="staff", uselist=False)