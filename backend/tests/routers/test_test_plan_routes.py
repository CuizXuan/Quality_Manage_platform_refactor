"""
Test Plan Router Tests — 验证静态路由不会被子路由 `{plan_id}` 抢占

纯路由顺序测试：不创建 TestClient、不登录、不操作数据库，只检查 router.routes 中的路径注册顺序。
"""

import pytest
from app.routers.test_plan import router as test_plan_router


class TestRunsRouteOrder:
    """验证 /runs 静态路由注册在 /{plan_id} 之前，不会被后者意外匹配"""

    def test_runs_list_route_before_plan_id(self):
        """GET /api/test-plans/runs 路由存在且在 /{plan_id} 之前"""
        routes = test_plan_router.routes
        paths = [r.path for r in routes]

        runs_index = None
        dynamic_plan_index = None
        for i, p in enumerate(paths):
            if p == "/api/test-plans/runs":
                runs_index = i
            elif p == "/api/test-plans/{plan_id}":
                dynamic_plan_index = i

        assert runs_index is not None, "/runs route not found in router"
        assert dynamic_plan_index is not None, "/{plan_id} route not found in router"
        assert runs_index < dynamic_plan_index, (
            f"/runs (index {runs_index}) must be registered before /{{plan_id}} (index {dynamic_plan_index})"
        )

    def test_runs_get_route_before_plan_id(self):
        """GET /api/test-plans/runs/{run_id} 路由存在且在 /{plan_id} 之前"""
        routes = test_plan_router.routes
        paths = [r.path for r in routes]

        runs_param_index = None
        dynamic_plan_index = None
        for i, p in enumerate(paths):
            if p == "/api/test-plans/runs/{run_id}":
                runs_param_index = i
            elif p == "/api/test-plans/{plan_id}":
                dynamic_plan_index = i

        assert runs_param_index is not None, "/runs/{run_id} route not found in router"
        assert dynamic_plan_index is not None, "/{plan_id} route not found in router"
        assert runs_param_index < dynamic_plan_index, (
            f"/runs/{{run_id}} (index {runs_param_index}) must be registered before /{{plan_id}} (index {dynamic_plan_index})"
        )

    def test_run_id_numeric_not_confused_with_plan_id(self):
        """纯路由顺序已保证 /runs/{run_id} 在 /{plan_id} 之前，不需要 DB 验证"""
        # 此验证已在 test_runs_get_route_before_plan_id 中覆盖
        # 数值型 run_id 不会被 /{plan_id} 匹配的原因：/runs/{run_id} 在 routes 列表中更靠前
        routes = test_plan_router.routes
        paths = [r.path for r in routes]
        assert "/api/test-plans/runs/{run_id}" in paths
        runs_param_index = paths.index("/api/test-plans/runs/{run_id}")
        dynamic_plan_index = paths.index("/api/test-plans/{plan_id}")
        assert runs_param_index < dynamic_plan_index