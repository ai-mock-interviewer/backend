from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from config.database import Base

class Resume(Base):
    """Resume model for storing user resumes"""
    
    __tablename__ = "resumes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)  # Original filename
    file_url = Column(String(500), nullable=False)  # S3 URL
    embedding_vector = Column(String)  # Vector stored as text (pgvector will handle conversion)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, user_id={self.user_id}, file_name='{self.file_name}')>"
