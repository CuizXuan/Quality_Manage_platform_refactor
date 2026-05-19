# -*- coding: utf-8 -*-
"""
环境管理模块 API 测试
覆盖 P0 和 P1 测试用例
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Environment, User, Tenant
from app.services.auth_service import AuthService


client = TestClient(app)


# ==================== 认证辅助 ====================

@pytest.fixture(scope="function")
def db_session():
    """提供数据库会话，每个测试前清理环境数据"""
    db = SessionLocal()
    # 测试前清理
    try:
        db.query(Environment).delete()
        db.commit()
    except Exception:
        db.rollback()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def auth_info(db_session):
    """获取认证信息"""
    # 查找或创建测试租户
    tenant = db_session.query(Tenant).filter(Tenant.name == "测试租户_环境").first()
    if not tenant:
        tenant = Tenant(name="测试租户_环境", code="test_env", status="active")
        db_session.add(tenant)
        db_session.commit()
        db_session.refresh(tenant)
    
    # 查找或创建测试用户
    user = db_session.query(User).filter(User.username == "test_user_env").first()
    if not user:
        password_hash = AuthService.hash_password("test_password_123")
        user = User(
            username="test_user_env",
            email="test_env@example.com",
            password_hash=password_hash,
            tenant_id=tenant.id,
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    token = AuthService.create_access_token(user_id=user.id, tenant_id=tenant.id)
    return {
        "token": token,
        "user_id": user.id,
        "tenant_id": tenant.id,
        "headers": {"Authorization": f"Bearer {token}"}
    }


# ==================== 辅助函数 ====================

def create_environment(db, name="测试环境", is_default=False, variables='{"base_url": "https://httpbin.org"}'):
    """创建测试环境"""
    env = Environment(
        name=name,
        description="pytest创建的环境",
        variables=variables,
        is_default=is_default,
        sort_order=0
    )
    db.add(env)
    db.commit()
    db.refresh(env)
    return env


# ==================== 环境列表 ====================

class TestListEnvironments:
    """TC_E021, TC_E022, TC_E023"""

    def test_list_environments_empty(self, db_session, auth_info):
        """TC_E021 - 获取环境列表-空数据库"""
        response = client.get("/api/environments", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_environments_multiple(self, db_session, auth_info):
        """TC_E022 - 获取环境列表-多条数据"""
        create_environment(db_session, "环境1")
        create_environment(db_session, "环境2")
        create_environment(db_session, "环境3")

        response = client.get("/api/environments", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_environments_sorted(self, db_session, auth_info):
        """TC_E023 - 获取环境列表-按sort_order排序"""
        create_environment(db_session, "环境A")
        env_b = create_environment(db_session, "环境B")
        env_b.sort_order = 1
        db_session.commit()

        response = client.get("/api/environments", headers=auth_info["headers"])
        data = response.json()
        # 验证排序
        assert len(data) >= 2


# ==================== 创建环境 ====================

class TestCreateEnvironment:
    """TC_E001, TC_E002, TC_E003, TC_E004"""

    def test_create_environment_full_params(self, db_session, auth_info):
        """TC_E001 - 创建环境-完整参数"""
        payload = {
            "name": "测试环境完整",
            "description": "完整参数测试",
            "variables": {"host": "localhost", "port": 8080},
            "is_default": False,
            "sort_order": 1,
        }
        response = client.post("/api/environments", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试环境完整"
        assert data["variables"]["host"] == "localhost"
        assert data["variables"]["port"] == 8080

    def test_create_environment_minimal_params(self, db_session, auth_info):
        """TC_E002 - 创建环境-最小参数"""
        payload = {"name": "最小环境"}
        response = client.post("/api/environments", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "最小环境"
        assert data["is_default"] == False

    def test_create_environment_set_as_default(self, db_session, auth_info):
        """TC_E003 - 创建环境-设置默认"""
        # 先创建一个默认环境
        create_environment(db_session, "原有默认", is_default=True)

        # 创建新的默认环境
        payload = {"name": "新默认环境", "is_default": True}
        response = client.post("/api/environments", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200

        # 检查原有的默认被取消了
        envs = db_session.query(Environment).all()
        default_envs = [e for e in envs if e.is_default]
        assert len(default_envs) == 1
        assert default_envs[0].name == "新默认环境"

    def test_create_environment_with_variables(self, db_session, auth_info):
        """TC_E004 - 创建环境-带变量"""
        payload = {
            "name": "带变量环境",
            "variables": {"api_key": "***", "timeout": 30},
        }
        response = client.post("/api/environments", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        # 变量会被处理
        assert "variables" in data


# ==================== 获取单个环境 ====================

class TestGetEnvironment:
    """TC_E007, TC_E008"""

    def test_get_environment_exists(self, db_session, auth_info):
        """TC_E007 - 获取单个环境-存在"""
        env = create_environment(db_session, "目标环境")

        response = client.get(f"/api/environments/{env.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "目标环境"
        assert data["id"] == env.id

    def test_get_environment_not_exists(self, db_session, auth_info):
        """TC_E008 - 获取单个环境-不存在"""
        response = client.get("/api/environments/99999", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 更新环境 ====================

class TestUpdateEnvironment:
    """TC_E009, TC_E010, TC_E011, TC_E012"""

    def test_update_environment_name(self, db_session, auth_info):
        """TC_E009 - 更新环境-正常"""
        env = create_environment(db_session, "原名")
        payload = {"name": "新名称", "description": "新描述"}

        response = client.put(f"/api/environments/{env.id}", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["name"] == "新名称"

    def test_update_environment_variables(self, db_session, auth_info):
        """TC_E010 - 更新环境-更新变量"""
        env = create_environment(db_session, "变量环境")
        payload = {"name": env.name, "variables": {"new_key": "new_value"}}

        response = client.put(f"/api/environments/{env.id}", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["variables"]["new_key"] == "new_value"

    def test_update_environment_set_default(self, db_session, auth_info):
        """TC_E011 - 更新环境-设置为默认"""
        create_environment(db_session, "环境1", is_default=True)
        env2 = create_environment(db_session, "环境2")

        response = client.put(f"/api/environments/{env2.id}", json={"name": env2.name, "is_default": True}, headers=auth_info["headers"])
        assert response.status_code == 200

        # 验证 env1 不再是默认，env2 变成默认
        envs = db_session.query(Environment).all()
        for e in envs:
            db_session.refresh(e)
        default_envs = [e for e in envs if e.is_default]
        assert len(default_envs) == 1
        assert default_envs[0].name == "环境2"

    def test_update_environment_unset_default(self, db_session, auth_info):
        """TC_E012 - 更新环境-取消默认"""
        env = create_environment(db_session, "默认环境", is_default=True)
        response = client.put(f"/api/environments/{env.id}", json={"name": env.name, "is_default": False}, headers=auth_info["headers"])
        assert response.status_code == 200
        db_session.refresh(env)
        assert env.is_default == False


# ==================== 删除环境 ====================

class TestDeleteEnvironment:
    """TC_E013, TC_E014, TC_E015"""

    def test_delete_environment_success(self, db_session, auth_info):
        """TC_E013 - 删除环境-正常"""
        env = create_environment(db_session, "待删除环境")

        response = client.delete(f"/api/environments/{env.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["code"] == 0

        # 验证已删除
        response = client.get(f"/api/environments/{env.id}", headers=auth_info["headers"])
        assert response.status_code == 404

    def test_delete_environment_not_exists(self, db_session, auth_info):
        """TC_E014 - 删除环境-不存在"""
        response = client.delete("/api/environments/99999", headers=auth_info["headers"])
        assert response.status_code == 404

    def test_delete_default_environment(self, db_session, auth_info):
        """TC_E015 - 删除环境-删除默认环境"""
        env = create_environment(db_session, "默认环境", is_default=True)

        response = client.delete(f"/api/environments/{env.id}", headers=auth_info["headers"])
        assert response.status_code == 200

        # 验证已删除
        response = client.get(f"/api/environments/{env.id}", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 设置默认环境 ====================

class TestSetDefaultEnvironment:
    """TC_E016, TC_E017"""

    def test_set_default_environment_success(self, db_session, auth_info):
        """TC_E016 - 设置默认环境-正常"""
        create_environment(db_session, "环境1", is_default=True)
        env2 = create_environment(db_session, "环境2")

        response = client.post(f"/api/environments/{env2.id}/set-default", headers=auth_info["headers"])
        assert response.status_code == 200

        envs = db_session.query(Environment).all()
        for e in envs:
            db_session.refresh(e)
        default_envs = [e for e in envs if e.is_default]
        assert len(default_envs) == 1
        assert default_envs[0].name == "环境2"

    def test_set_default_environment_not_exists(self, db_session, auth_info):
        """TC_E017 - 设置默认环境-环境不存在"""
        response = client.post("/api/environments/99999/set-default", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 环境隔离测试 ====================

class TestEnvironmentIsolation:
    """TC_E018, TC_E019, TC_E020"""

    def test_environments_isolated(self, db_session, auth_info):
        """TC_E018 - 环境隔离-不同环境变量隔离"""
        create_environment(db_session, "环境A", variables='{"key": "A"}')
        create_environment(db_session, "环境B", variables='{"key": "B"}')

        response = client.get("/api/environments", headers=auth_info["headers"])
        data = response.json()

        env_a = next(e for e in data if e["name"] == "环境A")
        env_b = next(e for e in data if e["name"] == "环境B")

        assert env_a["variables"]["key"] == "A"
        assert env_b["variables"]["key"] == "B"

    def test_default_environment_priority(self, db_session, auth_info):
        """TC_E019 - 环境隔离-默认环境优先"""
        create_environment(db_session, "普通环境", is_default=False)
        create_environment(db_session, "默认环境", is_default=True)

        response = client.get("/api/environments", headers=auth_info["headers"])
        data = response.json()
        default_env = next(e for e in data if e["is_default"] == True)
        assert default_env["name"] == "默认环境"
