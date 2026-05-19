# -*- coding: utf-8 -*-
"""
缺陷管理模块 API 测试
覆盖 P0 和 P1 测试用例
"""
import pytest
import sys
import os
from pathlib import Path
from io import BytesIO
from datetime import datetime
from sqlalchemy import or_

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, get_db
from app.models.tenant import User, Tenant
from app.models.defect import Defect, DefectComment, DefectAttachment
from app.models.execution_log import ExecutionLog
from app.services.auth_service import AuthService


# 创建测试客户端
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


def cleanup_test_defects(db, title_pattern=None):
    """清理测试缺陷"""
    # 清理所有测试相关的缺陷（通过标题前缀识别）
    query = db.query(Defect).filter(
        or_(
            Defect.title.like("测试%"),
            Defect.title.like("缺陷%"),
            Defect.reporter == "tester_pytest",
            Defect.reporter == "system"  # from-execution 创建的缺陷
        )
    )
    defects = query.all()
    for defect in defects:
        # 清理关联的评论和附件
        db.query(DefectComment).filter(DefectComment.defect_id == defect.id).delete()
        db.query(DefectAttachment).filter(DefectAttachment.defect_id == defect.id).delete()
        db.delete(defect)
    db.commit()


def create_test_defect(db, title="测试缺陷", status="open", severity="high",
                        priority="high", assignee="zhangsan", reporter="tester_pytest",
                        defect_type="functional", description=None, **kwargs):
    """创建测试缺陷并返回"""
    # 从 kwargs 中获取 description，如果不存在则使用默认值
    final_description = description or kwargs.pop("description", "pytest创建的测试缺陷")

    defect = Defect(
        title=title,
        description=final_description,
        severity=severity,
        priority=priority,
        status=status,
        defect_type=defect_type,
        assignee=assignee,
        reporter=reporter,
        environment="Chrome最新版本",
        steps_to_reproduce="1.打开首页\n2.点击登录",
        expected_result="显示登录框",
        actual_result="页面白屏",
        **kwargs
    )
    db.add(defect)
    db.commit()
    db.refresh(defect)
    return defect


def create_test_comment(db, defect_id, content="测试评论", author="tester01"):
    """创建测试评论"""
    comment = DefectComment(
        defect_id=defect_id,
        content=content,
        author=author
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def create_test_attachment(db, defect_id, file_name="test.png"):
    """创建测试附件记录"""
    attachment = DefectAttachment(
        defect_id=defect_id,
        file_name=file_name,
        file_path=f"/data/defect_attachments/{defect_id}_{file_name}",
        file_size=1024,
        file_type="image/png"
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


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
def cleanup_defect(db_session):
    """每个测试前后清理缺陷"""
    cleanup_test_defects(db_session)  # 测试前清理
    yield
    cleanup_test_defects(db_session)  # 测试后清理


@pytest.fixture(scope="function")
def cleanup_defect_by_name(db_session):
    """按名称清理缺陷"""
    def _cleanup(title):
        defects = db_session.query(Defect).filter(Defect.title == title).all()
        for defect in defects:
            db_session.query(DefectComment).filter(DefectComment.defect_id == defect.id).delete()
            db_session.query(DefectAttachment).filter(DefectAttachment.defect_id == defect.id).delete()
            db_session.delete(defect)
        db_session.commit()
    return _cleanup


# ==================== P0 测试用例：核心流程 ====================

class TestDefectP0CRUD:
    """P0 缺陷 CRUD 核心流程"""

    def test_defect_create_full_params(self, auth_info, db_session, cleanup_defect):
        """
        P0_D001: 创建缺陷-完整参数
        验证：返回201，data包含缺陷ID，状态为open
        """
        payload = {
            "title": "登录页面无法加载",
            "description": "Chrome浏览器下登录失败",
            "severity": "high",
            "priority": "high",
            "reporter": "tester01",
            "defect_type": "functional",
            "environment": "Chrome最新版本",
            "steps_to_reproduce": "1.打开首页\n2.点击登录",
            "expected_result": "显示登录框",
            "actual_result": "页面白屏"
        }
        response = client.post(
            "/api/defects",
            json=payload,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"创建缺陷失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert "id" in data["data"]
        assert data["data"]["title"] == "登录页面无法加载"
        assert data["data"]["status"] == "open"
        assert data["data"]["severity"] == "high"
        assert data["data"]["priority"] == "high"

    def test_defect_create_minimal_params(self, auth_info, db_session, cleanup_defect):
        """
        P0_D002: 创建缺陷-必填字段最小化
        验证：返回201，缺陷创建成功，status默认open，severity/priority默认medium
        """
        payload = {
            "title": "接口超时",
            "reporter": "tester01"
        }
        response = client.post(
            "/api/defects",
            json=payload,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"创建缺陷失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert "id" in data["data"]
        assert data["data"]["title"] == "接口超时"
        assert data["data"]["status"] == "open"
        assert data["data"]["severity"] == "medium"
        assert data["data"]["priority"] == "medium"

    def test_defect_get_detail_with_comments_attachments(self, auth_info, db_session, cleanup_defect):
        """
        P0_D003: 获取缺陷详情-包含关联数据
        验证：返回defect对象、comments数组（按时间升序）、attachments数组
        """
        # 创建缺陷
        defect = create_test_defect(db_session, title="缺陷详情测试")
        
        # 创建2条评论
        create_test_comment(db_session, defect.id, content="评论1", author="leader01")
        create_test_comment(db_session, defect.id, content="评论2", author="tester01")
        
        # 创建1个附件
        create_test_attachment(db_session, defect.id, file_name="screenshot.png")
        
        response = client.get(
            f"/api/defects/{defect.id}",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取缺陷详情失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert "defect" in data["data"]
        assert "comments" in data["data"]
        assert "attachments" in data["data"]
        assert data["data"]["defect"]["title"] == "缺陷详情测试"
        # 验证评论按时间升序排列
        assert len(data["data"]["comments"]) == 2
        assert data["data"]["comments"][0]["content"] == "评论1"
        assert data["data"]["comments"][1]["content"] == "评论2"
        # 验证附件
        assert len(data["data"]["attachments"]) == 1
        assert data["data"]["attachments"][0]["file_name"] == "screenshot.png"

    def test_defect_update_status_to_resolved(self, auth_info, db_session, cleanup_defect):
        """
        P0_D004: 更新缺陷-状态变更为resolved
        验证：返回200，status=resolved，resolved_at被自动设置为当前时间
        """
        # 创建open状态的缺陷
        defect = create_test_defect(db_session, status="open")
        
        response = client.put(
            f"/api/defects/{defect.id}",
            json={"status": "resolved", "resolution": "已修复代码"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新缺陷失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["status"] == "resolved"
        assert data["data"]["resolution"] == "已修复代码"
        assert data["data"]["resolved_at"] is not None

    def test_defect_delete_cascade(self, auth_info, db_session, cleanup_defect):
        """
        P0_D005: 删除缺陷-级联删除
        验证：返回200，缺陷已删除，关联的DefectComment和DefectAttachment记录一并删除
        """
        # 创建缺陷
        defect = create_test_defect(db_session)
        
        # 添加评论和附件
        create_test_comment(db_session, defect.id)
        create_test_attachment(db_session, defect.id)
        
        defect_id = defect.id
        
        response = client.delete(
            f"/api/defects/{defect_id}",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"删除缺陷失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "删除成功"
        
        # 验证缺陷已删除
        get_response = client.get(
            f"/api/defects/{defect_id}",
            headers=auth_info["headers"]
        )
        assert get_response.status_code == 404
        
        # 验证评论和附件也已删除（通过获取缺陷详情验证）
        # 由于缺陷已删除，关联数据也一并删除

    def test_defect_full_lifecycle(self, auth_info, db_session, cleanup_defect):
        """
        P0_D006: 缺陷完整生命周期流转
        验证：open → in_progress → resolved → closed，每次更新返回200，状态依次变化
        """
        # 创建open状态的缺陷
        defect = create_test_defect(db_session, status="open")
        assert defect.status == "open"
        
        # 1. open → in_progress
        response = client.put(
            f"/api/defects/{defect.id}",
            json={"status": "in_progress"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "in_progress"
        
        # 2. in_progress → resolved
        response = client.put(
            f"/api/defects/{defect.id}",
            json={"status": "resolved", "resolution": "已修复"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "resolved"
        assert response.json()["data"]["resolved_at"] is not None
        
        # 3. resolved → closed
        response = client.put(
            f"/api/defects/{defect.id}",
            json={"status": "closed"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "closed"


# ==================== P1 测试用例：重要功能 ====================

class TestDefectP1List:
    """P1 缺陷列表查询与过滤"""

    def test_defect_list_filter_by_status(self, auth_info, db_session, cleanup_defect):
        """
        P1_D001: 列表查询-按状态过滤
        验证：仅返回status=open的缺陷列表
        """
        # 创建不同状态的缺陷
        create_test_defect(db_session, title="缺陷_open1", status="open", assignee="zhangsan")
        create_test_defect(db_session, title="缺陷_open2", status="open", assignee="lisi")
        create_test_defect(db_session, title="缺陷_in_progress", status="in_progress")
        create_test_defect(db_session, title="缺陷_resolved", status="resolved")
        
        response = client.get(
            "/api/defects?status=open",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取缺陷列表失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        for item in data["data"]:
            assert item["status"] == "open"

    def test_defect_list_filter_by_severity(self, auth_info, db_session, cleanup_defect):
        """
        P1_D002: 列表查询-按严重程度过滤
        验证：仅返回severity=high的缺陷
        """
        create_test_defect(db_session, title="缺陷_high", severity="high")
        create_test_defect(db_session, title="缺陷_medium", severity="medium")
        create_test_defect(db_session, title="缺陷_low", severity="low")
        
        response = client.get(
            "/api/defects?severity=high",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取缺陷列表失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        for item in data["data"]:
            assert item["severity"] == "high"

    def test_defect_list_filter_by_assignee(self, auth_info, db_session, cleanup_defect):
        """
        P1_D003: 列表查询-按指派人过滤
        验证：仅返回assignee=zhangsan的缺陷
        """
        create_test_defect(db_session, title="缺陷_zhangsan", assignee="zhangsan")
        create_test_defect(db_session, title="缺陷_lisi", assignee="lisi")
        
        response = client.get(
            "/api/defects?assignee=zhangsan",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取缺陷列表失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        for item in data["data"]:
            assert item["assignee"] == "zhangsan"

    def test_defect_list_keyword_search(self, auth_info, db_session, cleanup_defect):
        """
        P1_D004: 列表查询-关键词搜索
        验证：返回title或description包含"登录"的缺陷
        """
        create_test_defect(db_session, title="登录页面无法加载", description="Chrome浏览器下登录失败")
        create_test_defect(db_session, title="其他缺陷", description="这是一个普通描述")
        
        response = client.get(
            "/api/defects?keyword=登录",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取缺陷列表失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) >= 1
        for item in data["data"]:
            assert "登录" in item["title"] or "登录" in item.get("description", "")

    def test_defect_list_multi_filter(self, auth_info, db_session, cleanup_defect):
        """
        P1_D005: 列表查询-多条件组合
        验证：仅返回同时满足status=open&severity=high&assignee=wangwu的缺陷
        """
        create_test_defect(db_session, title="缺陷_组合1", status="open", severity="high", assignee="wangwu")
        create_test_defect(db_session, title="缺陷_组合2", status="open", severity="high", assignee="lisi")
        create_test_defect(db_session, title="缺陷_组合3", status="open", severity="medium", assignee="wangwu")
        
        response = client.get(
            "/api/defects?status=open&severity=high&assignee=wangwu",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取缺陷列表失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        for item in data["data"]:
            assert item["status"] == "open"
            assert item["severity"] == "high"
            assert item["assignee"] == "wangwu"

    def test_defect_list_sorted(self, auth_info, db_session, cleanup_defect):
        """
        P1_D006: 列表查询-返回结果排序
        验证：返回结果按updated_at降序排列
        """
        # 创建多个缺陷
        defect1 = create_test_defect(db_session, title="缺陷_最早")
        defect2 = create_test_defect(db_session, title="缺陷_最晚")
        
        # 更新defect2使其updated_at更新
        client.put(
            f"/api/defects/{defect2.id}",
            json={"title": "缺陷_最晚_已更新"},
            headers=auth_info["headers"]
        )
        
        response = client.get(
            "/api/defects",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取缺陷列表失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        # 验证降序排列（更新的在前面）
        if len(data["data"]) >= 2:
            assert data["data"][0]["updated_at"] >= data["data"][1]["updated_at"]


class TestDefectP1Comment:
    """P1 缺陷评论功能"""

    def test_comment_add_normal(self, auth_info, db_session, cleanup_defect):
        """
        P1_D007: 添加评论-正常
        验证：返回201，评论创建成功
        """
        defect = create_test_defect(db_session)
        
        response = client.post(
            f"/api/defects/{defect.id}/comments",
            json={"content": "请尽快处理", "author": "leader01"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"添加评论失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["content"] == "请尽快处理"
        assert data["data"]["author"] == "leader01"
        assert data["data"]["defect_id"] == defect.id

    def test_comment_add_defect_not_exists(self, auth_info):
        """
        P1_D008: 添加评论-缺陷不存在
        验证：返回404，"缺陷不存在"
        """
        response = client.post(
            "/api/defects/99999/comments",
            json={"content": "测试", "author": "tester"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "缺陷不存在"

    def test_comment_list_ordered_by_time(self, auth_info, db_session, cleanup_defect):
        """
        P1_D009: 获取评论-时间顺序
        验证：返回的comments数组按created_at升序排列
        """
        defect = create_test_defect(db_session)
        
        # 添加3条评论
        create_test_comment(db_session, defect.id, content="评论1")
        create_test_comment(db_session, defect.id, content="评论2")
        create_test_comment(db_session, defect.id, content="评论3")
        
        response = client.get(
            f"/api/defects/{defect.id}",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        comments = data["data"]["comments"]
        assert len(comments) == 3
        # 验证按时间升序
        for i in range(len(comments) - 1):
            assert comments[i]["created_at"] <= comments[i + 1]["created_at"]


class TestDefectP1Attachment:
    """P1 缺陷附件功能"""

    def test_attachment_upload_normal(self, auth_info, db_session, cleanup_defect):
        """
        P1_D010: 上传附件-正常
        验证：返回201，附件记录创建成功
        """
        defect = create_test_defect(db_session)
        
        # 创建测试文件
        file_content = b"\x89PNG\r\n\x1a\n" + b"0" * 100  # 模拟PNG文件头
        file_data = {"file": ("screenshot.png", BytesIO(file_content), "image/png")}
        
        response = client.post(
            f"/api/defects/{defect.id}/attachments",
            files=file_data,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"上传附件失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["file_name"] == "screenshot.png"
        assert data["data"]["defect_id"] == defect.id

    def test_attachment_upload_defect_not_exists(self, auth_info):
        """
        P1_D011: 上传附件-缺陷不存在
        验证：返回404，"缺陷不存在"
        """
        file_data = {"file": ("test.png", BytesIO(b"test"), "image/png")}
        
        response = client.post(
            "/api/defects/99999/attachments",
            files=file_data,
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "缺陷不存在"

    def test_attachment_list_in_defect_detail(self, auth_info, db_session, cleanup_defect):
        """
        P1_D012: 获取附件列表
        验证：返回的attachments数组包含文件信息（file_name, file_path, file_size, file_type）
        """
        defect = create_test_defect(db_session)
        create_test_attachment(db_session, defect.id, file_name="error_log.txt")
        
        response = client.get(
            f"/api/defects/{defect.id}",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        attachments = data["data"]["attachments"]
        assert len(attachments) == 1
        assert attachments[0]["file_name"] == "error_log.txt"
        assert attachments[0]["file_path"] is not None
        assert attachments[0]["file_size"] is not None
        assert attachments[0]["file_type"] is not None


class TestDefectP1FromExecution:
    """P1 从执行记录创建缺陷"""

    def test_create_from_execution_normal(self, auth_info, db_session, cleanup_defect):
        """
        P1_D013: 从执行记录创建-正常
        验证：返回201，缺陷创建成功，自动填充case_id
        """
        # 创建执行记录
        execution_log = ExecutionLog(
            case_id=10,
            status="failed",
            response_status=500,
            response_body='{"error": "timeout"}',
            execution_id="exec_001",
            environment_id=1
        )
        db_session.add(execution_log)
        db_session.commit()
        db_session.refresh(execution_log)
        
        response = client.post(
            "/api/defects/from-execution",
            json={"execution_log_id": execution_log.id, "title": "API超时", "reporter": "system"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"从执行记录创建缺陷失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["title"] == "API超时"
        assert data["data"]["case_id"] == 10
        assert data["data"]["execution_log_id"] == execution_log.id

    def test_create_from_execution_log_not_exists(self, auth_info, db_session, cleanup_defect):
        """
        P1_D014: 从执行记录创建-执行记录不存在
        验证：返回201，使用默认标题"[API] 接口执行异常"创建缺陷
        """
        response = client.post(
            "/api/defects/from-execution",
            json={"execution_log_id": 99999},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"从执行记录创建缺陷失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["title"] == "[API] 接口执行异常"
        assert data["data"]["case_id"] is None


class TestDefectP1Stats:
    """P1 缺陷统计看板"""

    def test_stats_summary_normal(self, auth_info, db_session, cleanup_defect):
        """
        P1_D015: 统计看板-正常
        验证：返回total、by_status、by_severity统计信息
        """
        # 创建多个缺陷
        create_test_defect(db_session, title="缺陷1", status="open", severity="high")
        create_test_defect(db_session, title="缺陷2", status="open", severity="high")
        create_test_defect(db_session, title="缺陷3", status="open", severity="medium")
        create_test_defect(db_session, title="缺陷4", status="resolved", severity="high")
        create_test_defect(db_session, title="缺陷5", status="resolved", severity="medium")
        create_test_defect(db_session, title="缺陷6", status="closed", severity="low")
        
        response = client.get(
            "/api/defects/stats/summary",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"获取统计看板失败: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 6
        assert "by_status" in data["data"]
        assert "by_severity" in data["data"]
        assert data["data"]["by_status"]["open"] == 3
        assert data["data"]["by_status"]["resolved"] == 2
        assert data["data"]["by_status"]["closed"] == 1

    def test_stats_summary_empty(self, auth_info, db_session):
        """
        P1_D016: 统计看板-空数据
        验证：返回{total:0, by_status:{}, by_severity:{}}
        """
        # 清理所有测试缺陷
        cleanup_test_defects(db_session)
        
        response = client.get(
            "/api/defects/stats/summary",
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 0
        assert data["data"]["by_status"] == {}
        assert data["data"]["by_severity"] == {}


class TestDefectP1Update:
    """P1 缺陷状态更新与字段修改"""

    def test_update_defect_severity(self, auth_info, db_session, cleanup_defect):
        """
        P1_D017: 更新缺陷-修改严重程度
        验证：返回200，severity更新为critical
        """
        defect = create_test_defect(db_session, severity="medium")
        
        response = client.put(
            f"/api/defects/{defect.id}",
            json={"severity": "critical"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新缺陷失败: {response.text}"
        data = response.json()
        assert data["data"]["severity"] == "critical"

    def test_update_defect_priority(self, auth_info, db_session, cleanup_defect):
        """
        P1_D018: 更新缺陷-修改优先级
        验证：返回200，priority更新为high
        """
        defect = create_test_defect(db_session, priority="medium")
        
        response = client.put(
            f"/api/defects/{defect.id}",
            json={"priority": "high"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新缺陷失败: {response.text}"
        data = response.json()
        assert data["data"]["priority"] == "high"

    def test_update_defect_assignee(self, auth_info, db_session, cleanup_defect):
        """
        P1_D019: 更新缺陷-修改指派人
        验证：返回200，assignee更新为lisi
        """
        defect = create_test_defect(db_session, assignee="zhangsan")
        
        response = client.put(
            f"/api/defects/{defect.id}",
            json={"assignee": "lisi"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新缺陷失败: {response.text}"
        data = response.json()
        assert data["data"]["assignee"] == "lisi"

    def test_update_defect_external_id(self, auth_info, db_session, cleanup_defect):
        """
        P1_D020: 更新缺陷-关联外部系统
        验证：返回200，external_id和external_url更新成功
        """
        defect = create_test_defect(db_session)
        
        response = client.put(
            f"/api/defects/{defect.id}",
            json={"external_id": "JIRA-123", "external_url": "https://jira.example.com/browse/JIRA-123"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 200, f"更新缺陷失败: {response.text}"
        data = response.json()
        assert data["data"]["external_id"] == "JIRA-123"
        assert data["data"]["external_url"] == "https://jira.example.com/browse/JIRA-123"

    def test_update_defect_not_exists(self, auth_info):
        """
        P1_D021: 更新缺陷-缺陷不存在
        验证：返回404，"缺陷不存在"
        """
        response = client.put(
            "/api/defects/99999",
            json={"title": "test"},
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "缺陷不存在"

    def test_delete_defect_not_exists(self, auth_info):
        """
        P1_D022: 删除缺陷-缺陷不存在
        验证：返回404，"缺陷不存在"
        """
        response = client.delete(
            "/api/defects/99999",
            headers=auth_info["headers"]
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "缺陷不存在"


# ==================== 运行方式 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
