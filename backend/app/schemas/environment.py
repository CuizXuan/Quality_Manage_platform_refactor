from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, List, Dict, Any
from datetime import datetime


def _convert_variables(variables: Any) -> Dict[str, str]:
    """将 variables 从数组格式转为字典格式"""
    if not variables:
        return {}
    if isinstance(variables, dict):
        return variables
    if isinstance(variables, list):
        result = {}
        for item in variables:
            if isinstance(item, dict) and "key" in item:
                key = str(item["key"])
                value = str(item.get("value", ""))
                if key:
                    result[key] = value
        return result
    return {}


class EnvironmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    variables: Optional[Union[dict, List[dict]]] = None
    is_default: bool = False
    sort_order: int = 0

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('环境名称不能为空')
        return v.strip()

    @field_validator('variables', mode='before')
    @classmethod
    def validate_variables(cls, v: Any) -> Optional[dict]:
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, list):
            return _convert_variables(v)
        return {}


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(EnvironmentBase):
    pass


class EnvironmentResponse(EnvironmentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
