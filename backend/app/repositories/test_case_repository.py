from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.test_case import TestCase


class CaseListFilters:
    """Normalized filters for case list queries."""

    def __init__(
        self,
        folder_id: Optional[int] = None,
        folder_ids: Optional[List[int]] = None,
        keyword: Optional[str] = None,
        case_type: Optional[str] = None,
        methods: Optional[List[str]] = None,
        priorities: Optional[List[str]] = None,
        created_start: Optional[datetime] = None,
        created_end: Optional[datetime] = None,
        is_automated: Optional[bool] = None,
    ):
        self.folder_id = folder_id
        self.folder_ids = folder_ids or []
        self.keyword = keyword
        self.case_type = case_type
        self.methods = methods or []
        self.priorities = priorities or []
        self.created_start = created_start
        self.created_end = created_end
        self.is_automated = is_automated


class TestCaseRepository:
    """Repository for TestCase database operations."""

    @staticmethod
    def create(db: Session, data: dict) -> TestCase:
        """Create a new test case."""
        test_case = TestCase(**data)
        db.add(test_case)
        db.commit()
        db.refresh(test_case)
        return test_case

    @staticmethod
    def build_query(db: Session, filters: CaseListFilters):
        """Build filtered query for list and statistics."""
        query = db.query(TestCase)

        if filters.folder_id is not None:
            query = query.filter(TestCase.folder_id == filters.folder_id)

        if filters.folder_ids:
            query = query.filter(TestCase.folder_id.in_(filters.folder_ids))

        if filters.keyword:
            keyword = f"%{filters.keyword}%"
            query = query.filter(or_(TestCase.name.ilike(keyword), TestCase.url.ilike(keyword)))

        if filters.case_type is not None:
            query = query.filter(TestCase.case_type == filters.case_type)

        if filters.methods:
            query = query.filter(TestCase.method.in_(filters.methods))

        if filters.priorities:
            query = query.filter(TestCase.priority.in_(filters.priorities))

        if filters.created_start:
            query = query.filter(TestCase.created_at >= filters.created_start)

        if filters.created_end:
            query = query.filter(TestCase.created_at <= filters.created_end)

        if filters.is_automated is not None:
            query = query.filter(TestCase.is_automated == filters.is_automated)

        return query

    @staticmethod
    def list(
        db: Session,
        filters: CaseListFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[list[TestCase], int]:
        """List test cases with pagination and filtering."""
        query = TestCaseRepository.build_query(db, filters)
        total = query.count()
        items = (
            query.order_by(TestCase.updated_at.desc(), TestCase.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def count_by_type(db: Session) -> dict:
        """Count all cases grouped by type."""
        rows = db.query(TestCase.case_type, func.count(TestCase.id)).group_by(TestCase.case_type).all()
        return {case_type: total for case_type, total in rows}

    @staticmethod
    def automation_count(db: Session, filters: CaseListFilters) -> int:
        """Count automated cases under current filters."""
        query = TestCaseRepository.build_query(db, filters)
        return query.filter(TestCase.is_automated == True).count()

    @staticmethod
    def get_by_id(db: Session, case_id: int) -> Optional[TestCase]:
        """Get a test case by ID."""
        return db.query(TestCase).filter(TestCase.id == case_id).first()

    @staticmethod
    def update(db: Session, case_obj: TestCase, data: dict) -> TestCase:
        """Update a test case."""
        for key, value in data.items():
            if value is not None and hasattr(case_obj, key):
                setattr(case_obj, key, value)
        db.commit()
        db.refresh(case_obj)
        return case_obj

    @staticmethod
    def delete(db: Session, case_obj: TestCase) -> None:
        """Delete a test case."""
        db.delete(case_obj)
        db.commit()
