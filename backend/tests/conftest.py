# -*- coding: utf-8 -*-
"""
测试配置和共享 fixtures
"""
import pytest
import sys
import os

# 将 backend 目录添加到 Python 路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models import Base


# 创建内存 SQLite 数据库用于测试
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """覆盖数据库依赖，使用测试数据库"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """每个测试函数使用独立的数据库会话"""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI 测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_environment(db_session):
    """示例环境数据"""
    from app.models import Environment
    env = Environment(
        name="测试环境",
        description="自动化测试环境",
        variables='{"base_url": "http://test.example.com", "timeout": 30}',
        is_default=True,
    )
    db_session.add(env)
    db_session.commit()
    db_session.refresh(env)
    return env


@pytest.fixture
def sample_case(db_session):
    """示例用例数据"""
    from app.models import TestCase
    case = TestCase(
        name="测试用例",
        description="自动化测试用例",
        method="GET",
        url="http://httpbin.org/get",
        headers='{"Content-Type": "application/json"}',
        params="{}",
        body="",
        body_type="none",
        auth_type="none",
        auth_config="{}",
        folder_path="/test",
        sort_order=1,
        assertions='[{"type": "status_code", "expected": 200}]',
        timeout=30,
        follow_redirects=True,
        verify_ssl=False,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


@pytest.fixture
def sample_scenario(db_session, sample_case):
    """示例场景数据"""
    from app.models import Scenario, ScenarioStep
    scenario = Scenario(
        name="测试场景",
        description="自动化测试场景",
        folder_path="/test",
        variables="{}",
    )
    db_session.add(scenario)
    db_session.commit()
    db_session.refresh(scenario)

    step = ScenarioStep(
        scenario_id=scenario.id,
        case_id=sample_case.id,
        step_order=1,
        extract_rules="[]",
        skip_on_failure=False,
        retry_times=0,
        retry_interval=1,
        enabled=True,
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)

    return scenario


@pytest.fixture
def sample_defect(db_session):
    """示例缺陷数据"""
    from app.models import Defect
    defect = Defect(
        title="测试缺陷",
        description="自动化测试缺陷描述",
        severity="medium",
        priority="medium",
        status="open",
        defect_type="functional",
        assignee="tester",
        reporter="system",
    )
    db_session.add(defect)
    db_session.commit()
    db_session.refresh(defect)
    return defect


@pytest.fixture
def sample_dataset(db_session):
    """示例数据集"""
    from app.models import DataSet
    dataset = DataSet(
        name="测试数据集",
        description="自动化测试数据集",
        data_type="json",
        folder_path="/test",
        data='[{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]',
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


@pytest.fixture
def sample_mock_rule(db_session):
    """示例 MOCK 规则"""
    from app.models import MockRule
    rule = MockRule(
        name="测试 MOCK 规则",
        description="自动化测试 MOCK 规则",
        priority=1,
        enabled=True,
        method="GET",
        path="/test/mock",
        match_type="exact",
        response_status=200,
        response_body='{"code": 0, "message": "mock success"}',
        response_headers='{"Content-Type": "application/json"}',
        delay_ms=0,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule
