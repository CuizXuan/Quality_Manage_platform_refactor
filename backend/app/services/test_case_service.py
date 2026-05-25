import json
from datetime import datetime, time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.test_case import CaseVariant, TestCase
from app.models.api_test_case import ApiTestCase
from app.models.functional_test_case import FunctionalTestCase
from app.repositories.case_variant_repository import CaseVariantRepository
from app.repositories.test_case_repository import CaseListFilters, TestCaseRepository
from app.schemas.case_variant import VALID_VARIANT_TYPES


class TestCaseService:
    """Service for test case business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = TestCaseRepository()
        self.variant_repo = CaseVariantRepository()

    def _serialize_json_fields(self, data: dict) -> dict:
        """Serialize JSON fields to string for database storage."""
        json_fields = ["tags", "auto_script_config"]
        result = data.copy()
        for field in json_fields:
            if field in result and isinstance(result[field], (dict, list)):
                result[field] = json.dumps(result[field])
        return result

    def _load_json_value(self, value: str, fallback: Any) -> Any:
        """Load a JSON string and return fallback when content is invalid."""
        if not value:
            return fallback
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback

    def _next_auto_case_id(self, case_type: str, created_at: Optional[datetime] = None) -> str:
        """Generate date based case code for the given type."""
        prefix = "APICASE" if case_type == "api" else "FUNCCASE"
        date_value = created_at or datetime.utcnow()
        date_text = date_value.strftime("%Y%m%d")
        code_prefix = f"{prefix}-{date_text}"
        rows = (
            self.db.query(TestCase.auto_case_id)
            .filter(TestCase.auto_case_id.like(f"{code_prefix}%"))
            .all()
        )
        max_number = 0
        for (code,) in rows:
            suffix = str(code or "").replace(code_prefix, "", 1)
            if suffix.isdigit():
                max_number = max(max_number, int(suffix))
        return f"{code_prefix}{max_number + 1:02d}"

    def _normalize_api_case_data(self, data: dict) -> dict:
        """Support both nested case form and terminal save payload."""
        api_data = data.get("api_case") or {}
        return {
            "method": api_data.get("method") or data.get("method", "GET"),
            "url": api_data.get("url") or data.get("url", ""),
            "headers": api_data.get("headers") or data.get("headers", {}),
            "params": api_data.get("params") or data.get("query_params", {}),
            "body_type": api_data.get("body_type") or data.get("body_type", "none"),
            "body": api_data.get("body") if "body" in api_data else data.get("body", ""),
            "auth_config": api_data.get("auth_config") or data.get("auth_config", {}),
            "expected_status": api_data.get("expected_status") or data.get("expected_status", 200),
            "assertions": api_data.get("assertions", []),
        }

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
            "creator_name": self._get_creator_name(obj.created_by),
            "is_automated": bool(obj.is_automated),
            "auto_script_path": obj.auto_script_path or "",
            "auto_script_config": self._load_json_value(obj.auto_script_config, {}),
            "auto_case_id": obj.auto_case_id or "",
            "created_at": obj.created_at.isoformat() if obj.created_at else "",
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
            # Legacy API fields from main table
            "method": getattr(obj, "method", None),
            "url": getattr(obj, "url", None),
            "headers": json.loads(obj.headers) if getattr(obj, "headers", None) else {},
            "query_params": json.loads(obj.query_params) if getattr(obj, "query_params", None) else {},
            "body_type": getattr(obj, "body_type", "none"),
            "body": getattr(obj, "body", "") or "",
            "auth_config": json.loads(obj.auth_config) if getattr(obj, "auth_config", None) else {},
            "expected_status": getattr(obj, "expected_status", 200),
            # 质量基础关联字段
            "project_id": getattr(obj, "project_id", None),
            "version_id": getattr(obj, "version_id", None),
            "iteration_id": getattr(obj, "iteration_id", None),
            "requirement_id": getattr(obj, "requirement_id", None),
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
            "is_automated": data.get("is_automated", False),
            "auto_script_path": data.get("auto_script_path", ""),
            "auto_script_config": json.dumps(data.get("auto_script_config", {})),
            "auto_case_id": data.get("auto_case_id") or self._next_auto_case_id(data.get("case_type", "api")),
            "project_id": data.get("project_id"),
            "version_id": data.get("version_id"),
            "iteration_id": data.get("iteration_id"),
            "requirement_id": data.get("requirement_id"),
        }

        # For API cases, populate legacy debug fields on main table (required by DB schema)
        if case_data["case_type"] == "api":
            api_data = self._normalize_api_case_data(data)
            case_data["method"] = api_data.get("method", "GET")
            case_data["url"] = api_data.get("url", "")
            case_data["headers"] = json.dumps(api_data.get("headers", {}))
            case_data["query_params"] = json.dumps(api_data.get("params", {}))
            case_data["body_type"] = api_data.get("body_type", "none")
            case_data["body"] = api_data.get("body", "")
            case_data["auth_config"] = json.dumps(api_data.get("auth_config", {}))
            case_data["expected_status"] = api_data.get("expected_status", 200)

        case = self.repo.create(self.db, case_data)
        self.db.flush()

        # Create linked specialized record
        if case.case_type == "api":
            api_data = self._normalize_api_case_data(data)
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
            func_data = data.get("functional_case") or {}
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

        # Build response with linked specialized data (same as get_case)
        result = self._deserialize_json_fields(case)
        if case.case_type == "api":
            api_case = self.db.query(ApiTestCase).filter(ApiTestCase.testcase_id == case.id).first()
            if api_case:
                result["api_case"] = self._deserialize_api_case(api_case)
        else:
            func_case = self.db.query(FunctionalTestCase).filter(FunctionalTestCase.testcase_id == case.id).first()
            if func_case:
                result["functional_case"] = self._deserialize_func_case(func_case)
        return result

    def list_cases(
        self,
        page: int = 1,
        page_size: int = 20,
        folder_id: Optional[int] = None,
        folder_ids: Optional[List[int]] = None,
        keyword: Optional[str] = None,
        case_type: Optional[str] = None,
        methods: Optional[List[str]] = None,
        priorities: Optional[List[str]] = None,
        created_start: Optional[str] = None,
        created_end: Optional[str] = None,
        is_automated: Optional[bool] = None,
        project_id: Optional[int] = None,
        version_id: Optional[int] = None,
        iteration_id: Optional[int] = None,
        requirement_id: Optional[int] = None,
    ) -> Tuple[list[Dict[str, Any]], int, Dict[str, Any]]:
        """List test cases with pagination."""
        filters = self._build_filters(
            folder_id=folder_id,
            folder_ids=folder_ids,
            keyword=keyword,
            case_type=case_type,
            methods=methods,
            priorities=priorities,
            created_start=created_start,
            created_end=created_end,
            is_automated=is_automated,
            project_id=project_id,
            version_id=version_id,
            iteration_id=iteration_id,
            requirement_id=requirement_id,
        )
        cases, total = self.repo.list(self.db, filters=filters, page=page, page_size=page_size)
        items = [self._serialize_case_summary(c) for c in cases]
        stats = self.get_case_stats(filters, total)
        return items, total, stats

    def _build_filters(self, **kwargs) -> CaseListFilters:
        """Create repository filters from API query values."""
        return CaseListFilters(
            folder_id=kwargs.get("folder_id"),
            folder_ids=kwargs.get("folder_ids") or [],
            keyword=kwargs.get("keyword"),
            case_type=kwargs.get("case_type"),
            methods=kwargs.get("methods") or [],
            priorities=kwargs.get("priorities") or [],
            created_start=self._parse_date(kwargs.get("created_start"), False),
            created_end=self._parse_date(kwargs.get("created_end"), True),
            is_automated=kwargs.get("is_automated"),
            project_id=kwargs.get("project_id"),
            version_id=kwargs.get("version_id"),
            iteration_id=kwargs.get("iteration_id"),
            requirement_id=kwargs.get("requirement_id"),
        )

    def _parse_date(self, value: Optional[str], end_of_day: bool) -> Optional[datetime]:
        """Parse ISO date string for query range."""
        if not value:
            return None
        try:
            date_value = datetime.fromisoformat(value).date()
        except ValueError:
            return None
        return datetime.combine(date_value, time.max if end_of_day else time.min)

    def get_case_stats(self, filters: CaseListFilters, filtered_total: int) -> Dict[str, Any]:
        """Build summary cards and coverage stats for current filters."""
        type_counts = self.repo.count_by_type(self.db)
        automated = self.repo.automation_count(self.db, filters)
        coverage = round((automated / filtered_total) * 100, 1) if filtered_total else 0
        api_total = type_counts.get("api", 0)
        functional_total = type_counts.get("functional", 0)
        all_total = api_total + functional_total
        return {
            "total": all_total,
            "api_total": api_total,
            "functional_total": functional_total,
            "current_total": filtered_total,
            "automated": automated,
            "coverage": coverage,
        }

    def _serialize_case_summary(self, case: TestCase) -> Dict[str, Any]:
        """Serialize list item with type-specific fields."""
        result = self._deserialize_json_fields(case)
        if case.case_type == "api" and case.api_case:
            result["api_case"] = self._deserialize_api_case(case.api_case)
        if case.case_type == "functional" and case.functional_case:
            result["functional_case"] = self._deserialize_func_case(case.functional_case)
        return result

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
        fields = [
            "name",
            "description",
            "folder_id",
            "priority",
            "tags",
            "pre_condition",
            "is_automated",
            "auto_script_path",
            "auto_script_config",
            "auto_case_id",
            "project_id",
            "version_id",
            "iteration_id",
            "requirement_id",
        ]
        for field in fields:
            if field in data and data[field] is not None:
                if field in {"tags", "auto_script_config"}:
                    update_data[field] = json.dumps(data[field])
                else:
                    update_data[field] = data[field]

        # Update legacy API fields on main table
        if case.case_type == "api":
            api_data = data.get("api_case") or {}
            for field in ["method", "url", "body_type", "body", "expected_status"]:
                if field in api_data and api_data[field] is not None:
                    update_data[field] = api_data[field]
            if "headers" in api_data and api_data["headers"] is not None:
                update_data["headers"] = json.dumps(api_data["headers"])
            if "params" in api_data and api_data["params"] is not None:
                update_data["query_params"] = json.dumps(api_data["params"])
            if "auth_config" in api_data and api_data["auth_config"] is not None:
                update_data["auth_config"] = json.dumps(api_data["auth_config"])

        if update_data:
            for k, v in update_data.items():
                setattr(case, k, v)

        # Update linked specialized record
        if case.case_type == "api":
            api_case = self.db.query(ApiTestCase).filter(ApiTestCase.testcase_id == case_id).first()
            if api_case:
                api_data = data.get("api_case") or {}
                for field in ["method", "url", "body_type", "body", "expected_status"]:
                    if field in api_data and api_data[field] is not None:
                        setattr(api_case, field, api_data[field])
                for field in ["headers", "params", "auth_config", "assertions"]:
                    if field in api_data and api_data[field] is not None:
                        setattr(api_case, field, json.dumps(api_data[field]))
        else:
            func_case = self.db.query(FunctionalTestCase).filter(FunctionalTestCase.testcase_id == case_id).first()
            if func_case:
                func_data = data.get("functional_case") or {}
                for field in ["post_action", "expected_result"]:
                    if field in func_data and func_data[field] is not None:
                        setattr(func_case, field, func_data[field])
                for field in ["steps", "test_data"]:
                    if field in func_data and func_data[field] is not None:
                        setattr(func_case, field, json.dumps(func_data[field]))

        self.db.commit()
        self.db.refresh(case)
        return self._deserialize_json_fields(case)

    def batch_delete_cases(self, case_ids: List[int]) -> int:
        """Delete multiple test cases and return success count."""
        deleted_count = 0
        for case_id in case_ids:
            if self.delete_case(case_id):
                deleted_count += 1
        return deleted_count

    def batch_update_cases(self, case_ids: List[int], data: dict) -> int:
        """Batch update safe list fields."""
        allowed_fields = {"priority", "is_automated"}
        update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}
        if not update_data:
            return 0
        count = (
            self.db.query(TestCase)
            .filter(TestCase.id.in_(case_ids))
            .update(update_data, synchronize_session=False)
        )
        self.db.commit()
        return count

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
            "is_automated": original_data.get("is_automated", False),
            "auto_script_path": original_data.get("auto_script_path", ""),
            "auto_script_config": json.dumps(original_data.get("auto_script_config", {})),
            "auto_case_id": self._next_auto_case_id(original_data.get("case_type", "api")),
            "project_id": original_data.get("project_id"),
            "version_id": original_data.get("version_id"),
            "iteration_id": original_data.get("iteration_id"),
            "requirement_id": original_data.get("requirement_id"),
        }

        # Copy legacy API fields to main table if API case
        if case_data["case_type"] == "api":
            api_data = original_data.get("api_case") or {}
            case_data["method"] = api_data.get("method", "GET")
            case_data["url"] = api_data.get("url", "")
            case_data["headers"] = json.dumps(api_data.get("headers", {}))
            case_data["query_params"] = json.dumps(api_data.get("params", {}))
            case_data["body_type"] = api_data.get("body_type", "none")
            case_data["body"] = api_data.get("body", "")
            case_data["auth_config"] = json.dumps(api_data.get("auth_config", {}))
            case_data["expected_status"] = api_data.get("expected_status", 200)

        case = self.repo.create(self.db, case_data)
        self.db.flush()

        # Copy linked specialized record
        if case.case_type == "api":
            api_data = original_data.get("api_case") or {}
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
            func_data = original_data.get("functional_case") or {}
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

    def _get_creator_name(self, user_id: Optional[int]) -> str:
        """Return display name for list rendering."""
        if not user_id:
            return ""
        from app.models.platform import PlatformUser

        user = self.db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
        if not user:
            return str(user_id)
        return user.display_name or user.username
