from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

# Base schemas
class BankBase(BaseModel):
    bank_code: str
    bank_name: str

# Create schemas
class BankCreate(BankBase):
    @field_validator('bank_code')
    def validate_bank_code(cls, v):
        if not v.strip():
            raise ValueError('Bank code cannot be empty')
        if len(v) > 20:
            raise ValueError('Bank code cannot exceed 20 characters')
        # Allow only alphanumeric and specific characters
        if not all(c.isalnum() or c in ['-', '_'] for c in v):
            raise ValueError('Bank code can only contain letters, numbers, hyphens, and underscores')
        return v.upper()

    @field_validator('bank_name')
    def validate_bank_name(cls, v):
        if not v.strip():
            raise ValueError('Bank name cannot be empty')
        if len(v) > 255:
            raise ValueError('Bank name cannot exceed 255 characters')
        return v.strip()

# Update schemas
class BankUpdate(BaseModel):
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None

    @field_validator('bank_code')
    def validate_bank_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Bank code cannot be empty')
            if len(v) > 20:
                raise ValueError('Bank code cannot exceed 20 characters')
            if not all(c.isalnum() or c in ['-', '_'] for c in v):
                raise ValueError('Bank code can only contain letters, numbers, hyphens, and underscores')
            return v.upper()
        return v

    @field_validator('bank_name')
    def validate_bank_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Bank name cannot be empty')
            if len(v) > 255:
                raise ValueError('Bank name cannot exceed 255 characters')
            return v.strip()
        return v

# Response schemas
class BankResponse(BankBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    status: str
    created_by_username: Optional[str] = None
    updated_by_username: Optional[str] = None

    class Config:
        from_attributes = True

class BankSimpleResponse(BaseModel):
    id: int
    bank_code: str
    bank_name: str

    class Config:
        from_attributes = True

# List responses
class BankListResponse(BaseModel):
    banks: List[BankResponse]
    total: int

class BankSearchResponse(BaseModel):
    banks: List[BankSimpleResponse]
    total: int

# Bulk operations
class BankBulkCreate(BaseModel):
    banks: List[BankCreate]

class BankBulkCreateResponse(BaseModel):
    created: List[BankResponse]
    errors: List[dict]
    total_created: int
    total_errors: int

# Import/Export
class BankImportRow(BaseModel):
    bank_code: str
    bank_name: str

class BankImportRequest(BaseModel):
    banks: List[BankImportRow]
    overwrite_existing: bool = False