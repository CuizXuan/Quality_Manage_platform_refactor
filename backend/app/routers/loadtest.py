"""
LoadTest Router - 压力测试 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models.case import TestCase
from app.models.environment import Environment
from app.services.loadtest_engine import LoadTestEngine
from app.routers.cases import _parse_case
import json

router = APIRouter(prefix="/api/loadtest", tags=["LoadTest"])

# LoadTestEngine 单例
_loadtest_engine: Optional[LoadTestEngine] = None


def get_loadtest_engine() -> LoadTestEngine:
    global _loadtest_engine
    if _loadtest_engine is None:
        _loadtest_engine = LoadTestEngine()
    return _loadtest_engine


class LoadTestConfig(BaseModel):
    concurrency: int = 10
    total_requests: int = 100
    duration: int = 0  # 0 = 按请求数，>0 = 按时长（秒）
    ramp_up_time: int = 0


class LoadTestCreateRequest(BaseModel):
    target_type: str = "case"  # case or scenario
    target_id: int
    config: LoadTestConfig = LoadTestConfig()
    environment_id: Optional[int] = None


@router.post("")
async def create_loadtest(
    body: LoadTestCreateRequest,
    db: Session = Depends(get_db),
):
    """创建并启动压力测试"""
    engine = get_loadtest_engine()

    # 获取用例数据
    case_data = None
    if body.target_type == "case":
        case = db.query(TestCase).filter(TestCase.id == body.target_id).first()
        if case:
            case_data = _parse_case(case)

    if not case_data:
        return {"code": 1, "message": "Target case not found"}

    # 获取环境变量
    env_vars = {}
    if body.environment_id:
        env = db.query(Environment).filter(Environment.id == body.environment_id).first()
        if env:
            env_vars = json.loads(env.variables or "{}")
    else:
        env = db.query(Environment).filter(Environment.is_default == True).first()
        if env:
            env_vars = json.loads(env.variables or "{}")

    # 启动压测（异步执行，不等待完成）
    config_dict = body.config.model_dump()
    test_id = f"loadtest_{int(__import__('time').time() * 1000)}"

    # 记录测试信息
    engine._tests[test_id] = {
        "test_id": test_id,
        "status": "pending",
        "config": config_dict,
        "target_type": body.target_type,
        "target_id": body.target_id,
        "response_times": [],
        "status_codes": [],
        "errors": [],
        "request_count": 0,
        "success_count": 0,
        "failure_count": 0,
    }

    # 异步启动
    import asyncio
    asyncio.create_task(
        engine.run_loadtest(case_data, config_dict, env_vars)
    )

    return {
        "code": 0,
        "message": "Load test started",
        "data": {
            "id": test_id,
            "status": "running",
        },
    }


@router.get("/{test_id}")
async def get_loadtest_status(test_id: str):
    """获取压测状态"""
    engine = get_loadtest_engine()
    test_info = engine._tests.get(test_id)
    if not test_info:
        return {"code": 1, "message": "Test not found"}

    return {
        "code": 0,
        "data": {
            "id": test_id,
            "status": test_info.get("status", "unknown"),
            "request_count": test_info.get("request_count", 0),
            "success_count": test_info.get("success_count", 0),
            "failure_count": test_info.get("failure_count", 0),
        },
    }


@router.post("/{test_id}/stop")
async def stop_loadtest(test_id: str):
    """停止压力测试"""
    engine = get_loadtest_engine()
    test_info = engine._tests.get(test_id)
    if not test_info:
        return {"code": 1, "message": "Test not found"}

    stop_event = test_info.get("stop_event")
    if stop_event:
        stop_event.set()

    test_info["status"] = "stopped"
    return {"code": 0, "message": "Test stopped"}


@router.get("/{test_id}/metrics")
async def get_loadtest_metrics(test_id: str):
    """获取压测指标"""
    engine = get_loadtest_engine()
    metrics = engine.get_metrics(test_id)
    if not metrics:
        return {"code": 1, "message": "Test not found"}

    return {
        "code": 0,
        "data": metrics,
    }
