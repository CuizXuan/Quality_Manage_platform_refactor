from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    display_name: str = ""
    phone: str = ""
    organization_id: Optional[int] = None
    role_ids: list[int] = []


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    organization_id: Optional[int] = None
    role_ids: Optional[list[int]] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    phone: str
    status: str
    organization_id: Optional[int]
    organization_name: Optional[str] = None
    roles: list[str] = []
    role_ids: list[int] = []
    created_at: datetime
    last_login_at: Optional[datetime] = None


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    code: str = Field(..., min_length=2, max_length=80)
    description: str = ""
    permissions: list[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[list[str]] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str
    is_system: bool
    status: str
    permissions: list[str] = []
    created_at: datetime


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: str = ""
    parent_id: Optional[int] = None
    sort_order: int = 0


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None


class OrganizationResponse(BaseModel):
    id: int
    parent_id: Optional[int]
    name: str
    code: str
    description: str
    status: str
    sort_order: int
    user_count: int = 0
    created_at: datetime


class MenuCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=100)
    path: str = ""
    icon: str = ""
    component: str = ""
    permission_code: str = ""
    parent_id: Optional[int] = None
    visible: bool = True
    sort_order: int = 0


class MenuUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    component: Optional[str] = None
    permission_code: Optional[str] = None
    parent_id: Optional[int] = None
    visible: Optional[bool] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None


class MenuResponse(BaseModel):
    id: int
    parent_id: Optional[int]
    name: str
    code: str
    path: str
    icon: str
    component: str
    permission_code: str
    visible: bool
    status: str
    sort_order: int
    created_at: datetime

