"""
API Asset Service 测试
关键路径测试：OpenAPI 导入、get_debug_payload、generate_case_from_api
"""

import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all models to resolve relationship references before Base.metadata.create_all
from app.models.base import Base
from app.models.api_asset import ApiGroup, ApiDefinition, ApiImportRecord
from app.models.test_case import TestCase
from app.models.api_test_case import ApiTestCase
from app.models.platform import Organization, PlatformUser, PlatformRole, PlatformMenu, PlatformPermission, PlatformUserRole
from app.models.terminal import DebugRequest, DebugResult
from app.models.case_folder import CaseFolder
from app.models.functional_test_case import FunctionalTestCase
from app.models.dictionary import DictType, DictItem
from app.models.docgen import DocGenerationTask, DocGenerationRule, DocGenerationTemplate
from app.models.quality_foundation import QualityProject, QualityVersion, QualityIteration, RequirementItem
from app.models.report import Defect
from app.models.scenario import Scenario, ScenarioStep, ExecutionRun

import app.services.api_asset_service as svc


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return create_engine("sqlite:///:memory:", echo=False)


@pytest.fixture
def session(engine):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ── OpenAPI Import Tests ───────────────────────────────────────────────────────

class TestOpenApiImport:
    """测试 import_openapi 生成分组和 API 定义"""

    def test_import_creates_group_and_apis(self, session):
        """导入最小 OpenAPI JSON 后生成分组和 API 定义"""
        raw_content = json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Pet Store API"},
            "paths": {
                "/pets": {
                    "get": {
                        "summary": "List pets",
                        "tags": ["pets"],
                        "parameters": [
                            {"name": "limit", "in": "query", "description": "max results", "schema": {"type": "integer"}}
                        ],
                        "responses": {"200": {"description": "OK"}}
                    },
                    "post": {
                        "summary": "Create a pet",
                        "tags": ["pets"],
                        "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                        "responses": {"201": {"description": "Created"}}
                    }
                },
                "/store/order": {
                    "post": {
                        "summary": "Place order",
                        "tags": ["store"],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        })

        result = svc.import_openapi(
            session,
            source_type="json",
            raw_content=raw_content,
            project_id=None,
        )

        assert result["imported"] == 3
        assert result["skipped"] == 0
        # root + pets + store = 3 groups
        assert result["groups_created"] == 3

        groups = session.query(ApiGroup).all()
        assert len(groups) >= 2

        apis = session.query(ApiDefinition).all()
        assert len(apis) == 3

        # Verify one API has correct fields
        pet_api = session.query(ApiDefinition).filter(ApiDefinition.path == "/pets").first()
        assert pet_api is not None
        assert pet_api.method == "GET"
        assert pet_api.name == "List pets"
        # parameters should be stored as JSON string
        params = json.loads(pet_api.parameters)
        assert isinstance(params, list)

    def test_import_skips_invalid_methods(self, session):
        """无效 HTTP 方法被过滤（不计入 skipped，skipped 只统计 operation 非 dict 的情况）"""
        raw_content = json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Test API"},
            "paths": {
                "/valid": {"get": {"summary": "Valid", "responses": {"200": {}}}},
                "/broken": {"get": "not-a-dict"}
            }
        })

        result = svc.import_openapi(session, source_type="json", raw_content=raw_content)

        assert result["imported"] == 1
        assert result["skipped"] == 1  # /broken operation is not a dict

    def test_import_creates_nested_groups_by_tag(self, session):
        """按 tag 分组，子分组挂在根分组下"""
        raw_content = json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Multi Service"},
            "paths": {
                "/users": {"get": {"summary": "Get Users", "tags": ["users"], "responses": {"200": {}}}},
                "/orders": {"get": {"summary": "Get Orders", "tags": ["orders"], "responses": {"200": {}}}},
            }
        })

        result = svc.import_openapi(session, source_type="json", raw_content=raw_content)

        groups = session.query(ApiGroup).order_by(ApiGroup.sort_order).all()
        assert len(groups) == 3  # root + users + orders

        root = session.query(ApiGroup).filter(ApiGroup.name == "Multi Service").first()
        users_group = session.query(ApiGroup).filter(ApiGroup.name == "users").first()
        assert users_group.parent_id == root.id


# ── get_debug_payload Tests ─────────────────────────────────────────────────────

class TestGetDebugPayload:
    """测试 get_debug_payload 返回完整的调试参数"""

    def test_returns_method_url_headers(self, session):
        """返回 method、url、headers"""
        group = ApiGroup(name="Test Group")
        session.add(group)
        session.commit()

        api = ApiDefinition(
            group_id=group.id,
            name="Test API",
            method="POST",
            path="/api/v1/resource",
            base_url="https://api.example.com",
            parameters=json.dumps([
                {"name": "X-API-Key", "in": "header", "default": "test-key-123"},
                {"name": "X-Request-ID", "in": "header", "default": ""},
            ]),
            request_body=json.dumps({}),
            status="active",
        )
        session.add(api)
        session.commit()

        payload = svc.get_debug_payload(session, api.id)

        assert payload is not None
        assert payload["method"] == "POST"
        assert payload["url"] == "https://api.example.com/api/v1/resource"
        assert payload["headers"]["X-API-Key"] == "test-key-123"
        assert payload["body_type"] == "none"

    def test_extracts_query_params(self, session):
        """提取 query 参数"""
        group = ApiGroup(name="Qry Group")
        session.add(group)
        session.commit()

        api = ApiDefinition(
            group_id=group.id,
            name="Query API",
            method="GET",
            path="/api/search",
            parameters=json.dumps([
                {"name": "q", "in": "query", "default": "keyword"},
                {"name": "page", "in": "query", "default": "1"},
                {"name": "X-Header", "in": "header", "default": "hval"},
            ]),
            request_body=json.dumps({}),
            status="active",
        )
        session.add(api)
        session.commit()

        payload = svc.get_debug_payload(session, api.id)

        assert payload["query_params"]["q"] == "keyword"
        assert payload["query_params"]["page"] == "1"
        assert "X-Header" not in payload["query_params"]  # header not in query_params

    def test_extracts_json_body_from_openapi_spec(self, session):
        """从 OpenAPI requestBody 提取 JSON body 示例"""
        group = ApiGroup(name="Body Group")
        session.add(group)
        session.commit()

        api = ApiDefinition(
            group_id=group.id,
            name="Body API",
            method="POST",
            path="/api/v1/items",
            parameters=json.dumps([]),
            request_body=json.dumps({
                "content": {
                    "application/json": {
                        "example": {"name": "item1", "price": 100}
                    }
                }
            }),
            status="active",
        )
        session.add(api)
        session.commit()

        payload = svc.get_debug_payload(session, api.id)

        assert payload["body_type"] == "json"
        body = json.loads(payload["body"])
        assert body["name"] == "item1"

    def test_returns_none_for_missing_api(self, session):
        """不存在的 API 返回 None"""
        result = svc.get_debug_payload(session, 99999)
        assert result is None


# ── generate_case_from_api Tests ─────────────────────────────────────────────

class TestGenerateCaseFromApi:
    """测试 generate_case_from_api 创建 TestCase 和 ApiTestCase"""

    def test_creates_test_case_with_api_case(self, session):
        """从 ApiDefinition 生成测试用例，并关联 ApiTestCase"""
        group = ApiGroup(name="Gen Group")
        session.add(group)
        session.commit()

        api = ApiDefinition(
            group_id=group.id,
            name="Generate Me",
            method="POST",
            path="/api/v1/generate",
            base_url="https://api.gen.com",
            summary="生成接口",
            description="用于生成测试的接口",
            parameters=json.dumps([
                {"name": "q", "in": "query", "default": "test"},
                {"name": "X-Token", "in": "header", "default": "tok123"},
            ]),
            request_body=json.dumps({
                "content": {
                    "application/json": {
                        "example": {"username": "tester", "email": "test@example.com"}
                    }
                }
            }),
            status="active",
            project_id=None,
        )
        session.add(api)
        session.commit()

        case = svc.generate_case_from_api(session, api.id)

        assert case is not None
        assert case.name == "生成接口"
        assert case.method == "POST"
        assert case.case_type == "api"
        assert case.url == "https://api.gen.com/api/v1/generate"
        assert case.auto_case_id is not None

        # ApiTestCase record exists
        api_case = session.query(ApiTestCase).filter(ApiTestCase.testcase_id == case.id).first()
        assert api_case is not None
        assert api_case.method == "POST"
        assert api_case.url == "https://api.gen.com/api/v1/generate"

        # JSON fields are stored as JSON strings (not raw list/dict)
        headers = json.loads(api_case.headers)
        assert isinstance(headers, dict)
        params = json.loads(api_case.params)
        assert isinstance(params, dict)  # query_params stored as dict
        assertions = json.loads(api_case.assertions)
        assert isinstance(assertions, list)

    def test_reuses_debug_payload_for_case_fields(self, session):
        """生成的用例复用 get_debug_payload 的 header/query/body 提取逻辑"""
        group = ApiGroup(name="Reuse Group")
        session.add(group)
        session.commit()

        api = ApiDefinition(
            group_id=group.id,
            name="Reuse API",
            method="GET",
            path="/api/reuse",
            parameters=json.dumps([
                {"name": "page", "in": "query", "default": "10"},
                {"name": "X-Debug", "in": "header", "default": "true"},
            ]),
            request_body=json.dumps({}),
            status="active",
        )
        session.add(api)
        session.commit()

        case = svc.generate_case_from_api(session, api.id)
        api_case = session.query(ApiTestCase).filter(ApiTestCase.testcase_id == case.id).first()

        # headers and params come from get_debug_payload via reuse
        assert json.loads(api_case.headers).get("X-Debug") == "true"
        assert json.loads(api_case.params).get("page") == "10"

    def test_returns_none_for_missing_api(self, session):
        """不存在的 API 返回 None"""
        result = svc.generate_case_from_api(session, 99999)
        assert result is None

    def test_json_fields_are_deserializable(self, session):
        """验证所有 JSON 字段可反序列化，且 TestCase 主表与 ApiTestCase 一致"""
        group = ApiGroup(name="JSON Check")
        session.add(group)
        session.commit()

        api = ApiDefinition(
            group_id=group.id,
            name="JSON Check API",
            method="POST",
            path="/api/jsoncheck",
            parameters=json.dumps([
                {"name": "size", "in": "query", "default": "large"},
                {"name": "X-Token", "in": "header", "default": "tok123"},
            ]),
            request_body=json.dumps({
                "content": {
                    "application/json": {
                        "example": {"a": 1, "b": "test"}
                    }
                }
            }),
            status="active",
        )
        session.add(api)
        session.commit()

        case = svc.generate_case_from_api(session, api.id)
        api_case = session.query(ApiTestCase).filter(ApiTestCase.testcase_id == case.id).first()

        # TestCase 主表字段从 get_debug_payload 填充
        tc_headers = json.loads(case.headers)
        tc_params = json.loads(case.query_params)
        assert tc_headers.get("X-Token") == "tok123"
        assert tc_params.get("size") == "large"
        assert case.body_type == "json"
        body = json.loads(case.body)
        assert body["a"] == 1

        # ApiTestCase 明细字段与 TestCase 主表一致
        assert json.loads(api_case.headers) == tc_headers
        assert json.loads(api_case.params) == tc_params
        assert api_case.body_type == case.body_type
        assert json.loads(api_case.body) == body

        # 其他 JSON 字段仍为空/默认值
        assert json.loads(case.cookies) == {}
        assert json.loads(case.auth_config) == {}
        assert json.loads(api_case.assertions) == []
        assert isinstance(json.loads(api_case.auth_config), dict)

    def test_generated_case_inherits_project_id_and_source_api_id(self, session):
        """从 ApiDefinition 生成用例时继承 project_id 和写入 source_api_id"""
        group = ApiGroup(name="Inherit Group")
        session.add(group)
        session.commit()

        api = ApiDefinition(
            group_id=group.id,
            name="Inherit API",
            method="GET",
            path="/api/inherit",
            summary="继承测试",
            description="验证归属继承",
            parameters=json.dumps([]),
            request_body=json.dumps({}),
            status="active",
            project_id=42,
        )
        session.add(api)
        session.commit()

        case = svc.generate_case_from_api(session, api.id)

        assert case is not None
        assert case.project_id == 42, f"Expected project_id=42, got {case.project_id}"
        assert case.source_api_id == api.id, f"Expected source_api_id={api.id}, got {case.source_api_id}"


# ── CRUD Tests ─────────────────────────────────────────────────────────────────

class TestApiGroupCrud:
    def test_create_and_list_group(self, session):
        """创建分组并列出"""
        from app.schemas.api_asset import ApiGroupCreate
        data = ApiGroupCreate(name="CRUD Group", sort_order=1)
        group = svc.create_group(session, data)
        assert group.id is not None

        groups = svc.list_groups(session)
        assert any(g.name == "CRUD Group" for g in groups)

    def test_update_group(self, session):
        """更新分组"""
        from app.schemas.api_asset import ApiGroupCreate, ApiGroupUpdate
        group = svc.create_group(session, ApiGroupCreate(name="To Update"))
        updated = svc.update_group(session, group.id, ApiGroupUpdate(name="Updated Name"))
        assert updated.name == "Updated Name"

    def test_delete_group(self, session):
        """删除分组"""
        from app.schemas.api_asset import ApiGroupCreate
        group = svc.create_group(session, ApiGroupCreate(name="To Delete"))
        result = svc.delete_group(session, group.id)
        assert result is True
        assert svc.get_debug_payload(session, 99999) is None  # not found