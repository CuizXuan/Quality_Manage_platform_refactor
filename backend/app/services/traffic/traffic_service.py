# -*- coding: utf-8 -*-
"""
Phase 5 - 流量录制服务
"""
import json
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.traffic_models import TrafficRecord, TrafficTag


class TrafficRecordService:
    """流量录制服务"""

    SOURCE_TYPES = ["nginx", "envoy", "kubernetes", "custom"]

    def __init__(self, db: Session):
        self.db = db

    def create_record(
        self,
        name: str,
        source: str,
        project_id: int,
        user_id: int,
        filter_rules: Optional[dict] = None,
        environment_id: Optional[int] = None,
    ) -> dict:
        """
        创建录制任务
        """
        if source not in self.SOURCE_TYPES:
            return {"success": False, "error": f"Invalid source type: {source}"}

        record = TrafficRecord(
            name=name,
            source=source,
            filter_rules=json.dumps(filter_rules, ensure_ascii=False) if filter_rules else None,
            project_id=project_id,
            environment_id=environment_id,
            created_by=user_id,
            status="pending",
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return {
            "success": True,
            "record_id": record.id,
            "status": record.status,
        }

    def start_recording(self, record_id: int) -> dict:
        """
        开始录制
        """
        record = self.db.query(TrafficRecord).filter(TrafficRecord.id == record_id).first()
        if not record:
            return {"success": False, "error": "Record not found"}

        if record.status == "recording":
            return {"success": False, "error": "Recording already in progress"}

        record.status = "recording"
        record.time_range_start = datetime.utcnow()
        self.db.commit()

        return {
            "success": True,
            "record_id": record.id,
            "status": "recording",
            "start_time": record.time_range_start.isoformat() if record.time_range_start else None,
        }

    def stop_recording(self, record_id: int) -> dict:
        """
        停止录制
        """
        record = self.db.query(TrafficRecord).filter(TrafficRecord.id == record_id).first()
        if not record:
            return {"success": False, "error": "Record not found"}

        record.status = "completed"
        record.time_range_end = datetime.utcnow()

        # 模拟统计数据
        record.request_count = 1000
        record.unique_apis = 50

        self.db.commit()
        self.db.refresh(record)

        return {
            "success": True,
            "record_id": record.id,
            "status": "completed",
            "stats": {
                "request_count": record.request_count,
                "unique_apis": record.unique_apis,
                "duration_seconds": (
                    (record.time_range_end - record.time_range_start).total_seconds()
                    if record.time_range_start and record.time_range_end
                    else 0
                ),
            },
        }

    def get_record(self, record_id: int) -> Optional[dict]:
        """获取录制详情"""
        record = self.db.query(TrafficRecord).filter(TrafficRecord.id == record_id).first()
        if not record:
            return None

        return self._record_to_dict(record)

    def list_records(
        self, project_id: int, page: int = 1, page_size: int = 20
    ) -> dict:
        """获取录制列表"""
        query = (
            self.db.query(TrafficRecord)
            .filter(TrafficRecord.project_id == project_id)
            .order_by(TrafficRecord.created_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [self._record_to_dict(r) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def delete_record(self, record_id: int) -> dict:
        """删除录制"""
        record = self.db.query(TrafficRecord).filter(TrafficRecord.id == record_id).first()
        if not record:
            return {"success": False, "error": "Record not found"}

        self.db.delete(record)
        self.db.commit()

        return {"success": True}

    def _record_to_dict(self, record: TrafficRecord) -> dict:
        """转换记录为字典"""
        return {
            "id": record.id,
            "name": record.name,
            "source": record.source,
            "filter_rules": json.loads(record.filter_rules) if record.filter_rules else None,
            "request_count": record.request_count,
            "unique_apis": record.unique_apis,
            "status": record.status,
            "time_range_start": record.time_range_start.isoformat() if record.time_range_start else None,
            "time_range_end": record.time_range_end.isoformat() if record.time_range_end else None,
            "project_id": record.project_id,
            "environment_id": record.environment_id,
            "created_by": record.created_by,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }


class TrafficTagService:
    """流量标签服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_tag(
        self,
        tag_name: str,
        tag_value: str,
        match_rules: Optional[dict] = None,
        description: Optional[str] = None,
    ) -> dict:
        """创建流量标签"""
        tag = TrafficTag(
            tag_name=tag_name,
            tag_value=tag_value,
            match_rules=json.dumps(match_rules, ensure_ascii=False) if match_rules else None,
            description=description,
        )

        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)

        return {"success": True, "id": tag.id}

    def list_tags(self) -> List[dict]:
        """获取标签列表"""
        tags = self.db.query(TrafficTag).all()
        return [
            {
                "id": t.id,
                "tag_name": t.tag_name,
                "tag_value": t.tag_value,
                "match_rules": json.loads(t.match_rules) if t.match_rules else None,
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tags
        ]

    def delete_tag(self, tag_id: int) -> dict:
        """删除标签"""
        tag = self.db.query(TrafficTag).filter(TrafficTag.id == tag_id).first()
        if not tag:
            return {"success": False, "error": "Tag not found"}

        self.db.delete(tag)
        self.db.commit()

        return {"success": True}
