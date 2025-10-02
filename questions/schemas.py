from pydantic import BaseModel
from datetime import datetime
from typing import List
from uuid import UUID

class QuestionResponse(BaseModel):
    """Schema for question response"""
    id: UUID
    text: str
    type: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class QuestionListResponse(BaseModel):
    """Schema for question list response"""
    questions: List[QuestionResponse]
    total_count: int
