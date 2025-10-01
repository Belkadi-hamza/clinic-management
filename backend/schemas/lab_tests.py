from pydantic import BaseModel
from typing import Optional

class LabTestBase(BaseModel):
    test_code: str
    test_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    specimen_type: Optional[str] = None
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    measurement_unit: Optional[str] = None
    is_favorite: Optional[bool] = False

class LabTestCreate(LabTestBase):
    created_by: int

class LabTestUpdate(BaseModel):
    test_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    specimen_type: Optional[str] = None
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    measurement_unit: Optional[str] = None
    is_favorite: Optional[bool] = None
    updated_by: Optional[int] = None

class LabTestResponse(LabTestBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True