# -*- coding: utf-8 -*-
"""
日志模块 API 测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.execution_log import ExecutionLog
from app.models.case import TestCase
from app.models.scenario import Scenario
from app.models import User, Tenant
from app.services.auth_service import AuthService


client = TestClient(app)


# ==================== 认证辅助 ====================

@pytest.fixture(scope="function")
def db_session():
    """提供数据库会话，每个测试前清理日志数据"""
    db = SessionLocal()
    # 测试前清理
    try:
        db.query(ExecutionLog).delete()
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
    tenant = db_session.query(Tenant).filter(Tenant.name == "测试租户_日志").first()
    if not tenant:
        tenant = Tenant(name="测试租户_日志", code="test_log", status="active")
        db_session.add(tenant)
        db_session.commit()
        db_session.refresh(tenant)
    
    user = db_session.query(User).filter(User.username == "test_user_log").first()
    if not user:
        password_hash = AuthService.hash_password("test_password_123")
        user = User(
            username="test_user_log",
            email="test_log@example.com",
            password_hash=password_hash,
            tenant_id=tenant.id,
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    token = AuthService.create_access_token(user_id=user.id, tenant_id=tenant.id)
    return {"Authorization": f"Bearer {token}"}


# ==================== 辅助函数 ====================

def create_test_log(db, case_id=None, scenario_id=None, status="success",
                    response_status=200, response_time_ms=100):
    """创建测试日志"""
    log = ExecutionLog(
        case_id=case_id,
        scenario_id=scenario_id,
        scenario_step_id=None,
        execution_type="single" if case_id else "scenario",
        execution_id="exec_001",
        request_url="http://example.com/api",
        request_method="GET",
        request_headers="{}",
        request_body="",
        response_status=response_status,
        response_headers="{}",
        response_body='{"result": "ok"}',
        response_size=100,
        response_time_ms=response_time_ms,
        status=status,
        assertion_results="[]",
        environment_id=1,
        triggered_by="user",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def create_test_case(db, name="测试用例"):
    """创建测试用例"""
    case = TestCase(
        name=name,
        description="测试",
        method="GET",
        url="http://example.com",
        headers="{}",
        params="{}",
        body="",
        body_type="none",
        auth_type="none",
        auth_config="{}",
        folder_path="/test",
        sort_order=1,
        timeout=30,
        follow_redirects=True,
        verify_ssl=False,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def create_test_scenario(db, name="测试场景"):
    """创建测试场景"""
    scenario = Scenario(
        name=name,
        description="测试场景",
        folder_path="/test",
        variables="{}",
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


# ==================== 日志列表 ====================

class TestListLogs:
    """获取日志列表"""

    def test_list_logs_empty(self, db_session, auth_info):
        """获取日志列表-空数据库"""
        response = client.get("/api/logs", headers=auth_info)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_logs_multiple(self, db_session, auth_info):
        """获取日志列表-多条记录"""
        create_test_log(db_session, status="success")
        create_test_log(db_session, status="failed")
        create_test_log(db_session, status="success")

        response = client.get("/api/logs", headers=auth_info)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_logs_filter_by_case_id(self, db_session, auth_info):
        """按用例ID过滤日志"""
        case = create_test_case(db_session)
        log1 = create_test_log(db_session, case_id=case.id)
        log2 = create_test_log(db_session)  # 无关联用例

        response = client.get(f"/api/logs?case_id={case.id}", headers=auth_info)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == log1.id

    def test_list_logs_filter_by_status(self, db_session, auth_info):
        """按状态过滤日志"""
        create_test_log(db_session, status="success")
        create_test_log(db_session, status="failed")
        create_test_log(db_session, status="failed")

        response = client.get("/api/logs?status=failed", headers=auth_info)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(log["status"] == "failed" for log in data)

    def test_list_logs_pagination(self, db_session, auth_info):
        """日志列表-分页"""
        for i in range(10):
            create_test_log(db_session)

        response = client.get("/api/logs?skip=0&limit=5", headers=auth_info)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        response = client.get("/api/logs?skip=5&limit=5", headers=auth_info)
        data = response.json()
        assert len(data) == 5

    def test_list_logs_order_by_created_at_desc(self, db_session, auth_info):
        """日志列表-按创建时间倒序"""
        import time
        log1 = create_test_log(db_session)
        time.sleep(0.01)
        log2 = create_test_log(db_session)

        response = client.get("/api/logs", headers=auth_info)
        data = response.json()
        # 最新的应该在前面
        assert data[0]["id"] == log2.id


# ==================== 获取单个日志 ====================

class TestGetLog:
    """获取单个日志详情"""

    def test_get_log_exists(self, db_session, auth_info):
        """获取日志-存在"""
        log = create_test_log(db_session, status="success")

        response = client.get(f"/api/logs/{log.id}", headers=auth_info)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == log.id
        assert data["status"] == "success"

    def test_get_log_not_exists(self, db_session, auth_info):
        """获取日志-不存在"""
        response = client.get("/api/logs/99999", headers=auth_info)
        assert response.status_code == 200  # 注意：API返回200但error字段为not found
        data = response.json()
        assert "error" in data


# ==================== 删除日志 ====================

class TestDeleteLog:
    """删除日志"""

    def test_delete_log_success(self, db_session, auth_info):
        """删除日志-正常"""
        log = create_test_log(db_session)

        response = client.delete(f"/api/logs/{log.id}", headers=auth_info)
        assert response.status_code == 200
        assert response.json()["code"] == 0

        # 验证已删除
        response = client.get(f"/api/logs/{log.id}", headers=auth_info)
        data = response.json()
        assert "error" in data

    def test_delete_log_not_exists(self, db_session, auth_info):
        """删除日志-不存在（不报错）"""
        response = client.delete("/api/logs/99999", headers=auth_info)
        assert response.status_code == 200
        assert response.json()["code"] == 0


# ==================== 批量删除日志 ====================

class TestBatchDeleteLogs:
    """批量删除日志"""

    def test_batch_delete_logs_success(self, db_session, auth_info):
        """批量删除日志-正常"""
        log1 = create_test_log(db_session)
        log2 = create_test_log(db_session)
        log3 = create_test_log(db_session)

        response = client.delete(f"/api/logs/batch-delete?ids={log1.id}&ids={log2.id}", headers=auth_info)
        assert response.status_code == 200
        assert response.json()["code"] == 0

        # 验证删除结果
        response = client.get("/api/logs", headers=auth_info)
        data = response.json()
        remaining_ids = [log["id"] for log in data]
        assert log1.id not in remaining_ids
        assert log2.id not in remaining_ids
        assert log3.id in remaining_ids

    def test_batch_delete_logs_empty_list(self, db_session, auth_info):
        """批量删除日志-空列表"""
        create_test_log(db_session)
        create_test_log(db_session)

        response = client.delete("/api/logs/batch-delete", headers=auth_info)
        assert response.status_code == 200  # 空列表不报错

        response = client.get("/api/logs", headers=auth_info)
        assert len(response.json()) == 2  # 没删除任何东西


# ==================== 日志内容验证 ====================

class TestLogContent:
    """日志内容验证"""

    def test_log_response_parsing(self, db_session, auth_info):
        """日志响应解析"""
        log = create_test_log(
            db_session,
            response_status=200,
            response_time_ms=150,
            status="success"
        )

        response = client.get(f"/api/logs/{log.id}", headers=auth_info)
        data = response.json()

        assert data["response_status"] == 200
        assert data["response_time_ms"] == 150
        assert data["status"] == "success"

    def test_log_case_association(self, db_session, auth_info):
        """日志用例关联"""
        case = create_test_case(db_session)
        log = create_test_log(db_session, case_id=case.id)

        response = client.get(f"/api/logs/{log.id}", headers=auth_info)
        data = response.json()

        assert data["case_id"] == case.id

    def test_log_scenario_association(self, db_session, auth_info):
        """日志场景关联"""
        scenario = create_test_scenario(db_session)
        log = create_test_log(db_session, scenario_id=scenario.id)

        response = client.get(f"/api/logs/{log.id}", headers=auth_info)
        data = response.json()

        assert data["scenario_id"] == scenario.id
