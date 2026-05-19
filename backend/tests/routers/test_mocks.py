# -*- coding: utf-8 -*-
"""
MOCK 模块 API 测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, get_db
from app.models.mock_rule import MockRule
from app.models.tenant import User, Tenant
from app.services.auth_service import AuthService


client = TestClient(app)


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


def get_auth_headers(token):
    """获取认证头"""
    return {"Authorization": f"Bearer {token}"}


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """提供数据库会话，每个测试前清理Mock规则数据"""
    db = SessionLocal()
    # 测试前清理
    try:
        db.query(MockRule).delete()
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
    token, user_id, tenant_id = get_test_user_token(db_session)
    return {
        "token": token,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "headers": get_auth_headers(token)
    }


# ==================== 辅助函数 ====================

def create_mock_rule(db, name="测试规则", path="/test/mock",
                     method="GET", enabled=True, response_status=200,
                     response_body='{"code": 0}', delay_ms=0):
    """创建 MOCK 规则"""
    import json
    rule = MockRule(
        name=name,
        description="pytest创建",
        path=path,
        method=method.upper(),
        response_status=response_status,
        response_headers=json.dumps({"Content-Type": "application/json"}),
        response_body=response_body,
        response_template_type="none",
        delay_ms=delay_ms,
        match_conditions="[]",
        enabled=enabled,
        hit_count=0,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


# ==================== MOCK 规则列表 ====================

class TestListMockRules:
    """获取 MOCK 规则列表"""

    def test_list_mock_rules_empty(self, auth_info, db_session):
        """获取规则列表-空数据库"""
        response = client.get("/api/mocks", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["code"] == 0
        assert response.json()["data"] == []

    def test_list_mock_rules_multiple(self, auth_info, db_session):
        """获取规则列表-多条规则"""
        create_mock_rule(db_session, "规则1")
        create_mock_rule(db_session, "规则2")

        response = client.get("/api/mocks", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

    def test_list_mock_rules_filter_by_enabled(self, auth_info, db_session):
        """按启用状态过滤"""
        create_mock_rule(db_session, "启用规则", enabled=True)
        create_mock_rule(db_session, "停用规则", enabled=False)

        response = client.get("/api/mocks?enabled=true", headers=auth_info["headers"])
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "启用规则"

        response = client.get("/api/mocks?enabled=false", headers=auth_info["headers"])
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "停用规则"

    def test_list_mock_rules_filter_by_method(self, auth_info, db_session):
        """按方法过滤"""
        create_mock_rule(db_session, "GET规则", method="GET")
        create_mock_rule(db_session, "POST规则", method="POST")

        response = client.get("/api/mocks?method=GET", headers=auth_info["headers"])
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["method"] == "GET"

    def test_list_mock_rules_keyword_filter(self, auth_info, db_session):
        """关键词过滤"""
        create_mock_rule(db_session, "用户相关规则")
        create_mock_rule(db_session, "订单相关规则")

        response = client.get("/api/mocks?keyword=用户", headers=auth_info["headers"])
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "用户相关规则"


# ==================== 创建 MOCK 规则 ====================

class TestCreateMockRule:
    """创建 MOCK 规则"""

    def test_create_mock_rule_full_params(self, auth_info, db_session):
        """创建规则-完整参数"""
        payload = {
            "name": "完整规则",
            "description": "完整参数测试",
            "path": "/api/users",
            "method": "POST",
            "response_status": 201,
            "response_headers": {"Content-Type": "application/json"},
            "response_body": '{"id": 1, "name": "created"}',
            "response_template_type": "none",
            "delay_ms": 100,
            "match_conditions": [],
            "enabled": True,
        }
        response = client.post("/api/mocks", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "完整规则"
        assert data["response_status"] == 201
        assert data["delay_ms"] == 100

    def test_create_mock_rule_minimal_params(self, auth_info, db_session):
        """创建规则-最小参数"""
        payload = {
            "name": "最小规则",
            "path": "/test",
            "method": "GET",
            "response_status": 200,
            "response_body": "ok",
        }
        response = client.post("/api/mocks", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "最小规则"
        assert data["enabled"] == True  # 默认启用

    def test_create_mock_rule_method_uppercase(self, auth_info, db_session):
        """创建规则-method转大写"""
        payload = {
            "name": "小写方法",
            "path": "/test",
            "method": "get",
            "response_status": 200,
            "response_body": "ok",
        }
        response = client.post("/api/mocks", json=payload, headers=auth_info["headers"])
        data = response.json()["data"]
        assert data["method"] == "GET"


# ==================== 获取 MOCK 规则 ====================

class TestGetMockRule:
    """获取规则详情"""

    def test_get_mock_rule_exists(self, auth_info, db_session):
        """获取规则-存在"""
        rule = create_mock_rule(db_session, "目标规则")

        response = client.get(f"/api/mocks/{rule.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "目标规则"
        assert data["id"] == rule.id

    def test_get_mock_rule_not_exists(self, auth_info, db_session):
        """获取规则-不存在"""
        response = client.get("/api/mocks/99999", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 更新 MOCK 规则 ====================

class TestUpdateMockRule:
    """更新 MOCK 规则"""

    def test_update_mock_rule_name(self, auth_info, db_session):
        """更新规则-名称"""
        rule = create_mock_rule(db_session, "原名")
        payload = {"name": "新名称"}

        response = client.put(f"/api/mocks/{rule.id}", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "新名称"

    def test_update_mock_rule_response(self, auth_info, db_session):
        """更新规则-响应"""
        rule = create_mock_rule(db_session, "响应规则")
        payload = {
            "response_status": 500,
            "response_body": '{"error": "server error"}',
        }

        response = client.put(f"/api/mocks/{rule.id}", json=payload, headers=auth_info["headers"])
        data = response.json()["data"]
        assert data["response_status"] == 500
        assert "server error" in data["response_body"]

    def test_update_mock_rule_toggle_enabled(self, auth_info, db_session):
        """更新规则-切换启用状态"""
        rule = create_mock_rule(db_session, "启用规则", enabled=True)
        payload = {"enabled": False}

        response = client.put(f"/api/mocks/{rule.id}", json=payload, headers=auth_info["headers"])
        assert response.json()["data"]["enabled"] == False

    def test_update_mock_rule_not_exists(self, auth_info, db_session):
        """更新规则-不存在"""
        payload = {"name": "新名称"}
        response = client.put("/api/mocks/99999", json=payload, headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 删除 MOCK 规则 ====================

class TestDeleteMockRule:
    """删除 MOCK 规则"""

    def test_delete_mock_rule_success(self, auth_info, db_session):
        """删除规则-正常"""
        rule = create_mock_rule(db_session, "待删除")

        response = client.delete(f"/api/mocks/{rule.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["code"] == 0

        response = client.get(f"/api/mocks/{rule.id}", headers=auth_info["headers"])
        assert response.status_code == 404

    def test_delete_mock_rule_not_exists(self, auth_info, db_session):
        """删除规则-不存在"""
        response = client.delete("/api/mocks/99999", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 切换 MOCK 规则状态 ====================

class TestToggleMockRule:
    """切换规则启用状态"""

    def test_toggle_mock_rule_enable_to_disable(self, auth_info, db_session):
        """切换-启用转停用"""
        rule = create_mock_rule(db_session, "规则", enabled=True)
        assert rule.enabled == True

        response = client.post(f"/api/mocks/{rule.id}/toggle", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["data"]["enabled"] == False

    def test_toggle_mock_rule_disable_to_enable(self, auth_info, db_session):
        """切换-停用转启用"""
        rule = create_mock_rule(db_session, "规则", enabled=False)
        assert rule.enabled == False

        response = client.post(f"/api/mocks/{rule.id}/toggle", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["data"]["enabled"] == True

    def test_toggle_mock_rule_not_exists(self, auth_info, db_session):
        """切换-不存在"""
        response = client.post("/api/mocks/99999/toggle", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== MOCK 入口测试 ====================

class TestMockEntry:
    """MOCK 入口端点测试"""

    def test_mock_entry_match_rule(self, auth_info, db_session):
        """MOCK入口-匹配规则"""
        create_mock_rule(
            db_session,
            name="匹配规则",
            path="/test",
            method="GET",
            response_status=200,
            response_body='{"mocked": true}',
        )

        response = client.get("/mock/test", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["mocked"] == True

    def test_mock_entry_not_found(self, auth_info, db_session):
        """MOCK入口-规则不存在"""
        response = client.get("/mock/nonexistent", headers=auth_info["headers"])
        assert response.status_code == 404

    def test_mock_entry_disabled_rule(self, auth_info, db_session):
        """MOCK入口-规则已禁用"""
        create_mock_rule(
            db_session,
            name="禁用规则",
            path="/disabled",
            method="GET",
            enabled=False,
        )

        response = client.get("/mock/disabled", headers=auth_info["headers"])
        assert response.status_code == 404  # 禁用的规则不会被匹配

    def test_mock_entry_delay(self, auth_info, db_session):
        """MOCK入口-延迟响应"""
        import time
        create_mock_rule(
            db_session,
            name="延迟规则",
            path="/delay",
            method="GET",
            delay_ms=100,
        )

        start = time.time()
        response = client.get("/mock/delay", headers=auth_info["headers"])
        elapsed = (time.time() - start) * 1000
        assert response.status_code == 200
        assert elapsed >= 90  # 允许一些误差

    def test_mock_entry_post_method(self, auth_info, db_session):
        """MOCK入口-POST方法"""
        create_mock_rule(
            db_session,
            name="POST规则",
            path="/post",
            method="POST",
            response_status=201,
            response_body='{"created": true}',
        )

        response = client.post("/mock/post", json={"data": "test"}, headers=auth_info["headers"])
        assert response.status_code == 201


# ==================== MOCK 规则统计 ====================

class TestMockRuleStats:
    """MOCK 规则命中统计"""

    def test_mock_hit_count_increments(self, auth_info, db_session):
        """命中计数递增"""
        rule = create_mock_rule(db_session, "计数规则", path="/hit")
        assert rule.hit_count == 0

        # 访问两次
        client.get("/mock/hit", headers=auth_info["headers"])
        client.get("/mock/hit", headers=auth_info["headers"])

        # 刷新数据库中的规则
        db_session.refresh(rule)
        assert rule.hit_count == 2
