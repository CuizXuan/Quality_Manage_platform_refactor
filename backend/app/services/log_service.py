"""Operation Log Service — 提供统一的日志记录能力"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.platform import OperationLog


class LogService:
    """操作日志服务，注入到需要记录操作的模块中。"""

    def __init__(self, db: Session, user_id: Optional[int] = None, username: str = ""):
        self.db = db
        self.user_id = user_id
        self.username = username or "system"

    def log(
        self,
        action: str,
        module: str,
        detail: str = "",
        ip: str = "",
    ) -> OperationLog:
        """记录一条操作日志。"""
        entry = OperationLog(
            user_id=self.user_id,
            username=self.username,
            action=action,
            module=module,
            detail=detail,
            ip=ip,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def log_crud(
        self,
        action: str,
        module: str,
        resource_name: str,
        resource_id: Optional[int] = None,
        extra: str = "",
    ):
        """便捷方法：记录 CRUD 操作。"""
        detail = f"{resource_name}"
        if resource_id:
            detail += f" ID={resource_id}"
        if extra:
            detail += f" | {extra}"
        self.log(action=action, module=module, detail=detail)