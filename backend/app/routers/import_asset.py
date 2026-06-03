from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.import_asset import ImportJobResponse, ImportRequest
from app.services.import_service import ImportService

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/openapi", response_model=ImportJobResponse)
def import_openapi(data: ImportRequest, db: Session = Depends(get_db)):
    if data.source_type != "openapi":
        raise HTTPException(status_code=400, detail="source_type must be openapi")
    return ImportService(db).import_document(data.model_dump())


@router.post("/postman", response_model=ImportJobResponse)
def import_postman(data: ImportRequest, db: Session = Depends(get_db)):
    if data.source_type != "postman":
        raise HTTPException(status_code=400, detail="source_type must be postman")
    return ImportService(db).import_document(data.model_dump())


@router.post("/apifox", response_model=ImportJobResponse)
def import_apifox(data: ImportRequest, db: Session = Depends(get_db)):
    if data.source_type != "apifox":
        raise HTTPException(status_code=400, detail="source_type must be apifox")
    return ImportService(db).import_document(data.model_dump())


@router.get("/jobs", response_model=list[ImportJobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return ImportService(db).list_jobs()
