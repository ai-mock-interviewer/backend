from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from .models import Question

class QuestionService:
    """Question service for handling question operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_questions(self) -> List[Question]:
        """Get all questions"""
        return self.db.query(Question).all()
    
    def get_question_by_id(self, question_id: UUID) -> Optional[Question]:
        """Get question by ID"""
        return self.db.query(Question).filter(Question.id == question_id).first()
    
    def get_questions_by_type(self, question_type: str) -> List[Question]:
        """Get questions by type (e.g., 'technical', 'behavioral', 'system_design')"""
        return self.db.query(Question).filter(Question.type == question_type).all()
    
    def get_questions_by_text_search(self, search_text: str) -> List[Question]:
        """Get questions by text search (case-insensitive)"""
        return self.db.query(Question).filter(Question.text.ilike(f"%{search_text}%")).all()
