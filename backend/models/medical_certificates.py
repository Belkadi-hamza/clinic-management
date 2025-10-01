from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MedicalCertificate(Base):
    __tablename__ = "medical_certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_code = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    issuing_doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False, index=True)
    visit_id = Column(Integer, ForeignKey('patient_visits.id'), nullable=True, index=True)
    issue_date = Column(Date, nullable=False, index=True)
    certificate_type = Column(Enum('sick_leave', 'fitness', 'pregnancy', 'vaccination', 'dental', 'other', name='certificate_type'), nullable=False)
    title = Column(String(255), nullable=False)
    duration_days = Column(Integer, nullable=True)  # For sick leave certificates
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    work_resumption_date = Column(Date, nullable=True)  # When patient can resume work
    accident_date = Column(Date, nullable=True)  # For work-related accidents
    diagnosis = Column(Text, nullable=True)
    medical_findings = Column(Text, nullable=True)
    restrictions = Column(Text, nullable=True)  # Activity restrictions
    recommendations = Column(Text, nullable=True)
    treatment_plan = Column(Text, nullable=True)
    is_work_related = Column(Boolean, default=False)
    is_confidential = Column(Boolean, default=False)
    status = Column(Enum('draft', 'issued', 'cancelled', 'expired', name='certificate_status'), default='draft')
    cancellation_reason = Column(Text, nullable=True)
    template_used = Column(String(100), nullable=True)  # Which template was used
    digital_signature = Column(Text, nullable=True)  # Doctor's digital signature
    qr_code = Column(Text, nullable=True)  # QR code for verification
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    issuing_doctor = relationship("Doctor")
    visit = relationship("PatientVisit")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class CertificateTemplate(Base):
    __tablename__ = "certificate_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_code = Column(String(20), unique=True, nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    certificate_type = Column(Enum('sick_leave', 'fitness', 'pregnancy', 'vaccination', 'dental', 'other', name='certificate_type'), nullable=False)
    content = Column(Text, nullable=False)  # HTML or template content
    variables = Column(Text, nullable=True)  # JSON string of available variables
    header_content = Column(Text, nullable=True)
    footer_content = Column(Text, nullable=True)
    clinic_name = Column(String(255), nullable=True)
    clinic_address = Column(Text, nullable=True)
    clinic_phone = Column(String(20), nullable=True)
    clinic_email = Column(String(255), nullable=True)
    doctor_signature_line = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    version = Column(String(20), default='1.0')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class MedicalReport(Base):
    __tablename__ = "medical_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_code = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False, index=True)
    visit_id = Column(Integer, ForeignKey('patient_visits.id'), nullable=True, index=True)
    report_date = Column(Date, nullable=False, index=True)
    report_type = Column(Enum('lab', 'radiology', 'clinical', 'surgical', 'discharge', 'other', name='report_type'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    findings = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)  # Prescribed medications
    follow_up_instructions = Column(Text, nullable=True)
    is_confidential = Column(Boolean, default=True)
    status = Column(Enum('draft', 'finalized', 'delivered', 'archived', name='report_status'), default='draft')
    template_used = Column(String(100), nullable=True)
    digital_signature = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("Doctor")
    visit = relationship("PatientVisit")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])