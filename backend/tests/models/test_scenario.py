# =============================================================================
# Scenario Models Tests
# =============================================================================
# TDD: Tests for Scenario, ScenarioStep, ExecutionRun models
# =============================================================================

import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.scenario import Scenario, ScenarioStep, ExecutionRun


# Test fixtures
@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    return create_engine("sqlite:///:memory:", echo=False)


@pytest.fixture
def session(engine):
    """Create database session."""
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestScenario:
    """Tests for Scenario model."""

    def test_create_scenario(self, session):
        """Test creating a scenario."""
        scenario = Scenario(
            name="Login Flow",
            description="Test login and logout flow",
            status="draft",
            version=1,
            created_by=1,
        )
        session.add(scenario)
        session.commit()

        assert scenario.id is not None
        assert scenario.name == "Login Flow"
        assert scenario.description == "Test login and logout flow"
        assert scenario.status == "draft"
        assert scenario.version == 1
        assert scenario.created_by == 1
        assert scenario.created_at is not None

    def test_scenario_default_values(self, session):
        """Test scenario default values."""
        scenario = Scenario(name="Test Scenario")
        session.add(scenario)
        session.commit()

        assert scenario.status == "draft"
        assert scenario.version == 1
        assert scenario.description == ""


class TestScenarioStep:
    """Tests for ScenarioStep model."""

    def test_create_scenario_step(self, session):
        """Test creating a scenario step."""
        scenario = Scenario(
            name="Test Scenario",
            status="draft",
            version=1,
        )
        session.add(scenario)
        session.commit()

        step = ScenarioStep(
            scenario_id=scenario.id,
            case_id=1,
            name="Step 1: Login",
            sort_order=1,
            enabled=True,
            retry_count=0,
            timeout_ms=30000,
            failure_strategy="stop",
        )
        session.add(step)
        session.commit()

        assert step.id is not None
        assert step.scenario_id == scenario.id
        assert step.case_id == 1
        assert step.name == "Step 1: Login"
        assert step.sort_order == 1
        assert step.enabled == True  # SQLite stores bool as integer
        assert step.retry_count == 0
        assert step.timeout_ms == 30000
        assert step.failure_strategy == "stop"

    def test_scenario_step_with_variant_id(self, session):
        """Test scenario step with variant_id."""
        scenario = Scenario(name="Test Scenario", status="draft", version=1)
        session.add(scenario)
        session.commit()

        step = ScenarioStep(
            scenario_id=scenario.id,
            case_id=1,
            variant_id=5,
            name="Step with variant",
            sort_order=1,
            enabled=True,
            retry_count=0,
            timeout_ms=30000,
            failure_strategy="continue",
        )
        session.add(step)
        session.commit()

        assert step.variant_id == 5

    def test_scenario_step_failure_strategies(self, session):
        """Test different failure strategies."""
        strategies = ["stop", "continue", "retry", "skip"]

        scenario = Scenario(name="Test Scenario", status="draft", version=1)
        session.add(scenario)
        session.commit()

        for i, strategy in enumerate(strategies):
            step = ScenarioStep(
                scenario_id=scenario.id,
                case_id=i + 1,
                name=f"Step {i}",
                sort_order=i,
                enabled=True,
                retry_count=0,
                timeout_ms=30000,
                failure_strategy=strategy,
            )
            session.add(step)
            session.commit()

            assert step.failure_strategy == strategy


class TestScenarioStepExtractInjectRules:
    """Tests for extract_rules and inject_rules JSON fields."""

    def test_extract_rules_default(self, session):
        """Test extract_rules default value."""
        scenario = Scenario(name="Test", status="draft", version=1)
        session.add(scenario)
        session.commit()

        step = ScenarioStep(
            scenario_id=scenario.id,
            case_id=1,
            name="Step",
            sort_order=1,
            enabled=True,
            retry_count=0,
            timeout_ms=30000,
            failure_strategy="stop",
        )
        session.add(step)
        session.commit()

        assert step.extract_rules == "[]"
        assert step.inject_rules == "[]"

    def test_extract_rules_json(self, session):
        """Test extract_rules JSON storage."""
        scenario = Scenario(name="Test", status="draft", version=1)
        session.add(scenario)
        session.commit()

        rules = [
            {
                "type": "jsonpath",
                "source": "body",
                "expression": "$.data.token",
                "var_name": "auth_token",
            },
            {
                "type": "header",
                "source": "response",
                "expression": "X-Request-Id",
                "var_name": "request_id",
            },
        ]

        step = ScenarioStep(
            scenario_id=scenario.id,
            case_id=1,
            name="Step",
            sort_order=1,
            enabled=True,
            retry_count=0,
            timeout_ms=30000,
            failure_strategy="stop",
            extract_rules='[{"type": "jsonpath", "source": "body", "expression": "$.data.token", "var_name": "auth_token"}, {"type": "header", "source": "response", "expression": "X-Request-Id", "var_name": "request_id"}]',
        )
        session.add(step)
        session.commit()

        assert "jsonpath" in step.extract_rules
        assert "auth_token" in step.extract_rules
        assert "X-Request-Id" in step.extract_rules


class TestExecutionRun:
    """Tests for ExecutionRun model."""

    def test_create_execution_run(self, session):
        """Test creating an execution run."""
        run = ExecutionRun(
            run_type="case",
            target_id=1,
            environment_id=1,
            status="pending",
        )
        session.add(run)
        session.commit()

        assert run.id is not None
        assert run.run_type == "case"
        assert run.target_id == 1
        assert run.environment_id == 1
        assert run.status == "pending"
        assert run.started_at is None
        assert run.finished_at is None
        assert run.duration_ms is None
        assert run.summary == "{}"

    def test_execution_run_types(self, session):
        """Test run_type values."""
        for run_type in ["case", "scenario"]:
            run = ExecutionRun(
                run_type=run_type,
                target_id=1,
                environment_id=1,
                status="pending",
            )
            session.add(run)
            session.commit()
            assert run.run_type == run_type

    def test_execution_run_statuses(self, session):
        """Test different statuses."""
        statuses = ["pending", "running", "passed", "failed", "stopped"]

        for status in statuses:
            run = ExecutionRun(
                run_type="case",
                target_id=1,
                environment_id=1,
                status=status,
            )
            session.add(run)
            session.commit()
            assert run.status == status

    def test_execution_run_timing(self, session):
        """Test timing fields."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 1, 30)

        run = ExecutionRun(
            run_type="case",
            target_id=1,
            environment_id=1,
            status="passed",
            started_at=start_time,
            finished_at=end_time,
            duration_ms=90000,
        )
        session.add(run)
        session.commit()

        assert run.started_at == start_time
        assert run.finished_at == end_time
        assert run.duration_ms == 90000

    def test_execution_run_summary(self, session):
        """Test summary JSON field."""
        summary = '{"total": 10, "passed": 8, "failed": 2}'

        run = ExecutionRun(
            run_type="case",
            target_id=1,
            environment_id=1,
            status="failed",
            summary=summary,
        )
        session.add(run)
        session.commit()

        assert "total" in run.summary
        assert "passed" in run.summary
