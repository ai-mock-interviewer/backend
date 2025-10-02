from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from .models import Question
from .schemas import QuestionResponse, QuestionListResponse
from .services import QuestionService
from config.database import get_db

router = APIRouter(prefix="/questions", tags=["questions"])

@router.get("/", response_model=QuestionListResponse)
async def get_all_questions(
    type: Optional[str] = Query(None, description="Filter by question type"),
    search: Optional[str] = Query(None, description="Search in question text"),
    db: Session = Depends(get_db)
):
    """Get all questions with optional filtering"""
    question_service = QuestionService(db)
    
    if type:
        questions = question_service.get_questions_by_type(type)
    elif search:
        questions = question_service.get_questions_by_text_search(search)
    else:
        questions = question_service.get_all_questions()
    
    return QuestionListResponse(
        questions=[
            QuestionResponse(
                id=question.id,
                text=question.text,
                type=question.type,
                created_at=question.created_at,
                updated_at=question.updated_at
            ) for question in questions
        ],
        total_count=len(questions)
    )

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific question by ID"""
    question_service = QuestionService(db)
    question = question_service.get_question_by_id(question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return QuestionResponse(
        id=question.id,
        text=question.text,
        type=question.type,
        created_at=question.created_at,
        updated_at=question.updated_at
    )
