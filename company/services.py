from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from .models import Company
from .schemas import CompanyResponse, CompanyListResponse

class CompanyService:
    """Company service for handling company operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_companies(self) -> List[Company]:
        """Get all companies"""
        return self.db.query(Company).all()
    
    def get_company_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID"""
        return self.db.query(Company).filter(Company.id == company_id).first()
    
    def get_company_by_name(self, name: str) -> Optional[Company]:
        """Get company by name (case-insensitive)"""
        return self.db.query(Company).filter(Company.name.ilike(f"%{name}%")).first()
