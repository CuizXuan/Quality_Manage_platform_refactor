from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.routers.platform_auth import get_current_platform_user
from app.schemas.case_variant import CaseVariantCreate, CaseVariantListResponse
from app.schemas.test_case import (
    DeleteResponse,
    TestCaseCreate,
    TestCaseListResponse,
    TestCaseResponse,
    TestCaseUpdate,
)
from app.services.test_case_service import TestCaseService

router = APIRouter(prefix="/api/case", tags=["用例管理"])


@router.post("", response_model=TestCaseResponse)
def create_testcase(
    case: TestCaseCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Create a new test case."""
    service = TestCaseService(db)
    data = case.model_dump()
    data["created_by"] = current_user.id
    result = service.create_case(data)
    return result


@router.get("", response_model=TestCaseListResponse)
def list_testcases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_type: Optional[str] = Query(None, description="用例类型: functional 或 api"),
    folder_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """List test cases with pagination."""
    service = TestCaseService(db)
    items, total = service.list_cases(
        page=page, page_size=page_size, case_type=case_type, folder_id=folder_id, keyword=keyword
    )
    return TestCaseListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{case_id}", response_model=TestCaseResponse)
def get_testcase(
    case_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Get a test case by ID."""
    service = TestCaseService(db)
    result = service.get_case(case_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test case not found")
    return result


@router.put("/{case_id}", response_model=TestCaseResponse)
def update_testcase(
    case_id: int,
    case: TestCaseUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Update a test case."""
    service = TestCaseService(db)
    data = case.model_dump(exclude_unset=True)
    result = service.update_case(case_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Test case not found")
    return result


@router.delete("/{case_id}", response_model=DeleteResponse)
def delete_testcase(
    case_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Delete a test case."""
    service = TestCaseService(db)
    success = service.delete_case(case_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test case not found")
    return {"id": case_id}


@router.post("/{case_id}/copy", response_model=TestCaseResponse)
def copy_testcase(
    case_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Copy a test case."""
    service = TestCaseService(db)
    result = service.copy_case(case_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Test case not found")
    return result


@router.post("/{case_id}/variant", response_model=dict)
def create_variant(
    case_id: int,
    variant: CaseVariantCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Create a case variant."""
    service = TestCaseService(db)
    data = variant.model_dump()
    data["created_by"] = current_user.id
    try:
        result = service.create_variant(case_id, data)
        return result
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{case_id}/variant", response_model=CaseVariantListResponse)
def list_variants(
    case_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    variant_type: Optional[str] = Query(None),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """List variants for a test case."""
    service = TestCaseService(db)
    try:
        items, total = service.list_variants(
            case_id, page=page, page_size=page_size, variant_type=variant_type
        )
        return CaseVariantListResponse(items=items, total=total, page=page, page_size=page_size)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))