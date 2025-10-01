from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MedicalReport(Base):
    __tablename__ = "medical_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_code = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False, index=True)
    visit_id = Column(Integer, ForeignKey('patient_visits.id'), nullable=True, index=True)
    report_date = Column(Date, nullable=False, index=True)
    report_type = Column(Enum('lab', 'radiology', 'clinical', 'surgical', 'discharge', 'pathology', 'imaging', 'other', name='report_type'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    findings = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)  # Prescribed medications
    follow_up_instructions = Column(Text, nullable=True)
    test_results = Column(JSON, nullable=True)  # Structured test results
    normal_range = Column(Text, nullable=True)  # Normal range for test results
    abnormal_notes = Column(Text, nullable=True)  # Notes about abnormal results
    imaging_findings = Column(Text, nullable=True)  # Specific to radiology reports
    impression = Column(Text, nullable=True)  # Radiologist's impression
    technique = Column(Text, nullable=True)  # Imaging technique used
    comparison = Column(Text, nullable=True)  # Comparison with previous studies
    clinical_history = Column(Text, nullable=True)  # Patient's clinical history
    is_confidential = Column(Boolean, default=True)
    status = Column(Enum('draft', 'finalized', 'reviewed', 'delivered', 'archived', name='report_status'), default='draft')
    reviewed_by_id = Column(Integer, ForeignKey('doctors.id'), nullable=True)  # Second opinion/review
    review_date = Column(Date, nullable=True)
    review_notes = Column(Text, nullable=True)
    template_used = Column(String(100), nullable=True)
    digital_signature = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)
    attachment_urls = Column(JSON, nullable=True)  # URLs to attached files/images
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("Doctor", foreign_keys=[doctor_id])
    visit = relationship("PatientVisit")
    reviewer = relationship("Doctor", foreign_keys=[reviewed_by_id])
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class ReportTemplate(Base):
    __tablename__ = "report_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_code = Column(String(20), unique=True, nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    report_type = Column(Enum('lab', 'radiology', 'clinical', 'surgical', 'discharge', 'pathology', 'imaging', 'other', name='report_type'), nullable=False)
    content = Column(Text, nullable=False)  # HTML or template content
    variables = Column(JSON, nullable=True)  # Available template variables
    header_content = Column(Text, nullable=True)
    footer_content = Column(Text, nullable=True)
    styles = Column(Text, nullable=True)  # CSS styles for the template
    sections = Column(JSON, nullable=True)  # Template sections structure
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

class ReportCategory(Base):
    __tablename__ = "report_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    category_code = Column(String(20), unique=True, nullable=False, index=True)
    category_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum('lab', 'radiology', 'clinical', 'surgical', 'discharge', 'pathology', 'imaging', 'other', name='report_type'), nullable=False)
    parent_category_id = Column(Integer, ForeignKey('report_categories.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    parent_category = relationship("ReportCategory", remote_side=[id], backref="sub_categories")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])

class LabTestResult(Base):
    __tablename__ = "lab_test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    result_code = Column(String(20), unique=True, nullable=False, index=True)
    report_id = Column(Integer, ForeignKey('medical_reports.id'), nullable=False, index=True)
    test_name = Column(String(255), nullable=False)
    test_code = Column(String(50), nullable=True)
    result_value = Column(String(100), nullable=True)
    numeric_value = Column(Integer, nullable=True)
    unit = Column(String(50), nullable=True)
    normal_range = Column(String(100), nullable=True)
    flag = Column(Enum('normal', 'low', 'high', 'critical', 'abnormal', name='result_flag'), nullable=True)
    notes = Column(Text, nullable=True)
    performed_by = Column(String(255), nullable=True)
    performed_date = Column(Date, nullable=True)
    verified_by = Column(String(255), nullable=True)
    verified_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey('system_users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    deleted_by = Column(Integer, ForeignKey('system_users.id'), nullable=True)
    
    # Relationships
    report = relationship("MedicalReport")
    creator = relationship("SystemUser", foreign_keys=[created_by])
    updater = relationship("SystemUser", foreign_keys=[updated_by])
    deleter = relationship("SystemUser", foreign_keys=[deleted_by])