from typing import Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.test_case import TestCase


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
    def list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        folder_id: Optional[int] = None,
        keyword: Optional[str] = None,
        case_type: Optional[str] = None,
    ) -> Tuple[list[TestCase], int]:
        """List test cases with pagination and filtering."""
        query = db.query(TestCase)

        if folder_id is not None:
            query = query.filter(TestCase.folder_id == folder_id)

        if keyword:
            query = query.filter(TestCase.name.ilike(f"%{keyword}%"))

        if case_type is not None:
            query = query.filter(TestCase.case_type == case_type)

        total = query.count()
        items = (
            query.order_by(TestCase.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

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
