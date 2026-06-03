from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SecretVariablePayload(BaseModel):
    key: str = Field(..., max_length=100)
    value: str = ""
    is_secret: bool = False


class VariableSetPayload(BaseModel):
    name: str = Field(..., max_length=100)
    scope: str = "shared"
    sort_order: int = 0
    enabled: bool = True
    variables: List[SecretVariablePayload] = Field(default_factory=list)


class EnvironmentCreate(BaseModel):
    project_id: Optional[int] = None
    name: str = Field(..., max_length=100)
    code: str = Field(default="", max_length=50)
    base_url: Optional[str] = Field(default=None, max_length=500)
    description: str = ""
    enabled: bool = True
    variable_sets: List[VariableSetPayload] = Field(default_factory=list)


class EnvironmentResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    name: str
    code: str = ""
    base_url: Optional[str] = None
    description: str = ""
    enabled: bool = True
    variable_sets: List[Dict] = []


class RenderRequestPayload(BaseModel):
    method: str
    url: str
    query_params: Dict = Field(default_factory=dict)
    headers: Dict = Field(default_factory=dict)
    cookies: Dict = Field(default_factory=dict)
    auth_config: Dict = Field(default_factory=dict)
    body_type: str = "none"
    body: str = ""
    environment_id: Optional[int] = None


class RenderRequestResponse(BaseModel):
    method: str
    url: str
    query_params: Dict
    headers: Dict
    cookies: Dict
    auth_config: Dict
    body_type: str
    body: str
    resolved_variables: Dict[str, str] = {}
