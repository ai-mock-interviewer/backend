from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from config.database import Base

class Question(Base):
    """Question model for storing interview questions"""
    
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    text = Column(String, nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "technical", "behavioral", "system_design"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company_questions = relationship("CompanyQuestion", back_populates="question")
    
    def __repr__(self):
        return f"<Question(id={self.id}, type='{self.type}')>"

class CompanyQuestion(Base):
    """Junction table for company-question relationships"""
    
    __tablename__ = "company_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="company_questions")
    question = relationship("Question", back_populates="company_questions")
    
    def __repr__(self):
        return f"<CompanyQuestion(id={self.id}, company_id={self.company_id}, question_id={self.question_id})>"
