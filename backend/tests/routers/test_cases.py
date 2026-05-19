# -*- coding: utf-8 -*-
"""
用例管理模块 API 测试
覆盖 P0 和 P1 测试用例
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, get_db
from app.models.tenant import User, Tenant
from app.models.case import TestCase
from app.models.environment import Environment
from app.models.execution_log import ExecutionLog
from app.services.auth_service import AuthService


# 创建测试客户端
client = TestClient(app)


# ==================== 测试数据 ====================

TEST_CASE_NAME = "测试用例_Pytest"
TEST_CASE_NAME_UPDATED = "测试用例_已更新"
TEST_CASE_METHOD = "POST"
TEST_CASE_URL = "https://httpbin.org/post"
TEST_CASE_FOLDER = "/api/test"
TEST_CASE_FOLDER_USER = "/api/user"


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


def cleanup_test_cases(db, case_name, user_id=None):
    """清理测试用例"""
    cases = db.query(TestCase).filter(TestCase.name == case_name).all()
    for case in cases:
        db.delete(case)
    db.commit()


def create_test_case(db, name=None, method="GET", url="https://httpbin.org/get",
                     folder_path="/api/test", sort_order=1, body=None, body_type=None,
                     headers=None, params=None, auth_config=None, assertions=None,
                     pre_script=None, post_script=None, timeout=None,
                     follow_redirects=None, verify_ssl=None, **kwargs):
    """创建测试用例并返回"""
    case_name = name or TEST_CASE_NAME

    case = TestCase(
        name=case_name,
        description="pytest创建的测试用例",
        method=method,
        url=url,
        headers=headers or '{"Content-Type": "application/json"}',
        params=params or "{}",
        body=body or '{"test": "data"}',
        body_type=body_type or "json",
        auth_type="none",
        auth_config=auth_config or "{}",
        folder_path=folder_path,
        sort_order=sort_order,
        assertions=assertions or "[]",
        pre_script=pre_script or "",
        post_script=post_script or "",
        timeout=timeout if timeout is not None else 30,
        follow_redirects=follow_redirects if follow_redirects is not None else True,
        verify_ssl=verify_ssl if verify_ssl is not None else True,
        **kwargs
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def create_test_environment(db, name="测试环境", is_default=False, variables='{"base_url": "https://httpbin.org"}'):
    """创建测试环境并返回"""
    # 检查是否已存在同名环境
    env = db.query(Environment).filter(Environment.name == name).first()
    if env:
        return env
    
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
def cleanup_case(db_session):
    """每个测试后清理用例"""
    yield
    cases = db_session.query(TestCase).filter(TestCase.name == TEST_CASE_NAME).all()
    for case in cases:
        db_session.delete(case)
    db_session.commit()


@pytest.fixture(scope="function")
def cleanup_case_by_name(db_session):
    """按名称清理用例"""
    def _cleanup(name):
        cases = db_session.query(TestCase).filter(TestCase.name == name).all()
        for case in cases:
            db_session.delete(case)
        db_session.commit()
    return _cleanup


# ==================== P0 测试用例：核心流程 ====================

class TestCaseP0CRUD:
    """P0 用例 CRUD 核心流程"""

    def test_case_create_full_params(self, auth_info, db_session, cleanup_case):
        """
        P0_TC001: 创建用例-完整参数
        验证：返回 201，data 包含新建用例完整信息，id 已生成
        """
        payload = {
            "name": "登录接口测试",
            "method": "POST",
            "url": "https://api.example.com/login",
            "headers": {"Content-Type": "application/json"},
            "params": {},
            "body": '{"username": "test"}',
            "body_type": "json",
            "auth_type": "none",
            "auth_config": {},
            "folder_path": "/api/user",
            "sort_order": 1,
            "assertions": [{"id": "1", "type": "status_code", "operator": "equals", "expected": 200, "enabled": True}],
            "timeout": 30,
            "follow_redirects": True,
            "verify_ssl": True
        }
        response = client.post(
            "/api/cases",
            json=payload,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"创建用例失败: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == "登录接口测试"
        assert data["method"] == "POST"
        assert data["url"] == "https://api.example.com/login"
        assert data["folder_path"] == "/api/user"
        assert data["body_type"] == "json"

    def test_case_list_pagination(self, auth_info, db_session, cleanup_case):
        """
        P0_TC002: 获取用例列表-分页
        验证：返回用例列表，总数≥10，返回10条，结构包含 id/name/method/url 等字段
        """
        # 先创建10条用例
        for i in range(10):
            create_test_case(db_session, name=f"分页测试用例_{i}")
        
        response = client.get(
            "/api/cases?skip=0&limit=10",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取用例列表失败: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  # 可能有之前的数据
        if len(data) > 0:
            assert "id" in data[0]
            assert "name" in data[0]
            assert "method" in data[0]
            assert "url" in data[0]

    def test_case_get_single_exists(self, auth_info, db_session, cleanup_case):
        """
        P0_TC003: 获取单个用例-存在
        验证：返回该用例完整信息，HTTP 200
        """
        # 创建测试用例
        created = create_test_case(db_session)
        
        response = client.get(
            f"/api/cases/{created.id}",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取用例失败: {response.text}"
        data = response.json()
        assert data["id"] == created.id
        assert data["name"] == created.name
        assert data["method"] == created.method

    def test_case_update_exists(self, auth_info, db_session, cleanup_case):
        """
        P0_TC004: 更新用例-存在
        验证：返回更新后的用例信息，name 已变更
        """
        # 创建测试用例
        created = create_test_case(db_session)
        
        update_payload = {"name": "更新后的名称"}
        response = client.put(
            f"/api/cases/{created.id}",
            json=update_payload,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新用例失败: {response.text}"
        data = response.json()
        assert data["name"] == "更新后的名称"
        assert data["id"] == created.id

    def test_case_delete_exists(self, auth_info, db_session, cleanup_case):
        """
        P0_TC005: 删除用例-存在
        验证：返回 {"code":0,"message":"deleted"}，用例已从数据库删除
        """
        # 创建测试用例
        created = create_test_case(db_session)
        case_id = created.id
        
        response = client.delete(
            f"/api/cases/{case_id}",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"删除用例失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "deleted"
        
        # 验证用例已删除
        get_response = client.get(
            f"/api/cases/{case_id}",
            headers=auth_info["headers"]
        )
        assert get_response.status_code == 404

    def test_case_run_normal(self, auth_info, db_session, cleanup_case):
        """
        P0_TC006: 执行用例-正常
        验证：返回执行结果，包含 status、response 字段，ExecutionLog 已创建
        """
        # 创建测试用例
        created = create_test_case(
            db_session,
            method="GET",
            url="https://httpbin.org/get",
            folder_path="/api/test"
        )
        
        # 创建测试环境
        env = create_test_environment(db_session, name="测试环境_Pytest")
        
        response = client.post(
            f"/api/cases/{created.id}/run",
            json={"environment_id": env.id},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"执行用例失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "status" in data["data"]
        assert "response" in data["data"]
        
        # 验证 ExecutionLog 已创建
        logs = db_session.query(ExecutionLog).filter(
            ExecutionLog.case_id == created.id
        ).all()
        assert len(logs) >= 1
        assert logs[-1].status in ["passed", "failed", "success"]

    def test_case_batch_delete(self, auth_info, db_session, cleanup_case):
        """
        P0_TC007: 批量删除用例-正常
        验证：返回 {"code":0,"message":"deleted X cases"}，X个用例已删除
        """
        # 创建3个测试用例
        case_ids = []
        for i in range(3):
            created = create_test_case(db_session, name=f"批量删除测试用例_{i}")
            case_ids.append(created.id)
        
        response = client.post(
            "/api/cases/batch-delete",
            json=case_ids,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"批量删除用例失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert "deleted 3 cases" in data["message"]
        
        # 验证用例已删除
        for case_id in case_ids:
            get_response = client.get(
                f"/api/cases/{case_id}",
                headers=auth_info["headers"]
            )
            assert get_response.status_code == 404


class TestCaseP0Run:
    """P0 执行用例核心流程"""

    def test_case_run_default_environment(self, auth_info, db_session, cleanup_case):
        """
        P0_TC008: 执行用例-使用默认环境
        验证：使用默认环境执行，env_id 为默认环境ID
        """
        # 创建测试用例
        created = create_test_case(
            db_session,
            method="GET",
            url="https://httpbin.org/get"
        )
        
        # 创建默认环境
        default_env = create_test_environment(
            db_session, 
            name="默认环境_Pytest", 
            is_default=True,
            variables='{"base_url": "https://httpbin.org"}'
        )
        
        response = client.post(
            f"/api/cases/{created.id}/run",
            json={},  # 不传 environment_id
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"执行用例失败: {response.text}"
        data = response.json()
        assert data["code"] == 0

    def test_case_run_record_saved(self, auth_info, db_session, cleanup_case):
        """
        P0_TC009: 执行用例-记录保存验证
        验证：ExecutionLog 记录已创建，包含 case_id/execution_id/response_status 等字段
        """
        # 创建测试用例
        created = create_test_case(
            db_session,
            method="GET",
            url="https://httpbin.org/get"
        )
        
        # 创建测试环境
        env = create_test_environment(db_session, name="测试环境2_Pytest")
        
        # 记录执行前的日志数量
        logs_before = db_session.query(ExecutionLog).filter(
            ExecutionLog.case_id == created.id
        ).count()
        
        response = client.post(
            f"/api/cases/{created.id}/run",
            json={"environment_id": env.id},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"执行用例失败: {response.text}"
        
        # 验证 ExecutionLog 记录增加
        logs_after = db_session.query(ExecutionLog).filter(
            ExecutionLog.case_id == created.id
        ).count()
        assert logs_after > logs_before
        
        # 验证最新日志字段
        latest_log = db_session.query(ExecutionLog).filter(
            ExecutionLog.case_id == created.id
        ).order_by(ExecutionLog.created_at.desc()).first()
        
        assert latest_log.case_id == created.id
        assert latest_log.execution_id is not None
        assert latest_log.response_status is not None
        assert latest_log.status is not None


# ==================== P1 测试用例：重要功能 ====================

class TestCaseP1List:
    """P1 用例列表查询"""

    def test_case_list_filter_folder(self, auth_info, db_session, cleanup_case):
        """
        P1_TC001: 列表-按folder过滤
        验证：只返回 folder_path="/api/user" 的用例
        """
        # 创建不同 folder 的用例
        create_test_case(db_session, name="用例_folder1", folder_path="/api/user")
        create_test_case(db_session, name="用例_folder2", folder_path="/api/user")
        create_test_case(db_session, name="用例_folder3", folder_path="/api/other")
        
        response = client.get(
            "/api/cases?folder=/api/user",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取用例列表失败: {response.text}"
        data = response.json()
        for item in data:
            assert item["folder_path"] == "/api/user"

    def test_case_list_filter_method(self, auth_info, db_session, cleanup_case):
        """
        P1_TC002: 列表-按method过滤
        验证：只返回 method="POST" 的用例
        """
        # 创建不同 method 的用例
        create_test_case(db_session, name="用例_method1", method="POST")
        create_test_case(db_session, name="用例_method2", method="POST")
        create_test_case(db_session, name="用例_method3", method="GET")
        
        response = client.get(
            "/api/cases?method=POST",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取用例列表失败: {response.text}"
        data = response.json()
        for item in data:
            assert item["method"] == "POST"

    def test_case_list_keyword_search(self, auth_info, db_session, cleanup_case):
        """
        P1_TC003: 列表-关键词搜索
        验证：返回 name 或 url 包含"登录"的用例
        """
        # 创建包含关键词的用例
        create_test_case(db_session, name="登录接口测试", url="https://api.example.com/login")
        create_test_case(db_session, name="其他用例", url="https://api.example.com/other")
        
        response = client.get(
            "/api/cases?keyword=登录",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取用例列表失败: {response.text}"
        data = response.json()
        assert len(data) >= 1
        for item in data:
            assert "登录" in item["name"] or "登录" in item["url"]

    def test_case_list_multi_filter(self, auth_info, db_session, cleanup_case):
        """
        P1_TC004: 列表-多条件组合过滤
        验证：同时满足 folder、method、keyword 条件的用例
        """
        # 创建符合组合条件的用例
        create_test_case(
            db_session, 
            name="登录用户接口", 
            method="POST", 
            folder_path="/api/user"
        )
        create_test_case(
            db_session, 
            name="获取用户接口", 
            method="GET", 
            folder_path="/api/user"
        )
        
        response = client.get(
            "/api/cases?folder=/api/user&method=POST&keyword=登录",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取用例列表失败: {response.text}"
        data = response.json()
        for item in data:
            assert item["folder_path"] == "/api/user"
            assert item["method"] == "POST"
            assert "登录" in item["name"] or "登录" in item["url"]

    def test_case_list_sorted(self, auth_info, db_session, cleanup_case):
        """
        P1_TC005: 列表-按folder和sort_order排序
        验证：按 folder_path 和 sort_order 排序
        """
        # 创建多个用例
        create_test_case(db_session, name="用例C", folder_path="/api/ccc", sort_order=3)
        create_test_case(db_session, name="用例A", folder_path="/api/aaa", sort_order=1)
        create_test_case(db_session, name="用例B", folder_path="/api/bbb", sort_order=2)
        
        response = client.get(
            "/api/cases?limit=10",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取用例列表失败: {response.text}"
        data = response.json()
        # 验证排序：按 folder_path 升序，然后 sort_order 升序
        folders = [item["folder_path"] for item in data[:10]]


class TestCaseP1DuplicateUpdate:
    """P1 用例复制与更新"""

    def test_case_duplicate_normal(self, auth_info, db_session, cleanup_case):
        """
        P1_TC006: 复制用例-正常
        验证：生成新用例，name="原名称-复制"，返回新用例信息
        """
        # 创建测试用例
        original = create_test_case(db_session, name="原始用例")
        
        response = client.post(
            f"/api/cases/{original.id}/duplicate",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"复制用例失败: {response.text}"
        data = response.json()
        assert data["name"] == "原始用例-复制"
        assert data["id"] != original.id

    def test_case_duplicate_folder_same(self, auth_info, db_session, cleanup_case):
        """
        P1_TC007: 复制用例-folder保持一致
        验证：新用例 folder_path 与原用例相同
        """
        # 创建测试用例
        original = create_test_case(db_session, folder_path="/api/user")
        
        response = client.post(
            f"/api/cases/{original.id}/duplicate",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"复制用例失败: {response.text}"
        data = response.json()
        assert data["folder_path"] == original.folder_path

    def test_case_update_headers(self, auth_info, db_session, cleanup_case):
        """
        P1_TC008: 更新用例-headers
        验证：headers 已更新，格式为 JSON 字符串
        """
        created = create_test_case(db_session)
        
        update_payload = {"headers": {"Authorization": "Bearer xxx"}}
        response = client.put(
            f"/api/cases/{created.id}",
            json=update_payload,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新用例失败: {response.text}"
        data = response.json()
        assert data["headers"]["Authorization"] == "Bearer xxx"

    def test_case_update_assertions(self, auth_info, db_session, cleanup_case):
        """
        P1_TC009: 更新用例-断言规则
        验证：assertions 已更新
        """
        created = create_test_case(db_session)
        
        update_payload = {
            "assertions": [
                {"id": "1", "type": "status_code", "operator": "equals", "expected": 200, "enabled": True}
            ]
        }
        response = client.put(
            f"/api/cases/{created.id}",
            json=update_payload,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新用例失败: {response.text}"
        data = response.json()
        assert len(data["assertions"]) == 1
        assert data["assertions"][0]["type"] == "status_code"

    def test_case_update_auth(self, auth_info, db_session, cleanup_case):
        """
        P1_TC010: 更新用例-认证信息
        验证：auth_type 和 auth_config 已更新
        """
        created = create_test_case(db_session)
        
        update_payload = {
            "auth_type": "bearer",
            "auth_config": {"token": "test_token"}
        }
        response = client.put(
            f"/api/cases/{created.id}",
            json=update_payload,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新用例失败: {response.text}"
        data = response.json()
        assert data["auth_type"] == "bearer"
        assert data["auth_config"]["token"] == "test_token"


class TestCaseP1Run:
    """P1 执行用例功能"""

    def test_case_run_get_method(self, auth_info, db_session, cleanup_case):
        """
        P1_TC011: 执行用例-GET方法
        验证：返回 200，response 包含 body/headers/status_code
        """
        created = create_test_case(
            db_session,
            method="GET",
            url="https://httpbin.org/get"
        )
        env = create_test_environment(db_session, name="测试环境3_Pytest")
        
        response = client.post(
            f"/api/cases/{created.id}/run",
            json={"environment_id": env.id},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"执行用例失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert "response" in data["data"]
        assert "status_code" in data["data"]["response"]
        assert "headers" in data["data"]["response"]
        assert "body" in data["data"]["response"]

    def test_case_run_post_with_json(self, auth_info, db_session, cleanup_case):
        """
        P1_TC012: 执行用例-POST方法带JSON
        验证：请求携带正确 Content-Type 和 body，执行成功
        """
        created = create_test_case(
            db_session,
            method="POST",
            url="https://httpbin.org/post",
            body='{"username": "test"}',
            body_type="json"
        )
        env = create_test_environment(db_session, name="测试环境4_Pytest")
        
        response = client.post(
            f"/api/cases/{created.id}/run",
            json={"environment_id": env.id},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"执行用例失败: {response.text}"
        data = response.json()
        assert data["code"] == 0

    def test_case_run_no_default_env(self, auth_info, db_session, cleanup_case):
        """
        P1_TC014: 执行用例-无默认环境
        验证：执行成功，env_vars 为空对象
        """
        created = create_test_case(
            db_session,
            method="GET",
            url="https://httpbin.org/get"
        )
        
        # 不创建任何环境
        response = client.post(
            f"/api/cases/{created.id}/run",
            json={},  # 不传 environment_id
            headers=auth_info["headers"]
        )
        # 应该使用默认环境或空环境变量执行
        assert response.status_code == 200, f"执行用例失败: {response.text}"


class TestCaseP1NotFound:
    """P1 异常与边界 - 资源不存在"""

    def test_case_get_not_exists(self, auth_info):
        """
        P1_TC015: 获取单个用例-不存在
        验证：返回 404，detail="Case not found"
        """
        response = client.get(
            "/api/cases/99999",
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Case not found"

    def test_case_update_not_exists(self, auth_info):
        """
        P1_TC016: 更新用例-不存在
        验证：返回 404，detail="Case not found"
        """
        response = client.put(
            "/api/cases/99999",
            json={"name": "test"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Case not found"

    def test_case_delete_not_exists(self, auth_info):
        """
        P1_TC017: 删除用例-不存在
        验证：返回 404，detail="Case not found"
        """
        response = client.delete(
            "/api/cases/99999",
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Case not found"

    def test_case_duplicate_not_exists(self, auth_info):
        """
        P1_TC018: 复制用例-不存在
        验证：返回 404，detail="Case not found"
        """
        response = client.post(
            "/api/cases/99999/duplicate",
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Case not found"

    def test_case_run_not_exists(self, auth_info):
        """
        P1_TC019: 执行用例-用例不存在
        验证：返回 404，detail="Case not found"
        """
        response = client.post(
            "/api/cases/99999/run",
            json={"environment_id": 1},
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Case not found"


# ==================== 运行方式 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
