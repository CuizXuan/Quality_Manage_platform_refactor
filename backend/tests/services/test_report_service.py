# =============================================================================
# Report Service Tests
# =============================================================================
# 核心链路回归测试：报告生成、摘要计算、门禁聚合评估
# =============================================================================

import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.report import Report, QualityGate
from app.models.scenario import Scenario, ExecutionRun
from app.services.report_service import ReportService
from app.services.quality_gate_service import QualityGateService


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


# ── ReportService.build_summary Tests ─────────────────────────────────────────

class TestBuildSummary:
    """测试 ReportService.build_summary() 计算通过率"""

    def test_build_summary_normal(self):
        """正常数据：通过率 = passed / total * 100"""
        execution_data = {"total": 100, "passed": 90, "failed": 5, "skipped": 5, "duration_ms": 5000}
        result = ReportService.build_summary(execution_data)

        assert result["total"] == 100
        assert result["passed"] == 90
        assert result["failed"] == 5
        assert result["skipped"] == 5
        assert result["pass_rate"] == 90.0

    def test_build_summary_all_passed(self):
        """全部通过：通过率为 100"""
        execution_data = {"total": 50, "passed": 50, "failed": 0, "skipped": 0}
        result = ReportService.build_summary(execution_data)
        assert result["pass_rate"] == 100.0

    def test_build_summary_all_failed(self):
        """全部失败：通过率为 0"""
        execution_data = {"total": 20, "passed": 0, "failed": 20, "skipped": 0}
        result = ReportService.build_summary(execution_data)
        assert result["pass_rate"] == 0.0

    def test_build_summary_empty(self):
        """无数据：通过率默认为 0"""
        execution_data = {}
        result = ReportService.build_summary(execution_data)
        assert result["pass_rate"] == 0.0

    def test_build_summary_zero_total(self):
        """total 为 0：避免除零错误，通过率为 0"""
        execution_data = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        result = ReportService.build_summary(execution_data)
        assert result["pass_rate"] == 0.0

    def test_build_summary_partial(self):
        """部分通过：计算正确的小数精度"""
        execution_data = {"total": 3, "passed": 1, "failed": 1, "skipped": 1}
        result = ReportService.build_summary(execution_data)
        assert result["pass_rate"] == round(1 / 3 * 100, 2)


# ── ReportService.create_report Tests ──────────────────────────────────────────

class TestCreateReport:
    """测试从执行数据自动创建报告"""

    def test_create_report_with_execution_data(self, session):
        """提供 execution_data 时自动计算 summary"""
        svc = ReportService(session)
        data = {
            "name": "Test Report",
            "report_type": "execution",
            "target_id": 1,
            "target_name": "Test Scenario",
            "execution_data": {"total": 100, "passed": 95, "failed": 3, "skipped": 2, "duration_ms": 3000},
        }
        report = svc.create_report(data)

        assert report.name == "Test Report"
        assert report.report_type == "execution"
        assert report.summary["total"] == 100
        assert report.summary["passed"] == 95
        assert report.summary["failed"] == 3
        assert report.summary["pass_rate"] == 95.0

    def test_create_report_without_execution_data(self, session):
        """不提供 execution_data 时使用传入的 summary"""
        svc = ReportService(session)
        data = {
            "name": "Manual Report",
            "report_type": "scenario",
            "summary": {"total": 50, "passed": 50, "failed": 0, "skipped": 0, "pass_rate": 100.0},
        }
        report = svc.create_report(data)

        assert report.summary["pass_rate"] == 100.0

    def test_create_report_idempotent(self, session):
        """报告创建后能正确查询回来"""
        svc = ReportService(session)
        data = {
            "name": "Query Test Report",
            "report_type": "execution",
            "execution_data": {"total": 10, "passed": 8, "failed": 1, "skipped": 1},
        }
        created = svc.create_report(data)
        fetched = svc.get_report(created.id)

        assert fetched is not None
        assert fetched["name"] == "Query Test Report"
        assert fetched["summary"]["pass_rate"] == 80.0


# ── QualityGate Evaluation Tests ───────────────────────────────────────────────

class TestQualityGateEvaluation:
    """测试质量门禁评估逻辑"""

    def test_evaluate_gate_pass(self, session):
        """通过率达标：门禁通过"""
        gate = QualityGate(
            name="Pass Rate Gate",
            gate_type="execution",
            enabled=True,
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 90}],
            gate_level="blocking",
        )
        session.add(gate)
        session.commit()

        svc = QualityGateService(session)
        result = svc.evaluate_gate(gate.id, {"pass_rate": 95.0})

        assert result["overall_result"] == "pass"
        assert result["details"][0]["result"] == "pass"

    def test_evaluate_gate_fail(self, session):
        """通过率不达标：门禁失败"""
        gate = QualityGate(
            name="Pass Rate Gate",
            gate_type="execution",
            enabled=True,
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 90}],
            gate_level="blocking",
        )
        session.add(gate)
        session.commit()

        svc = QualityGateService(session)
        result = svc.evaluate_gate(gate.id, {"pass_rate": 80.0})

        assert result["overall_result"] == "fail"
        assert result["details"][0]["result"] == "fail"

    def test_evaluate_gate_skipped_missing_metric(self, session):
        """指标缺失：条件跳过"""
        gate = QualityGate(
            name="Duration Gate",
            gate_type="execution",
            enabled=True,
            conditions=[{"metric": "avg_duration", "operator": "<=", "threshold": 5000}],
            gate_level="warning",
        )
        session.add(gate)
        session.commit()

        svc = QualityGateService(session)
        result = svc.evaluate_gate(gate.id, {})  # 传入空指标

        assert result["overall_result"] == "skipped"
        assert result["details"][0]["result"] == "skipped"

    def test_evaluate_gate_disabled(self, session):
        """门禁未启用：返回 skipped"""
        gate = QualityGate(
            name="Disabled Gate",
            gate_type="execution",
            enabled=False,
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 90}],
            gate_level="blocking",
        )
        session.add(gate)
        session.commit()

        svc = QualityGateService(session)
        result = svc.evaluate_gate(gate.id, {"pass_rate": 99.0})

        assert result["overall_result"] == "skipped"

    def test_evaluate_all_gates(self, session):
        """评估所有启用的门禁"""
        gate1 = QualityGate(
            name="Pass Rate Gate",
            gate_type="execution",
            enabled=True,
            conditions=[{"metric": "pass_rate", "operator": ">=", "threshold": 90}],
            gate_level="blocking",
        )
        gate2 = QualityGate(
            name="Critical Defects Gate",
            gate_type="execution",
            enabled=True,
            conditions=[{"metric": "critical_defects", "operator": "<=", "threshold": 0}],
            gate_level="warning",
        )
        session.add_all([gate1, gate2])
        session.commit()

        svc = QualityGateService(session)
        metrics = {"pass_rate": 95.0, "critical_defects": 0}
        results = svc.evaluate_all_gates_for_execution(metrics, gate_type="execution")

        assert len(results) == 2
        assert results[0]["overall_result"] == "pass"
        assert results[1]["overall_result"] == "pass"


# ── Metrics Aggregation Tests ──────────────────────────────────────────────────

class TestMetricsAggregation:
    """测试从报告自动聚合指标"""

    def test_aggregate_pass_rate(self, session):
        """从 summary 正确提取 pass_rate"""
        svc = ReportService(session)
        data = {
            "name": "Metrics Test Report",
            "report_type": "execution",
            "execution_data": {"total": 100, "passed": 85, "failed": 10, "skipped": 5},
        }
        report = svc.create_report(data)

        summary = report.summary
        aggregated = {
            "pass_rate": summary.get("pass_rate"),
            "test_pass_rate": summary.get("pass_rate"),
            "failed": summary.get("failed", 0),
            "defect_count": 0,
            "critical_defects": 0,
        }

        assert aggregated["pass_rate"] == 85.0
        assert aggregated["test_pass_rate"] == 85.0
        assert aggregated["failed"] == 10


# ── _create_report_from_run Tests ──────────────────────────────────────────────

class TestCreateReportFromRun:
    """测试 _create_report_from_run 使用真实场景执行 summary 结构"""

    def test_create_report_from_run_with_real_summary(self, session):
        """使用真实场景执行 summary 结构：total_steps / executed / passed / failed / steps"""
        from app.models.scenario import Scenario, ScenarioStep, ExecutionRun
        from app.services.scenario_service import _create_report_from_run

        # 构造场景
        scenario = Scenario(name="Login Flow", status="active", version=1)
        session.add(scenario)
        session.commit()

        # 构造执行记录
        run = ExecutionRun(
            run_type="scenario",
            target_id=scenario.id,
            status="passed",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
        )
        session.add(run)
        session.commit()

        # 真实场景执行 summary 结构
        real_summary = {
            "total_steps": 2,
            "executed": 2,
            "passed": 1,
            "failed": 1,
            "steps": [
                {"step_id": 1, "case_id": 1, "name": "Step 1", "status": "passed"},
                {"step_id": 2, "case_id": 2, "name": "Step 2", "status": "failed"},
            ],
        }

        _create_report_from_run(session, run, scenario, real_summary, 1000)

        # 断言报告数据
        report = session.query(Report).filter(Report.target_id == run.id).first()
        assert report is not None
        assert report.report_type == "execution"
        assert report.name == "Login Flow - 执行报告"

        # 验证 summary 字段
        assert report.summary["total"] == 2        # total_steps
        assert report.summary["passed"] == 1
        assert report.summary["failed"] == 1
        assert report.summary["skipped"] == 0     # 2 - 2 = 0
        assert report.summary["pass_rate"] == 50.0  # 1/2*100

        # 验证 metrics 字段
        assert report.metrics["run_id"] == run.id
        assert report.metrics["scenario_id"] == scenario.id
        assert report.metrics["step_results"] is not None
        assert len(report.metrics["step_results"]) == 2
        assert report.metrics["step_results"][0]["status"] == "passed"
        assert report.metrics["step_results"][1]["status"] == "failed"

        # triggered_by 应为 None（ExecutionRun 无此字段）
        assert report.triggered_by is None

    def test_create_report_from_run_idempotent(self, session):
        """同一个 run 调用两次，只创建一条报告"""
        from app.models.scenario import Scenario, ExecutionRun
        from app.services.scenario_service import _create_report_from_run

        scenario = Scenario(name="Idempotent Test", status="active", version=1)
        session.add(scenario)
        session.commit()

        run = ExecutionRun(
            run_type="scenario",
            target_id=scenario.id,
            status="passed",
        )
        session.add(run)
        session.commit()

        summary = {
            "total_steps": 3,
            "executed": 3,
            "passed": 3,
            "failed": 0,
            "steps": [],
        }

        # 第一次调用
        _create_report_from_run(session, run, scenario, summary, 500)
        # 第二次调用（幂等）
        _create_report_from_run(session, run, scenario, summary, 500)

        reports = session.query(Report).filter(Report.target_id == run.id).all()
        assert len(reports) == 1

    def test_create_report_skipped_calculation(self, session):
        """total_steps=5, executed=3 时，skipped=2"""
        from app.models.scenario import Scenario, ExecutionRun
        from app.services.scenario_service import _create_report_from_run

        scenario = Scenario(name="Skip Test", status="active", version=1)
        session.add(scenario)
        session.commit()

        run = ExecutionRun(
            run_type="scenario",
            target_id=scenario.id,
            status="failed",
        )
        session.add(run)
        session.commit()

        summary = {
            "total_steps": 5,
            "executed": 3,
            "passed": 2,
            "failed": 1,
            "steps": [],
        }

        _create_report_from_run(session, run, scenario, summary, 800)

        report = session.query(Report).filter(Report.target_id == run.id).first()
        assert report.summary["skipped"] == 2  # 5 - 3
        assert report.summary["total"] == 5
        assert report.summary["pass_rate"] == 40.0  # 2/5*100