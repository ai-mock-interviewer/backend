from pydantic import BaseModel
from datetime import datetime
from typing import List
from uuid import UUID

class CompanyResponse(BaseModel):
    """Schema for company response"""
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CompanyListResponse(BaseModel):
    """Schema for company list response"""
    companies: List[CompanyResponse]
    total_count: int
