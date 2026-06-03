from typing import Dict, Optional

from pydantic import BaseModel


class AssetTraceResponse(BaseModel):
    id: int
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    relation_type: str
    project_id: Optional[int] = None
    version_tag: str = ""
    metadata: Dict = {}
