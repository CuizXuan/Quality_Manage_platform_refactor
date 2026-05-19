from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from app.database import get_db
from app.models.environment import Environment
from app.schemas.environment import EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse
from app.middleware.tenant_middleware import get_current_tenant_id

router = APIRouter(prefix="/api/environments", tags=["Environments"])


def get_tenant_id(request: Request) -> int:
    tenant_id = get_current_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="需要租户权限")
    return tenant_id


def _convert_variables(variables: Any) -> Dict[str, str]:
    """将 variables 从数组格式转为字典格式"""
    if not variables:
        return {}
    if isinstance(variables, dict):
        return variables
    if isinstance(variables, list):
        result = {}
        for item in variables:
            if isinstance(item, dict) and "key" in item:
                key = str(item["key"])
                value = str(item.get("value", ""))
                if key:
                    result[key] = value
        return result
    return {}


@router.get("", response_model=List[EnvironmentResponse])
def list_environments(db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    envs = db.query(Environment).filter(Environment.tenant_id == tenant_id).order_by(Environment.sort_order).all()
    return [_parse_env(e) for e in envs]


@router.post("", response_model=EnvironmentResponse)
def create_environment(data: EnvironmentCreate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    # 检查重复名称
    existing = db.query(Environment).filter(
        Environment.tenant_id == tenant_id,
        Environment.name == data.name
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="环境名称已存在")

    if data.is_default:
        db.query(Environment).filter(Environment.tenant_id == tenant_id).update({Environment.is_default: False})

    variables_dict = _convert_variables(data.variables)

    env = Environment(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        variables=json.dumps(variables_dict),
        is_default=data.is_default,
        sort_order=data.sort_order,
    )
    db.add(env)
    db.commit()
    db.refresh(env)
    return _parse_env(env)


@router.get("/{env_id}", response_model=EnvironmentResponse)
def get_environment(env_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    env = db.query(Environment).filter(Environment.id == env_id, Environment.tenant_id == tenant_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return _parse_env(env)


@router.put("/{env_id}", response_model=EnvironmentResponse)
def update_environment(env_id: int, data: EnvironmentUpdate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    env = db.query(Environment).filter(Environment.id == env_id, Environment.tenant_id == tenant_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    # 检查重复名称（排除自己）
    if data.name != env.name:
        duplicate = db.query(Environment).filter(
            Environment.tenant_id == tenant_id,
            Environment.name == data.name,
            Environment.id != env_id
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="环境名称已存在")

    if data.is_default:
        db.query(Environment).filter(Environment.id != env_id, Environment.tenant_id == tenant_id).update({Environment.is_default: False})

    for key, value in data.model_dump().items():
        if key == "variables":
            setattr(env, key, json.dumps(_convert_variables(value)) if value else "{}")
        else:
            setattr(env, key, value)
    db.commit()
    db.refresh(env)
    return _parse_env(env)


@router.delete("/{env_id}")
def delete_environment(env_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    env = db.query(Environment).filter(Environment.id == env_id, Environment.tenant_id == tenant_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    db.delete(env)
    db.commit()
    return {"code": 0, "message": "deleted"}


@router.post("/{env_id}/set-default")
def set_default_environment(env_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    env = db.query(Environment).filter(Environment.id == env_id, Environment.tenant_id == tenant_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    db.query(Environment).filter(Environment.tenant_id == tenant_id).update({Environment.is_default: False})
    env.is_default = True
    db.commit()
    return {"code": 0, "message": "set as default"}


def _parse_env(env: Environment) -> dict:
    return {
        "id": env.id,
        "name": env.name,
        "description": env.description,
        "variables": json.loads(env.variables or "{}"),
        "is_default": env.is_default,
        "sort_order": env.sort_order,
        "created_at": env.created_at,
        "updated_at": env.updated_at,
    }
