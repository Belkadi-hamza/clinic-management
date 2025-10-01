from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class BillingCategoryBase(BaseModel):
    category_name: str
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: bool = True
    default_price: Optional[Decimal] = None
    tax_rate: Decimal = Decimal('0.0')
    requires_doctor_approval: bool = False
    is_insurance_claimable: bool = True

    @field_validator('category_name')
    def category_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()

    @field_validator('tax_rate')
    def tax_rate_range(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Tax rate must be between 0 and 100')
        return v

    @field_validator('default_price')
    def validate_default_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Default price cannot be negative')
        return v

class BillingCategoryCreate(BillingCategoryBase):
    pass

class BillingCategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: Optional[bool] = None
    default_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    requires_doctor_approval: Optional[bool] = None
    is_insurance_claimable: Optional[bool] = None

class BillingCategoryResponse(BillingCategoryBase):
    id: int
    category_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    parent_category_name: Optional[str] = None
    sub_category_count: int = 0
    service_count: int = 0
    
    class Config:
        from_attributes = True

class BillingCategoryWithChildren(BillingCategoryResponse):
    sub_categories: List['BillingCategoryResponse'] = []
    medical_services: List['MedicalServiceResponse'] = []

class MedicalServiceBase(BaseModel):
    service_name: str
    description: Optional[str] = None
    standard_price: Decimal
    category_id: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_active: bool = True
    requires_specialist: bool = False
    is_lab_service: bool = False
    is_radiology_service: bool = False
    is_procedure: bool = False

    @field_validator('service_name')
    def service_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Service name cannot be empty')
        return v.strip()

    @field_validator('standard_price')
    def standard_price_positive(cls, v):
        if v <= 0:
            raise ValueError('Standard price must be positive')
        return v

    @field_validator('duration_minutes')
    def duration_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Duration must be positive')
        return v

class MedicalServiceCreate(MedicalServiceBase):
    pass

class MedicalServiceUpdate(BaseModel):
    service_name: Optional[str] = None
    description: Optional[str] = None
    standard_price: Optional[Decimal] = None
    category_id: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    requires_specialist: Optional[bool] = None
    is_lab_service: Optional[bool] = None
    is_radiology_service: Optional[bool] = None
    is_procedure: Optional[bool] = None

class MedicalServiceResponse(MedicalServiceBase):
    id: int
    service_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    
    class Config:
        from_attributes = True

class VisitServiceBase(BaseModel):
    visit_id: int
    service_id: int
    actual_price: Decimal
    quantity: int = 1
    discount_amount: Decimal = Decimal('0.0')
    discount_percentage: Decimal = Decimal('0.0')
    tax_amount: Decimal = Decimal('0.0')
    performed_by_doctor_id: Optional[int] = None
    notes: Optional[str] = None
    service_date: Optional[datetime] = None

    @field_validator('actual_price')
    def actual_price_positive(cls, v):
        if v <= 0:
            raise ValueError('Actual price must be positive')
        return v

    @field_validator('quantity')
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

    @field_validator('discount_amount')
    def discount_amount_non_negative(cls, v):
        if v < 0:
            raise ValueError('Discount amount cannot be negative')
        return v

    @field_validator('discount_percentage')
    def discount_percentage_range(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Discount percentage must be between 0 and 100')
        return v

    @field_validator('tax_amount')
    def tax_amount_non_negative(cls, v):
        if v < 0:
            raise ValueError('Tax amount cannot be negative')
        return v

class VisitServiceCreate(VisitServiceBase):
    pass  # Remove computed validator - final_price should be calculated in CRUD layer

class VisitServiceUpdate(BaseModel):
    actual_price: Optional[Decimal] = None
    quantity: Optional[int] = None
    discount_amount: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    performed_by_doctor_id: Optional[int] = None
    notes: Optional[str] = None
    service_date: Optional[datetime] = None

class VisitServiceResponse(VisitServiceBase):
    id: int
    final_price: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    service_name: Optional[str] = None
    service_code: Optional[str] = None
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    visit_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BillingCategoryTree(BaseModel):
    category: BillingCategoryResponse
    children: List['BillingCategoryTree'] = []
    services: List[MedicalServiceResponse] = []

class ServicePriceUpdate(BaseModel):
    service_id: int
    new_price: Decimal

    @field_validator('new_price')
    def new_price_positive(cls, v):
        if v <= 0:
            raise ValueError('New price must be positive')
        return v

class BulkServicePriceUpdate(BaseModel):
    price_updates: List[ServicePriceUpdate]

class CategoryStats(BaseModel):
    category_id: int
    category_name: str
    total_services: int
    active_services: int
    total_revenue: Decimal
    average_price: Decimal
    most_used_service: Optional[str] = None

class ServiceUsageStats(BaseModel):
    service_id: int
    service_name: str
    usage_count: int
    total_revenue: Decimal
    average_price: Decimal

class BillingCategorySearch(BaseModel):
    category_name: Optional[str] = None
    is_active: Optional[bool] = None
    parent_category_id: Optional[int] = None

class MedicalServiceSearch(BaseModel):
    service_name: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    service_type: Optional[str] = None  # 'lab', 'radiology', 'procedure', 'consultation'

class VisitServiceSearch(BaseModel):
    visit_id: Optional[int] = None
    service_id: Optional[int] = None
    patient_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None