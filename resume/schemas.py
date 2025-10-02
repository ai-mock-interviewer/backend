from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class ResumeResponse(BaseModel):
    """Schema for resume response"""
    id: UUID
    user_id: int
    file_name: str
    file_url: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class ResumeListResponse(BaseModel):
    """Schema for resume list response"""
    resumes: List[ResumeResponse]
    total_count: int

class ResumeUploadResponse(BaseModel):
    """Schema for resume upload response"""
    success: bool
    resume: ResumeResponse
    message: str
