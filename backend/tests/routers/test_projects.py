# -*- coding: utf-8 -*-
"""
项目管理API测试
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, get_db
from app.models.tenant import User, Tenant, Project
from app.services.auth_service import AuthService


# 创建测试客户端
client = TestClient(app)


# ==================== 测试数据 ====================

TEST_PROJECT_NAME = "测试项目_Pytest"
TEST_PROJECT_KEY = "TPY"  # key 长度需要 >= 3
TEST_PROJECT_DESC = "这是pytest测试创建的项目"


# ==================== 辅助函数 ====================

def get_test_user_token(db):
    """获取测试用户token，如果用户不存在则创建"""
    # 查找或创建测试租户
    tenant = db.query(Tenant).filter(Tenant.name == "测试租户_Pytest").first()
    if not tenant:
        tenant = Tenant(name="测试租户_Pytest", code="test_pytest", status="active")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    
    # 查找或创建测试用户
    user = db.query(User).filter(User.username == "test_user_pytest").first()
    if not user:
        password_hash = AuthService.hash_password("test_password_123")
        user = User(
            username="test_user_pytest",
            email="test_pytest@example.com",
            password_hash=password_hash,
            tenant_id=tenant.id,
            status="active"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 生成token
    token = AuthService.create_access_token(user_id=user.id, tenant_id=tenant.id)
    return token, user.id, tenant.id


def cleanup_test_data(db, project_name, user_id, project_key=None):
    """清理测试数据"""
    # 按名称和创建者删除
    project = db.query(Project).filter(
        Project.name == project_name,
        Project.created_by == user_id
    ).first()
    if project:
        db.delete(project)
        db.commit()
    # 也按 key 清理（防止重复 key 问题）
    if project_key:
        projects = db.query(Project).filter(
            Project.key == project_key.upper()
        ).all()
        for p in projects:
            db.delete(p)
        db.commit()


def get_auth_headers(token):
    """获取认证头"""
    return {"Authorization": f"Bearer {token}"}


# ==================== Fixtures ====================

@pytest.fixture(scope="module")
def db_session():
    """提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def auth_info(db_session):
    """获取认证信息"""
    token, user_id, tenant_id = get_test_user_token(db_session)
    return {
        "token": token,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "headers": get_auth_headers(token)
    }


@pytest.fixture(scope="function")
def cleanup_project(db_session, auth_info):
    """每个测试后清理项目"""
    yield
    cleanup_test_data(db_session, TEST_PROJECT_NAME, auth_info["user_id"], TEST_PROJECT_KEY)


# ==================== 项目CRUD测试 ====================

class TestProjectAPI:
    """项目管理API测试类"""
    
    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_get_projects_unauthorized(self):
        """测试未授权访问项目列表"""
        response = client.get("/api/projects")
        assert response.status_code == 401
    
    def test_get_projects_authorized(self, auth_info, cleanup_project):
        """测试获取项目列表（已授权）"""
        response = client.get(
            "/api/projects",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_create_project(self, auth_info, cleanup_project):
        """测试创建项目"""
        payload = {
            "name": TEST_PROJECT_NAME,
            "key": TEST_PROJECT_KEY,
            "description": TEST_PROJECT_DESC
        }
        response = client.post(
            "/api/projects",
            json=payload,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == TEST_PROJECT_NAME
        assert data["key"] == TEST_PROJECT_KEY
        assert data["description"] == TEST_PROJECT_DESC
        assert "id" in data
        assert "tenant_id" in data
    
    def test_get_single_project(self, auth_info, db_session):
        """测试获取单个项目"""
        # 先创建一个项目
        payload = {
            "name": TEST_PROJECT_NAME,
            "key": TEST_PROJECT_KEY,
            "description": TEST_PROJECT_DESC
        }
        create_response = client.post(
            "/api/projects",
            json=payload,
            headers=auth_info["headers"]
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]
        
        try:
            # 获取单个项目
            response = client.get(
                f"/api/projects/{project_id}",
                headers=auth_info["headers"]
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == project_id
            assert data["name"] == TEST_PROJECT_NAME
        finally:
            # 清理
            cleanup_test_data(db_session, TEST_PROJECT_NAME, auth_info["user_id"])
    
    def test_get_nonexistent_project(self, auth_info):
        """测试获取不存在的项目"""
        response = client.get(
            "/api/projects/99999",
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
    
    def test_delete_project(self, auth_info, db_session):
        """测试删除项目"""
        # 先创建一个项目
        payload = {
            "name": TEST_PROJECT_NAME,
            "key": TEST_PROJECT_KEY,
            "description": TEST_PROJECT_DESC
        }
        create_response = client.post(
            "/api/projects",
            json=payload,
            headers=auth_info["headers"]
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]
        
        # 删除项目
        delete_response = client.delete(
            f"/api/projects/{project_id}",
            headers=auth_info["headers"]
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "删除成功"
        
        # 验证项目已被删除
        get_response = client.get(
            f"/api/projects/{project_id}",
            headers=auth_info["headers"]
        )
        assert get_response.status_code == 404
    
    def test_create_project_duplicate_key(self, auth_info, cleanup_project):
        """测试创建重复key的项目"""
        payload = {
            "name": TEST_PROJECT_NAME + "_1",
            "key": TEST_PROJECT_KEY,
            "description": "第一个项目"
        }
        response1 = client.post(
            "/api/projects",
            json=payload,
            headers=auth_info["headers"]
        )
        assert response1.status_code == 200
        
        # 尝试用相同的key创建另一个项目
        payload2 = {
            "name": TEST_PROJECT_NAME + "_2",
            "key": TEST_PROJECT_KEY,
            "description": "第二个项目"
        }
        response2 = client.post(
            "/api/projects",
            json=payload2,
            headers=auth_info["headers"]
        )
        assert response2.status_code == 400


# ==================== 运行方式 ====================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
