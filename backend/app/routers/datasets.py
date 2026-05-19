import csv
import json
import io
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.database import get_db
from app.models.dataset import DataSet, DataSetRow
from app.models.case import TestCase
from app.models.environment import Environment
from app.models.execution_log import ExecutionLog
from app.schemas.dataset import (
    DataSetCreate, DataSetUpdate, DataSetResponse,
    DataSetRowCreate, DataSetRowResponse, DataSetTestRequest,
    DataSetImportRequest,
)
from app.services.request_executor import RequestExecutor
from app.middleware.tenant_middleware import get_current_tenant_id

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


def get_tenant_id(request: Request) -> int:
    """从请求状态获取当前租户 ID"""
    tenant_id = get_current_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="需要租户权限")
    return tenant_id


def _parse_dataset(ds: DataSet) -> dict:
    return {
        "id": ds.id,
        "name": ds.name,
        "description": ds.description or "",
        "type": ds.type or "csv",
        "file_path": ds.file_path or "",
        "content": ds.content or "",
        "headers": json.loads(ds.headers or "[]"),
        "row_count": ds.row_count,
        "created_at": ds.created_at,
        "updated_at": ds.updated_at,
    }


@router.get("", response_model=List[DataSetResponse])
def list_datasets(
    keyword: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    query = db.query(DataSet).filter(DataSet.tenant_id == tenant_id)
    if keyword:
        query = query.filter(DataSet.name.contains(keyword))
    datasets = query.order_by(desc(DataSet.created_at)).offset(skip).limit(limit).all()
    return [_parse_dataset(ds) for ds in datasets]


@router.post("", response_model=DataSetResponse)
def create_dataset(data: DataSetCreate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    dataset = DataSet(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        type=data.type,
        file_path=data.file_path,
        content=data.content,
        headers="[]",
        row_count=0,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return _parse_dataset(dataset)


@router.get("/{dataset_id}", response_model=DataSetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return _parse_dataset(ds)


@router.put("/{dataset_id}", response_model=DataSetResponse)
def update_dataset(dataset_id: int, data: DataSetUpdate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    for key, value in data.model_dump().items():
        if value is not None:
            setattr(ds, key, value)
    db.commit()
    db.refresh(ds)
    return _parse_dataset(ds)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(ds)
    db.commit()
    return {"code": 0, "message": "deleted"}


# ---------- 数据集行（DataSetRow）----------

@router.get("/{dataset_id}/rows", response_model=List[DataSetRowResponse])
def list_dataset_rows(
    dataset_id: int,
    enabled_only: bool = Query(False),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    # 验证数据集归属
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    query = db.query(DataSetRow).filter(DataSetRow.dataset_id == dataset_id)
    if enabled_only:
        query = query.filter(DataSetRow.enabled == True)
    rows = query.order_by(DataSetRow.row_index).all()
    return [_parse_row(r) for r in rows]


@router.post("/{dataset_id}/rows", response_model=DataSetRowResponse)
def create_dataset_row(
    dataset_id: int,
    data: DataSetRowCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    row = DataSetRow(
        dataset_id=dataset_id,
        row_index=data.row_index,
        variables=json.dumps(data.variables or {}),
        enabled=data.enabled,
    )
    db.add(row)
    db.flush()  # 确保新行被刷入DB，否则count会漏掉

    # 更新行数
    count = db.query(DataSetRow).filter(DataSetRow.dataset_id == dataset_id).count()
    ds.row_count = count
    db.commit()
    db.refresh(row)
    return _parse_row(row)


@router.put("/{dataset_id}/rows/{row_id}", response_model=DataSetRowResponse)
def update_dataset_row(
    dataset_id: int,
    row_id: int,
    data: DataSetRowCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    # 验证数据集归属
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    row = db.query(DataSetRow).filter(
        DataSetRow.id == row_id,
        DataSetRow.dataset_id == dataset_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    row.row_index = data.row_index
    row.variables = json.dumps(data.variables or {})
    row.enabled = data.enabled
    db.commit()
    db.refresh(row)
    return _parse_row(row)


@router.delete("/{dataset_id}/rows/{row_id}")
def delete_dataset_row(
    dataset_id: int,
    row_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    # 验证数据集归属
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    row = db.query(DataSetRow).filter(
        DataSetRow.id == row_id,
        DataSetRow.dataset_id == dataset_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    db.delete(row)
    db.flush()  # 确保删除被刷入DB，否则count会多算

    # 更新行数
    if ds:
        count = db.query(DataSetRow).filter(DataSetRow.dataset_id == dataset_id).count()
        ds.row_count = count
    db.commit()
    return {"code": 0, "message": "deleted"}


# ---------- 导入 CSV/JSON 到数据集 ----------
@router.post("/{dataset_id}/import")
def import_data(
    dataset_id: int,
    data: DataSetImportRequest,  # 使用专用的 ImportRequest schema
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """从 content 字段解析 CSV/JSON 数据并批量写入行"""
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    content = data.content
    data_type = data.type

    headers = []
    rows_to_insert = []

    if data_type == "csv":
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames or []
        for i, row in enumerate(reader):
            rows_to_insert.append({
                "row_index": i,
                "variables": row,
                "enabled": True,
            })
    elif data_type == "json":
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list) and len(parsed) > 0:
                headers = list(parsed[0].keys()) if isinstance(parsed[0], dict) else []
                for i, item in enumerate(parsed):
                    rows_to_insert.append({
                        "row_index": i,
                        "variables": item if isinstance(item, dict) else {"value": item},
                        "enabled": True,
                    })
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON content")
    else:
        raise HTTPException(status_code=400, detail="Unsupported type, use csv or json")

    # 删除旧行
    db.query(DataSetRow).filter(DataSetRow.dataset_id == dataset_id).delete()

    # 批量插入
    for r in rows_to_insert:
        db.add(DataSetRow(
            dataset_id=dataset_id,
            row_index=r["row_index"],
            variables=json.dumps(r["variables"]),
            enabled=r["enabled"],
        ))

    # 更新表头和行数
    ds.headers = json.dumps(headers)
    ds.row_count = len(rows_to_insert)
    db.commit()
    db.refresh(ds)
    return {"code": 0, "message": f"imported {len(rows_to_insert)} rows", "headers": headers}


# ---------- 数据驱动测试 ----------
@router.post("/{dataset_id}/test")
async def test_dataset(
    dataset_id: int,
    body: DataSetTestRequest,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """使用数据集中的行变量驱动测试执行"""
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 获取环境变量
    env_vars = {}
    env_id = body.environment_id
    if env_id:
        env = db.query(Environment).filter(Environment.id == env_id, Environment.tenant_id == tenant_id).first()
        if env:
            env_vars = json.loads(env.variables or "{}")
    else:
        env = db.query(Environment).filter(Environment.is_default == True, Environment.tenant_id == tenant_id).first()
        if env:
            env_id = env.id
            env_vars = json.loads(env.variables or "{}")

    # 获取行
    query = db.query(DataSetRow).filter(
        DataSetRow.dataset_id == dataset_id,
        DataSetRow.enabled == True,
    )
    if body.row_indices is not None and len(body.row_indices) > 0:
        query = query.filter(DataSetRow.row_index.in_(body.row_indices))

    rows = query.order_by(DataSetRow.row_index).all()

    # 这里需要 target 用例信息（前端传入或从数据集关联）
    # Phase 2 中数据集测试需要指定用例 ID，通过 case_id query 参数传入
    return {"code": 0, "message": "data-driven test endpoint", "row_count": len(rows)}


@router.get("/{dataset_id}/rows/{row_id}", response_model=DataSetRowResponse)
def get_dataset_row(
    dataset_id: int,
    row_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    # 验证数据集归属
    ds = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.tenant_id == tenant_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    row = db.query(DataSetRow).filter(
        DataSetRow.id == row_id,
        DataSetRow.dataset_id == dataset_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    return _parse_row(row)


def _parse_row(row: DataSetRow) -> dict:
    return {
        "id": row.id,
        "dataset_id": row.dataset_id,
        "row_index": row.row_index,
        "variables": json.loads(row.variables or "{}"),
        "enabled": row.enabled,
    }
