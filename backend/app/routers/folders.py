from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel, field_serializer
from app.database import get_db
from app.models.case_folder import CaseFolder

router = APIRouter(prefix="/api/folders", tags=["Folders"])


class FolderCreate(BaseModel):
    name: str
    parent_id: int | None = None
    sort_order: int = 0


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None


class FolderResponse(BaseModel):
    id: int
    name: str
    parent_id: int | None
    sort_order: int
    created_at: datetime
    updated_at: datetime | None

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None

    class Config:
        from_attributes = True


@router.get("", response_model=List[FolderResponse])
def list_folders(db: Session = Depends(get_db)):
    folders = db.query(CaseFolder).order_by(CaseFolder.sort_order, CaseFolder.id).all()
    return folders


@router.post("", response_model=FolderResponse, status_code=201)
def create_folder(data: FolderCreate, db: Session = Depends(get_db)):
    folder = CaseFolder(**data.model_dump())
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.put("/{folder_id}", response_model=FolderResponse)
def update_folder(folder_id: int, data: FolderUpdate, db: Session = Depends(get_db)):
    folder = db.query(CaseFolder).filter(CaseFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(folder, key, value)
    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=204)
def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    folder = db.query(CaseFolder).filter(CaseFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    has_children = db.query(CaseFolder).filter(CaseFolder.parent_id == folder_id).first()
    if has_children:
        raise HTTPException(status_code=400, detail="Folder has sub-folders, delete them first")
    db.delete(folder)
    db.commit()
