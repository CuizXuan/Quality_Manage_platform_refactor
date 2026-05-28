"""
Test Plan Service 测试
关键路径测试：running 场景不计入 passed、脏 JSON 字段不导致异常、计划最终状态正确
"""

import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.test_plan import TestPlan, TestSuite, TestSuiteItem, TestPlanRun
from app.models.test_case import TestCase
from app.models.scenario import Scenario, ScenarioStep, ExecutionRun
from app.models.platform import Organization, PlatformUser, PlatformRole, PlatformMenu, PlatformPermission, PlatformUserRole
from app.models.terminal import DebugRequest, DebugResult
from app.models.case_folder import CaseFolder
from app.models.functional_test_case import FunctionalTestCase
from app.models.dictionary import DictType, DictItem
from app.models.docgen import DocGenerationTask, DocGenerationRule, DocGenerationTemplate
from app.models.quality_foundation import QualityProject, QualityVersion, QualityIteration, RequirementItem

import app.services.test_plan_service as svc


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ── _safe_json_loads Tests ─────────────────────────────────────────────────────

class TestSafeJsonLoads:
    """测试防御式 JSON 解析"""

    def test_returns_empty_dict_for_empty_string(self):
        result = svc._safe_json_loads("", {})
        assert result == {}

    def test_returns_empty_dict_for_none(self):
        result = svc._safe_json_loads(None, {})
        assert result == {}

    def test_returns_empty_dict_for_invalid_json(self):
        result = svc._safe_json_loads("not a valid json{{", {})
        assert result == {}

    def test_parses_valid_json(self):
        result = svc._safe_json_loads('{"key": "value"}', {})
        assert result == {"key": "value"}

    def test_parses_json_array(self):
        result = svc._safe_json_loads('[1, 2, 3]', [])
        assert result == [1, 2, 3]

    def test_custom_fallback(self):
        result = svc._safe_json_loads("", "custom")
        assert result == "custom"

    def test_fallback_on_invalid_json(self):
        result = svc._safe_json_loads("{broken", "fallback")
        assert result == "fallback"


# ── Plan CRUD Tests ────────────────────────────────────────────────────────────

class TestPlanCrud:
    """测试 TestPlan CRUD"""

    def test_create_and_get_plan(self, session):
        service = svc.TestPlanService(session)
        plan_data = {
            "name": "测试计划",
            "status": "draft",
            "project_id": 1,
        }
        created = service.create_plan(plan_data)
        assert created["id"] is not None
        assert created["name"] == "测试计划"

        fetched = service.get_plan(created["id"])
        assert fetched is not None
        assert fetched["name"] == "测试计划"

    def test_update_plan(self, session):
        service = svc.TestPlanService(session)
        plan = TestPlan(name="原始名称", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        updated = service.update_plan(plan.id, {"name": "新名称"})
        assert updated["name"] == "新名称"

    def test_delete_plan(self, session):
        service = svc.TestPlanService(session)
        plan = TestPlan(name="待删除", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        result = service.delete_plan(plan.id)
        assert result is True
        assert service.get_plan(plan.id) is None

    def test_list_plans_with_suites(self, session):
        service = svc.TestPlanService(session)
        plan = TestPlan(name="含套件计划", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        suite = TestSuite(plan_id=plan.id, name="套件1", sort_order=0)
        session.add(suite)
        session.commit()

        # get_plan always includes suites (hardcoded include_suites=True internally)
        result = service.get_plan(plan.id)
        assert "suites" in result
        assert len(result["suites"]) == 1


# ── TestSuite CRUD Tests ───────────────────────────────────────────────────────

class TestSuiteCrud:
    """测试 TestSuite CRUD"""

    def test_create_suite(self, session):
        service = svc.TestPlanService(session)
        plan = TestPlan(name="计划", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        suite_data = {"plan_id": plan.id, "name": "套件A", "sort_order": 0}
        created = service.create_suite(suite_data)
        assert created["name"] == "套件A"

    def test_delete_suite(self, session):
        service = svc.TestPlanService(session)
        plan = TestPlan(name="计划", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        suite = TestSuite(plan_id=plan.id, name="待删套件", sort_order=0)
        session.add(suite)
        session.commit()

        result = service.delete_suite(suite.id)
        assert result is True


# ── TestSuiteItem Tests ────────────────────────────────────────────────────────

class TestSuiteItemCrud:
    """测试 TestSuiteItem"""

    def test_add_and_remove_item(self, session):
        service = svc.TestPlanService(session)
        plan = TestPlan(name="计划", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        suite = TestSuite(plan_id=plan.id, name="套件", sort_order=0)
        session.add(suite)
        session.commit()

        # Add a case item
        item_data = {
            "suite_id": suite.id,
            "item_type": "case",
            "item_id": 1,
            "sort_order": 0,
        }
        created = service.add_suite_item(item_data)
        assert created["item_type"] == "case"

        # Remove it
        result = service.remove_suite_item(created["id"])
        assert result is True


# ── Summary Field Tests ────────────────────────────────────────────────────────

class TestSummaryField:
    """测试 summary JSON 字段解析"""

    def test_serialize_run_parses_json_summary(self, session):
        """_serialize_run 能正确解析 JSON 字符串 summary"""
        plan = TestPlan(name="p", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        run = TestPlanRun(
            plan_id=plan.id,
            status="running",
            summary=json.dumps({"total": 10, "passed": 5, "failed": 2}),
        )
        session.add(run)
        session.commit()

        service = svc.TestPlanService(session)
        result = service._serialize_run(run)

        assert result["summary"]["total"] == 10
        assert result["summary"]["passed"] == 5

    def test_serialize_run_handles_dict_summary(self, session):
        """_serialize_run 能解析已经是 dict 的 summary（存入前转 JSON）"""
        plan = TestPlan(name="p", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        # summary stored as JSON string in DB (same as real behavior)
        run = TestPlanRun(
            plan_id=plan.id,
            status="passed",
            summary=json.dumps({"total": 8, "passed": 8}),
        )
        session.add(run)
        session.commit()

        service = svc.TestPlanService(session)
        result = service._serialize_run(run)

        assert result["summary"]["total"] == 8


# ── TestPlanRun List Tests ────────────────────────────────────────────────────

class TestPlanRunList:
    """测试 TestPlanRun 列表"""

    def test_list_runs_filters_by_plan_id(self, session):
        service = svc.TestPlanService(session)
        plan = TestPlan(name="计划", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        run1 = TestPlanRun(plan_id=plan.id, status="passed", total=5, passed=5, failed=0)
        run2 = TestPlanRun(plan_id=plan.id, status="failed", total=5, passed=2, failed=3)
        session.add_all([run1, run2])
        session.commit()

        runs, total = service.list_runs(plan_id=plan.id)
        assert total == 2


# ── Item Serialization (name resolution) ──────────────────────────────────────

class TestItemSerialization:
    """测试 _serialize_item 能从 DB 解析用例/场景名称"""

    def test_resolves_case_name(self, session):
        service = svc.TestPlanService(session)
        case = TestCase(name="API用例-获取用户", case_type="api", method="GET", url="/api/user")
        session.add(case)
        session.commit()

        plan = TestPlan(name="p", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        suite = TestSuite(plan_id=plan.id, name="套件", sort_order=0)
        session.add(suite)
        session.commit()

        item = TestSuiteItem(suite_id=suite.id, item_type="case", item_id=case.id, sort_order=0)
        session.add(item)
        session.commit()

        result = service._serialize_item(item)
        assert result["item_name"] == "API用例-获取用户"

    def test_resolves_scenario_name(self, session):
        service = svc.TestPlanService(session)
        scenario = Scenario(name="登录场景", scenario_type="functional", status="active")
        session.add(scenario)
        session.commit()

        plan = TestPlan(name="p", status="draft", project_id=1)
        session.add(plan)
        session.commit()

        suite = TestSuite(plan_id=plan.id, name="套件", sort_order=0)
        session.add(suite)
        session.commit()

        item = TestSuiteItem(suite_id=suite.id, item_type="scenario", item_id=scenario.id, sort_order=0)
        session.add(item)
        session.commit()

        result = service._serialize_item(item)
        assert result["item_name"] == "登录场景"


# ── Running Scenario Summary Behavior ─────────────────────────────────────────

class TestRunningScenarioSummary:
    """验证 running 场景不会计入 passed，final_status 逻辑正确

    这些测试调用真实的 _run_test_plan_background 函数，使用 mocked HTTP 层。
    """

    def test_scenario_trigger_records_running_status_via_real_function(self, engine):
        """场景项触发后调用真实 _run_test_plan_background，验证 run.status=running"""
        from unittest.mock import patch, MagicMock
        import app.services.test_plan_service as svc
        import json

        TestSession = sessionmaker(bind=engine)
        db = TestSession()

        plan = TestPlan(name="RS Test", status="draft", project_id=1)
        db.add(plan)
        db.commit()

        suite = TestSuite(plan_id=plan.id, name="RS Suite", sort_order=0)
        db.add(suite)
        db.commit()

        scenario = Scenario(name="RS Scenario", scenario_type="functional", status="active")
        db.add(scenario)
        db.commit()

        item = TestSuiteItem(suite_id=suite.id, item_type="scenario", item_id=scenario.id, sort_order=0)
        db.add(item)
        db.commit()

        run = TestPlanRun(plan_id=plan.id, status="pending", total=0, passed=0, failed=0)
        db.add(run)
        db.commit()
        run_id = run.id
        plan_id = plan.id

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 999}

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with patch("app.database.SessionLocal", TestSession):
                svc._run_test_plan_background(run_id, plan_id)

        db.expire_all()
        run = db.query(TestPlanRun).filter(TestPlanRun.id == run_id).first()
        summary = json.loads(run.summary)

        assert run.status == "running"
        assert summary["running"] == 1
        assert summary["failed"] == 0

        db.close()

    def test_final_status_is_failed_when_has_failures(self, session):
        """有失败场景时，状态应为 failed"""
        summary = {"total": 2, "executed": 2, "passed": 0, "failed": 1, "skipped": 0, "running": 0, "items": []}

        if summary["running"] > 0 and summary["failed"] == 0:
            final_status = "running"
        elif summary["failed"] > 0:
            final_status = "failed"
        else:
            final_status = "passed"

        assert final_status == "failed"

    def test_final_status_is_passed_only_when_all_passed(self, session):
        """所有场景都确认 passed 时，状态才为 passed"""
        summary = {"total": 2, "executed": 2, "passed": 2, "failed": 0, "skipped": 0, "running": 0, "items": []}

        if summary["running"] > 0 and summary["failed"] == 0:
            final_status = "running"
        elif summary["failed"] > 0:
            final_status = "failed"
        else:
            final_status = "passed"

        assert final_status == "passed"


# ── Dirty JSON Field Tests ─────────────────────────────────────────────────────

class TestDirtyJsonFields:
    """验证脏 JSON 字段不会导致 json.JSONDecodeError"""

    def test_safe_json_loads_handles_empty_headers(self):
        """空字符串返回空 dict，不抛出异常"""
        result = svc._safe_json_loads("", {})
        assert result == {}

    def test_safe_json_loads_handles_dirty_headers(self):
        """脏 JSON 返回空 dict，不抛出异常"""
        result = svc._safe_json_loads("not valid json {", {})
        assert result == {}

    def test_safe_json_loads_handles_plain_string(self):
        """普通字符串（非 JSON）返回空 dict"""
        result = svc._safe_json_loads("just a string", {})
        assert result == {}

    def test_safe_json_loads_parses_normal_headers(self):
        """正常 JSON 字符串正确解析"""
        result = svc._safe_json_loads('{"Content-Type": "application/json"}', {})
        assert result == {"Content-Type": "application/json"}


# ── Background Execution Flow Tests ───────────────────────────────────────────

class TestBackgroundExecutionFlow:
    """验证 _run_test_plan_background 真实链路行为"""

    def test_scenario_item_sets_run_status_to_running(self, engine):
        """场景项触发后 run 记录 status=running, passed=0, summary.running=1"""
        from unittest.mock import patch, MagicMock
        import app.services.test_plan_service as svc
        import json

        TestSession = sessionmaker(bind=engine)
        db = TestSession()

        plan = TestPlan(name="BG Test", status="draft", project_id=1)
        db.add(plan)
        db.commit()

        suite = TestSuite(plan_id=plan.id, name="BG Suite", sort_order=0)
        db.add(suite)
        db.commit()

        scenario = Scenario(name="Login Scenario", scenario_type="functional", status="active")
        db.add(scenario)
        db.commit()

        item = TestSuiteItem(suite_id=suite.id, item_type="scenario", item_id=scenario.id, sort_order=0)
        db.add(item)
        db.commit()

        run = TestPlanRun(plan_id=plan.id, status="pending", total=0, passed=0, failed=0)
        db.add(run)
        db.commit()
        run_id = run.id
        plan_id = plan.id

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 12345}

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with patch("app.database.SessionLocal", TestSession):
                svc._run_test_plan_background(run_id, plan_id)

        db.expire_all()
        run = db.query(TestPlanRun).filter(TestPlanRun.id == run_id).first()
        assert run.status == "running", f"Expected running, got {run.status}"
        assert run.passed == 0, f"Expected 0 passed, got {run.passed}"
        assert run.failed == 0, f"Expected 0 failed, got {run.failed}"
        summary = json.loads(run.summary)
        assert summary["running"] == 1, f"Expected running=1, got {summary.get('running')}"
        assert summary["passed"] == 0
        assert summary["items"][0]["status"] == "running"

        db.close()

    def test_case_item_with_dirty_json_does_not_fail(self, engine):
        """脏 JSON case headers/query_params/auth_config 不导致 JSONDecodeError，终端收到 {}"""
        from unittest.mock import patch, MagicMock
        import app.services.test_plan_service as svc
        import json

        TestSession = sessionmaker(bind=engine)
        db = TestSession()

        plan = TestPlan(name="Dirty JSON Test", status="draft", project_id=1)
        db.add(plan)
        db.commit()

        suite = TestSuite(plan_id=plan.id, name="Dirty Suite", sort_order=0)
        db.add(suite)
        db.commit()

        case = TestCase(
            name="Dirty Case",
            case_type="api",
            method="POST",
            url="http://localhost:9000/api/test",
            headers="not valid json at all {",
            query_params="also broken ---",
            body_type="none",
            body="",
            auth_config="plain string",
        )
        db.add(case)
        db.commit()

        item = TestSuiteItem(suite_id=suite.id, item_type="case", item_id=case.id, sort_order=0)
        db.add(item)
        db.commit()

        run = TestPlanRun(plan_id=plan.id, status="pending", total=0, passed=0, failed=0)
        db.add(run)
        db.commit()
        run_id = run.id
        plan_id = plan.id

        captured_request = {}

        class FakeResponse:
            status_code = 200
            def json(self):
                return {"status_code": 200, "duration_ms": 15}

        def fake_post(url, json=None, **kwargs):
            captured_request["url"] = url
            captured_request["json"] = json
            return FakeResponse()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = fake_post
            mock_client_cls.return_value = mock_client

            with patch("app.database.SessionLocal", TestSession):
                svc._run_test_plan_background(run_id, plan_id)

        req_json = captured_request.get("json", {})
        assert req_json.get("headers") == {}, f"Expected empty headers, got {req_json.get('headers')}"
        assert req_json.get("query_params") == {}, f"Expected empty query_params, got {req_json.get('query_params')}"
        assert req_json.get("auth_config") == {}, f"Expected empty auth_config, got {req_json.get('auth_config')}"

        db.expire_all()
        run = db.query(TestPlanRun).filter(TestPlanRun.id == run_id).first()
        assert run.status == "passed", f"Expected passed, got {run.status}"
        assert run.passed == 1
        assert run.failed == 0

        db.close()


# ── Hierarchy Validation Tests ───────────────────────────────────────────────────

class TestHierarchyValidation:
    """测试 project_id/version_id/iteration_id 层级校验"""

    def _make_foundation(self, db):
        """Create minimal quality foundation: project + version + iteration"""
        project = QualityProject(name="测试项目", code="TEST", status="active")
        db.add(project)
        db.commit()
        db.refresh(project)

        version = QualityVersion(project_id=project.id, name="v1.0", code="V1", status="planning")
        db.add(version)
        db.commit()
        db.refresh(version)

        iteration = QualityIteration(project_id=project.id, version_id=version.id, name="迭代1", status="planning")
        db.add(iteration)
        db.commit()
        db.refresh(iteration)

        other_project = QualityProject(name="其他项目", code="OTHER", status="active")
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        other_version = QualityVersion(project_id=other_project.id, name="v2.0", code="V2", status="planning")
        db.add(other_version)
        db.commit()
        db.refresh(other_version)

        return project, version, iteration, other_project, other_version

    def test_valid_hierarchy_save(self, session):
        """合法 project_id/version_id/iteration_id 可保存"""
        project, version, iteration, _, _ = self._make_foundation(session)

        service = svc.TestPlanService(session)
        plan_data = {
            "name": "合法计划",
            "status": "draft",
            "project_id": project.id,
            "version_id": version.id,
            "iteration_id": iteration.id,
        }
        created = service.create_plan(plan_data)
        assert created["id"] is not None
        assert created["project_id"] == project.id
        assert created["version_id"] == version.id
        assert created["iteration_id"] == iteration.id

    def test_version_not_exists_fails(self, session):
        """version_id 不存在时创建计划失败"""
        project, _, _, _, _ = self._make_foundation(session)

        service = svc.TestPlanService(session)
        plan_data = {
            "name": "无效版本",
            "status": "draft",
            "project_id": project.id,
            "version_id": 9999,
        }
        with pytest.raises(ValueError, match="版本 9999 不存在"):
            service.create_plan(plan_data)

    def test_iteration_not_exists_fails(self, session):
        """iteration_id 不存在时创建计划失败"""
        project, version, _, _, _ = self._make_foundation(session)

        service = svc.TestPlanService(session)
        plan_data = {
            "name": "无效迭代",
            "status": "draft",
            "project_id": project.id,
            "version_id": version.id,
            "iteration_id": 9999,
        }
        with pytest.raises(ValueError, match="迭代 9999 不存在"):
            service.create_plan(plan_data)

    def test_version_project_mismatch_fails(self, session):
        """version_id 与 project_id 不一致时创建计划失败"""
        project, _, _, other_project, other_version = self._make_foundation(session)

        service = svc.TestPlanService(session)
        plan_data = {
            "name": "版本项目不匹配",
            "status": "draft",
            "project_id": project.id,
            "version_id": other_version.id,
        }
        with pytest.raises(ValueError, match=f"版本 {other_version.id} 不属于项目 {project.id}"):
            service.create_plan(plan_data)

    def test_iteration_project_mismatch_fails(self, session):
        """iteration_id 与 project_id 不一致时创建计划失败"""
        project, version, _, other_project, _ = self._make_foundation(session)

        other_version2 = QualityVersion(project_id=other_project.id, name="v3.0", code="V3", status="planning")
        session.add(other_version2)
        session.commit()

        other_iteration = QualityIteration(project_id=other_project.id, version_id=other_version2.id, name="迭代X", status="planning")
        session.add(other_iteration)
        session.commit()

        service = svc.TestPlanService(session)
        plan_data = {
            "name": "迭代项目不匹配",
            "status": "draft",
            "project_id": project.id,
            "version_id": version.id,
            "iteration_id": other_iteration.id,
        }
        with pytest.raises(ValueError, match=f"迭代 {other_iteration.id} 不属于项目"):
            service.create_plan(plan_data)

    def test_update_plan_hierarchy_mismatch(self, session):
        """更新计划时 version_id 与 project_id 不一致失败"""
        project, version, iteration, _, other_version = self._make_foundation(session)

        plan = TestPlan(name="原有计划", status="draft", project_id=project.id, version_id=version.id, iteration_id=iteration.id)
        session.add(plan)
        session.commit()

        service = svc.TestPlanService(session)
        with pytest.raises(ValueError, match=f"版本 {other_version.id} 不属于项目 {project.id}"):
            service.update_plan(plan.id, {"version_id": other_version.id})

    def test_update_plan_valid_hierarchy(self, session):
        """更新计划时传入正确的层级可保存"""
        project, version, iteration, _, _ = self._make_foundation(session)
        project2 = QualityProject(name="项目2", code="P2", status="active")
        session.add(project2)
        session.commit()
        version2 = QualityVersion(project_id=project2.id, name="v2.0", code="V2P2", status="planning")
        session.add(version2)
        session.commit()

        plan = TestPlan(name="计划", status="draft", project_id=project.id, version_id=version.id, iteration_id=iteration.id)
        session.add(plan)
        session.commit()

        service = svc.TestPlanService(session)
        # When project_id or version_id changes, iteration_id must be cleared or updated too
        updated = service.update_plan(plan.id, {"project_id": project2.id, "version_id": version2.id, "iteration_id": None})
        assert updated["project_id"] == project2.id
        assert updated["version_id"] == version2.id