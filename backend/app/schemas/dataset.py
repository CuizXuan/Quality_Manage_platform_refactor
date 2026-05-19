from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DataSetRowBase(BaseModel):
    row_index: int
    variables: Dict[str, Any] = {}
    enabled: bool = True


class DataSetRowCreate(DataSetRowBase):
    pass


class DataSetRowUpdate(BaseModel):
    variables: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class DataSetRowResponse(DataSetRowBase):
    id: int
    dataset_id: int

    class Config:
        from_attributes = True


class DataSetBase(BaseModel):
    name: str
    description: str = ""
    type: str = "csv"  # csv / json
    file_path: str = ""
    content: str = ""


class DataSetCreate(DataSetBase):
    pass


class DataSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None


class DataSetResponse(DataSetBase):
    id: int
    headers: List[Any] = []
    row_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataSetTestRequest(BaseModel):
    environment_id: Optional[int] = None
    row_indices: Optional[List[int]] = None  # 空列表或不传则执行全部
    variables: Dict[str, Any] = {}


class DataSetImportRequest(BaseModel):
    """导入数据请求 schema"""
    name: Optional[str] = None
    type: Optional[str] = None
    content: str
