from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.routers.platform_auth import get_current_platform_user
from app.services import quality_foundation_service as service
from app.services.log_service import LogService
from app.schemas.quality_foundation import (
    QualityProjectCreate,
    QualityProjectUpdate,
    QualityProjectResponse,
    QualityVersionCreate,
    QualityVersionUpdate,
    QualityVersionResponse,
    QualityIterationCreate,
    QualityIterationUpdate,
    QualityIterationResponse,
    RequirementItemCreate,
    RequirementItemUpdate,
    RequirementItemResponse,
    RequirementCoverageResponse,
)

router = APIRouter(prefix="/api/foundation", tags=["foundation"])


@router.get("/projects", response_model=List[QualityProjectResponse])
def list_projects(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    return service.list_projects(db, keyword, status, skip, limit)


@router.get("/projects/{project_id}", response_model=QualityProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    project = service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects", response_model=QualityProjectResponse)
def create_project(
    data: QualityProjectCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.create_project(db, data)
    LogService(db, current_user.id, current_user.username).log_crud("创建", "项目管理", result.name, result.id)
    return result


@router.put("/projects/{project_id}", response_model=QualityProjectResponse)
def update_project(
    project_id: int,
    data: QualityProjectUpdate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    project = service.update_project(db, project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    LogService(db, current_user.id, current_user.username).log_crud("更新", "项目管理", project.name, project.id)
    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.delete_project(db, project_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Project not found")
    LogService(db, current_user.id, current_user.username).log_crud("删除", "项目管理", None, project_id)
    return {"success": True}


@router.get("/versions", response_model=List[QualityVersionResponse])
def list_versions(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    return service.list_versions(db, project_id, skip, limit)


@router.get("/versions/{version_id}", response_model=QualityVersionResponse)
def get_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    version = service.get_version(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/versions", response_model=QualityVersionResponse)
def create_version(
    data: QualityVersionCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        result = service.create_version(db, data)
        LogService(db, current_user.id, current_user.username).log_crud("创建", "版本管理", result.name, result.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/versions/{version_id}", response_model=QualityVersionResponse)
def update_version(
    version_id: int,
    data: QualityVersionUpdate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        version = service.update_version(db, version_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    LogService(db, current_user.id, current_user.username).log_crud("更新", "版本管理", version.name, version.id)
    return version


@router.delete("/versions/{version_id}")
def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.delete_version(db, version_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Version not found")
    LogService(db, current_user.id, current_user.username).log_crud("删除", "版本管理", None, version_id)
    return {"success": True}


@router.get("/iterations", response_model=List[QualityIterationResponse])
def list_iterations(
    project_id: Optional[int] = None,
    version_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    return service.list_iterations(db, project_id, version_id, skip, limit)


@router.get("/iterations/{iteration_id}", response_model=QualityIterationResponse)
def get_iteration(
    iteration_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    iteration = service.get_iteration(db, iteration_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")
    return iteration


@router.post("/iterations", response_model=QualityIterationResponse)
def create_iteration(
    data: QualityIterationCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        result = service.create_iteration(db, data)
        LogService(db, current_user.id, current_user.username).log_crud("创建", "迭代管理", result.name, result.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/iterations/{iteration_id}", response_model=QualityIterationResponse)
def update_iteration(
    iteration_id: int,
    data: QualityIterationUpdate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        iteration = service.update_iteration(db, iteration_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")
    LogService(db, current_user.id, current_user.username).log_crud("更新", "迭代管理", iteration.name, iteration.id)
    return iteration


@router.delete("/iterations/{iteration_id}")
def delete_iteration(
    iteration_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.delete_iteration(db, iteration_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Iteration not found")
    LogService(db, current_user.id, current_user.username).log_crud("删除", "迭代管理", None, iteration_id)
    return {"success": True}


@router.get("/requirements", response_model=List[RequirementItemResponse])
def list_requirements(
    project_id: Optional[int] = None,
    version_id: Optional[int] = None,
    iteration_id: Optional[int] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    return service.list_requirements(db, project_id, version_id, iteration_id, keyword, status, skip, limit)


@router.get("/requirements/coverage", response_model=RequirementCoverageResponse)
def get_requirement_coverage(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    return service.get_requirement_coverage(db, project_id)


@router.get("/requirements/{requirement_id}", response_model=RequirementItemResponse)
def get_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    requirement = service.get_requirement(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.post("/requirements", response_model=RequirementItemResponse)
def create_requirement(
    data: RequirementItemCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        result = service.create_requirement(db, data)
        LogService(db, current_user.id, current_user.username).log_crud("创建", "需求管理", result.title, result.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/requirements/{requirement_id}", response_model=RequirementItemResponse)
def update_requirement(
    requirement_id: int,
    data: RequirementItemUpdate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        requirement = service.update_requirement(db, requirement_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    LogService(db, current_user.id, current_user.username).log_crud("更新", "需求管理", requirement.title, requirement.id)
    return requirement


@router.delete("/requirements/{requirement_id}")
def delete_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.delete_requirement(db, requirement_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Requirement not found")
    LogService(db, current_user.id, current_user.username).log_crud("删除", "需求管理", None, requirement_id)
    return {"success": True}