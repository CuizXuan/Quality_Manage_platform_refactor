from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.routers.platform_auth import get_current_platform_user
from app.schemas.case_folder import (
    CaseFolderCreate,
    CaseFolderResponse,
    CaseFolderTreeResponse,
    CaseFolderUpdate,
)

router = APIRouter(prefix="/api/case/folders", tags=["用例分类"])


@router.post("", response_model=CaseFolderResponse)
def create_folder(
    folder: CaseFolderCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Create a new folder."""
    from app.models.case_folder import CaseFolder
    db_folder = CaseFolder(**folder.model_dump())
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder


@router.get("", response_model=CaseFolderTreeResponse)
def list_folders(
    case_type: Optional[str] = Query(None, description="用例类型: functional 或 api"),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """List folders."""
    from app.models.case_folder import CaseFolder
    query = db.query(CaseFolder)
    if case_type:
        query = query.filter(CaseFolder.case_type == case_type)
    folders = query.order_by(CaseFolder.sort_order, CaseFolder.id).all()
    return CaseFolderTreeResponse(items=folders, total=len(folders))


@router.get("/{folder_id}", response_model=CaseFolderResponse)
def get_folder(
    folder_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Get a folder by ID."""
    from app.models.case_folder import CaseFolder
    folder = db.query(CaseFolder).filter(CaseFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.put("/{folder_id}", response_model=CaseFolderResponse)
def update_folder(
    folder_id: int,
    folder: CaseFolderUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Update a folder."""
    from app.models.case_folder import CaseFolder
    db_folder = db.query(CaseFolder).filter(CaseFolder.id == folder_id).first()
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    update_data = folder.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_folder, key, value)
    db.commit()
    db.refresh(db_folder)
    return db_folder


@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Delete a folder."""
    from app.models.case_folder import CaseFolder
    folder = db.query(CaseFolder).filter(CaseFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    db.delete(folder)
    db.commit()
    return {"id": folder_id}