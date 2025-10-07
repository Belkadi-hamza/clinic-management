from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, Enum, Boolean
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
    line = Column(String(255))
    city = Column(String(100))
    profile_image = Column(Text)
    hire_date = Column(Date)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    doctor_code = Column(String(20), unique=True, nullable=True)
    specialization = Column(String(100), nullable=True)
    license_number = Column(String(100), nullable=True)
    is_doctor = Column(Boolean, default=False, nullable=True)
    
    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    department = relationship("Department", foreign_keys=[department_id])
    role = relationship("Role", foreign_keys=[role_id])
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])