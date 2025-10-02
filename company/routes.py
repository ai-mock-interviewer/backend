from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from .models import Company
from .schemas import CompanyResponse, CompanyListResponse
from .services import CompanyService
from config.database import get_db

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/", response_model=CompanyListResponse)
async def get_all_companies(db: Session = Depends(get_db)):
    """Get all companies"""
    company_service = CompanyService(db)
    companies = company_service.get_all_companies()
    
    return CompanyListResponse(
        companies=[
            CompanyResponse(
                id=company.id,
                name=company.name,
                created_at=company.created_at,
                updated_at=company.updated_at
            ) for company in companies
        ],
        total_count=len(companies)
    )

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific company by ID"""
    company_service = CompanyService(db)
    company = company_service.get_company_by_id(company_id)
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return CompanyResponse(
        id=company.id,
        name=company.name,
        created_at=company.created_at,
        updated_at=company.updated_at
    )
