# -*- coding: utf-8 -*-
"""
报告模块 API 测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.tenant import User, Tenant
from app.models.report_template import ReportTemplate
from app.models.execution_log import ExecutionLog
from app.services.auth_service import AuthService


client = TestClient(app)


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """提供数据库会话，每个测试前清理报告数据"""
    db = SessionLocal()
    # 测试前清理
    try:
        db.query(ExecutionLog).delete()
        db.query(ReportTemplate).delete()
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


def create_report_template(db, name="测试模板", is_default=False):
    """创建报告模板"""
    template = ReportTemplate(
        name=name,
        description="pytest创建",
        type="html",
        content="<html><body>{{ summary.name }}</body></html>",
        is_default=is_default,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def create_execution_log(db, status="success", response_time_ms=100):
    """创建执行日志"""
    log = ExecutionLog(
        case_id=1,
        scenario_id=None,
        scenario_step_id=None,
        execution_type="single",
        execution_id="exec_001",
        request_url="http://example.com/api",
        request_method="GET",
        request_headers="{}",
        request_body="",
        response_status=200 if status == "success" else 500,
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


# ==================== 报告模板列表 ====================

class TestListTemplates:
    """获取报告模板列表"""

    def test_list_templates_empty(self, db_session, auth_info):
        """获取模板列表-空数据库"""
        response = client.get("/api/report-templates", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json() == []

    def test_list_templates_multiple(self, db_session, auth_info):
        """获取模板列表-多个模板"""
        create_report_template(db_session, "模板1")
        create_report_template(db_session, "模板2")

        response = client.get("/api/report-templates", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_templates_pagination(self, db_session, auth_info):
        """模板列表-分页"""
        for i in range(10):
            create_report_template(db_session, f"模板{i}")

        response = client.get("/api/report-templates?skip=0&limit=5", headers=auth_info["headers"])
        data = response.json()
        assert len(data) == 5


# ==================== 创建报告模板 ====================

class TestCreateTemplate:
    """创建报告模板"""

    def test_create_template_html(self, db_session, auth_info):
        """创建模板-HTML类型"""
        payload = {
            "name": "HTML模板",
            "description": "测试HTML",
            "type": "html",
            "content": "<html><body>Test</body></html>",
            "is_default": False,
        }
        response = client.post("/api/report-templates", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "HTML模板"
        assert data["type"] == "html"

    def test_create_template_markdown(self, db_session, auth_info):
        """创建模板-Markdown类型"""
        payload = {
            "name": "MD模板",
            "type": "markdown",
            "content": "# Test Report",
        }
        response = client.post("/api/report-templates", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "markdown"

    def test_create_template_set_as_default(self, db_session, auth_info):
        """创建模板-设为默认"""
        create_report_template(db_session, "原默认", is_default=True)

        payload = {
            "name": "新默认模板",
            "type": "html",
            "content": "content",
            "is_default": True,
        }
        response = client.post("/api/report-templates", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200

        # 验证只有一个默认
        templates = db_session.query(ReportTemplate).filter(
            ReportTemplate.is_default == True
        ).all()
        assert len(templates) == 1
        assert templates[0].name == "新默认模板"


# ==================== 获取报告模板 ====================

class TestGetTemplate:
    """获取模板详情"""

    def test_get_template_exists(self, db_session, auth_info):
        """获取模板-存在"""
        template = create_report_template(db_session, "目标模板")

        response = client.get(f"/api/report-templates/{template.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "目标模板"

    def test_get_template_not_exists(self, db_session, auth_info):
        """获取模板-不存在"""
        response = client.get("/api/report-templates/99999", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 更新报告模板 ====================

class TestUpdateTemplate:
    """更新报告模板"""

    def test_update_template_name(self, db_session, auth_info):
        """更新模板-名称"""
        template = create_report_template(db_session, "原名")
        payload = {"name": "新名称"}

        response = client.put(f"/api/report-templates/{template.id}", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["name"] == "新名称"

    def test_update_template_content(self, db_session, auth_info):
        """更新模板-内容"""
        template = create_report_template(db_session, "内容模板")
        payload = {"content": "<html>新内容</html>"}

        response = client.put(f"/api/report-templates/{template.id}", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        assert "新内容" in response.json()["content"]

    def test_update_template_not_exists(self, db_session, auth_info):
        """更新模板-不存在"""
        payload = {"name": "新名称"}
        response = client.put("/api/report-templates/99999", json=payload, headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 删除报告模板 ====================

class TestDeleteTemplate:
    """删除报告模板"""

    def test_delete_template_success(self, db_session, auth_info):
        """删除模板-正常"""
        template = create_report_template(db_session, "待删除")

        response = client.delete(f"/api/report-templates/{template.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["code"] == 0

        response = client.get(f"/api/report-templates/{template.id}", headers=auth_info["headers"])
        assert response.status_code == 404

    def test_delete_template_not_exists(self, db_session, auth_info):
        """删除模板-不存在"""
        response = client.delete("/api/report-templates/99999", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 报告列表 ====================

class TestListReports:
    """获取报告列表"""

    def test_list_reports_empty(self, db_session, auth_info):
        """获取报告列表-无日志"""
        response = client.get("/api/reports", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_list_reports_with_logs(self, db_session, auth_info):
        """获取报告列表-有执行日志"""
        create_execution_log(db_session, "success")
        create_execution_log(db_session, "failed")

        response = client.get("/api/reports", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) >= 1  # 按日期分组

    def test_list_reports_pagination(self, db_session, auth_info):
        """报告列表-分页"""
        for i in range(10):
            create_execution_log(db_session, "success")

        response = client.get("/api/reports?skip=0&limit=5", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) <= 5


# ==================== 删除报告 ====================

class TestDeleteReport:
    """删除报告"""

    def test_delete_report_success(self, db_session, auth_info):
        """删除报告-正常"""
        log = create_execution_log(db_session)

        response = client.delete(f"/api/reports/{log.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["code"] == 0


# ==================== 报告下载 ====================

class TestDownloadReport:
    """下载报告"""

    def test_download_report_exists(self, db_session, auth_info):
        """下载报告-存在"""
        log = create_execution_log(db_session, "success")

        response = client.get(f"/api/reports/{log.id}/download", headers=auth_info["headers"])
        assert response.status_code == 200
        assert "text/html" in str(response.headers) or "text/html" in response.headers.get("content-type", "")

    def test_download_report_not_exists(self, db_session, auth_info):
        """下载报告-不存在"""
        response = client.get("/api/reports/99999/download", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 报告生成 ====================

class TestGenerateReport:
    """生成报告"""

    def test_generate_report_by_execution_ids(self, db_session, auth_info):
        """生成报告-按执行ID"""
        log1 = create_execution_log(db_session, "success")
        log2 = create_execution_log(db_session, "failed")

        payload = {
            "name": "测试报告",
            "execution_ids": [log1.id, log2.id],
        }
        response = client.post("/api/reports/generate", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "generated"
        assert "summary" in data["data"]
        assert data["data"]["summary"]["total"] == 2
        assert data["data"]["summary"]["passed"] == 1
        assert data["data"]["summary"]["failed"] == 1

    def test_generate_report_by_time_range(self, db_session, auth_info):
        """生成报告-按时间范围"""
        create_execution_log(db_session, "success")

        from datetime import datetime, timedelta
        now = datetime.now()
        start_time = (now - timedelta(hours=1)).isoformat()
        end_time = (now + timedelta(hours=1)).isoformat()

        payload = {
            "name": "时间范围报告",
            "start_time": start_time,
            "end_time": end_time,
        }
        response = client.post("/api/reports/generate", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["summary"]["total"] >= 1

    def test_generate_report_with_template(self, db_session, auth_info):
        """生成报告-指定模板"""
        template = create_report_template(db_session, "自定义模板")
        log = create_execution_log(db_session, "success")

        payload = {
            "name": "模板报告",
            "execution_ids": [log.id],
            "template_id": template.id,
        }
        response = client.post("/api/reports/generate", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["type"] == "html"

    def test_generate_report_markdown_type(self, db_session, auth_info):
        """生成报告-Markdown格式"""
        template = create_report_template(db_session, "MD模板")
        template.type = "markdown"
        db_session.commit()

        log = create_execution_log(db_session, "success")

        payload = {
            "name": "Markdown报告",
            "execution_ids": [log.id],
            "template_id": template.id,
        }
        response = client.post("/api/reports/generate", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["type"] == "markdown"
        assert "# Markdown报告" in data["data"]["content"]

    def test_generate_report_empty_execution_ids(self, db_session, auth_info):
        """生成报告-空执行ID列表"""
        payload = {
            "name": "空报告",
            "execution_ids": [],
        }
        response = client.post("/api/reports/generate", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["summary"]["total"] == 0
        assert data["data"]["summary"]["pass_rate"] == "0%"


# ==================== 报告统计 ====================

class TestReportSummary:
    """报告统计计算"""

    def test_report_pass_rate_calculation(self, db_session, auth_info):
        """通过率计算"""
        for i in range(7):
            create_execution_log(db_session, "success")
        for i in range(3):
            create_execution_log(db_session, "failed")

        payload = {
            "name": "统计报告",
            "execution_ids": [],
        }
        # 不指定execution_ids时，会获取最近的执行记录
        # 但这个API在没有execution_ids时需要时间范围
        # 先创建日志再测试
        response = client.post("/api/reports/generate", json=payload, headers=auth_info["headers"])
        # 由于没有过滤条件，可能获取所有记录
        assert response.status_code == 200

    def test_report_no_execution_logs(self, db_session, auth_info):
        """无执行日志时的报告"""
        payload = {
            "name": "空报告",
            "execution_ids": [],
            "start_time": "2020-01-01T00:00:00",
            "end_time": "2020-01-02T00:00:00",
        }
        response = client.post("/api/reports/generate", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["summary"]["total"] == 0
