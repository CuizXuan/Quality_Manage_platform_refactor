# -*- coding: utf-8 -*-
"""
数据集模块 API 测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.dataset import DataSet, DataSetRow
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


def create_test_dataset(db, name="测试数据集", data_type="json", content=None):
    """创建测试数据集"""
    ds = DataSet(
        name=name,
        description="pytest创建",
        type=data_type,
        file_path="",
        content=content or "",
        headers="[]",
        row_count=0,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


def create_dataset_row(db, dataset_id, row_index=0, variables=None, enabled=True):
    """创建数据集行"""
    import json
    row = DataSetRow(
        dataset_id=dataset_id,
        row_index=row_index,
        variables=json.dumps(variables or {"key": "value"}),
        enabled=enabled,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """提供数据库会话，每个测试前清理数据集数据"""
    db = SessionLocal()
    # 测试前清理
    try:
        db.query(DataSetRow).delete()
        db.query(DataSet).delete()
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


# ==================== 数据集列表 ====================

class TestListDatasets:
    """获取数据集列表"""

    def test_list_datasets_empty(self, auth_info, db_session):
        """获取数据集列表-空数据库"""
        response = client.get("/api/datasets", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json() == []

    def test_list_datasets_multiple(self, auth_info, db_session):
        """获取数据集列表-多个数据集"""
        create_test_dataset(db_session, "数据集1")
        create_test_dataset(db_session, "数据集2")

        response = client.get("/api/datasets", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_datasets_keyword_filter(self, auth_info, db_session):
        """获取数据集列表-关键词过滤"""
        create_test_dataset(db_session, "用户数据集")
        create_test_dataset(db_session, "订单数据集")

        response = client.get("/api/datasets?keyword=用户", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "用户数据集"

    def test_list_datasets_pagination(self, auth_info, db_session):
        """数据集列表-分页"""
        for i in range(10):
            create_test_dataset(db_session, f"数据集{i}")

        response = client.get("/api/datasets?skip=0&limit=5", headers=auth_info["headers"])
        data = response.json()
        assert len(data) == 5

        response = client.get("/api/datasets?skip=5&limit=5", headers=auth_info["headers"])
        data = response.json()
        assert len(data) == 5


# ==================== 创建数据集 ====================

class TestCreateDataset:
    """创建数据集"""

    def test_create_dataset_json(self, auth_info, db_session):
        """创建数据集-JSON类型"""
        payload = {
            "name": "JSON数据集",
            "description": "测试JSON数据集",
            "type": "json",
            "content": '[{"id": 1, "name": "test1"}]',
        }
        response = client.post("/api/datasets", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "JSON数据集"
        assert data["type"] == "json"

    def test_create_dataset_csv(self, auth_info, db_session):
        """创建数据集-CSV类型"""
        payload = {
            "name": "CSV数据集",
            "type": "csv",
            "content": "id,name\n1,test1\n2,test2",
        }
        response = client.post("/api/datasets", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CSV数据集"

    def test_create_dataset_minimal(self, auth_info, db_session):
        """创建数据集-最小参数"""
        payload = {"name": "最小数据集"}
        response = client.post("/api/datasets", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "最小数据集"
        assert data["type"] == "csv"  # 默认类型


# ==================== 获取单个数据集 ====================

class TestGetDataset:
    """获取数据集详情"""

    def test_get_dataset_exists(self, auth_info, db_session):
        """获取数据集-存在"""
        ds = create_test_dataset(db_session, "目标数据集")

        response = client.get(f"/api/datasets/{ds.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "目标数据集"
        assert data["id"] == ds.id

    def test_get_dataset_not_exists(self, auth_info, db_session):
        """获取数据集-不存在"""
        response = client.get("/api/datasets/99999", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 更新数据集 ====================

class TestUpdateDataset:
    """更新数据集"""

    def test_update_dataset_name(self, auth_info, db_session):
        """更新数据集-名称"""
        ds = create_test_dataset(db_session, "原名")
        payload = {"name": "新名称"}

        response = client.put(f"/api/datasets/{ds.id}", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["name"] == "新名称"

    def test_update_dataset_content(self, auth_info, db_session):
        """更新数据集-内容"""
        ds = create_test_dataset(db_session, "内容数据集")
        payload = {"content": '{"updated": true}'}

        response = client.put(f"/api/datasets/{ds.id}", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["content"] == '{"updated": true}'


# ==================== 删除数据集 ====================

class TestDeleteDataset:
    """删除数据集"""

    def test_delete_dataset_success(self, auth_info, db_session):
        """删除数据集-正常"""
        ds = create_test_dataset(db_session, "待删除")

        response = client.delete(f"/api/datasets/{ds.id}", headers=auth_info["headers"])
        assert response.status_code == 200
        assert response.json()["code"] == 0

        response = client.get(f"/api/datasets/{ds.id}", headers=auth_info["headers"])
        assert response.status_code == 404

    def test_delete_dataset_not_exists(self, auth_info, db_session):
        """删除数据集-不存在"""
        response = client.delete("/api/datasets/99999", headers=auth_info["headers"])
        assert response.status_code == 404


# ==================== 数据集行操作 ====================

class TestDatasetRows:
    """数据集行CRUD"""

    def test_list_dataset_rows(self, auth_info, db_session):
        """获取数据集行列表"""
        ds = create_test_dataset(db_session)
        create_dataset_row(db_session, ds.id, 0, {"a": 1})
        create_dataset_row(db_session, ds.id, 1, {"b": 2})

        response = client.get(f"/api/datasets/{ds.id}/rows", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_dataset_rows_enabled_only(self, auth_info, db_session):
        """获取数据集行-仅启用"""
        ds = create_test_dataset(db_session)
        create_dataset_row(db_session, ds.id, 0, {"a": 1}, enabled=True)
        create_dataset_row(db_session, ds.id, 1, {"b": 2}, enabled=False)
        create_dataset_row(db_session, ds.id, 2, {"c": 3}, enabled=True)

        response = client.get(f"/api/datasets/{ds.id}/rows?enabled_only=true", headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_create_dataset_row(self, auth_info, db_session):
        """创建数据集行"""
        ds = create_test_dataset(db_session)
        payload = {
            "row_index": 0,
            "variables": {"username": "test", "password": "***"},
            "enabled": True,
        }

        response = client.post(f"/api/datasets/{ds.id}/rows", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["row_index"] == 0
        assert data["variables"]["username"] == "test"

        # 验证row_count更新
        db_session.refresh(ds)
        assert ds.row_count == 1

    def test_create_dataset_row_dataset_not_exists(self, auth_info, db_session):
        """创建数据集行-数据集不存在"""
        payload = {"row_index": 0, "variables": {}, "enabled": True}
        response = client.post("/api/datasets/99999/rows", json=payload, headers=auth_info["headers"])
        assert response.status_code == 404

    def test_update_dataset_row(self, auth_info, db_session):
        """更新数据集行"""
        ds = create_test_dataset(db_session)
        row = create_dataset_row(db_session, ds.id, 0, {"old": "value"})

        payload = {"row_index": 5, "variables": {"new": "value"}, "enabled": False}
        response = client.put(f"/api/datasets/{ds.id}/rows/{row.id}", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["row_index"] == 5
        assert data["variables"]["new"] == "value"
        assert data["enabled"] == False

    def test_delete_dataset_row(self, auth_info, db_session):
        """删除数据集行"""
        ds = create_test_dataset(db_session)
        row1 = create_dataset_row(db_session, ds.id, 0)
        row2 = create_dataset_row(db_session, ds.id, 1)

        response = client.delete(f"/api/datasets/{ds.id}/rows/{row1.id}", headers=auth_info["headers"])
        assert response.status_code == 200

        # 验证row_count更新
        db_session.refresh(ds)
        assert ds.row_count == 1

        # 验证只剩一行
        response = client.get(f"/api/datasets/{ds.id}/rows", headers=auth_info["headers"])
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == row2.id


# ==================== 数据导入 ====================

class TestImportData:
    """导入数据到数据集"""

    def test_import_json(self, auth_info, db_session):
        """导入JSON数据"""
        ds = create_test_dataset(db_session)
        payload = {
            "name": "测试",
            "type": "json",
            "content": '[{"id": 1}, {"id": 2}, {"id": 3}]',
        }

        response = client.post(f"/api/datasets/{ds.id}/import", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "imported 3 rows" in data["message"]

        # 验证行数据
        response = client.get(f"/api/datasets/{ds.id}/rows", headers=auth_info["headers"])
        rows = response.json()
        assert len(rows) == 3

    def test_import_csv(self, auth_info, db_session):
        """导入CSV数据"""
        ds = create_test_dataset(db_session)
        payload = {
            "name": "测试",
            "type": "csv",
            "content": "id,name\n1,Alice\n2,Bob",
        }

        response = client.post(f"/api/datasets/{ds.id}/import", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert "imported 2 rows" in data["message"]

    def test_import_invalid_json(self, auth_info, db_session):
        """导入无效JSON"""
        ds = create_test_dataset(db_session)
        payload = {
            "name": "测试",
            "type": "json",
            "content": "not valid json",
        }

        response = client.post(f"/api/datasets/{ds.id}/import", json=payload, headers=auth_info["headers"])
        assert response.status_code == 400

    def test_import_replaces_existing_rows(self, auth_info, db_session):
        """导入会替换现有行"""
        ds = create_test_dataset(db_session)
        create_dataset_row(db_session, ds.id, 0)  # 旧行

        payload = {
            "name": "测试",
            "type": "json",
            "content": '[{"id": "new"}]',
        }
        response = client.post(f"/api/datasets/{ds.id}/import", json=payload, headers=auth_info["headers"])

        # 验证只有新行
        response = client.get(f"/api/datasets/{ds.id}/rows", headers=auth_info["headers"])
        rows = response.json()
        assert len(rows) == 1
        assert rows[0]["variables"]["id"] == "new"


# ==================== 数据集测试 ====================

class TestDatasetTest:
    """数据驱动测试"""

    def test_dataset_test_endpoint(self, auth_info, db_session):
        """数据集测试端点"""
        ds = create_test_dataset(db_session)
        create_dataset_row(db_session, ds.id, 0, {"var1": "a"}, enabled=True)
        create_dataset_row(db_session, ds.id, 1, {"var1": "b"}, enabled=True)

        payload = {"environment_id": None}
        response = client.post(f"/api/datasets/{ds.id}/test", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["row_count"] == 2

    def test_dataset_test_specific_rows(self, auth_info, db_session):
        """数据集测试-指定行"""
        ds = create_test_dataset(db_session)
        create_dataset_row(db_session, ds.id, 0, {"var1": "a"}, enabled=True)
        create_dataset_row(db_session, ds.id, 1, {"var1": "b"}, enabled=True)
        create_dataset_row(db_session, ds.id, 2, {"var1": "c"}, enabled=True)

        payload = {"environment_id": None, "row_indices": [0, 2]}
        response = client.post(f"/api/datasets/{ds.id}/test", json=payload, headers=auth_info["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 2  # 只测试第0和第2行
