# -*- coding: utf-8 -*-
"""
Phase 4 - 版本管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.tenant import User
from app.services.auth_service import AuthService
from app.services.version_service import VersionService

router = APIRouter(prefix="/api/versions", tags=["版本管理"])
security = HTTPBearer(auto_error=False)


# ==================== 依赖项 ====================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    auth_service = AuthService(db)
    payload = auth_service.decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ==================== 请求/响应模型 ====================

class VersionCreate(BaseModel):
    project_id: int
    name: str
    tag: Optional[str] = None
    commit_hash: Optional[str] = None
    description: Optional[str] = None
    baseline_id: Optional[int] = None


class VersionUpdate(BaseModel):
    name: Optional[str] = None
    tag: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class QualityReportBind(BaseModel):
    report_id: str
    summary: Optional[dict] = None


class VersionResponse(BaseModel):
    id: int
    project_id: int
    name: str
    tag: Optional[str]
    commit_hash: Optional[str]
    description: Optional[str]
    baseline_id: Optional[int]
    quality_report_id: Optional[str]
    test_summary: Optional[dict]
    status: str
    released_at: Optional[str]
    created_at: str
    updated_at: str


class PageResponse(BaseModel):
    items: List[VersionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str


# ==================== 版本 CRUD ====================

@router.get("", summary="获取版本列表")
def get_versions(
    project_id: int = Query(..., description="项目ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目的版本列表"""
    version_service = VersionService(db)
    versions, total = version_service.get_versions(
        project_id=project_id,
        page=page,
        page_size=page_size,
        status=status
    )
    
    items = [
        VersionResponse(
            id=v.id,
            project_id=v.project_id,
            name=v.name,
            tag=v.tag,
            commit_hash=v.commit_hash,
            description=v.description,
            baseline_id=v.baseline_id,
            quality_report_id=v.quality_report_id,
            test_summary=v.test_summary,
            status=v.status,
            released_at=v.released_at.isoformat() if v.released_at else None,
            created_at=v.created_at.isoformat() if v.created_at else "",
            updated_at=v.updated_at.isoformat() if v.updated_at else ""
        ) for v in versions
    ]
    
    total_pages = (total + page_size - 1) // page_size
    
    return PageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("", response_model=VersionResponse, summary="创建版本")
def create_version(
    request: VersionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新版本"""
    version_service = VersionService(db)
    
    version, success, error = version_service.create_version(
        project_id=request.project_id,
        user_id=current_user.id,
        name=request.name,
        tag=request.tag,
        commit_hash=request.commit_hash,
        description=request.description,
        baseline_id=request.baseline_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        name=version.name,
        tag=version.tag,
        commit_hash=version.commit_hash,
        description=version.description,
        baseline_id=version.baseline_id,
        quality_report_id=version.quality_report_id,
        test_summary=version.test_summary,
        status=version.status,
        released_at=version.released_at.isoformat() if version.released_at else None,
        created_at=version.created_at.isoformat() if version.created_at else "",
        updated_at=version.updated_at.isoformat() if version.updated_at else ""
    )


@router.get("/{version_id}", response_model=VersionResponse, summary="获取版本详情")
def get_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取版本详情"""
    version_service = VersionService(db)
    version = version_service.get_version_by_id(version_id)
    
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        name=version.name,
        tag=version.tag,
        commit_hash=version.commit_hash,
        description=version.description,
        baseline_id=version.baseline_id,
        quality_report_id=version.quality_report_id,
        test_summary=version.test_summary,
        status=version.status,
        released_at=version.released_at.isoformat() if version.released_at else None,
        created_at=version.created_at.isoformat() if version.created_at else "",
        updated_at=version.updated_at.isoformat() if version.updated_at else ""
    )


@router.put("/{version_id}", response_model=VersionResponse, summary="更新版本")
def update_version(
    version_id: int,
    request: VersionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新版本"""
    version_service = VersionService(db)
    
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.tag is not None:
        update_data["tag"] = request.tag
    if request.description is not None:
        update_data["description"] = request.description
    if request.status is not None:
        update_data["status"] = request.status
    
    version, success, error = version_service.update_version(
        version_id=version_id,
        user_id=current_user.id,
        **update_data
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        name=version.name,
        tag=version.tag,
        commit_hash=version.commit_hash,
        description=version.description,
        baseline_id=version.baseline_id,
        quality_report_id=version.quality_report_id,
        test_summary=version.test_summary,
        status=version.status,
        released_at=version.released_at.isoformat() if version.released_at else None,
        created_at=version.created_at.isoformat() if version.created_at else "",
        updated_at=version.updated_at.isoformat() if version.updated_at else ""
    )


@router.delete("/{version_id}", response_model=MessageResponse, summary="删除版本")
def delete_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除版本"""
    version_service = VersionService(db)
    success, error = version_service.delete_version(version_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return MessageResponse(message="删除成功")


# ==================== 版本质量报告 ====================

@router.post("/{version_id}/report", response_model=VersionResponse, summary="绑定质量报告")
def bind_quality_report(
    version_id: int,
    request: QualityReportBind,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """绑定版本质量报告"""
    version_service = VersionService(db)
    
    version, success, error = version_service.bind_quality_report(
        version_id=version_id,
        report_data={"report_id": request.report_id, "summary": request.summary}
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        name=version.name,
        tag=version.tag,
        commit_hash=version.commit_hash,
        description=version.description,
        baseline_id=version.baseline_id,
        quality_report_id=version.quality_report_id,
        test_summary=version.test_summary,
        status=version.status,
        released_at=version.released_at.isoformat() if version.released_at else None,
        created_at=version.created_at.isoformat() if version.created_at else "",
        updated_at=version.updated_at.isoformat() if version.updated_at else ""
    )


@router.get("/{version_id}/report", summary="获取版本质量报告")
def get_quality_report(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取版本质量报告"""
    version_service = VersionService(db)
    report = version_service.get_quality_report(version_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return report


@router.get("/{version_id}/summary", summary="获取版本测试摘要")
def get_version_summary(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取版本测试摘要"""
    version_service = VersionService(db)
    summary = version_service.get_version_summary(version_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return summary


# ==================== 版本操作 ====================

@router.post("/{version_id}/release", response_model=VersionResponse, summary="发布版本")
def release_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布版本"""
    version_service = VersionService(db)
    version, success, error = version_service.release_version(version_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        name=version.name,
        tag=version.tag,
        commit_hash=version.commit_hash,
        description=version.description,
        baseline_id=version.baseline_id,
        quality_report_id=version.quality_report_id,
        test_summary=version.test_summary,
        status=version.status,
        released_at=version.released_at.isoformat() if version.released_at else None,
        created_at=version.created_at.isoformat() if version.created_at else "",
        updated_at=version.updated_at.isoformat() if version.updated_at else ""
    )


@router.post("/{version_id}/archive", response_model=VersionResponse, summary="归档版本")
def archive_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """归档版本"""
    version_service = VersionService(db)
    version, success, error = version_service.archive_version(version_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        name=version.name,
        tag=version.tag,
        commit_hash=version.commit_hash,
        description=version.description,
        baseline_id=version.baseline_id,
        quality_report_id=version.quality_report_id,
        test_summary=version.test_summary,
        status=version.status,
        released_at=version.released_at.isoformat() if version.released_at else None,
        created_at=version.created_at.isoformat() if version.created_at else "",
        updated_at=version.updated_at.isoformat() if version.updated_at else ""
    )


@router.get("/compare/{v1_id}/{v2_id}", summary="对比两个版本")
def compare_versions(
    v1_id: int,
    v2_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """对比两个版本的测试结果"""
    version_service = VersionService(db)
    comparison = version_service.compare_versions(v1_id, v2_id)
    
    if not comparison:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return comparison
