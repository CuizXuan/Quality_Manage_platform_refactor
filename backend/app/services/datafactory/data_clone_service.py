# -*- coding: utf-8 -*-
"""
Phase 5 - 数据克隆与快照服务
"""
import json
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.data_factory_models import DataSnapshot, DataCloneTask


class DataCloneService:
    """数据克隆服务"""

    CLONE_TYPES = {
        "full": "全量克隆",
        "partial": "部分克隆",
        "mask": "脱敏克隆",
    }

    def __init__(self, db: Session):
        self.db = db

    def create_task(
        self,
        name: str,
        source_env_id: int,
        target_env_id: int,
        project_id: int,
        user_id: int,
        tables: Optional[List[str]] = None,
        clone_type: str = "full",
        mask_rule_ids: Optional[List[int]] = None,
    ) -> dict:
        """创建克隆任务"""
        task = DataCloneTask(
            name=name,
            source_env_id=source_env_id,
            target_env_id=target_env_id,
            tables=json.dumps(tables, ensure_ascii=False) if tables else None,
            clone_type=clone_type,
            mask_rules=json.dumps(mask_rule_ids, ensure_ascii=False) if mask_rule_ids else None,
            status="pending",
            progress=0,
            created_by=user_id,
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return {"success": True, "task_id": task.id}

    def start_task(self, task_id: int) -> dict:
        """启动克隆任务"""
        task = self.db.query(DataCloneTask).filter(DataCloneTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}

        if task.status == "running":
            return {"success": False, "error": "Task already running"}

        task.status = "running"
        task.started_at = datetime.utcnow()
        self.db.commit()

        # 模拟克隆执行
        self._simulate_clone(task)

        return {
            "success": True,
            "task_id": task.id,
            "status": task.status,
        }

    def _simulate_clone(self, task: DataCloneTask):
        """模拟克隆执行（实际项目中连接数据库执行）"""
        import time
        time.sleep(0.5)  # 模拟延迟

        task.status = "completed"
        task.progress = 100
        task.completed_at = datetime.utcnow()
        self.db.commit()

    def stop_task(self, task_id: int) -> dict:
        """停止克隆任务"""
        task = self.db.query(DataCloneTask).filter(DataCloneTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}

        task.status = "failed"
        task.error_message = "Task stopped by user"
        task.completed_at = datetime.utcnow()
        self.db.commit()

        return {"success": True, "status": task.status}

    def get_task(self, task_id: int) -> Optional[dict]:
        """获取任务详情"""
        task = self.db.query(DataCloneTask).filter(DataCloneTask.id == task_id).first()
        if not task:
            return None
        return self._task_to_dict(task)

    def list_tasks(
        self, project_id: int, page: int = 1, page_size: int = 20
    ) -> dict:
        """获取任务列表"""
        # 注意：这里简化处理，实际应该通过环境关联查询
        query = (
            self.db.query(DataCloneTask)
            .order_by(DataCloneTask.created_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [self._task_to_dict(t) for t in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def delete_task(self, task_id: int) -> dict:
        """删除任务"""
        task = self.db.query(DataCloneTask).filter(DataCloneTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}

        self.db.delete(task)
        self.db.commit()
        return {"success": True}

    def _task_to_dict(self, task: DataCloneTask) -> dict:
        """转换任务为字典"""
        return {
            "id": task.id,
            "name": task.name or f"Clone Task #{task.id}",
            "source_env_id": task.source_env_id,
            "target_env_id": task.target_env_id,
            "tables": json.loads(task.tables) if task.tables else [],
            "clone_type": task.clone_type,
            "clone_type_name": self.CLONE_TYPES.get(task.clone_type, task.clone_type),
            "mask_rules": json.loads(task.mask_rules) if task.mask_rules else [],
            "status": task.status,
            "progress": task.progress,
            "error_message": task.error_message,
            "created_by": task.created_by,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }


class DataSnapshotService:
    """数据快照服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_snapshot(
        self,
        name: str,
        source_type: str,
        project_id: int,
        source_id: Optional[str] = None,
        data_content: Optional[dict] = None,
        expires_in_days: Optional[int] = None,
    ) -> dict:
        """创建快照"""
        snapshot = DataSnapshot(
            name=name,
            source_type=source_type,
            source_id=source_id,
            data_content=json.dumps(data_content, ensure_ascii=False) if data_content else None,
            size_bytes=len(json.dumps(data_content, ensure_ascii=False)) if data_content else 0,
            record_count=len(data_content) if isinstance(data_content, list) else 1,
            project_id=project_id,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None,
        )

        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        return {"success": True, "snapshot_id": snapshot.id}

    def get_snapshot(self, snapshot_id: int) -> Optional[dict]:
        """获取快照详情"""
        snapshot = self.db.query(DataSnapshot).filter(DataSnapshot.id == snapshot_id).first()
        if not snapshot:
            return None
        return self._snapshot_to_dict(snapshot)

    def list_snapshots(self, project_id: int) -> List[dict]:
        """获取快照列表"""
        snapshots = (
            self.db.query(DataSnapshot)
            .filter(DataSnapshot.project_id == project_id)
            .order_by(DataSnapshot.created_at.desc())
            .all()
        )

        return [self._snapshot_to_dict(s) for s in snapshots]

    def restore_snapshot(self, snapshot_id: int) -> dict:
        """恢复快照"""
        snapshot = self.db.query(DataSnapshot).filter(DataSnapshot.id == snapshot_id).first()
        if not snapshot:
            return {"success": False, "error": "Snapshot not found"}

        if snapshot.expires_at and snapshot.expires_at < datetime.utcnow():
            return {"success": False, "error": "Snapshot has expired"}

        # 返回快照数据（实际项目中会写入目标数据库）
        return {
            "success": True,
            "snapshot_id": snapshot.id,
            "data_content": json.loads(snapshot.data_content) if snapshot.data_content else None,
            "record_count": snapshot.record_count,
        }

    def delete_snapshot(self, snapshot_id: int) -> dict:
        """删除快照"""
        snapshot = self.db.query(DataSnapshot).filter(DataSnapshot.id == snapshot_id).first()
        if not snapshot:
            return {"success": False, "error": "Snapshot not found"}

        self.db.delete(snapshot)
        self.db.commit()
        return {"success": True}

    def _snapshot_to_dict(self, snapshot: DataSnapshot) -> dict:
        """转换快照为字典"""
        return {
            "id": snapshot.id,
            "name": snapshot.name,
            "source_type": snapshot.source_type,
            "source_id": snapshot.source_id,
            "size_bytes": snapshot.size_bytes,
            "record_count": snapshot.record_count,
            "project_id": snapshot.project_id,
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
            "expires_at": snapshot.expires_at.isoformat() if snapshot.expires_at else None,
            "is_expired": snapshot.expires_at < datetime.utcnow() if snapshot.expires_at else False,
        }
