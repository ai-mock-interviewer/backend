from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from .models import Resume
from .schemas import ResumeResponse, ResumeListResponse, ResumeUploadResponse
from .services import ResumeService
from auth.dependencies import get_current_active_user
from auth.models import User
from config.database import get_db

router = APIRouter(prefix="/resumes", tags=["resumes"])

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a resume file - PDF only"""
    # Basic validation (additional validation in service)
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    resume_service = ResumeService(db)
    return await resume_service.upload_resume(file, current_user.user_id)

@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all resumes for current user"""
    resume_service = ResumeService(db)
    resumes = resume_service.get_user_resumes(current_user.user_id)
    
    return ResumeListResponse(
        resumes=[
            ResumeResponse(
                id=resume.id,
                user_id=resume.user_id,
                file_name=resume.file_name,
                file_url=resume.file_url,
                uploaded_at=resume.uploaded_at
            ) for resume in resumes
        ],
        total_count=len(resumes)
    )

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a resume"""
    resume_service = ResumeService(db)
    success = await resume_service.delete_resume(resume_id, current_user.user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return {"message": "Resume deleted successfully"}
