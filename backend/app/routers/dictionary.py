from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.models.dictionary import SystemDictionary
from app.schemas.dictionary import DictionaryCreate, DictionaryUpdate, DictionaryResponse
from app.routers.platform_auth import get_current_platform_user

router = APIRouter(prefix="/api/system/dictionaries", tags=["系统字典管理"])


@router.get("", response_model=list[DictionaryResponse])
def list_dictionaries(
    category: str = None,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    query = db.query(SystemDictionary)
    if category:
        query = query.filter(SystemDictionary.category == category)
    return query.order_by(SystemDictionary.category, SystemDictionary.sort_order).all()


@router.post("", response_model=DictionaryResponse)
def create_dictionary(
    request: DictionaryCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    existing = db.query(SystemDictionary).filter(
        SystemDictionary.category == request.category,
        SystemDictionary.code == request.code,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该分类下已存在相同编码的字典项")

    item = SystemDictionary(**request.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{dictionary_id}", response_model=DictionaryResponse)
def update_dictionary(
    dictionary_id: int,
    request: DictionaryUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    item = db.query(SystemDictionary).filter(SystemDictionary.id == dictionary_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="字典项不存在")

    if request.category and request.code:
        existing = db.query(SystemDictionary).filter(
            SystemDictionary.category == request.category,
            SystemDictionary.code == request.code,
            SystemDictionary.id != dictionary_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该分类下已存在相同编码的字典项")

    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{dictionary_id}")
def delete_dictionary(
    dictionary_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    item = db.query(SystemDictionary).filter(SystemDictionary.id == dictionary_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="字典项不存在")
    db.delete(item)
    db.commit()
    return {"message": "删除成功"}