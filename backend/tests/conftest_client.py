# -*- coding: utf-8 -*-
"""
FastAPI TestClient fixture
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """创建TestClient实例用于测试"""
    with TestClient(app) as c:
        yield c
