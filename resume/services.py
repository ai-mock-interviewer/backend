from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from fastapi import UploadFile, HTTPException
import uuid
from uuid import UUID
from sentence_transformers import SentenceTransformer
import json
try:
    import magic  # python-magic for file type detection
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from .models import Resume
from .schemas import ResumeUploadResponse, ResumeResponse
from config.object_storage import s3_service
from auth.models import User

class ResumeService:
    """Resume service for handling resume operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def _validate_pdf_file(self, file: UploadFile) -> bool:
        """Validate that the uploaded file is actually a PDF"""
        try:
            # Check file extension
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                return False
            
            # Read file content to check MIME type
            file_content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            # Check MIME type using python-magic if available
            if MAGIC_AVAILABLE:
                mime_type = magic.from_buffer(file_content, mime=True)
                if mime_type != 'application/pdf':
                    return False
            
            # Additional PDF header validation (always check this)
            if not file_content.startswith(b'%PDF-'):
                return False
            
            return True
            
        except Exception as e:
            print(f"PDF validation error: {str(e)}")
            return False
    
    async def upload_resume(
        self, 
        file: UploadFile, 
        user_id: int
    ) -> ResumeUploadResponse:
        """Upload resume to S3, parse content, generate embedding, and create database record"""
        try:
            # Validate PDF file type
            if not self._validate_pdf_file(file):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only PDF files are allowed."
                )
            
            # Validate file size (max 10MB)
            if file.size and file.size > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="File size must be less than 10MB"
                )
            
            # Upload to S3
            s3_result = await s3_service.upload_file(
                file=file,
                folder="resumes",
                user_id=user_id
            )
            
            # Parse PDF content
            parsed_content = await self._parse_pdf_content(s3_result["s3_key"])
            
            # Generate embedding
            embedding = self.embedding_model.encode(parsed_content)
            embedding_vector = embedding.tolist()  # Convert to Python list for pgvector
            
            # Create database record
            resume = Resume(
                user_id=user_id,
                file_name=s3_result["original_filename"],
                file_url=s3_result["file_url"],
                embedding_vector=embedding_vector  # Store as native vector
            )
            
            self.db.add(resume)
            self.db.commit()
            self.db.refresh(resume)
            
            return ResumeUploadResponse(
                success=True,
                resume=ResumeResponse(
                    id=resume.id,
                    user_id=resume.user_id,
                    file_name=resume.file_name,
                    file_url=resume.file_url,
                    uploaded_at=resume.uploaded_at
                ),
                message="Resume uploaded and processed successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload resume: {str(e)}"
            )
    
    def get_resume_by_id(self, resume_id: UUID) -> Optional[Resume]:
        """Get resume by ID"""
        return self.db.query(Resume).filter(Resume.id == resume_id).first()
    
    def get_user_resumes(self, user_id: int) -> List[Resume]:
        """Get all resumes for a user"""
        return self.db.query(Resume).filter(Resume.user_id == user_id).all()
    
    async def delete_resume(self, resume_id: UUID, user_id: int) -> bool:
        """Delete resume from S3 and database"""
        try:
            resume = self.db.query(Resume).filter(
                and_(Resume.id == resume_id, Resume.user_id == user_id)
            ).first()
            
            if not resume:
                return False
            
            # Delete from database
            self.db.delete(resume)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete resume: {str(e)}"
            )
    
    def find_similar_resumes(self, query_text: str, limit: int = 10, user_id: Optional[int] = None) -> List[Resume]:
        """Find resumes similar to the given query text using vector similarity"""
        try:
            # Generate embedding for query text
            query_embedding = self.embedding_model.encode(query_text).tolist()
            
            # Build base query
            if user_id:
                # Find similar resumes for a specific user
                query = self.db.query(Resume).filter(Resume.user_id == user_id)
            else:
                # Find similar resumes across all users
                query = self.db.query(Resume)
            
            # Add vector similarity ordering and limit
            # Using cosine distance for similarity (lower is more similar)
            similar_resumes = query.order_by(
                Resume.embedding_vector.cosine_distance(query_embedding)
            ).limit(limit).all()
            
            return similar_resumes
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to find similar resumes: {str(e)}"
            )
    
    def find_resumes_by_similarity_to_resume(self, resume_id: UUID, limit: int = 10) -> List[Resume]:
        """Find resumes similar to a specific resume"""
        try:
            # Get the target resume
            target_resume = self.get_resume_by_id(resume_id)
            if not target_resume or not target_resume.embedding_vector:
                return []
            
            # Find similar resumes (excluding the target resume itself)
            similar_resumes = self.db.query(Resume).filter(
                Resume.id != resume_id,
                Resume.embedding_vector.isnot(None)
            ).order_by(
                Resume.embedding_vector.cosine_distance(target_resume.embedding_vector)
            ).limit(limit).all()
            
            return similar_resumes
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to find similar resumes: {str(e)}"
            )

    async def _parse_pdf_content(self, s3_key: str) -> str:
        """Parse PDF content from S3"""
        try:
            # Get file from S3
            response = s3_service.s3_client.get_object(
                Bucket=s3_service.bucket_name,
                Key=s3_key
            )
            file_content = response['Body'].read()
            
            # Parse PDF
            from pypdf import PdfReader
            import io
            
            pdf_reader = PdfReader(io.BytesIO(file_content))
            parsed_text = ""
            
            for page in pdf_reader.pages:
                parsed_text += page.extract_text() + "\n"
            
            return parsed_text.strip()
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse PDF: {str(e)}"
            )
