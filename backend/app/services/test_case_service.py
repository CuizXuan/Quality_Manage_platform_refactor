import json
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.test_case import CaseVariant, TestCase
from app.models.api_test_case import ApiTestCase
from app.models.functional_test_case import FunctionalTestCase
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
        json_fields = ["tags"]
        result = data.copy()
        for field in json_fields:
            if field in result and isinstance(result[field], list):
                result[field] = json.dumps(result[field])
        return result

    def _deserialize_json_fields(self, obj: TestCase) -> Dict[str, Any]:
        """Deserialize JSON string fields from database."""
        return {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description or "",
            "folder_id": obj.folder_id,
            "priority": obj.priority or "P2",
            "tags": json.loads(obj.tags) if obj.tags else [],
            "pre_condition": obj.pre_condition or "",
            "case_type": obj.case_type,
            "source_debug_id": obj.source_debug_id,
            "created_by": obj.created_by,
            "created_at": obj.created_at.isoformat() if obj.created_at else "",
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }

    def create_case(self, data: dict) -> Dict[str, Any]:
        """Create a new test case with linked specialized record."""
        # Prepare main table data
        case_data = {
            "name": data["name"],
            "description": data.get("description", ""),
            "folder_id": data.get("folder_id"),
            "priority": data.get("priority", "P2"),
            "tags": json.dumps(data.get("tags", [])),
            "pre_condition": data.get("pre_condition", ""),
            "case_type": data.get("case_type", "api"),
            "source_debug_id": data.get("source_debug_id"),
            "created_by": data.get("created_by"),
        }

        case = self.repo.create(self.db, case_data)
        self.db.flush()

        # Create linked specialized record
        if case.case_type == "api":
            api_data = data.get("api_case", {})
            api_case = ApiTestCase(
                testcase_id=case.id,
                method=api_data.get("method", "GET"),
                url=api_data.get("url", ""),
                headers=json.dumps(api_data.get("headers", {})),
                params=json.dumps(api_data.get("params", {})),
                body_type=api_data.get("body_type", "none"),
                body=api_data.get("body", ""),
                auth_config=json.dumps(api_data.get("auth_config", {})),
                expected_status=api_data.get("expected_status", 200),
                assertions=json.dumps(api_data.get("assertions", [])),
            )
            self.db.add(api_case)
        else:
            func_data = data.get("functional_case", {})
            func_case = FunctionalTestCase(
                testcase_id=case.id,
                steps=json.dumps(func_data.get("steps", [])),
                test_data=json.dumps(func_data.get("test_data", {})),
                post_action=func_data.get("post_action", ""),
                expected_result=func_data.get("expected_result", ""),
            )
            self.db.add(func_case)

        self.db.commit()
        self.db.refresh(case)
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
        """Get a test case by ID with linked specialized data."""
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            return None

        result = self._deserialize_json_fields(case)

        if case.case_type == "api":
            api_case = self.db.query(ApiTestCase).filter(ApiTestCase.testcase_id == case_id).first()
            if api_case:
                result["api_case"] = self._deserialize_api_case(api_case)
        else:
            func_case = self.db.query(FunctionalTestCase).filter(FunctionalTestCase.testcase_id == case_id).first()
            if func_case:
                result["functional_case"] = self._deserialize_func_case(func_case)

        return result

    def _deserialize_api_case(self, api_case: ApiTestCase) -> Dict[str, Any]:
        """Deserialize API test case linked record."""
        return {
            "id": api_case.id,
            "testcase_id": api_case.testcase_id,
            "method": api_case.method,
            "url": api_case.url,
            "headers": json.loads(api_case.headers) if api_case.headers else {},
            "params": json.loads(api_case.params) if api_case.params else {},
            "body_type": api_case.body_type,
            "body": api_case.body or "",
            "auth_config": json.loads(api_case.auth_config) if api_case.auth_config else {},
            "expected_status": api_case.expected_status,
            "assertions": json.loads(api_case.assertions) if api_case.assertions else [],
        }

    def _deserialize_func_case(self, func_case: FunctionalTestCase) -> Dict[str, Any]:
        """Deserialize functional test case linked record."""
        return {
            "id": func_case.id,
            "testcase_id": func_case.testcase_id,
            "steps": json.loads(func_case.steps) if func_case.steps else [],
            "test_data": json.loads(func_case.test_data) if func_case.test_data else {},
            "post_action": func_case.post_action or "",
            "expected_result": func_case.expected_result or "",
        }

    def update_case(self, case_id: int, data: dict) -> Optional[Dict[str, Any]]:
        """Update a test case and its linked specialized record."""
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            return None

        # Update main table fields
        update_data = {}
        for field in ["name", "description", "folder_id", "priority", "pre_condition"]:
            if field in data and data[field] is not None:
                if field == "tags":
                    update_data[field] = json.dumps(data[field])
                else:
                    update_data[field] = data[field]

        if update_data:
            for k, v in update_data.items():
                setattr(case, k, v)

        # Update linked specialized record
        if case.case_type == "api":
            api_case = self.db.query(ApiTestCase).filter(ApiTestCase.testcase_id == case_id).first()
            if api_case:
                api_data = data.get("api_case", {})
                for field in ["method", "url", "body_type", "body", "expected_status"]:
                    if field in api_data and api_data[field] is not None:
                        setattr(api_case, field, api_data[field])
                for field in ["headers", "params", "auth_config", "assertions"]:
                    if field in api_data and api_data[field] is not None:
                        setattr(api_case, field, json.dumps(api_data[field]))
        else:
            func_case = self.db.query(FunctionalTestCase).filter(FunctionalTestCase.testcase_id == case_id).first()
            if func_case:
                func_data = data.get("functional_case", {})
                for field in ["post_action", "expected_result"]:
                    if field in func_data and func_data[field] is not None:
                        setattr(func_case, field, func_data[field])
                for field in ["steps", "test_data"]:
                    if field in func_data and func_data[field] is not None:
                        setattr(func_case, field, json.dumps(func_data[field]))

        self.db.commit()
        self.db.refresh(case)
        return self._deserialize_json_fields(case)

    def delete_case(self, case_id: int) -> bool:
        """Delete a test case and its linked specialized records."""
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            return False

        # Delete linked specialized records
        self.db.query(ApiTestCase).filter(ApiTestCase.testcase_id == case_id).delete()
        self.db.query(FunctionalTestCase).filter(FunctionalTestCase.testcase_id == case_id).delete()
        self.variant_repo.delete_by_case(self.db, case_id)
        self.repo.delete(self.db, case)
        return True

    def create_variant(self, case_id: int, data: dict) -> Dict[str, Any]:
        """Create a case variant."""
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            raise ValueError("Test case not found")

        if data.get("variant_type") and data["variant_type"] not in VALID_VARIANT_TYPES:
            raise ValueError(f"Invalid variant type: {data['variant_type']}")

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
        case = self.repo.get_by_id(self.db, case_id)
        if not case:
            raise ValueError("Test case not found")

        variants, total = self.variant_repo.list_by_case(
            self.db, case_id, page=page, page_size=page_size, variant_type=variant_type
        )
        items = [self._deserialize_variant(v) for v in variants]
        return items, total

    def copy_case(self, case_id: int, created_by: int) -> Optional[Dict[str, Any]]:
        """Copy a test case with its linked specialized record."""
        original = self.repo.get_by_id(self.db, case_id)
        if not original:
            return None

        # Get original's linked specialized data
        original_data = self.get_case(case_id)
        new_name = f"{original.name} - 副本"

        case_data = {
            "name": new_name,
            "description": original_data.get("description", ""),
            "folder_id": original_data.get("folder_id"),
            "priority": original_data.get("priority", "P2"),
            "tags": json.dumps(original_data.get("tags", [])),
            "pre_condition": original_data.get("pre_condition", ""),
            "case_type": original_data.get("case_type", "api"),
            "source_debug_id": None,
            "created_by": created_by,
        }

        case = self.repo.create(self.db, case_data)
        self.db.flush()

        # Copy linked specialized record
        if case.case_type == "api":
            api_data = original_data.get("api_case", {})
            api_case = ApiTestCase(
                testcase_id=case.id,
                method=api_data.get("method", "GET"),
                url=api_data.get("url", ""),
                headers=json.dumps(api_data.get("headers", {})),
                params=json.dumps(api_data.get("params", {})),
                body_type=api_data.get("body_type", "none"),
                body=api_data.get("body", ""),
                auth_config=json.dumps(api_data.get("auth_config", {})),
                expected_status=api_data.get("expected_status", 200),
                assertions=json.dumps(api_data.get("assertions", [])),
            )
            self.db.add(api_case)
        else:
            func_data = original_data.get("functional_case", {})
            func_case = FunctionalTestCase(
                testcase_id=case.id,
                steps=json.dumps(func_data.get("steps", [])),
                test_data=json.dumps(func_data.get("test_data", {})),
                post_action=func_data.get("post_action", ""),
                expected_result=func_data.get("expected_result", ""),
            )
            self.db.add(func_case)

        self.db.commit()
        self.db.refresh(case)
        return self._deserialize_json_fields(case)

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