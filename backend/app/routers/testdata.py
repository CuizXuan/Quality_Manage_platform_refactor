# -*- coding: utf-8 -*-
"""
Phase 5 - 测试数据工厂 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.datafactory import DataMaskService, DataGenService, DataCloneService, DataSnapshotService

router = APIRouter(prefix="/api/test-data", tags=["测试数据工厂 (Phase 5)"])


# ==================== Dependencies ====================

def get_mask_service(db: Session = Depends(get_db)) -> DataMaskService:
    return DataMaskService(db)


def get_gen_service(db: Session = Depends(get_db)) -> DataGenService:
    return DataGenService(db)


def get_clone_service(db: Session = Depends(get_db)) -> DataCloneService:
    return DataCloneService(db)


def get_snapshot_service(db: Session = Depends(get_db)) -> DataSnapshotService:
    return DataSnapshotService(db)


# ==================== Mask Rules APIs ====================

class MaskRuleCreateRequest(BaseModel):
    name: str
    field_pattern: str
    mask_type: str
    project_id: int
    mask_config: Optional[dict] = None
    priority: int = 0


class MaskRuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    field_pattern: Optional[str] = None
    mask_type: Optional[str] = None
    mask_config: Optional[dict] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


@router.get("/mask-rules")
async def list_mask_rules(
    project_id: int,
    service: DataMaskService = Depends(get_mask_service),
):
    """获取脱敏规则列表"""
    return service.list_rules(project_id)


@router.post("/mask-rules")
async def create_mask_rule(
    request: MaskRuleCreateRequest,
    service: DataMaskService = Depends(get_mask_service),
):
    """创建脱敏规则"""
    result = service.create_rule(
        name=request.name,
        field_pattern=request.field_pattern,
        mask_type=request.mask_type,
        project_id=request.project_id,
        mask_config=request.mask_config,
        priority=request.priority,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.put("/mask-rules/{rule_id}")
async def update_mask_rule(
    rule_id: int,
    request: MaskRuleUpdateRequest,
    service: DataMaskService = Depends(get_mask_service),
):
    """更新脱敏规则"""
    result = service.update_rule(
        rule_id=rule_id,
        name=request.name,
        field_pattern=request.field_pattern,
        mask_type=request.mask_type,
        mask_config=request.mask_config,
        priority=request.priority,
        enabled=request.enabled,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/mask-rules/{rule_id}")
async def delete_mask_rule(
    rule_id: int,
    service: DataMaskService = Depends(get_mask_service),
):
    """删除脱敏规则"""
    result = service.delete_rule(rule_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/mask-rules/preview")
async def preview_mask(
    data: dict,
    rule_id: int,
    service: DataMaskService = Depends(get_mask_service),
):
    """预览脱敏结果"""
    return service.preview_mask(data, rule_id)


@router.post("/mask/apply")
async def apply_mask(
    data: dict,
    rules: List[dict],
    service: DataMaskService = Depends(get_mask_service),
):
    """应用脱敏规则"""
    return {"success": True, "masked_data": service.apply_mask(data, rules)}


# ==================== Data Generation APIs ====================

class TemplateCreateRequest(BaseModel):
    name: str
    template_type: str
    project_id: int
    data_schema: dict
    generation_rules: Optional[dict] = None


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    data_schema: Optional[dict] = None
    generation_rules: Optional[dict] = None


class GenerateRequest(BaseModel):
    template_id: int
    count: int = 1
    unique_fields: Optional[List[str]] = None


@router.get("/templates")
async def list_templates(
    project_id: int,
    service: DataGenService = Depends(get_gen_service),
):
    """获取数据生成模板列表"""
    return service.list_templates(project_id)


@router.post("/templates")
async def create_template(
    request: TemplateCreateRequest,
    service: DataGenService = Depends(get_gen_service),
):
    """创建数据生成模板"""
    result = service.create_template(
        name=request.name,
        template_type=request.template_type,
        schema=request.data_schema,
        project_id=request.project_id,
        generation_rules=request.generation_rules,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    request: TemplateUpdateRequest,
    service: DataGenService = Depends(get_gen_service),
):
    """更新数据生成模板"""
    result = service.update_template(
        template_id=template_id,
        name=request.name,
        schema=request.data_schema,
        generation_rules=request.generation_rules,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    service: DataGenService = Depends(get_gen_service),
):
    """删除数据生成模板"""
    result = service.delete_template(template_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/templates/{template_id}/preview")
async def preview_template(
    template_id: int,
    service: DataGenService = Depends(get_gen_service),
):
    """预览模板生成结果"""
    return service.preview_template(template_id)


@router.post("/generate")
async def generate_data(
    request: GenerateRequest,
    service: DataGenService = Depends(get_gen_service),
):
    """生成测试数据"""
    return service.generate(
        template_id=request.template_id,
        count=request.count,
        unique_fields=request.unique_fields,
    )


@router.get("/field-types")
async def get_field_types(
    service: DataGenService = Depends(get_gen_service),
):
    """获取支持的字段类型"""
    return service.FIELD_GENERATORS.keys()


# ==================== Data Clone APIs ====================

class CloneTaskCreateRequest(BaseModel):
    name: str
    source_env_id: int
    target_env_id: int
    project_id: int
    tables: Optional[List[str]] = None
    clone_type: str = "full"
    mask_rule_ids: Optional[List[int]] = None


@router.get("/clone-tasks")
async def list_clone_tasks(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    service: DataCloneService = Depends(get_clone_service),
):
    """获取克隆任务列表"""
    return service.list_tasks(project_id, page, page_size)


@router.post("/clone-tasks")
async def create_clone_task(
    request: CloneTaskCreateRequest,
    req: Request,
    service: DataCloneService = Depends(get_clone_service),
):
    """创建克隆任务"""
    user_id = getattr(req.state, "user_id", None) or 1

    result = service.create_task(
        name=request.name,
        source_env_id=request.source_env_id,
        target_env_id=request.target_env_id,
        project_id=request.project_id,
        user_id=user_id,
        tables=request.tables,
        clone_type=request.clone_type,
        mask_rule_ids=request.mask_rule_ids,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/clone-tasks/{task_id}/start")
async def start_clone_task(
    task_id: int,
    service: DataCloneService = Depends(get_clone_service),
):
    """启动克隆任务"""
    result = service.start_task(task_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/clone-tasks/{task_id}/stop")
async def stop_clone_task(
    task_id: int,
    service: DataCloneService = Depends(get_clone_service),
):
    """停止克隆任务"""
    result = service.stop_task(task_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/clone-tasks/{task_id}")
async def delete_clone_task(
    task_id: int,
    service: DataCloneService = Depends(get_clone_service),
):
    """删除克隆任务"""
    result = service.delete_task(task_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ==================== Data Snapshot APIs ====================

class SnapshotCreateRequest(BaseModel):
    name: str
    source_type: str
    project_id: int
    source_id: Optional[str] = None
    data_content: Optional[dict] = None
    expires_in_days: Optional[int] = None


@router.get("/snapshots")
async def list_snapshots(
    project_id: int,
    service: DataSnapshotService = Depends(get_snapshot_service),
):
    """获取快照列表"""
    return service.list_snapshots(project_id)


@router.post("/snapshots")
async def create_snapshot(
    request: SnapshotCreateRequest,
    service: DataSnapshotService = Depends(get_snapshot_service),
):
    """创建数据快照"""
    result = service.create_snapshot(
        name=request.name,
        source_type=request.source_type,
        project_id=request.project_id,
        source_id=request.source_id,
        data_content=request.data_content,
        expires_in_days=request.expires_in_days,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/snapshots/{snapshot_id}/restore")
async def restore_snapshot(
    snapshot_id: int,
    service: DataSnapshotService = Depends(get_snapshot_service),
):
    """恢复快照"""
    result = service.restore_snapshot(snapshot_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    service: DataSnapshotService = Depends(get_snapshot_service),
):
    """删除快照"""
    result = service.delete_snapshot(snapshot_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
