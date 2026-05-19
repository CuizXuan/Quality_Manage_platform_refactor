from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StepItem(BaseModel):
    """执行步骤项"""
    order: int
    description: str
    expected_result: str
    test_data: Dict[str, Any] = Field(default_factory=dict)


class FunctionalTestCaseCreate(BaseModel):
    steps: List[StepItem] = Field(default_factory=list)
    test_data: Dict[str, Any] = Field(default_factory=dict)
    post_action: str = ""
    expected_result: str = ""


class FunctionalTestCaseUpdate(BaseModel):
    steps: Optional[List[StepItem]] = None
    test_data: Optional[Dict[str, Any]] = None
    post_action: Optional[str] = None
    expected_result: Optional[str] = None


class FunctionalTestCaseResponse(BaseModel):
    id: int
    testcase_id: int
    steps: List[StepItem]
    test_data: Dict[str, Any]
    post_action: str
    expected_result: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True