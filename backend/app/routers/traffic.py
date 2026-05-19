# -*- coding: utf-8 -*-
"""
Phase 5 - 全链路压测 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.traffic import (
    TrafficRecordService,
    TrafficTagService,
    TrafficReplayService,
    DiffEngineService,
)

router = APIRouter(prefix="/api/traffic", tags=["全链路压测 (Phase 5)"])


# ==================== Traffic Record APIs ====================

def get_record_service(db: Session = Depends(get_db)) -> TrafficRecordService:
    return TrafficRecordService(db)


def get_tag_service(db: Session = Depends(get_db)) -> TrafficTagService:
    return TrafficTagService(db)


def get_replay_service(db: Session = Depends(get_db)) -> TrafficReplayService:
    return TrafficReplayService(db)


def get_diff_service(db: Session = Depends(get_db)) -> DiffEngineService:
    return DiffEngineService(db)


class RecordCreateRequest(BaseModel):
    name: str
    source: str  # nginx/envoy/kubernetes/custom
    project_id: int
    filter_rules: Optional[dict] = None
    environment_id: Optional[int] = None


class RecordResponse(BaseModel):
    record_id: int
    status: str
    start_time: Optional[str] = None


@router.post("/record", response_model=RecordResponse)
async def create_record(
    request: RecordCreateRequest,
    req: Request,
    service: TrafficRecordService = Depends(get_record_service),
):
    """创建录制任务"""
    user_id = getattr(req.state, "user_id", None) or 1

    result = service.create_record(
        name=request.name,
        source=request.source,
        project_id=request.project_id,
        user_id=user_id,
        filter_rules=request.filter_rules,
        environment_id=request.environment_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/record/{record_id}/start")
async def start_recording(
    record_id: int,
    service: TrafficRecordService = Depends(get_record_service),
):
    """开始录制"""
    result = service.start_recording(record_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/record/{record_id}/stop")
async def stop_recording(
    record_id: int,
    service: TrafficRecordService = Depends(get_record_service),
):
    """停止录制"""
    result = service.stop_recording(record_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/record/{record_id}")
async def get_record(
    record_id: int,
    service: TrafficRecordService = Depends(get_record_service),
):
    """获取录制详情"""
    record = service.get_record(record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return record


@router.get("/records/{project_id}")
async def list_records(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    service: TrafficRecordService = Depends(get_record_service),
):
    """获取录制列表"""
    return service.list_records(project_id, page, page_size)


@router.delete("/record/{record_id}")
async def delete_record(
    record_id: int,
    service: TrafficRecordService = Depends(get_record_service),
):
    """删除录制"""
    result = service.delete_record(record_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# ==================== Traffic Tag APIs ====================

class TagCreateRequest(BaseModel):
    tag_name: str
    tag_value: str
    match_rules: Optional[dict] = None
    description: Optional[str] = None


@router.post("/tag")
async def create_tag(
    request: TagCreateRequest,
    service: TrafficTagService = Depends(get_tag_service),
):
    """创建流量标签"""
    return service.create_tag(
        tag_name=request.tag_name,
        tag_value=request.tag_value,
        match_rules=request.match_rules,
        description=request.description,
    )


@router.get("/tags")
async def list_tags(
    service: TrafficTagService = Depends(get_tag_service),
):
    """获取标签列表"""
    return service.list_tags()


@router.delete("/tag/{tag_id}")
async def delete_tag(
    tag_id: int,
    service: TrafficTagService = Depends(get_tag_service),
):
    """删除标签"""
    result = service.delete_tag(tag_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# ==================== Traffic Replay APIs ====================

class ReplayCreateRequest(BaseModel):
    record_id: int
    project_id: int
    config: Optional[dict] = None
    target_environment_id: Optional[int] = None
    enable_shadow: bool = False


@router.post("/replay")
async def create_replay(
    request: ReplayCreateRequest,
    service: TrafficReplayService = Depends(get_replay_service),
):
    """创建回放任务"""
    result = service.create_replay(
        record_id=request.record_id,
        project_id=request.project_id,
        config=request.config,
        target_environment_id=request.target_environment_id,
        enable_shadow=request.enable_shadow,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/replay/{replay_id}/start")
async def start_replay(
    replay_id: int,
    service: TrafficReplayService = Depends(get_replay_service),
):
    """开始回放"""
    result = service.start_replay(replay_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/replay/{replay_id}/stop")
async def stop_replay(
    replay_id: int,
    service: TrafficReplayService = Depends(get_replay_service),
):
    """停止回放"""
    result = service.stop_replay(replay_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/replay/{replay_id}")
async def get_replay(
    replay_id: int,
    service: TrafficReplayService = Depends(get_replay_service),
):
    """获取回放详情"""
    replay = service.get_replay(replay_id)

    if not replay:
        raise HTTPException(status_code=404, detail="Replay not found")

    return replay


@router.get("/replays/{project_id}")
async def list_replays(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    service: TrafficReplayService = Depends(get_replay_service),
):
    """获取回放列表"""
    return service.list_replays(project_id, page, page_size)


@router.get("/replay/{replay_id}/progress")
async def get_replay_progress(
    replay_id: int,
    service: TrafficReplayService = Depends(get_replay_service),
):
    """获取回放进度"""
    return service.get_replay_progress(replay_id)


@router.delete("/replay/{replay_id}")
async def delete_replay(
    replay_id: int,
    service: TrafficReplayService = Depends(get_replay_service),
):
    """删除回放"""
    result = service.delete_replay(replay_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# ==================== Diff Report APIs ====================

@router.get("/replay/{replay_id}/diff")
async def get_diff_report(
    replay_id: int,
    service: DiffEngineService = Depends(get_diff_service),
):
    """获取 Diff 报告"""
    return service.generate_diff_report(replay_id)


@router.post("/compare")
async def compare_responses(
    original: dict,
    replay: dict,
    ignore_fields: Optional[List[str]] = None,
    service: DiffEngineService = Depends(get_diff_service),
):
    """对比两个响应"""
    return service.compare_responses(original, replay, ignore_fields)
