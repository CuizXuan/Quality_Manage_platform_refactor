# -*- coding: utf-8 -*-
"""
Phase 5 - 流量回放服务
"""
import json
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.traffic_models import TrafficReplay, TrafficRecord, DiffReport, CompareResult


class TrafficReplayService:
    """流量回放服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_replay(
        self,
        record_id: int,
        project_id: int,
        config: Optional[dict] = None,
        target_environment_id: Optional[int] = None,
        enable_shadow: bool = False,
    ) -> dict:
        """
        创建回放任务
        """
        # 检查录制是否存在
        record = self.db.query(TrafficRecord).filter(TrafficRecord.id == record_id).first()
        if not record:
            return {"success": False, "error": "Record not found"}

        replay = TrafficReplay(
            record_id=record_id,
            replay_config=json.dumps(config, ensure_ascii=False) if config else None,
            target_environment_id=target_environment_id,
            enable_shadow=enable_shadow,
            status="pending",
        )

        self.db.add(replay)
        self.db.commit()
        self.db.refresh(replay)

        return {
            "success": True,
            "replay_id": replay.id,
            "status": replay.status,
        }

    def start_replay(self, replay_id: int) -> dict:
        """
        开始回放
        """
        replay = self.db.query(TrafficReplay).filter(TrafficReplay.id == replay_id).first()
        if not replay:
            return {"success": False, "error": "Replay not found"}

        if replay.status == "running":
            return {"success": False, "error": "Replay already running"}

        replay.status = "running"
        replay.started_at = datetime.utcnow()
        self.db.commit()

        # 模拟回放进度更新
        self._simulate_replay_progress(replay)

        return {
            "success": True,
            "replay_id": replay.id,
            "status": "running",
            "started_at": replay.started_at.isoformat() if replay.started_at else None,
        }

    def _simulate_replay_progress(self, replay: TrafficReplay):
        """模拟回放进度（实际项目中由后台任务更新）"""
        # 模拟统计数据
        replay.total_requests = 1000
        replay.success_count = 980
        replay.diff_count = 20
        replay.status = "completed"
        replay.completed_at = datetime.utcnow()
        self.db.commit()

    def stop_replay(self, replay_id: int) -> dict:
        """
        停止回放
        """
        replay = self.db.query(TrafficReplay).filter(TrafficReplay.id == replay_id).first()
        if not replay:
            return {"success": False, "error": "Replay not found"}

        replay.status = "stopped"
        replay.completed_at = datetime.utcnow()
        self.db.commit()

        return {"success": True, "status": "stopped"}

    def get_replay(self, replay_id: int) -> Optional[dict]:
        """获取回放详情"""
        replay = self.db.query(TrafficReplay).filter(TrafficReplay.id == replay_id).first()
        if not replay:
            return None

        return self._replay_to_dict(replay)

    def list_replays(
        self, project_id: int, page: int = 1, page_size: int = 20
    ) -> dict:
        """获取回放列表"""
        query = (
            self.db.query(TrafficReplay)
            .join(TrafficRecord)
            .filter(TrafficRecord.project_id == project_id)
            .order_by(TrafficReplay.created_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [self._replay_to_dict(r) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def get_replay_progress(self, replay_id: int) -> dict:
        """获取回放进度"""
        replay = self.db.query(TrafficReplay).filter(TrafficReplay.id == replay_id).first()
        if not replay:
            return {"error": "Replay not found"}

        progress = {
            "replay_id": replay.id,
            "status": replay.status,
            "total_requests": replay.total_requests,
            "success_count": replay.success_count,
            "diff_count": replay.diff_count,
            "success_rate": (
                replay.success_count / replay.total_requests
                if replay.total_requests > 0
                else 0
            ),
        }

        if replay.started_at:
            progress["started_at"] = replay.started_at.isoformat()
        if replay.completed_at:
            progress["completed_at"] = replay.completed_at.isoformat()

        return progress

    def delete_replay(self, replay_id: int) -> dict:
        """删除回放"""
        replay = self.db.query(TrafficReplay).filter(TrafficReplay.id == replay_id).first()
        if not replay:
            return {"success": False, "error": "Replay not found"}

        self.db.delete(replay)
        self.db.commit()

        return {"success": True}

    def _replay_to_dict(self, replay: TrafficReplay) -> dict:
        """转换回放为字典"""
        return {
            "id": replay.id,
            "record_id": replay.record_id,
            "replay_config": json.loads(replay.replay_config) if replay.replay_config else None,
            "status": replay.status,
            "total_requests": replay.total_requests,
            "success_count": replay.success_count,
            "diff_count": replay.diff_count,
            "success_rate": (
                replay.success_count / replay.total_requests
                if replay.total_requests > 0
                else 0
            ),
            "target_environment_id": replay.target_environment_id,
            "enable_shadow": replay.enable_shadow,
            "started_at": replay.started_at.isoformat() if replay.started_at else None,
            "completed_at": replay.completed_at.isoformat() if replay.completed_at else None,
            "created_at": replay.created_at.isoformat() if replay.created_at else None,
        }


class DiffEngineService:
    """Diff 对比引擎"""

    # 无意义的差异字段（时间戳等）
    IGNORED_FIELDS = ["timestamp", "created_at", "updated_at", "request_id", "trace_id"]

    def __init__(self, db: Session):
        self.db = db

    def generate_diff_report(self, replay_id: int) -> dict:
        """
        生成 Diff 报告
        """
        replay = self.db.query(TrafficReplay).filter(TrafficReplay.id == replay_id).first()
        if not replay:
            return {"error": "Replay not found"}

        # 获取已有的对比结果
        results = (
            self.db.query(CompareResult)
            .filter(CompareResult.replay_id == replay_id)
            .all()
        )

        if not results:
            # 模拟生成一些 Diff 报告
            diffs = self._generate_mock_diffs(replay)
            return {
                "replay_id": replay_id,
                "summary": {
                    "total": replay.total_requests,
                    "matched": replay.success_count,
                    "diff_count": replay.diff_count,
                    "match_rate": (
                        replay.success_count / replay.total_requests
                        if replay.total_requests > 0
                        else 0
                    ),
                },
                "diffs": diffs,
            }

        # 从数据库中的对比结果生成报告
        diff_items = []
        for r in results:
            if not r.is_match:
                diff_items.append(
                    {
                        "request_signature": r.request_signature,
                        "is_match": r.is_match,
                        "diff_fields": json.loads(r.diff_fields) if r.diff_fields else [],
                        "latency_diff_ms": r.latency_diff_ms,
                    }
                )

        return {
            "replay_id": replay_id,
            "summary": {
                "total": replay.total_requests,
                "matched": replay.success_count,
                "diff_count": replay.diff_count,
                "match_rate": (
                    replay.success_count / replay.total_requests
                    if replay.total_requests > 0
                    else 0
                ),
            },
            "diffs": diff_items,
        }

    def _generate_mock_diffs(self, replay: TrafficReplay) -> List[dict]:
        """生成模拟的 Diff 数据"""
        diffs = []
        diff_count = min(replay.diff_count, 20)  # 最多显示 20 条

        for i in range(diff_count):
            diffs.append(
                {
                    "request": f"POST /api/users/{i + 1}",
                    "original_status": 200,
                    "replay_status": 200,
                    "diff_fields": ["$.data.updated_at"],
                    "original_value": "2026-01-11T10:00:00Z",
                    "replay_value": "2026-01-11T11:00:00Z",
                    "latency_diff_ms": 50 + i * 10,
                }
            )

        return diffs

    def compare_responses(
        self, original: dict, replay: dict, ignore_fields: Optional[List[str]] = None
    ) -> dict:
        """
        对比两个响应
        """
        if ignore_fields is None:
            ignore_fields = self.IGNORED_FIELDS

        diff_fields = []
        all_keys = set(original.keys()) | set(replay.keys())

        for key in all_keys:
            if key in ignore_fields:
                continue

            if key not in original:
                diff_fields.append({"field": key, "type": "missing_in_original", "value": replay[key]})
            elif key not in replay:
                diff_fields.append({"field": key, "type": "missing_in_replay", "value": original[key]})
            elif original[key] != replay[key]:
                diff_fields.append(
                    {
                        "field": key,
                        "type": "value_changed",
                        "original": original[key],
                        "replay": replay[key],
                    }
                )

        return {
            "is_match": len(diff_fields) == 0,
            "diff_fields": diff_fields,
        }

    def filter_insignificant_diffs(self, diffs: List[dict]) -> List[dict]:
        """
        过滤无意义差异
        """
        significant_diffs = []

        for diff in diffs:
            # 过滤时间类差异
            if diff.get("type") == "value_changed":
                field = diff.get("field", "")
                if any(ignored in field.lower() for ignored in ["time", "date", "timestamp"]):
                    continue

            significant_diffs.append(diff)

        return significant_diffs
