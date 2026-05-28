"""
Quality Analytics Service Tests
关键统计语义测试：summary dict 处理、门禁评估、scope_filter 过滤、质量评分公式
"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.report import Report, Defect, QualityGate
from app.models.quality_foundation import RequirementItem
from app.models.test_case import TestCase
from app.models.functional_test_case import FunctionalTestCase
import app.services.quality_analytics_service as svc


# ── Fixtures ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


@pytest.fixture
def req_base(engine, session):
    """Seed a RequirementItem (no TestCase yet)"""
    req = RequirementItem(
        title="REQ-1", status="active",
        project_id=1, version_id=None, iteration_id=None,
    )
    session.add(req)
    session.commit()
    return req.id


# ── _safe_json_loads ───────────────────────────────────────────────────────────

class TestSafeJsonLoads:
    """_safe_json_loads 必须对 dict/list 直接返回，对字符串才 JSON 解析"""

    def test_returns_dict_for_already_parsed_dict(self):
        data = {"total": 10, "passed": 8, "failed": 2}
        result = svc.QualityAnalyticsService._safe_json_loads(None, data, data)
        assert result == data

    def test_returns_list_for_already_parsed_list(self):
        data = [{"metric": "pass_rate", "operator": ">=", "threshold": 90}]
        result = svc.QualityAnalyticsService._safe_json_loads(None, data, data)
        assert result == data

    def test_parses_string_json(self):
        result = svc.QualityAnalyticsService._safe_json_loads(None, '{"k": 1}', {})
        assert result == {"k": 1}

    def test_fallback_for_empty_string(self):
        result = svc.QualityAnalyticsService._safe_json_loads(None, "", [])
        assert result == []


# ── Overview — Report Summary ─────────────────────────────────────────────────

class TestOverviewReportSummary:
    """Report.summary 为 dict（已解析）时，通过率等统计正确"""

    def test_dict_summary_produces_correct_pass_rate(self, session):
        r = Report(
            project_id=1,
            name="Test Report",
            report_type="execution",
            summary={"total": 10, "passed": 9, "failed": 1},  # already dict
            executed_at=datetime.utcnow(),
        )
        session.add(r)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        result = srv.get_overview(project_id=1)

        metrics = result["metrics"]
        assert metrics["total_cases"] == 10
        assert metrics["passed_cases"] == 9
        assert metrics["average_pass_rate"] == 90.0

    def test_string_summary_also_works(self, session):
        r = Report(
            project_id=1,
            name="Test Report",
            report_type="execution",
            summary=json.dumps({"total": 20, "passed": 10, "failed": 10}),
            executed_at=datetime.utcnow(),
        )
        session.add(r)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        result = srv.get_overview(project_id=1)

        metrics = result["metrics"]
        assert metrics["average_pass_rate"] == 50.0

    def test_empty_summary_no_crash(self, session):
        r = Report(
            project_id=1,
            name="Test Report",
            report_type="execution",
            summary={},
            executed_at=datetime.utcnow(),
        )
        session.add(r)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        result = srv.get_overview(project_id=1)
        assert result["metrics"]["average_pass_rate"] == 0.0


# ── Overview — Quality Score / Closure Rate ────────────────────────────────────

class TestQualityScoreNoDefects:
    """无缺陷时，质量评分不因 closure_rate 扣分（全额 25 分）"""

    def test_zero_defects_full_closure_score(self, session):
        # One passing report → pass_rate 100%
        r = Report(
            project_id=1,
            name="Test Report",
            report_type="execution",
            summary={"total": 10, "passed": 10, "failed": 0},
            executed_at=datetime.utcnow(),
        )
        session.add(r)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        result = srv.get_overview(project_id=1)

        # pass_rate_score = 100 * 0.6 = 60
        # closure_score   = 100 * 0.25 = 25  (no defects → full)
        # coverage_score = 0
        assert result["metrics"]["quality_score"] == 85.0  # 60 + 25 + 0


# ── Release Gate — Conditions as List ─────────────────────────────────────────

class TestReleaseGateConditionsAsList:
    """QualityGate.conditions 为 Python list（已解析）时，门禁正确评估失败条件"""

    def test_conditions_list_evaluated_correctly(self, session):
        gate = QualityGate(
            name="Pass Rate Gate",
            gate_type="execution",
            enabled=True,
            gate_level="warning",
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 95}],
            scope_filter={},
        )
        session.add(gate)
        session.commit()

        # Report with 80% pass rate — should fail the >= 95 condition
        r = Report(
            project_id=1,
            name="Test Report",
            report_type="execution",
            summary={"total": 10, "passed": 8, "failed": 2},
            executed_at=datetime.utcnow(),
        )
        session.add(r)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        result = srv.get_release_gate(project_id=1)

        assert result["result"]["overall_pass"] is False
        assert result["result"]["conditions_failed"] == 1
        assert any("pass_rate" in b for b in result["result"]["blockers"])

    def test_pass_rate_threshold_met(self, session):
        gate = QualityGate(
            name="Pass Rate Gate",
            gate_type="execution",
            enabled=True,
            gate_level="blocking",
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 80}],
            scope_filter={},
        )
        session.add(gate)
        session.commit()

        r = Report(
            project_id=1,
            name="Test Report",
            report_type="execution",
            summary={"total": 10, "passed": 8, "failed": 2},
            executed_at=datetime.utcnow(),
        )
        session.add(r)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        result = srv.get_release_gate(project_id=1)

        assert result["result"]["overall_pass"] is True
        assert result["result"]["conditions_passed"] == 1


# ── Release Gate — scope_filter ───────────────────────────────────────────────

class TestReleaseGateScopeFilter:
    """带 scope_filter 的门禁，只有传入匹配的 project_id/version_id 才被检查"""

    def test_scoped_gate_matched_by_project_id(self, session):
        gate_matching = QualityGate(
            name="Project Gate",
            gate_type="execution",
            enabled=True,
            gate_level="warning",
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 99}],
            scope_filter={"project_id": 1},
        )
        gate_other = QualityGate(
            name="Other Project Gate",
            gate_type="execution",
            enabled=True,
            gate_level="warning",
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 99}],
            scope_filter={"project_id": 999},
        )
        session.add_all([gate_matching, gate_other])

        r = Report(
            project_id=1,
            name="Test Report",
            report_type="execution",
            summary={"total": 10, "passed": 5, "failed": 5},
            executed_at=datetime.utcnow(),
        )
        session.add(r)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        result = srv.get_release_gate(project_id=1)

        # Both gates are queried; gate_other is skipped in Python scope check
        assert result["gates_checked"] == 2
        assert result["result"]["conditions_failed"] == 1
        assert "Project Gate" in result["result"]["blockers"][0]

    def test_global_gate_without_scope_checked(self, session):
        """空 scope_filter 的门禁属于全局门禁，任何 project_id 都应检查"""
        gate = QualityGate(
            name="Global Gate",
            gate_type="execution",
            enabled=True,
            gate_level="warning",
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 95}],
            scope_filter={},
        )
        session.add(gate)
        r = Report(
            project_id=1,
            name="Test Report",
            report_type="execution",
            summary={"total": 10, "passed": 5, "failed": 5},
            executed_at=datetime.utcnow(),
        )
        session.add(r)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        result = srv.get_release_gate(project_id=1)

        assert result["gates_checked"] == 1
        assert result["result"]["conditions_failed"] == 1


# ── Requirement Coverage ──────────────────────────────────────────────────────

class TestRequirementCoverageConsistency:
    """overview 中的 requirement_covered 与 get_requirement_coverage 保持一致"""

    def test_requirement_covered_via_functional_test_case(self, session, req_base):
        """只有 RequirementItem 关联 FunctionalTestCase 时才算已覆盖"""
        # Create a TestCase linked to the requirement
        tc = TestCase(
            name="Test", method="GET", url="http://e.com",
            case_type="functional", requirement_id=req_base,
            expected_status=200,
        )
        session.add(tc)
        session.commit()

        # FunctionalTestCase references the TestCase
        ftc = FunctionalTestCase(testcase_id=tc.id)
        session.add(ftc)
        session.commit()

        srv = svc.QualityAnalyticsService(session)
        overview = srv.get_overview(project_id=1)
        coverage = srv.get_requirement_coverage(project_id=1)

        # Both should report 1 covered requirement
        assert overview["metrics"]["requirement_covered"] == 1
        assert coverage["coverage_rate"] == 100.0

    def test_requirement_without_test_case_not_covered(self, session, req_base):
        srv = svc.QualityAnalyticsService(session)
        overview = srv.get_overview(project_id=1)
        assert overview["metrics"]["requirement_covered"] == 0