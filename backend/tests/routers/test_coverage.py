# -*- coding: utf-8 -*-
"""
代码覆盖率模块 API 测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import CoverageRecord, CodeRepository
from app.models.tenant import User, Tenant
from app.services.auth_service import AuthService


client = TestClient(app)


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """提供数据库会话，每个测试前清理覆盖率数据"""
    db = SessionLocal()
    # 测试前清理
    try:
        db.query(CoverageRecord).delete()
        db.query(CodeRepository).delete()
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
    tenant = db.query(Tenant).filter(Tenant.name == "测试租户_Pytest").first()
    if not tenant:
        tenant = Tenant(name="测试租户_Pytest", code="test_pytest", status="active")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    
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
    
    token = AuthService.create_access_token(user_id=user.id, tenant_id=tenant.id)
    return token, user.id, tenant.id


def get_auth_headers(token):
    """获取认证头"""
    return {"Authorization": f"Bearer {token}"}

def create_coverage_record(db, repository_id=1, commit_hash="abc123",
                          file_path="src/main.py", total_lines=100,
                          covered_lines=80, report_date=None):
    """创建覆盖率记录"""
    from datetime import date
    record = CoverageRecord(
        repository_id=repository_id,
        commit_hash=commit_hash,
        file_path=file_path,
        total_lines=total_lines,
        covered_lines=covered_lines,
        line_coverage=round(covered_lines / total_lines * 100, 2) if total_lines > 0 else 0,
        uncovered_lines='[]',
        branch_coverage=0,
        function_coverage=0,
        report_format="lcov",
        report_date=report_date or date.today(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_repository(db, name="测试仓库"):
    """创建代码仓库"""
    repo = CodeRepository(
        name=name,
        url="http://git.example.com/test",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


# ==================== 覆盖率汇总 ====================

class TestCoverageSummary:
    """覆盖率汇总接口"""

    def test_get_coverage_summary_no_data(self, db_session, auth_info):
        """获取覆盖率-无数据"""
        response = client.get("/api/coverage/summary", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["line_coverage"] == 0

    def test_get_coverage_summary_with_data(self, db_session, auth_info):
        """获取覆盖率-有数据"""
        create_coverage_record(db_session, total_lines=100, covered_lines=80)
        create_coverage_record(db_session, total_lines=50, covered_lines=40)

        response = client.get("/api/coverage/summary", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        # 总行数 150，覆盖 120，覆盖率 80%
        assert data["total_lines"] == 150
        assert data["covered_lines"] == 120
        assert data["line_coverage"] == 80.0

    def test_get_coverage_summary_by_repository(self, db_session, auth_info):
        """获取覆盖率-按仓库过滤"""
        create_coverage_record(db_session, repository_id=1, file_path="a.py")
        create_coverage_record(db_session, repository_id=2, file_path="b.py")

        response = client.get("/api/coverage/summary?repository_id=1", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["files"]) == 1
        assert "a.py" in data["files"][0]["file_path"]

    def test_get_coverage_summary_by_commit(self, db_session, auth_info):
        """获取覆盖率-按提交哈希过滤"""
        create_coverage_record(db_session, commit_hash="abc", file_path="a.py")
        create_coverage_record(db_session, commit_hash="def", file_path="b.py")

        response = client.get("/api/coverage/summary?commit_hash=abc", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["files"]) == 1


# ==================== 文件覆盖率列表 ====================

class TestFileCoverageList:
    """文件覆盖率列表"""

    def test_get_file_coverage_list(self, db_session, auth_info):
        """获取文件覆盖率列表"""
        repo = create_repository(db_session)
        create_coverage_record(db_session, repository_id=repo.id, file_path="a.py")
        create_coverage_record(db_session, repository_id=repo.id, file_path="b.py")

        response = client.get(f"/api/coverage/files?repository_id={repo.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

    def test_get_file_coverage_list_empty(self, db_session, auth_info):
        """获取文件覆盖率列表-无数据"""
        repo = create_repository(db_session)
        response = client.get(f"/api/coverage/files?repository_id={repo.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()["data"]
        assert data == []


# ==================== 覆盖率上传 ====================

class TestCoverageUpload:
    """覆盖率报告上传"""

    def test_upload_coverage_lcov_format(self, db_session, auth_info):
        """上传覆盖率-lcov格式"""
        repo = create_repository(db_session)

        lcov_content = """SF:src/app.py
DA:1,1
DA:2,1
DA:3,0
DA:4,1
end_of_record
SF:src/utils.py
DA:1,1
DA:2,0
end_of_record
"""
        from io import BytesIO
        files = {"file": ("coverage.lcov", BytesIO(lcov_content.encode()), "text/plain")}

        response = client.post(
            f"/api/coverage/upload?repository_id={repo.id}&commit_hash=abc123&report_format=lcov",
            files=files,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data["data"]
        assert data["data"]["summary"]["total_files"] == 2

    def test_upload_coverage_invalid_format(self, db_session, auth_info):
        """上传覆盖率-无效格式"""
        repo = create_repository(db_session)
        content = "invalid content"
        from io import BytesIO
        files = {"file": ("coverage.txt", BytesIO(content.encode()), "text/plain")}

        # 无效格式会回退到lcov解析
        response = client.post(
            f"/api/coverage/upload?repository_id={repo.id}&commit_hash=abc&report_format=unknown",
            files=files,
            headers=auth_info["headers"]
        )
        assert response.status_code == 200


# ==================== 覆盖率详情 ====================

class TestCoverageDetails:
    """覆盖率详情验证"""

    def test_coverage_percentage_calculation(self, db_session, auth_info):
        """覆盖率百分比计算"""
        create_coverage_record(db_session, total_lines=200, covered_lines=150)

        response = client.get("/api/coverage/summary", headers=auth_info["headers"])
        data = response.json()["data"]
        assert data["line_coverage"] == 75.0  # 150/200 = 75%

    def test_coverage_zero_lines(self, db_session, auth_info):
        """覆盖率-零行数"""
        create_coverage_record(db_session, total_lines=0, covered_lines=0)

        response = client.get("/api/coverage/summary", headers=auth_info["headers"])
        data = response.json()["data"]
        assert data["line_coverage"] == 0
        assert data["total_lines"] == 0


# ==================== 覆盖率记录关联 ====================

class TestCoverageAssociation:
    """覆盖率记录关联验证"""

    def test_coverage_repository_association(self, db_session, auth_info):
        """覆盖率-仓库关联"""
        repo1 = create_repository(db_session, "仓库1")
        repo2 = create_repository(db_session, "仓库2")

        create_coverage_record(db_session, repository_id=repo1.id, file_path="a.py")
        create_coverage_record(db_session, repository_id=repo2.id, file_path="b.py")

        response = client.get(f"/api/coverage/summary?repository_id={repo1.id}", headers=auth_info["headers"])
        data = response.json()["data"]
        assert len(data["files"]) == 1
        assert data["files"][0]["file_path"] == "a.py"

    def test_coverage_multiple_commits(self, db_session, auth_info):
        """覆盖率-多次提交"""
        create_coverage_record(db_session, commit_hash="v1", total_lines=100, covered_lines=80)
        create_coverage_record(db_session, commit_hash="v2", total_lines=100, covered_lines=90)

        response = client.get("/api/coverage/summary", headers=auth_info["headers"])
        data = response.json()["data"]
        # 返回所有记录
        assert data["total_lines"] == 200
