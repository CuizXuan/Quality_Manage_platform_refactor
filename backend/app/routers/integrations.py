from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
from app.database import get_db
from app.models import IntegrationConfig

router = APIRouter(prefix="/api/integrations", tags=["第三方集成"])

SUPPORTED_TYPES = ["jira", "tapd", "zentao", "github", "gitlab"]


class IntegrationCreate(BaseModel):
    name: str
    type: str
    config: dict = {}
    enabled: Optional[bool] = True


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None


@router.get("/defect-systems")
def list_defect_systems(db: Session = Depends(get_db)):
    configs = db.query(IntegrationConfig).filter(
        IntegrationConfig.type.in_(["jira", "tapd", "zentao"])
    ).order_by(IntegrationConfig.id.desc()).all()
    return {"code": 0, "data": configs}


@router.post("/defect-systems")
def create_defect_system(data: IntegrationCreate, db: Session = Depends(get_db)):
    if data.type not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的类型: {data.type}")
    cfg = IntegrationConfig(
        name=data.name,
        type=data.type,
        config=json.dumps(data.config),
        enabled=data.enabled,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return {"code": 0, "data": cfg}


@router.put("/defect-systems/{cfg_id}")
def update_defect_system(cfg_id: int, data: IntegrationUpdate, db: Session = Depends(get_db)):
    cfg = db.query(IntegrationConfig).filter(IntegrationConfig.id == cfg_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if k == "config":
            v = json.dumps(v)
        setattr(cfg, k, v)
    db.commit()
    db.refresh(cfg)
    return {"code": 0, "data": cfg}


@router.delete("/defect-systems/{cfg_id}")
def delete_defect_system(cfg_id: int, db: Session = Depends(get_db)):
    cfg = db.query(IntegrationConfig).filter(IntegrationConfig.id == cfg_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(cfg)
    db.commit()
    return {"code": 0, "message": "删除成功"}


@router.post("/defect-systems/{cfg_id}/test")
def test_connection(cfg_id: int, db: Session = Depends(get_db)):
    """测试第三方缺陷系统连接"""
    cfg = db.query(IntegrationConfig).filter(IntegrationConfig.id == cfg_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    cfg_data = json.loads(cfg.config or "{}")
    result = {"connected": False, "message": ""}

    try:
        if cfg.type == "jira":
            import requests
            url = cfg_data.get("url", "").rstrip("/")
            username = cfg_data.get("username", "")
            api_key = cfg_data.get("api_key", "")
            if url and username and api_key:
                resp = requests.get(
                    f"{url}/rest/api/2/myself",
                    auth=(username, api_key),
                    timeout=10,
                )
                if resp.status_code == 200:
                    result = {"connected": True, "message": "Jira 连接成功"}
                else:
                    result = {"connected": False, "message": f"HTTP {resp.status_code}"}
            else:
                result = {"connected": False, "message": "配置不完整"}

        elif cfg.type == "tapd":
            import requests
            url = cfg_data.get("url", "")
            token = cfg_data.get("api_token", "")
            if url and token:
                resp = requests.get(
                    f"{url}/tapi/rest/tapd/user?token={token}",
                    timeout=10,
                )
                if resp.status_code == 200:
                    result = {"connected": True, "message": "TAPD 连接成功"}
                else:
                    result = {"connected": False, "message": f"HTTP {resp.status_code}"}
            else:
                result = {"connected": False, "message": "配置不完整"}

        elif cfg.type == "zentao":
            import requests
            url = cfg_data.get("url", "")
            account = cfg_data.get("account", "")
            password = cfg_data.get("password", "")
            if url and account and password:
                resp = requests.post(
                    f"{url}/api-getSession",
                    json={"account": account, "password": password},
                    timeout=10,
                )
                if resp.status_code == 200:
                    result = {"connected": True, "message": "禅道连接成功"}
                else:
                    result = {"connected": False, "message": f"HTTP {resp.status_code}"}
            else:
                result = {"connected": False, "message": "配置不完整"}

    except Exception as e:
        result = {"connected": False, "message": str(e)}

    return {"code": 0, "data": result}


@router.get("/types")
def get_supported_types():
    return {"code": 0, "data": {
        "defect_systems": [
            {"type": "jira", "name": "Jira", "fields": ["url", "username", "api_key", "project_key"]},
            {"type": "tapd", "name": "TAPD", "fields": ["url", "api_token", "workspace_id"]},
            {"type": "zentao", "name": "禅道", "fields": ["url", "account", "password"]},
        ]
    }}
