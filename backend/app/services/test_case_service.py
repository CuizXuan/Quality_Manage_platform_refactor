import json
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.test_case import CaseVariant, TestCase
from app.repositories.case_variant_repository import CaseVariantRepository
from app.repositories.test_case_repository import TestCaseRepository
from app.schemas.case_variant import VALID_VARIANT_TYPES


class TestCaseService:
    """Service for test case business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = TestCaseRepository()
        self.variant_repo = CaseVariantRepository()

    def _serialize_json_fields(self, data: dict) -> dict:
        """Serialize JSON fields to string for database storage."""
        json_fields = ["query_params", "headers", "cookies", "auth_config"]
        result = data.copy()
        for field in json_fields:
            if field in result and isinstance(result[field], dict):
                result[field] = json.dumps(result[field])
        return result

    def _deserialize_json_fields(self, obj: TestCase) -> Dict[str, Any]:
        """Deserialize JSON string fields from database."""
        return {
            "id": obj.id,
            "case_type": obj.case_type,
            "folder_id": obj.folder_id,
            "name": obj.name,
            "description": obj.description or "",
            "method": obj.method,
            "url": obj.url,
            "query_params": json.loads(obj.query_params) if obj.query_params else {},
            "headers": json.loads(obj.headers) if obj.headers else {},
            "cookies": json.loads(obj.cookies) if obj.cookies else {},
            "auth_config": json.loads(obj.auth_config) if obj.auth_config else {},
            "body_type": obj.body_type,
            "body": obj.body or "",
            "expected_status": obj.expected_status,
            "source_debug_id": obj.source_debug_id,
            "created_by": obj.created_by,
            "created_at": obj.created_at.isoformat() if obj.created_at else "",
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }

    def create_case(self, data: dict) -> Dict[str, Any]:
        """Create a new test case."""
        data = self._serialize_json_fields(data)
        if "created_by" not in data:
            data["created_by"] = None
        case = self.repo.create(self.db, data)
        return self._deserialize_json_fields(case)

    def list_cases(
        self,
        page: int = 1,
        page_size: int = 20,
        folder_id: Optional[int] = None,
        keyword: Optional[str] = None,
        case_type: Optional[str] = None,
    ) -> Tuple[list[Dict[str, Any]], int]:
        """List test cases with pagination."""
        cases, total = self.repo.list(
            self.db, page=page, page_size=page_size, folder_id=folder_id, keyword=keyword, case_type=case_type
        )
        items = [self._deserialize_json_fields(c) for c in cases]
        return items, total

    def get_case(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Get a test case by ID."""
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            return None
        return self._deserialize_json_fields(case)

    def update_case(self, case_id: int, data: dict) -> Optional[Dict[str, Any]]:
        """Update a test case."""
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            return None
        data = self._serialize_json_fields(data)
        # Remove None values to preserve unchanged fields
        data = {k: v for k, v in data.items() if v is not None}
        updated = self.repo.update(self.db, case, data)
        return self._deserialize_json_fields(updated)

    def delete_case(self, case_id: int) -> bool:
        """Delete a test case and its variants."""
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            return False
        self.variant_repo.delete_by_case(self.db, case_id)
        self.repo.delete(self.db, case)
        return True

    def create_variant(self, case_id: int, data: dict) -> Dict[str, Any]:
        """Create a case variant."""
        # Check if case exists
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            raise ValueError("Test case not found")

        # Validate variant type
        if data.get("variant_type") and data["variant_type"] not in VALID_VARIANT_TYPES:
            raise ValueError(f"Invalid variant type: {data['variant_type']}")

        # Serialize JSON fields
        json_fields = ["override_params", "override_headers"]
        for field in json_fields:
            if field in data and isinstance(data[field], dict):
                data[field] = json.dumps(data[field])

        if "expected_schema" in data and isinstance(data.get("expected_schema"), dict):
            data["expected_schema"] = json.dumps(data["expected_schema"])

        if "assertions" in data:
            data["assertions"] = json.dumps(data["assertions"])

        if "created_by" not in data:
            data["created_by"] = None

        variant = self.variant_repo.create(self.db, case_id, data)
        return self._deserialize_variant(variant)

    def list_variants(
        self,
        case_id: int,
        page: int = 1,
        page_size: int = 20,
        variant_type: Optional[str] = None,
    ) -> Tuple[list[Dict[str, Any]], int]:
        """List variants for a test case."""
        # Check if case exists
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            raise ValueError("Test case not found")

        variants, total = self.variant_repo.list_by_case(
            self.db, case_id, page=page, page_size=page_size, variant_type=variant_type
        )
        items = [self._deserialize_variant(v) for v in variants]
        return items, total

    def _deserialize_variant(self, variant: CaseVariant) -> Dict[str, Any]:
        """Deserialize a variant from database model."""
        return {
            "id": variant.id,
            "case_id": variant.case_id,
            "name": variant.name,
            "variant_type": variant.variant_type,
            "override_params": json.loads(variant.override_params) if variant.override_params else {},
            "override_headers": json.loads(variant.override_headers) if variant.override_headers else {},
            "override_body": variant.override_body or "",
            "expected_status": variant.expected_status,
            "expected_schema": json.loads(variant.expected_schema) if variant.expected_schema else None,
            "assertions": json.loads(variant.assertions) if variant.assertions else [],
            "created_by": variant.created_by,
            "created_at": variant.created_at.isoformat() if variant.created_at else "",
        }
