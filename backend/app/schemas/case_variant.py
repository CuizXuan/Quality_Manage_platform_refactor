from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Valid variant types from design doc
VALID_VARIANT_TYPES = [
    "normal",
    "boundary",
    "empty",
    "missing_field",
    "type_error",
    "invalid_enum",
    "overlong_field",
    "auth_failed",
    "permission_denied",
    "response_schema",
    "response_business_value",
    "performance_threshold",
]


class CaseVariantCreate(BaseModel):
    name: str = Field(..., max_length=200)
    variant_type: str = Field(..., max_length=50)
    override_params: Dict[str, Any] = Field(default_factory=dict)
    override_headers: Dict[str, Any] = Field(default_factory=dict)
    override_body: str = ""
    expected_status: Optional[int] = None
    expected_schema: Optional[Dict[str, Any]] = None
    assertions: List[Any] = Field(default_factory=list)


class CaseVariantResponse(BaseModel):
    id: int
    case_id: int
    name: str
    variant_type: str
    override_params: Dict[str, Any]
    override_headers: Dict[str, Any]
    override_body: str
    expected_status: Optional[int] = None
    expected_schema: Optional[Dict[str, Any]] = None
    assertions: List[Any]
    created_by: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True


class CaseVariantListResponse(BaseModel):
    items: List[CaseVariantResponse]
    total: int
    page: int
    page_size: int
