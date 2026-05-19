# -*- coding: utf-8 -*-
"""
场景管理API测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.tenant import User, Tenant
from app.services.auth_service import AuthService


client = TestClient(app)


# ==================== Fixtures ====================

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def auth_headers(db_session):
    """获取认证头"""
    tenant = db_session.query(Tenant).filter(Tenant.name == "测试租户_Pytest").first()
    if not tenant:
        tenant = Tenant(name="测试租户_Pytest", code="test_pytest", status="active")
        db_session.add(tenant)
        db_session.commit()
        db_session.refresh(tenant)
    
    user = db_session.query(User).filter(User.username == "test_user_pytest").first()
    if not user:
        password_hash = AuthService.hash_password("test_password_123")
        user = User(
            username="test_user_pytest",
            email="test_pytest@example.com",
            password_hash=password_hash,
            tenant_id=tenant.id,
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    token = AuthService.create_access_token(user_id=user.id, tenant_id=tenant.id)
    return {"Authorization": f"Bearer {token}"}


# ==================== 测试用例 ====================

class TestScenariosAPI:
    """场景管理API测试"""
    
    def test_get_scenarios_unauthorized(self):
        """测试未授权访问场景列表"""
        response = client.get("/api/scenarios")
        assert response.status_code == 401
    
    def test_get_scenarios_authorized(self, auth_headers):
        """测试获取场景列表（已授权）"""
        response = client.get(
            "/api/scenarios",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)  # API 直接返回列表
    
    def test_create_scenario(self, auth_headers):
        """测试创建场景"""
        payload = {
            "name": "测试场景_Pytest",
            "folder_path": "/test"
        }
        response = client.post(
            "/api/scenarios",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # API 返回 {"code": 0, "data": {...}} 格式
        assert data["name"] == payload["name"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
