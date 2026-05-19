from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.test_case import CaseVariant


class CaseVariantRepository:
    """Repository for CaseVariant database operations."""

    @staticmethod
    def create(db: Session, case_id: int, data: dict) -> CaseVariant:
        """Create a new case variant."""
        variant = CaseVariant(case_id=case_id, **data)
        db.add(variant)
        db.commit()
        db.refresh(variant)
        return variant

    @staticmethod
    def list_by_case(
        db: Session,
        case_id: int,
        page: int = 1,
        page_size: int = 20,
        variant_type: Optional[str] = None,
    ) -> Tuple[list[CaseVariant], int]:
        """List variants for a specific test case."""
        query = db.query(CaseVariant).filter(CaseVariant.case_id == case_id)

        if variant_type:
            query = query.filter(CaseVariant.variant_type == variant_type)

        total = query.count()
        items = (
            query.order_by(CaseVariant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def delete_by_case(db: Session, case_id: int) -> None:
        """Delete all variants for a test case."""
        db.query(CaseVariant).filter(CaseVariant.case_id == case_id).delete()
        db.commit()
