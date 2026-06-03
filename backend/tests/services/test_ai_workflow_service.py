"""AIWorkflowService 单元测试 — 不真实访问 AI 模型。

为避免 Base.metadata 在多测试文件共享时出现的 'Table already defined'
问题，本文件使用 SQL 直接建表，并只 import 工作流服务所需的最小依赖。
"""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    # 显式建表，避免 Base.metadata 多文件共享时的冲突
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE ai_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type VARCHAR(20) NOT NULL,
                target_id INTEGER NOT NULL,
                analysis_type VARCHAR(50) NOT NULL,
                model_used VARCHAR(100) NOT NULL,
                raw_response TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                created_by INTEGER,
                created_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE ai_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                suggestion_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                accepted BOOLEAN DEFAULT 0,
                status VARCHAR(30) DEFAULT 'pending_review',
                accepted_at TIMESTAMP,
                accepted_by INTEGER,
                accepted_comment TEXT DEFAULT '',
                created_at TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES ai_analyses(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE ai_workflow_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_type VARCHAR(80) NOT NULL DEFAULT 'requirement_to_test_design',
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                source_name VARCHAR(200) DEFAULT '',
                source_type VARCHAR(30) DEFAULT 'other',
                input_payload TEXT DEFAULT '{}',
                result_payload TEXT DEFAULT '{}',
                current_step VARCHAR(80) DEFAULT '',
                created_by INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                finished_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE ai_workflow_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                step_order INTEGER NOT NULL DEFAULT 1,
                agent_type VARCHAR(80) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                input_payload TEXT DEFAULT '{}',
                output_payload TEXT DEFAULT '{}',
                suggestion_id INTEGER,
                error_message TEXT DEFAULT '',
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                created_at TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES ai_workflow_runs(id)
            )
        """))
        # 采纳路径需要的最小质量基础表（不导入 SQLAlchemy 模型以避免跨文件 metadata 冲突）
        conn.execute(text("""
            CREATE TABLE quality_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(50) NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE quality_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'planning',
                planned_release_at TIMESTAMP,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES quality_projects(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE quality_iterations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                version_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                status VARCHAR(20) DEFAULT 'planning',
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES quality_projects(id),
                FOREIGN KEY (version_id) REFERENCES quality_versions(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE requirement_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                version_id INTEGER,
                iteration_id INTEGER,
                title VARCHAR(300) NOT NULL,
                description TEXT DEFAULT '',
                source_type VARCHAR(30),
                source_key VARCHAR(100),
                priority VARCHAR(10) DEFAULT 'P2',
                status VARCHAR(20) DEFAULT 'open',
                owner_id INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES quality_projects(id),
                FOREIGN KEY (version_id) REFERENCES quality_versions(id),
                FOREIGN KEY (iteration_id) REFERENCES quality_iterations(id)
            )
        """))
        # 真实 TestCaseService.create_case 路径需要的三张表
        conn.execute(text("""
            CREATE TABLE test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                description TEXT DEFAULT '',
                folder_id INTEGER,
                priority VARCHAR(10) DEFAULT 'P2',
                tags TEXT DEFAULT '[]',
                pre_condition TEXT DEFAULT '',
                case_type VARCHAR(20) NOT NULL,
                source_debug_id INTEGER,
                created_by INTEGER,
                is_automated BOOLEAN DEFAULT 0,
                auto_script_path VARCHAR(1000) DEFAULT '',
                auto_script_config TEXT DEFAULT '{}',
                auto_case_id VARCHAR(100) DEFAULT '',
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                method VARCHAR(10),
                url VARCHAR(2000),
                headers TEXT DEFAULT '{}',
                query_params TEXT DEFAULT '{}',
                cookies TEXT DEFAULT '{}',
                auth_config TEXT DEFAULT '{}',
                body_type VARCHAR(20) DEFAULT 'none',
                body TEXT DEFAULT '',
                expected_status INTEGER DEFAULT 200,
                project_id INTEGER,
                version_id INTEGER,
                iteration_id INTEGER,
                requirement_id INTEGER,
                source_api_id INTEGER,
                source_type VARCHAR(30) DEFAULT 'manual',
                source_id INTEGER,
                version_tag VARCHAR(50) DEFAULT '',
                FOREIGN KEY (requirement_id) REFERENCES requirement_items(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE api_test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                testcase_id INTEGER NOT NULL UNIQUE,
                method VARCHAR(10) DEFAULT 'GET',
                url VARCHAR(2000) NOT NULL,
                headers TEXT DEFAULT '{}',
                params TEXT DEFAULT '{}',
                body_type VARCHAR(20) DEFAULT 'none',
                body TEXT DEFAULT '',
                auth_config TEXT DEFAULT '{}',
                expected_status INTEGER DEFAULT 200,
                assertions TEXT DEFAULT '[]',
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (testcase_id) REFERENCES test_cases(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE functional_test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                testcase_id INTEGER NOT NULL UNIQUE,
                steps TEXT DEFAULT '[]',
                test_data TEXT DEFAULT '{}',
                post_action TEXT DEFAULT '',
                expected_result TEXT DEFAULT '',
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (testcase_id) REFERENCES test_cases(id)
            )
        """))
        # 四期：场景采纳路径需要的最小表结构
        conn.execute(text("""
            CREATE TABLE scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                description TEXT DEFAULT '',
                status VARCHAR(20) DEFAULT 'draft',
                scenario_type VARCHAR(50) DEFAULT 'functional',
                priority VARCHAR(10) DEFAULT 'P2',
                version INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                project_id INTEGER,
                version_id INTEGER,
                iteration_id INTEGER,
                source_type VARCHAR(30) DEFAULT 'manual',
                source_id INTEGER,
                version_tag VARCHAR(50) DEFAULT ''
            )
        """))
        conn.execute(text("""
            CREATE TABLE scenario_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                case_id INTEGER NOT NULL,
                variant_id INTEGER,
                name VARCHAR(200) NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                retry_count INTEGER NOT NULL DEFAULT 0,
                timeout_ms INTEGER NOT NULL DEFAULT 30000,
                failure_strategy VARCHAR(20) NOT NULL DEFAULT 'stop',
                extract_rules TEXT DEFAULT '[]',
                inject_rules TEXT DEFAULT '[]',
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
            )
        """))
        # 五期：执行计划 / 启动执行需要的最小表
        conn.execute(text("""
            CREATE TABLE execution_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_type VARCHAR(20) NOT NULL,
                target_id INTEGER NOT NULL,
                environment_id INTEGER,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                duration_ms INTEGER,
                summary TEXT DEFAULT '{}'
            )
        """))
        conn.execute(text("""
            CREATE TABLE execution_environments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(50) DEFAULT '',
                base_url VARCHAR(500),
                description TEXT DEFAULT '',
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))
        # 六期：执行结果分析 Agent 需要 join reports 表
        conn.execute(text("""
            CREATE TABLE reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                report_type VARCHAR(20) NOT NULL,
                target_id INTEGER,
                target_name VARCHAR(200),
                environment VARCHAR(50),
                summary TEXT DEFAULT '{}',
                metrics TEXT DEFAULT '{}',
                executed_at TIMESTAMP,
                duration_ms INTEGER,
                triggered_by INTEGER,
                created_at TIMESTAMP,
                project_id INTEGER,
                version_id INTEGER,
                iteration_id INTEGER,
                source_type VARCHAR(30) DEFAULT 'execution',
                source_id INTEGER,
                version_tag VARCHAR(50) DEFAULT ''
            )
        """))
    return TestingSession()


class TestAIWorkflowService(unittest.TestCase):

    def _svc(self, db):
        from app.services.ai_workflow_service import AIWorkflowService
        return AIWorkflowService(db, None)

    def test_workflow_creates_two_steps_without_ai_config(self):
        db = _make_session()
        try:
            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录PRD",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录，三次失败后锁定5分钟。",
                }
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(result["steps"]), 3)
            self.assertEqual(result["steps"][0]["agent_type"], "requirement-analyst")
            self.assertEqual(result["steps"][1]["agent_type"], "test-designer")
            self.assertEqual(result["steps"][2]["agent_type"], "scenario-designer")
            self.assertEqual(result["steps"][0]["status"], "completed")
            self.assertEqual(result["steps"][1]["status"], "completed")
            self.assertEqual(result["steps"][2]["status"], "completed")
            self.assertEqual(
                result["result_payload"]["requirement_analysis"]["agent_type"],
                "requirement-analyst",
            )
            self.assertEqual(
                result["result_payload"]["test_design"]["agent_type"],
                "test-designer",
            )
            self.assertEqual(
                result["result_payload"]["scenario_design"]["agent_type"],
                "scenario-designer",
            )
        finally:
            db.close()

    def test_workflow_persists_run_and_step_rows(self):
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun, AIWorkflowStep
            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "下单",
                    "source_type": "user_story",
                    "content": "作为买家我希望下单成功后看到订单详情。",
                }
            )
            run_id = result["id"]
            runs = db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).all()
            steps = db.query(AIWorkflowStep).filter(AIWorkflowStep.run_id == run_id).all()
            self.assertEqual(len(runs), 1)
            self.assertEqual(len(steps), 3)
            self.assertEqual(runs[0].status, "completed")
            self.assertEqual(steps[0].step_order, 1)
            self.assertEqual(steps[1].step_order, 2)
            self.assertEqual(steps[2].step_order, 3)
            for step in steps:
                self.assertIsNotNone(step.suggestion_id)
                self.assertEqual(step.status, "completed")
        finally:
            db.close()

    def test_workflow_designer_step_receives_requirement_context(self):
        db = _make_session()
        try:
            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "搜索",
                    "source_type": "prd",
                    "content": "支持关键字模糊搜索，结果按相关度排序。",
                }
            )
            design_step = result["steps"][1]
            input_payload = design_step["input_payload"]
            self.assertIn("requirement_analysis", input_payload)
            self.assertIn("requirements", input_payload)
            self.assertIn("acceptance_criteria", input_payload)
            self.assertEqual(
                input_payload["upstream_suggestion_id"],
                result["steps"][0]["suggestion_id"],
            )
        finally:
            db.close()

    def test_workflow_marks_run_failed_when_step_raises(self):
        db = _make_session()
        try:
            from app.services.ai_agent_service import AIAgentService

            def fake_run_analyze(self, payload, created_by=None):
                raise RuntimeError("upstream boom")

            with patch.object(AIAgentService, "run_analyze_requirements", new=fake_run_analyze):
                result = self._svc(db).start_requirement_to_test_design(
                    {"source_name": "x", "source_type": "prd", "content": "y"}
                )
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["steps"][0]["status"], "failed")
            self.assertIn("upstream boom", result["steps"][0]["error_message"])
        finally:
            db.close()

    def test_get_run_returns_run_with_steps(self):
        db = _make_session()
        try:
            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "查询",
                    "source_type": "prd",
                    "content": "支持按订单号查询订单详情。",
                }
            )
            fetched = self._svc(db).get_run(run["id"])
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["id"], run["id"])
            self.assertEqual(len(fetched["steps"]), 3)
        finally:
            db.close()

    def test_get_run_returns_none_for_missing_id(self):
        db = _make_session()
        try:
            self.assertIsNone(self._svc(db).get_run(99999))
        finally:
            db.close()

    def test_workflow_passes_real_requirement_payload_to_designer(self):
        """step 2 必须拿到 step 1 业务 payload 内部字段，而不是空数组。"""
        db = _make_session()
        try:
            from app.services.ai_agent_service import AIAgentService

            fake_suggestion = {
                "suggestion_id": 11,
                "agent_type": "requirement-analyst",
                "status": "pending_review",
                "payload": {
                    "summary": "登录需求已结构化。",
                    "requirements": [
                        {"title": "手机号+密码登录", "priority": "P0"},
                        {"title": "三次失败锁定5分钟", "priority": "P1"},
                    ],
                    "acceptance_criteria": [
                        {"criteria": "密码错误3次后账户锁定5分钟", "priority": "P0"},
                    ],
                    "test_suggestions": ["覆盖边界：密码错误次数阈值", "覆盖反例：空手机号"],
                    "ambiguities": [],
                    "risks": ["未约定错误响应格式"],
                },
                "trace_meta": {"adoption_status": "pending"},
            }

            captured_inputs = []

            def fake_run_analyze(self, payload, created_by=None):
                return fake_suggestion

            def fake_run_design(self, payload, created_by=None):
                captured_inputs.append(payload)
                return {
                    "suggestion_id": 22,
                    "agent_type": "test-designer",
                    "status": "pending_review",
                    "payload": {
                        "summary": "基于需求生成测试设计。",
                        "test_points": [
                            "覆盖需求点：手机号+密码登录",
                            "覆盖需求点：三次失败锁定5分钟",
                            "验证验收点：密码错误3次后账户锁定5分钟",
                        ],
                        "functional_cases": [],
                        "api_cases": [],
                        "scenario_drafts": [],
                    },
                    "trace_meta": {},
                }

            with patch.object(
                AIAgentService, "run_analyze_requirements", new=fake_run_analyze
            ), patch.object(AIAgentService, "run_design_tests", new=fake_run_design):
                result = self._svc(db).start_requirement_to_test_design(
                    {
                        "source_name": "登录PRD",
                        "source_type": "prd",
                        "content": "支持手机号+密码登录，三次失败后锁定5分钟。",
                    }
                )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(captured_inputs), 1)
            design_input = captured_inputs[0]
            self.assertEqual(
                design_input["requirements"],
                [
                    {"title": "手机号+密码登录", "priority": "P0"},
                    {"title": "三次失败锁定5分钟", "priority": "P1"},
                ],
            )
            self.assertEqual(
                design_input["acceptance_criteria"],
                [{"criteria": "密码错误3次后账户锁定5分钟", "priority": "P0"}],
            )
            self.assertEqual(
                design_input["test_suggestions"],
                ["覆盖边界：密码错误次数阈值", "覆盖反例：空手机号"],
            )
            self.assertEqual(design_input["upstream_suggestion_id"], 11)
            # 完整上游 suggestion 仍保留供追溯和前端展示
            self.assertEqual(
                design_input["requirement_analysis"]["suggestion_id"], 11
            )
            self.assertEqual(
                design_input["requirement_analysis"]["agent_type"],
                "requirement-analyst",
            )
        finally:
            db.close()

    def test_fallback_test_design_generates_points_from_requirement_titles(self):
        """fallback 路径下 test-designer 也能基于真实需求生成 test_points。"""
        db = _make_session()
        try:
            from app.services.ai_agent_service import AIAgentService

            fake_suggestion = {
                "suggestion_id": 31,
                "agent_type": "requirement-analyst",
                "status": "pending_review",
                "payload": {
                    "summary": "搜索需求已结构化。",
                    "requirements": [
                        {"title": "支持关键字模糊搜索"},
                        {"title": "结果按相关度倒序排列"},
                    ],
                    "acceptance_criteria": [
                        {"criteria": "空关键字返回空列表"},
                    ],
                    "test_suggestions": [],
                    "ambiguities": [],
                    "risks": [],
                },
                "trace_meta": {},
            }

            def fake_run_analyze(self, payload, created_by=None):
                return fake_suggestion

            with patch.object(
                AIAgentService, "run_analyze_requirements", new=fake_run_analyze
            ):
                result = self._svc(db).start_requirement_to_test_design(
                    {
                        "source_name": "搜索",
                        "source_type": "prd",
                        "content": "支持关键字模糊搜索。",
                    }
                )

            self.assertEqual(result["status"], "completed")
            design_step = result["steps"][1]
            design_output = design_step["output_payload"]
            test_points = design_output["payload"]["test_points"]
            self.assertIn("覆盖需求点：支持关键字模糊搜索", test_points)
            self.assertIn("覆盖需求点：结果按相关度倒序排列", test_points)
            self.assertIn("验证验收点：空关键字返回空列表", test_points)
        finally:
            db.close()

    def test_failed_workflow_serialization_exposes_error_field(self):
        """失败时序列化结果必须包含顶层 error 字段，便于前端展示。"""
        db = _make_session()
        try:
            from app.services.ai_agent_service import AIAgentService

            def fake_run_analyze(self, payload, created_by=None):
                raise RuntimeError("upstream boom")

            with patch.object(
                AIAgentService, "run_analyze_requirements", new=fake_run_analyze
            ):
                result = self._svc(db).start_requirement_to_test_design(
                    {"source_name": "x", "source_type": "prd", "content": "y"}
                )

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"], "需求分析步骤失败")
            self.assertEqual(result["steps"][0]["status"], "failed")
            self.assertIn("upstream boom", result["steps"][0]["error_message"])
        finally:
            db.close()

    def test_successful_workflow_serialization_error_is_none(self):
        """成功完成的 workflow 序列化结果 error 必须为 None。"""
        db = _make_session()
        try:
            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "查询",
                    "source_type": "prd",
                    "content": "支持按订单号查询订单详情。",
                }
            )
            self.assertEqual(result["status"], "completed")
            self.assertIsNone(result["error"])
        finally:
            db.close()

    # ── Phase 2: Workflow Result Adoption ───────────────────────────────────

    @staticmethod
    def _build_completed_run_payload():
        """构造一段已完成的 workflow run result_payload。"""
        return {
            "requirement_analysis": {
                "suggestion_id": 101,
                "agent_type": "requirement-analyst",
                "status": "pending_review",
                "payload": {
                    "summary": "登录需求已结构化。",
                    "requirements": [
                        {
                            "title": "手机号+密码登录",
                            "description": "支持手机号+密码登录",
                            "source_type": "prd",
                            "source_key": "REQ-LOGIN-1",
                            "priority": "P0",
                        },
                        {
                            "title": "三次失败锁定5分钟",
                            "description": "失败阈值与锁定时长",
                            "source_key": "REQ-LOGIN-2",
                            "priority": "P1",
                        },
                    ],
                    "acceptance_criteria": [
                        {"criteria": "密码错误3次后账户锁定5分钟", "priority": "P0"},
                    ],
                    "test_suggestions": [],
                    "ambiguities": [],
                    "risks": [],
                },
                "trace_meta": {},
            },
            "test_design": {
                "suggestion_id": 202,
                "agent_type": "test-designer",
                "status": "pending_review",
                "payload": {
                    "summary": "已生成测试设计草稿。",
                    "test_points": ["覆盖需求点：手机号+密码登录"],
                    "functional_cases": [
                        {
                            "name": "正常登录流程",
                            "description": "输入正确手机号密码应能登录",
                            "priority": "P0",
                            "steps": ["打开登录页", "输入手机号密码", "点击登录"],
                            "expected_result": "登录成功并跳转首页",
                        }
                    ],
                    "api_cases": [
                        {
                            "name": "POST /api/login 正常",
                            "method": "POST",
                            "url": "/api/login",
                            "expected_status": 200,
                            "assertions": [{"type": "status_code", "value": 200}],
                        },
                        {
                            "name": "POST /api/login 错误密码",
                            "method": "POST",
                            "url": "/api/login",
                            "expected_status": 401,
                        },
                    ],
                },
                "trace_meta": {},
            },
        }

    def test_adopt_returns_none_for_missing_run(self):
        db = _make_session()
        try:
            self.assertIsNone(
                self._svc(db).adopt_requirement_to_test_design(
                    99999, {"project_id": 1}
                )
            )
        finally:
            db.close()

    def test_adopt_rejects_non_completed_run(self):
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            from datetime import datetime
            run = AIWorkflowRun(
                workflow_type="requirement_to_test_design",
                status="running",
                source_name="x",
                source_type="prd",
                input_payload="{}",
                result_payload="{}",
                current_step="requirement-analyst",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            result = self._svc(db).adopt_requirement_to_test_design(
                run.id, {"project_id": 1}
            )
            self.assertIsNotNone(result)
            self.assertEqual(result["summary"]["code"], "WORKFLOW_NOT_COMPLETED")
            self.assertEqual(result["summary"]["error_count"], 1)
            self.assertEqual(result["created_requirements"], [])
            self.assertEqual(result["created_cases"], [])
        finally:
            db.close()

    def test_adopt_rejects_other_workflow_type(self):
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            from datetime import datetime
            run = AIWorkflowRun(
                workflow_type="requirement_to_release",
                status="completed",
                source_name="x",
                source_type="prd",
                input_payload="{}",
                result_payload="{}",
                current_step="completed",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            result = self._svc(db).adopt_requirement_to_test_design(
                run.id, {"project_id": 1}
            )
            self.assertIsNotNone(result)
            self.assertEqual(result["summary"]["code"], "WORKFLOW_TYPE_MISMATCH")
        finally:
            db.close()

    def test_adopt_creates_requirements_and_cases_with_links(self):
        """采纳成功后能调用需求/用例创建接口并建立关联。"""
        db = _make_session()
        try:
            from app.services import ai_workflow_service as wf_module
            from app.services.test_case_service import TestCaseService

            # 准备一个已 completed 的 run
            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]

            # 用 patch 替换实际写入，验证参数
            requirement_calls = []
            case_calls = []
            next_requirement_id = [1000]

            def fake_create_requirement(db, data):
                payload = (
                    data.model_dump() if hasattr(data, "model_dump") else dict(data)
                )
                requirement_calls.append(payload)
                req_id = next_requirement_id[0]
                next_requirement_id[0] += 1
                return SimpleNamespace(id=req_id, **payload)

            def fake_create_case(self, data):
                case_calls.append(dict(data))
                case_id = 5000 + len(case_calls)
                data = dict(data)
                data["id"] = case_id
                data["case_type"] = data.get("case_type", "api")
                return data

            result_payload = self._build_completed_run_payload()
            with patch.object(
                wf_module, "create_requirement", new=fake_create_requirement
            ), patch.object(
                TestCaseService, "create_case", new=fake_create_case
            ):
                # 直接重新写入 result_payload 以使用我们构造的草稿
                from app.models.ai import AIWorkflowRun
                run_row = (
                    db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
                )
                import json as _json
                run_row.result_payload = _json.dumps(
                    result_payload, ensure_ascii=False
                )
                db.commit()

                adopt = self._svc(db).adopt_requirement_to_test_design(
                    run_id,
                    {
                        "project_id": 7,
                        "version_id": 11,
                        "iteration_id": 22,
                        "adopt_requirements": True,
                        "adopt_functional_cases": True,
                        "adopt_api_cases": True,
                        "link_cases_to_requirements": True,
                    },
                    created_by=99,
                )

            self.assertIsNotNone(adopt)
            self.assertEqual(adopt["summary"]["error_count"], 0)
            self.assertEqual(adopt["summary"]["requirements_created"], 2)
            self.assertEqual(adopt["summary"]["cases_created"], 3)
            # 验证调用了 2 次 create_requirement
            self.assertEqual(len(requirement_calls), 2)
            self.assertEqual(requirement_calls[0]["project_id"], 7)
            self.assertEqual(requirement_calls[0]["version_id"], 11)
            self.assertEqual(requirement_calls[0]["iteration_id"], 22)
            self.assertEqual(requirement_calls[0]["owner_id"], 99)
            self.assertEqual(requirement_calls[0]["priority"], "P0")
            self.assertEqual(requirement_calls[0]["source_type"], "prd")
            self.assertEqual(requirement_calls[0]["source_key"], "REQ-LOGIN-1")
            # 验证创建了 3 条用例
            self.assertEqual(len(case_calls), 3)
            functional = [c for c in case_calls if c["case_type"] == "functional"]
            api_cases = [c for c in case_calls if c["case_type"] == "api"]
            self.assertEqual(len(functional), 1)
            self.assertEqual(len(api_cases), 2)
            # 功能用例 requirement_id 关联到第一条需求
            self.assertEqual(functional[0]["requirement_id"], 1000)
            # 接口用例应能按 source_key 反查到第一条需求
            self.assertEqual(api_cases[0]["requirement_id"], 1000)
            # 验证 api_case 字段映射
            self.assertEqual(api_cases[0]["api_case"]["method"], "POST")
            self.assertEqual(api_cases[0]["api_case"]["url"], "/api/login")
            self.assertEqual(api_cases[0]["api_case"]["expected_status"], 200)
            self.assertEqual(api_cases[1]["api_case"]["expected_status"], 401)
        finally:
            db.close()

    def test_adopt_selected_indexes_filter_items(self):
        """selected indexes 为空数组时全部跳过；为子集时仅采纳选中项。"""
        db = _make_session()
        try:
            from app.services import ai_workflow_service as wf_module
            from app.services.test_case_service import TestCaseService
            from app.models.ai import AIWorkflowRun
            import json as _json

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "搜索",
                    "source_type": "prd",
                    "content": "支持关键字模糊搜索。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_completed_run_payload(), ensure_ascii=False
            )
            db.commit()

            requirement_calls = []
            case_calls = []
            next_id = [2000]

            def fake_create_requirement(db, data):
                payload = (
                    data.model_dump() if hasattr(data, "model_dump") else dict(data)
                )
                requirement_calls.append(payload)
                rid = next_id[0]
                next_id[0] += 1
                return SimpleNamespace(id=rid, **payload)

            def fake_create_case(self, data):
                case_calls.append(dict(data))
                cid = 6000 + len(case_calls)
                data = dict(data)
                data["id"] = cid
                return data

            with patch.object(
                wf_module, "create_requirement", new=fake_create_requirement
            ), patch.object(
                TestCaseService, "create_case", new=fake_create_case
            ):
                # 跳过所有需求和功能用例，仅采纳第 0 条接口用例
                adopt = self._svc(db).adopt_requirement_to_test_design(
                    run_id,
                    {
                        "project_id": 1,
                        "adopt_requirements": False,
                        "adopt_functional_cases": False,
                        "adopt_api_cases": True,
                        "selected_api_case_indexes": [0],
                        "link_cases_to_requirements": False,
                    },
                )

            self.assertIsNotNone(adopt)
            self.assertEqual(adopt["summary"]["requirements_created"], 0)
            self.assertEqual(adopt["summary"]["cases_created"], 1)
            # 没采纳需求时不应再调用 create_requirement
            self.assertEqual(len(requirement_calls), 0)
            # 仅调用 1 次 create_case（只采纳第 0 条接口用例）
            self.assertEqual(len(case_calls), 1)
            self.assertEqual(case_calls[0]["case_type"], "api")
            self.assertIsNone(case_calls[0]["requirement_id"])
            # 跳过的 1 条接口用例应记录
            skipped_api = [
                s for s in adopt["skipped"] if s.get("type") == "api_case"
            ]
            self.assertEqual(len(skipped_api), 1)
            self.assertEqual(skipped_api[0]["index"], 1)
        finally:
            db.close()

    def test_adopt_records_error_per_item_does_not_break_batch(self):
        """单条失败不影响其他条，错误计入 errors 数组。"""
        db = _make_session()
        try:
            from app.services import ai_workflow_service as wf_module
            from app.services.test_case_service import TestCaseService
            from app.models.ai import AIWorkflowRun
            import json as _json

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "x",
                    "source_type": "prd",
                    "content": "y",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_completed_run_payload(), ensure_ascii=False
            )
            db.commit()

            next_id = [3000]
            call_count = [0]

            def fake_create_requirement(db, data):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise ValueError("version 11 不存在")
                payload = (
                    data.model_dump() if hasattr(data, "model_dump") else dict(data)
                )
                rid = next_id[0]
                next_id[0] += 1
                return SimpleNamespace(id=rid, **payload)

            def fake_create_case(self, data):
                return {**data, "id": 7000 + call_count[0]}

            with patch.object(
                wf_module, "create_requirement", new=fake_create_requirement
            ), patch.object(
                TestCaseService, "create_case", new=fake_create_case
            ):
                adopt = self._svc(db).adopt_requirement_to_test_design(
                    run_id,
                    {
                        "project_id": 7,
                        "version_id": 11,
                        "adopt_requirements": True,
                        "adopt_functional_cases": True,
                        "adopt_api_cases": True,
                        "link_cases_to_requirements": True,
                    },
                )

            self.assertIsNotNone(adopt)
            self.assertEqual(adopt["summary"]["requirements_created"], 1)
            self.assertEqual(adopt["summary"]["error_count"], 1)
            self.assertEqual(len(adopt["errors"]), 1)
            self.assertEqual(
                adopt["errors"][0]["code"], "CREATE_REQUIREMENT_FAILED"
            )
            self.assertIn("version 11", adopt["errors"][0]["message"])
        finally:
            db.close()

    def test_adopt_uses_requirement_item_create_for_real_create_requirement(self):
        """不 patch create_requirement，验证真实入库路径会写入 requirement_items 表。

        需求 payload 中包含两条 requirement；通过最小质量基础表结构（见
        `_make_session`）支撑 `create_requirement` 的层级校验。
        """
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            # 1) 准备一个最小 quality_projects 行，让 project_id=7 通过校验
            db.execute(
                text(
                    "INSERT INTO quality_projects (id, name, code) VALUES (7, 'AI 项目', 'AI-PROJ')"
                )
            )
            db.commit()

            # 2) 准备一个 completed run，并把 result_payload 替换为构造数据
            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_completed_run_payload(), ensure_ascii=False
            )
            db.commit()

            # 3) 关闭用例采纳，只跑真实 create_requirement 路径
            adopt = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": False,
                    "adopt_api_cases": False,
                    "link_cases_to_requirements": False,
                },
                created_by=42,
            )

            # 4) 摘要断言
            self.assertIsNotNone(adopt)
            self.assertEqual(adopt["summary"]["requirements_created"], 2)
            self.assertEqual(adopt["summary"]["error_count"], 0)
            self.assertEqual(adopt["summary"]["cases_created"], 0)

            # 5) 直接 SQL 查询数据库确认 2 行真实入库
            rows = (
                db.execute(
                    text(
                        "SELECT id, project_id, title, source_type, source_key, priority, status, owner_id "
                        "FROM requirement_items ORDER BY id"
                    )
                )
                .mappings()
                .all()
            )
            self.assertEqual(len(rows), 2)
            first = rows[0]
            self.assertEqual(first["project_id"], 7)
            self.assertEqual(first["title"], "手机号+密码登录")
            self.assertEqual(first["source_type"], "prd")
            self.assertEqual(first["source_key"], "REQ-LOGIN-1")
            self.assertEqual(first["priority"], "P0")
            self.assertEqual(first["status"], "open")
            self.assertEqual(first["owner_id"], 42)
            second = rows[1]
            self.assertEqual(second["title"], "三次失败锁定5分钟")
            self.assertEqual(second["source_key"], "REQ-LOGIN-2")
            self.assertEqual(second["priority"], "P1")
        finally:
            db.close()

    def test_adopt_writes_real_test_cases_via_test_case_service(self):
        """不 patch TestCaseService.create_case，验证真实入库会写入主表和子表。

        关闭需求采纳（不依赖 requirement_items），只让功能/接口用例走真实路径。
        """
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            # 1) 准备一个 completed run
            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_completed_run_payload(), ensure_ascii=False
            )
            db.commit()

            # 2) 关闭需求采纳，只跑真实 create_case 路径
            adopt = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": False,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "link_cases_to_requirements": False,
                },
            )

            # 3) 摘要断言
            self.assertIsNotNone(adopt)
            self.assertEqual(adopt["summary"]["cases_created"], 3)
            self.assertEqual(adopt["summary"]["error_count"], 0)
            self.assertEqual(adopt["summary"]["requirements_created"], 0)

            # 4) 直接 SQL 查询三张表的真实行数
            case_rows = db.execute(
                text("SELECT id, name, case_type, requirement_id, project_id FROM test_cases ORDER BY id")
            ).mappings().all()
            self.assertEqual(len(case_rows), 3)

            func_rows = db.execute(
                text(
                    "SELECT testcase_id, expected_result FROM functional_test_cases ORDER BY testcase_id"
                )
            ).mappings().all()
            self.assertEqual(len(func_rows), 1)
            self.assertEqual(func_rows[0]["expected_result"], "登录成功并跳转首页")

            api_rows = db.execute(
                text(
                    "SELECT testcase_id, method, url, expected_status FROM api_test_cases ORDER BY testcase_id"
                )
            ).mappings().all()
            self.assertEqual(len(api_rows), 2)
            methods = {row["method"] for row in api_rows}
            self.assertEqual(methods, {"POST"})
            urls = {row["url"] for row in api_rows}
            self.assertEqual(urls, {"/api/login"})
            expected_statuses = sorted(row["expected_status"] for row in api_rows)
            self.assertEqual(expected_statuses, [200, 401])

            # 5) 用例的 project_id 应传入
            project_ids = {row["project_id"] for row in case_rows}
            self.assertEqual(project_ids, {7})
        finally:
            db.close()

    def test_adopt_blocks_duplicate_adoption_without_force(self):
        """首次采纳成功后，再次不传 force 触发应被阻止，不创建第二批业务数据。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            from app.services.test_case_service import TestCaseService
            import json as _json

            # 准备一个 completed run
            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_completed_run_payload(), ensure_ascii=False
            )
            db.commit()

            # 第一次采纳走真实路径
            first = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "link_cases_to_requirements": True,
                },
            )
            self.assertEqual(first["summary"]["error_count"], 0)
            self.assertEqual(first["summary"]["requirements_created"], 2)
            self.assertEqual(first["summary"]["cases_created"], 3)

            # 第二次：不传 force，应被阻止
            second = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "link_cases_to_requirements": True,
                },
            )
            self.assertEqual(second["summary"]["code"], "WORKFLOW_ALREADY_ADOPTED")
            self.assertEqual(second["summary"]["error_count"], 1)
            self.assertEqual(second["summary"]["requirements_created"], 0)
            self.assertEqual(second["summary"]["cases_created"], 0)
            self.assertFalse(second["summary"].get("force", False))

            # 关键断言：业务表行数没有增加
            req_count = db.execute(text("SELECT COUNT(*) FROM requirement_items")).scalar()
            self.assertEqual(req_count, 2)
            case_count = db.execute(text("SELECT COUNT(*) FROM test_cases")).scalar()
            self.assertEqual(case_count, 3)

            # 第三次：force=True 允许覆盖
            # 需求因 source_key 已存在被去重跳过；用例不受影响
            third = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "link_cases_to_requirements": True,
                    "force": True,
                },
            )
            self.assertNotEqual(third["summary"].get("code"), "WORKFLOW_ALREADY_ADOPTED")
            self.assertTrue(third["summary"].get("force"))
            self.assertEqual(third["summary"]["error_count"], 0)
            # 需求被去重跳过
            self.assertEqual(third["summary"]["requirements_created"], 0)
            self.assertEqual(third["summary"]["cases_created"], 3)
            self.assertEqual(third["summary"]["force_adoption_count"], 1)

            # 跳过的需求应在 skipped 数组里
            skipped_req = [
                s for s in third["skipped"] if s.get("type") == "requirement"
            ]
            self.assertEqual(len(skipped_req), 2)
            self.assertEqual(
                {s["source_key"] for s in skipped_req},
                {"REQ-LOGIN-1", "REQ-LOGIN-2"},
            )

            # 行数：需求不变，用例翻倍
            req_count = db.execute(text("SELECT COUNT(*) FROM requirement_items")).scalar()
            self.assertEqual(req_count, 2)
            case_count = db.execute(text("SELECT COUNT(*) FROM test_cases")).scalar()
            self.assertEqual(case_count, 6)

            # run.result_payload.adoption 也应记录 force=True 与累计字段
            refreshed = self._svc(db).get_run(run_id)
            adoption = refreshed["result_payload"].get("adoption") or {}
            self.assertEqual(adoption.get("status"), "completed")
            self.assertTrue(adoption.get("force"))
            self.assertEqual(adoption.get("force_adoption_count"), 1)
            # 需求去重后，累计 ID 仍为首次的 2 个
            self.assertEqual(len(adoption.get("cumulative_requirement_ids")), 2)
            # 用例累计 ID 跨 2 次共 6 个
            self.assertEqual(len(adoption.get("cumulative_case_ids")), 6)
            self.assertEqual(adoption.get("requirements_created"), 0)
            self.assertEqual(adoption.get("cases_created"), 3)
        finally:
            db.close()

    def test_adopt_force_skips_existing_source_key_requirements(self):
        """force 重新采纳时，相同 source_key 的需求应被去重跳过。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            # 准备一个 completed run
            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_completed_run_payload(), ensure_ascii=False
            )
            db.commit()

            # 首次采纳：2 条需求写入
            first = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "link_cases_to_requirements": True,
                },
            )
            self.assertEqual(first["summary"]["requirements_created"], 2)
            req_count = db.execute(text("SELECT COUNT(*) FROM requirement_items")).scalar()
            self.assertEqual(req_count, 2)

            # force=True 重新采纳：source_key 已存在，全部跳过
            second = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": False,
                    "adopt_api_cases": False,
                    "link_cases_to_requirements": False,
                    "force": True,
                },
            )
            self.assertEqual(second["summary"]["requirements_created"], 0)
            self.assertEqual(second["summary"]["force_adoption_count"], 1)
            self.assertEqual(second["summary"]["force"], True)

            # 跳过原因应在 skipped 数组
            skipped_req = [
                s for s in second["skipped"] if s.get("type") == "requirement"
            ]
            self.assertEqual(len(skipped_req), 2)
            self.assertEqual(
                {s["source_key"] for s in skipped_req},
                {"REQ-LOGIN-1", "REQ-LOGIN-2"},
            )
            for entry in skipped_req:
                self.assertIn("source_key 已存在", entry["reason"])

            # 关键：requirement_items 行数仍为 2
            req_count = db.execute(text("SELECT COUNT(*) FROM requirement_items")).scalar()
            self.assertEqual(req_count, 2)

            # 累计字段：force_adoption_count == 1，cumulative_requirement_ids 仍为 2
            refreshed = self._svc(db).get_run(run_id)
            adoption = refreshed["result_payload"].get("adoption") or {}
            self.assertEqual(adoption.get("force_adoption_count"), 1)
            self.assertEqual(len(adoption.get("cumulative_requirement_ids")), 2)
        finally:
            db.close()

    def test_adopt_force_response_top_level_cumulative_matches_summary(self):
        """force 第二次采纳后，顶层累计字段必须与 summary / run.result_payload.adoption 一致。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_completed_run_payload(), ensure_ascii=False
            )
            db.commit()

            # 首次采纳
            first = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "link_cases_to_requirements": True,
                },
            )
            self.assertIsNotNone(first)
            self.assertEqual(first["summary"]["requirements_created"], 2)
            self.assertEqual(first["summary"]["cases_created"], 3)
            # 首次：顶层字段存在并与 summary / adoption 一致
            self.assertEqual(first["force_adoption_count"], 0)
            self.assertEqual(
                first["cumulative_requirement_ids"],
                first["summary"]["cumulative_requirement_ids"],
            )
            self.assertEqual(
                first["cumulative_case_ids"],
                first["summary"]["cumulative_case_ids"],
            )
            first_adoption_ids = first["cumulative_requirement_ids"]
            self.assertEqual(len(first_adoption_ids), 2)
            self.assertEqual(
                first["cumulative_case_ids"],
                sorted(set(first["cumulative_case_ids"])),
            )

            # force 第二次采纳
            second = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "link_cases_to_requirements": True,
                    "force": True,
                },
            )
            self.assertIsNotNone(second)
            # 顶层字段必须与 summary / run.result_payload.adoption 完全一致
            self.assertEqual(
                second["force_adoption_count"],
                second["summary"]["force_adoption_count"],
            )
            self.assertEqual(second["force_adoption_count"], 1)
            self.assertEqual(
                second["cumulative_requirement_ids"],
                second["summary"]["cumulative_requirement_ids"],
            )
            self.assertEqual(
                second["cumulative_case_ids"],
                second["summary"]["cumulative_case_ids"],
            )

            refreshed = self._svc(db).get_run(run_id)
            adoption = refreshed["result_payload"].get("adoption") or {}
            self.assertEqual(
                second["force_adoption_count"],
                adoption.get("force_adoption_count"),
            )
            self.assertEqual(
                second["cumulative_requirement_ids"],
                adoption.get("cumulative_requirement_ids"),
            )
            self.assertEqual(
                second["cumulative_case_ids"],
                adoption.get("cumulative_case_ids"),
            )
            # 累计需求 ID 仍为首次 2 条（force 路径下被去重跳过）
            self.assertEqual(
                second["cumulative_requirement_ids"],
                first_adoption_ids,
            )
            # 累计用例 ID 跨两次共 6 条
            self.assertEqual(len(second["cumulative_case_ids"]), 6)
        finally:
            db.close()

    def test_adopt_force_links_new_cases_to_existing_requirements(self):
        """force 跳过需求后，新建的用例应能反查到既有需求 ID，而不是 None。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            from app.services.test_case_service import TestCaseService
            import json as _json

            # 准备 quality_projects 行，让真实 create_requirement 路径通过 project 校验
            db.execute(
                text(
                    "INSERT INTO quality_projects (id, name, code) VALUES (7, 'AI 项目', 'AI-PROJ')"
                )
            )
            db.commit()

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_completed_run_payload(), ensure_ascii=False
            )
            db.commit()

            # 捕获用例创建参数
            case_calls = []
            next_id = [4000]

            def fake_create_case(self, data):
                case_calls.append(dict(data))
                cid = next_id[0]
                next_id[0] += 1
                data = dict(data)
                data["id"] = cid
                return data

            with patch.object(TestCaseService, "create_case", new=fake_create_case):
                # 首次采纳：建立 2 条需求 + 3 条用例
                first = self._svc(db).adopt_requirement_to_test_design(
                    run_id,
                    {
                        "project_id": 7,
                        "adopt_requirements": True,
                        "adopt_functional_cases": True,
                        "adopt_api_cases": True,
                        "link_cases_to_requirements": True,
                    },
                )
            self.assertIsNotNone(first)
            self.assertEqual(first["summary"]["requirements_created"], 2)
            self.assertEqual(first["summary"]["cases_created"], 3)
            first_req_ids = sorted(
                item["requirement_id"] for item in first["created_requirements"]
            )
            self.assertEqual(len(first_req_ids), 2)
            # 首次采纳：所有用例均关联到既有需求
            self.assertEqual(len(case_calls), 3)
            for c in case_calls:
                self.assertIsNotNone(c["requirement_id"])
                self.assertIn(c["requirement_id"], first_req_ids)

            # 第二次 force 采纳：清空 case_calls 重新捕获
            case_calls.clear()
            with patch.object(TestCaseService, "create_case", new=fake_create_case):
                second = self._svc(db).adopt_requirement_to_test_design(
                    run_id,
                    {
                        "project_id": 7,
                        "adopt_requirements": True,
                        "adopt_functional_cases": True,
                        "adopt_api_cases": True,
                        "link_cases_to_requirements": True,
                        "force": True,
                    },
                )
            self.assertIsNotNone(second)
            # 需求被 source_key 去重跳过
            self.assertEqual(second["summary"]["requirements_created"], 0)
            self.assertEqual(second["summary"]["cases_created"], 3)
            skipped_req = [
                s for s in second["skipped"] if s.get("type") == "requirement"
            ]
            self.assertEqual(len(skipped_req), 2)
            # 跳过记录里应带出既有需求 ID
            for entry in skipped_req:
                self.assertIn("existing_requirement_id", entry)
                self.assertIn(entry["existing_requirement_id"], first_req_ids)

            # 关键断言：force 第二次新建的所有用例 requirement_id 都应指向既有需求 ID
            self.assertEqual(len(case_calls), 3)
            for c in case_calls:
                self.assertIsNotNone(
                    c["requirement_id"],
                    f"force 跳过需求后，用例 {c.get('name')} 应能反查到既有需求 ID",
                )
                self.assertIn(
                    c["requirement_id"],
                    first_req_ids,
                    f"用例 {c.get('name')} 关联到错误的需求 ID: {c['requirement_id']}",
                )

            # 业务表行数：需求仍为 2（用例被 patch 不入库）
            req_count = db.execute(text("SELECT COUNT(*) FROM requirement_items")).scalar()
            self.assertEqual(req_count, 2)
        finally:
            db.close()

    # ── Phase 4: Scenario Designer Agent ─────────────────────────────────────

    @staticmethod
    def _build_run_payload_with_scenarios():
        """构造一段已完成 + 含 scenario_design 草稿的 result_payload。

        用例名故意与 scenario steps 的 `case_name` 保持一致，便于在采纳时
        通过 `case_name` 反查到 test_case.id。
        """
        base = TestAIWorkflowService._build_completed_run_payload()
        base["scenario_design"] = {
            "suggestion_id": 303,
            "agent_type": "scenario-designer",
            "status": "pending_review",
            "payload": {
                "summary": "已基于测试设计草拟两个端到端场景。",
                "scenario_drafts": [
                    {
                        "name": "登录主流程",
                        "description": "覆盖正常登录的成功路径",
                        "scenario_type": "functional",
                        "priority": "P0",
                        "steps": [
                            {
                                "name": "执行正常登录流程",
                                "case_name": "正常登录流程",
                                "failure_strategy": "stop",
                                "timeout_ms": 15000,
                            }
                        ],
                    },
                    {
                        "name": "登录异常分支",
                        "description": "覆盖接口异常分支",
                        "scenario_type": "api",
                        "priority": "P1",
                        "steps": [
                            {
                                "name": "错误密码登录",
                                "case_name": "POST /api/login 错误密码",
                            }
                        ],
                    },
                ],
            },
            "trace_meta": {"adoption_status": "pending"},
        }
        return base

    def test_workflow_runs_three_steps_in_order_with_scenario_designer(self):
        """工作流必须依次跑过 requirement-analyst → test-designer → scenario-designer。"""
        db = _make_session()
        try:
            captured_scenario_inputs = []

            from app.services.ai_agent_service import AIAgentService

            def fake_run_design_scenarios(self, payload, created_by=None):
                captured_scenario_inputs.append(payload)
                return {
                    "suggestion_id": 999,
                    "agent_type": "scenario-designer",
                    "status": "pending_review",
                    "payload": {
                        "summary": "已基于测试设计生成场景草稿。",
                        "scenario_drafts": [
                            {
                                "name": "主流程",
                                "steps": [{"case_id": 1, "name": "step 1"}],
                            }
                        ],
                    },
                    "trace_meta": {},
                }

            with patch.object(
                AIAgentService,
                "run_design_scenarios",
                new=fake_run_design_scenarios,
            ):
                result = self._svc(db).start_requirement_to_test_design(
                    {
                        "source_name": "登录",
                        "source_type": "prd",
                        "content": "支持手机号+密码登录。",
                    }
                )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(captured_scenario_inputs), 1)
            scenario_input = captured_scenario_inputs[0]
            # 场景步骤的输入必须含上游两段的产物
            self.assertIn("requirement_analysis", scenario_input)
            self.assertIn("test_design", scenario_input)
            self.assertIn("functional_cases", scenario_input)
            self.assertIn("api_cases", scenario_input)
            # 顺序：步骤 1 → 2 → 3
            agent_types = [step["agent_type"] for step in result["steps"]]
            self.assertEqual(
                agent_types,
                ["requirement-analyst", "test-designer", "scenario-designer"],
            )
            # 上游 suggestion_id 必须是 test-designer 的 suggestion_id
            self.assertEqual(
                scenario_input["upstream_suggestion_id"],
                result["steps"][1]["suggestion_id"],
            )
        finally:
            db.close()

    def test_scenario_designer_fallback_generates_non_empty_drafts(self):
        """fallback 路径下 scenario-designer 也能基于功能/接口用例输出非空草稿。"""
        db = _make_session()
        try:
            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            self.assertEqual(result["status"], "completed")
            scenario_output = result["result_payload"]["scenario_design"]
            self.assertEqual(scenario_output["agent_type"], "scenario-designer")
            drafts = scenario_output["payload"]["scenario_drafts"]
            self.assertGreaterEqual(
                len(drafts), 1, "fallback 必须至少产出 1 个 scenario_draft"
            )
            # 每个草稿的 steps 数应 >= 1
            for draft in drafts:
                self.assertGreaterEqual(len(draft.get("steps") or []), 1)
        finally:
            db.close()

    def test_adopt_scenario_drafts_creates_scenarios_and_steps(self):
        """adopt_scenario_drafts=True 时应创建 scenarios 与 scenario_steps。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            from app.services.test_case_service import TestCaseService
            import json as _json

            # 让真实 create_requirement + create_case 走通
            db.execute(
                text(
                    "INSERT INTO quality_projects (id, name, code) VALUES (7, 'AI 项目', 'AI-PROJ')"
                )
            )
            db.commit()

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_run_payload_with_scenarios(),
                ensure_ascii=False,
            )
            db.commit()

            adopt = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "adopt_scenario_drafts": True,
                    "link_cases_to_requirements": True,
                    "link_scenario_steps_to_cases": True,
                },
            )
            self.assertIsNotNone(adopt)
            self.assertEqual(adopt["summary"]["error_count"], 0)
            self.assertEqual(adopt["summary"]["scenarios_created"], 2)
            self.assertEqual(len(adopt["created_scenarios"]), 2)

            # 验证 scenarios 真实落库
            scenario_rows = db.execute(
                text(
                    "SELECT id, name, scenario_type, priority, project_id, source_type, source_id, version_tag "
                    "FROM scenarios ORDER BY id"
                )
            ).mappings().all()
            self.assertEqual(len(scenario_rows), 2)
            self.assertEqual(scenario_rows[0]["name"], "登录主流程")
            self.assertEqual(scenario_rows[0]["scenario_type"], "functional")
            self.assertEqual(scenario_rows[0]["priority"], "P0")
            self.assertEqual(scenario_rows[0]["project_id"], 7)
            self.assertEqual(scenario_rows[0]["source_type"], "ai_workflow")
            self.assertEqual(scenario_rows[0]["source_id"], run_id)
            self.assertEqual(scenario_rows[0]["version_tag"], f"workflow:{run_id}")

            # scenario_steps 真实落库
            step_rows = db.execute(
                text(
                    "SELECT scenario_id, case_id, name, sort_order, failure_strategy, timeout_ms "
                    "FROM scenario_steps ORDER BY id"
                )
            ).mappings().all()
            self.assertEqual(len(step_rows), 2)
            # 第一个场景的步骤应能反查到 功能用例
            functional_case_id = next(
                item["case_id"]
                for item in adopt["created_cases"]
                if item["case_type"] == "functional"
            )
            self.assertEqual(step_rows[0]["scenario_id"], scenario_rows[0]["id"])
            self.assertEqual(step_rows[0]["case_id"], functional_case_id)
            self.assertEqual(step_rows[0]["failure_strategy"], "stop")
            self.assertEqual(step_rows[0]["timeout_ms"], 15000)
            # 第二个场景的步骤应能反查到 "POST /api/login 错误密码" 这条接口用例
            api_case_by_name = {
                item["name"]: item["case_id"]
                for item in adopt["created_cases"]
                if item["case_type"] == "api"
            }
            self.assertEqual(step_rows[1]["scenario_id"], scenario_rows[1]["id"])
            self.assertEqual(
                step_rows[1]["case_id"],
                api_case_by_name["POST /api/login 错误密码"],
            )
            self.assertEqual(step_rows[1]["failure_strategy"], "stop")
            self.assertEqual(step_rows[1]["timeout_ms"], 30000)

            # 累计字段写入 result_payload.adoption
            refreshed = self._svc(db).get_run(run_id)
            adoption = refreshed["result_payload"].get("adoption") or {}
            self.assertEqual(adoption.get("scenarios_created"), 2)
            self.assertEqual(len(adoption.get("cumulative_scenario_ids")), 2)
            # 顶层累计字段与 summary 一致
            self.assertEqual(
                adopt["cumulative_scenario_ids"],
                adoption.get("cumulative_scenario_ids"),
            )
            self.assertEqual(
                adopt["cumulative_scenario_ids"],
                adopt["summary"]["cumulative_scenario_ids"],
            )
        finally:
            db.close()

    def test_adopt_scenario_drafts_skips_when_no_step_resolves_case(self):
        """场景下所有 step 都无法解析到 test_case 时整场景跳过并报 SCENARIO_CASE_LINK_MISSING。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            # 准备一个 completed run
            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            payload = self._build_run_payload_with_scenarios()
            # 改写两个草稿：让所有 step 都无法解析
            payload["scenario_design"]["payload"]["scenario_drafts"] = [
                {
                    "name": "完全断链场景",
                    "scenario_type": "functional",
                    "priority": "P2",
                    "steps": [
                        {"name": "step-a", "case_name": "不存在的用例名 A"},
                        {"name": "step-b", "case_name": "不存在的用例名 B"},
                    ],
                }
            ]
            run_row.result_payload = _json.dumps(payload, ensure_ascii=False)
            db.commit()

            adopt = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "adopt_scenario_drafts": True,
                    "link_cases_to_requirements": True,
                    "link_scenario_steps_to_cases": True,
                },
            )
            self.assertIsNotNone(adopt)
            self.assertEqual(adopt["summary"]["scenarios_created"], 0)
            self.assertEqual(len(adopt["created_scenarios"]), 0)
            self.assertEqual(adopt["summary"]["error_count"], 1)
            err = adopt["errors"][0]
            self.assertEqual(err["code"], "SCENARIO_CASE_LINK_MISSING")
            self.assertEqual(err["type"], "scenario")
            # 业务表没有落库
            scenario_count = db.execute(
                text("SELECT COUNT(*) FROM scenarios")
            ).scalar()
            self.assertEqual(scenario_count, 0)
        finally:
            db.close()

    def test_adopt_force_with_only_scenarios_does_not_duplicate_requirements_or_cases(self):
        """force=True 但只勾选 adopt_scenario_drafts，不应重复需求/用例。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            db.execute(
                text(
                    "INSERT INTO quality_projects (id, name, code) VALUES (7, 'AI 项目', 'AI-PROJ')"
                )
            )
            db.commit()

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_run_payload_with_scenarios(),
                ensure_ascii=False,
            )
            db.commit()

            # 首次采纳：建立 2 需求 + 3 用例
            first = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "adopt_scenario_drafts": False,
                    "link_cases_to_requirements": True,
                },
            )
            self.assertEqual(first["summary"]["requirements_created"], 2)
            self.assertEqual(first["summary"]["cases_created"], 3)

            req_count_before = db.execute(
                text("SELECT COUNT(*) FROM requirement_items")
            ).scalar()
            case_count_before = db.execute(
                text("SELECT COUNT(*) FROM test_cases")
            ).scalar()

            # force=True 但只勾选 adopt_scenario_drafts
            second = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": False,
                    "adopt_functional_cases": False,
                    "adopt_api_cases": False,
                    "adopt_scenario_drafts": True,
                    "link_scenario_steps_to_cases": True,
                    "force": True,
                },
            )
            self.assertIsNotNone(second)
            # 需求/用例没增加
            self.assertEqual(second["summary"]["requirements_created"], 0)
            self.assertEqual(second["summary"]["cases_created"], 0)
            # 场景应能正常采纳（依赖已有用例）
            self.assertEqual(second["summary"]["scenarios_created"], 2)
            # 关键断言：业务表行数没变
            req_count_after = db.execute(
                text("SELECT COUNT(*) FROM requirement_items")
            ).scalar()
            case_count_after = db.execute(
                text("SELECT COUNT(*) FROM test_cases")
            ).scalar()
            self.assertEqual(req_count_after, req_count_before)
            self.assertEqual(case_count_after, case_count_before)
            # force_adoption_count 累加
            self.assertEqual(second["summary"]["force_adoption_count"], 1)
            # 累计场景 ID 来自本次
            self.assertGreaterEqual(len(second["cumulative_scenario_ids"]), 2)
        finally:
            db.close()

    def test_adopt_without_force_blocks_duplicate_scenarios(self):
        """首次未采纳场景，第二次无 force 触发应被阻止（不允许重复创建场景）。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            db.execute(
                text(
                    "INSERT INTO quality_projects (id, name, code) VALUES (7, 'AI 项目', 'AI-PROJ')"
                )
            )
            db.commit()

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_run_payload_with_scenarios(),
                ensure_ascii=False,
            )
            db.commit()

            # 首次完整采纳
            first = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "adopt_scenario_drafts": True,
                    "link_scenario_steps_to_cases": True,
                },
            )
            self.assertEqual(first["summary"]["scenarios_created"], 2)
            scenarios_after_first = db.execute(
                text("SELECT COUNT(*) FROM scenarios")
            ).scalar()
            self.assertEqual(scenarios_after_first, 2)

            # 第二次无 force：被 WORKFLOW_ALREADY_ADOPTED 阻止，场景表行数不变
            second = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_scenario_drafts": True,
                    "link_scenario_steps_to_cases": True,
                },
            )
            self.assertEqual(second["summary"]["code"], "WORKFLOW_ALREADY_ADOPTED")
            self.assertEqual(second["summary"]["scenarios_created"], 0)
            scenarios_after_second = db.execute(
                text("SELECT COUNT(*) FROM scenarios")
            ).scalar()
            self.assertEqual(scenarios_after_second, 2)
        finally:
            db.close()

    def test_link_scenario_steps_off_writes_skipped_not_error(self):
        """link_scenario_steps_to_cases=False 时，场景应写入 skipped，error_count 不增。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            db.execute(
                text(
                    "INSERT INTO quality_projects (id, name, code) VALUES (7, 'AI 项目', 'AI-PROJ')"
                )
            )
            db.commit()

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                self._build_run_payload_with_scenarios(),
                ensure_ascii=False,
            )
            db.commit()

            adopt = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "adopt_scenario_drafts": True,
                    "link_scenario_steps_to_cases": False,
                },
            )
            self.assertIsNotNone(adopt)
            # 不创建任何场景
            self.assertEqual(adopt["summary"]["scenarios_created"], 0)
            self.assertEqual(len(adopt["created_scenarios"]), 0)
            # 关键断言：error_count 仍为 0（用户主动关闭，不应报错）
            self.assertEqual(adopt["summary"]["error_count"], 0)
            # 跳过的场景应有 2 条
            skipped_scenarios = [
                s for s in adopt["skipped"] if s.get("type") == "scenario"
            ]
            self.assertEqual(len(skipped_scenarios), 2)
            for entry in skipped_scenarios:
                self.assertIn("link_scenario_steps_to_cases 已关闭", entry["reason"])
            # summary.skipped_count 包含 scenario 跳过
            self.assertGreaterEqual(adopt["summary"]["skipped_count"], 2)
            # 业务表确认无落库
            scenarios_count = db.execute(
                text("SELECT COUNT(*) FROM scenarios")
            ).scalar()
            self.assertEqual(scenarios_count, 0)
            steps_count = db.execute(
                text("SELECT COUNT(*) FROM scenario_steps")
            ).scalar()
            self.assertEqual(steps_count, 0)
        finally:
            db.close()

    def test_cumulative_case_ids_supply_by_index_for_force_adopt(self):
        """force=True + 仅 adopt_scenario_drafts=True + 草稿 step 仅含 case_index，
        应能从 cumulative_case_ids 解析到历史用例并创建 scenario_steps。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            db.execute(
                text(
                    "INSERT INTO quality_projects (id, name, code) VALUES (7, 'AI 项目', 'AI-PROJ')"
                )
            )
            db.commit()

            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = run["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )

            # 首次采纳：写入需求/用例，场景故意不采纳
            run_row.result_payload = _json.dumps(
                self._build_run_payload_with_scenarios(),
                ensure_ascii=False,
            )
            db.commit()
            first = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": True,
                    "adopt_functional_cases": True,
                    "adopt_api_cases": True,
                    "adopt_scenario_drafts": False,
                    "link_cases_to_requirements": True,
                },
            )
            self.assertEqual(first["summary"]["requirements_created"], 2)
            self.assertEqual(first["summary"]["cases_created"], 3)
            first_cumulative_case_ids = list(first["cumulative_case_ids"])
            self.assertEqual(len(first_cumulative_case_ids), 3)
            scenarios_after_first = db.execute(
                text("SELECT COUNT(*) FROM scenarios")
            ).scalar()
            self.assertEqual(scenarios_after_first, 0)

            # 第二次 force：仅采纳场景；草稿 step 全部只给 case_index，不给 case_id / case_name
            payload = self._build_run_payload_with_scenarios()
            # 关键：保留首次的 adoption（cumulative_case_ids 在其中），
            # 否则替换 result_payload 会让 previous_adoption 变空
            payload["adoption"] = first["summary"].get("adoption_snapshot") or {
                "status": "completed",
                "cumulative_case_ids": first_cumulative_case_ids,
                "cumulative_requirement_ids": first["cumulative_requirement_ids"],
                "force_adoption_count": 0,
            }
            for draft in payload["scenario_design"]["payload"]["scenario_drafts"]:
                for step in draft.get("steps", []):
                    step.pop("case_id", None)
                    step.pop("case_name", None)
                    # 历史 created_cases 是 [functional, api, api]，索引 0/1/2
                    if draft["name"].endswith("主流程"):
                        step["case_index"] = 0
                    else:
                        step["case_index"] = 1
            run_row.result_payload = _json.dumps(payload, ensure_ascii=False)
            db.commit()

            second = self._svc(db).adopt_requirement_to_test_design(
                run_id,
                {
                    "project_id": 7,
                    "adopt_requirements": False,
                    "adopt_functional_cases": False,
                    "adopt_api_cases": False,
                    "adopt_scenario_drafts": True,
                    "link_scenario_steps_to_cases": True,
                    "force": True,
                },
            )
            self.assertIsNotNone(second)
            self.assertEqual(second["summary"]["error_count"], 0)
            self.assertEqual(second["summary"]["scenarios_created"], 2)
            self.assertEqual(len(second["created_scenarios"]), 2)
            # 累计场景 ID 包含 2 个新场景
            self.assertGreaterEqual(len(second["cumulative_scenario_ids"]), 2)

            # 校验 scenario_steps 真实落库，且 case_id 指向历史用例（cumulative_case_ids）
            step_rows = db.execute(
                text(
                    "SELECT scenario_id, case_id, name, sort_order "
                    "FROM scenario_steps ORDER BY id"
                )
            ).mappings().all()
            self.assertEqual(len(step_rows), 2)
            first_scenario_id = second["created_scenarios"][0]["scenario_id"]
            second_scenario_id = second["created_scenarios"][1]["scenario_id"]
            first_step = next(r for r in step_rows if r["scenario_id"] == first_scenario_id)
            second_step = next(r for r in step_rows if r["scenario_id"] == second_scenario_id)
            # 主流程 step (case_index=0) → functional case
            # 异常分支 step (case_index=1) → 第一个 api case
            self.assertIn(first_step["case_id"], first_cumulative_case_ids)
            self.assertIn(second_step["case_id"], first_cumulative_case_ids)
            # case_id 0 应对应 functional case（test_cases[0]）
            functional_case_id = first_cumulative_case_ids[0]
            self.assertEqual(first_step["case_id"], functional_case_id)
            # 异常分支 case_index=1 → 第一个 api case（test_cases[1]）
            self.assertEqual(second_step["case_id"], first_cumulative_case_ids[1])
        finally:
            db.close()


    # ── Phase 5: Execution Planner Agent ────────────────────────────────────

    @staticmethod
    def _insert_scenarios(db, scenario_records):
        """直接往 scenarios 表插入场景行，返回场景 ID 列表。"""
        scenario_ids = []
        for idx, record in enumerate(scenario_records):
            db.execute(
                text(
                    """
                    INSERT INTO scenarios
                      (id, name, description, status, scenario_type, priority, version,
                       source_type, source_id, version_tag)
                    VALUES
                      (:id, :name, :description, :status, :scenario_type, :priority, :version,
                       :source_type, :source_id, :version_tag)
                    """
                ),
                {
                    "id": record["id"],
                    "name": record["name"],
                    "description": record.get("description", ""),
                    "status": record.get("status", "active"),
                    "scenario_type": record.get("scenario_type", "functional"),
                    "priority": record.get("priority", "P2"),
                    "version": record.get("version", 1),
                    "source_type": record.get("source_type", "ai_workflow"),
                    "source_id": record.get("source_id", 0),
                    "version_tag": record.get("version_tag", "workflow:0"),
                },
            )
            scenario_ids.append(record["id"])
        db.commit()
        return scenario_ids

    def _build_run_with_adoption(self, db, scenario_ids, run_id_seed=0):
        """构造一个已 completed + 含 adoption 块的 workflow run。"""
        run = self._svc(db).start_requirement_to_test_design(
            {
                "source_name": "登录",
                "source_type": "prd",
                "content": "支持手机号+密码登录。",
            }
        )
        run_id = run["id"]
        from app.models.ai import AIWorkflowRun
        import json as _json

        run_row = (
            db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
        )
        adoption_block = {
            "status": "completed",
            "force": False,
            "force_adoption_count": 0,
            "requirements_created": 0,
            "cases_created": 0,
            "scenarios_created": len(scenario_ids),
            "scenario_ids": list(scenario_ids),
            "cumulative_scenario_ids": list(scenario_ids),
        }
        result_payload = {
            "adoption": adoption_block,
            "requirement_analysis": {"payload": {}},
            "test_design": {"payload": {}},
            "scenario_design": {"payload": {"scenario_drafts": []}},
        }
        run_row.result_payload = _json.dumps(result_payload, ensure_ascii=False)
        db.commit()
        return run_id

    def test_plan_execution_generates_plan_without_creating_runs(self):
        """plan_execution_for_workflow 写入执行计划但绝不创建 execution_runs。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [
                    {"id": 101, "name": "登录主流程", "priority": "P0"},
                    {"id": 102, "name": "登录异常分支", "priority": "P1"},
                ],
            )
            run_id = self._build_run_with_adoption(db, scenario_ids)

            # 起始行数：execution_runs 应当为 0
            runs_before = db.execute(
                text("SELECT COUNT(*) FROM execution_runs")
            ).scalar()
            self.assertEqual(runs_before, 0)

            result = self._svc(db).plan_execution_for_workflow(
                run_id,
                {"environment_id": 1},
            )

            # 返回值断言
            self.assertIsNotNone(result)
            self.assertNotIn("error", result)
            self.assertEqual(result["run_id"], run_id)
            self.assertEqual(result["agent_type"], "execution-planner")
            self.assertEqual(result["status"], "pending_confirm")
            self.assertIsNotNone(result["suggestion_id"])

            # payload 应包含执行计划
            payload = result["payload"]
            self.assertIn("execution_batches", payload)
            self.assertIsInstance(payload["execution_batches"], list)
            # 至少 1 个 batch；fallback 会按优先级分批
            self.assertGreaterEqual(len(payload["execution_batches"]), 1)
            for batch in payload["execution_batches"]:
                self.assertIn("scenario_ids", batch)
                self.assertIn("priority", batch)
                self.assertIn("run_mode", batch)
                # scenario_ids 必须落在 cumulative_scenario_ids 范围内
                for sid in batch["scenario_ids"]:
                    self.assertIn(sid, scenario_ids)

            # 写回 run.result_payload.execution_plan
            refreshed = self._svc(db).get_run(run_id)
            exec_plan = refreshed["result_payload"].get("execution_plan") or {}
            self.assertEqual(exec_plan.get("status"), "pending_confirm")
            self.assertEqual(
                exec_plan.get("agent_type"), "execution-planner"
            )
            self.assertEqual(
                exec_plan.get("suggestion_id"), result["suggestion_id"]
            )

            # 关键断言：plan 阶段绝不创建 execution_runs
            runs_after = db.execute(
                text("SELECT COUNT(*) FROM execution_runs")
            ).scalar()
            self.assertEqual(runs_after, 0)
        finally:
            db.close()

    def test_plan_execution_rejects_run_without_adopted_scenarios(self):
        """累计采纳场景为空时应返回 WORKFLOW_NO_SCENARIOS。"""
        db = _make_session()
        try:
            run = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "空场景",
                    "source_type": "prd",
                    "content": "无场景的测试。",
                }
            )
            run_id = run["id"]
            from app.models.ai import AIWorkflowRun
            import json as _json

            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            # adoption 块存在但 cumulative_scenario_ids 为空
            run_row.result_payload = _json.dumps(
                {
                    "adoption": {
                        "status": "completed",
                        "cumulative_scenario_ids": [],
                        "scenario_ids": [],
                    },
                },
                ensure_ascii=False,
            )
            db.commit()

            result = self._svc(db).plan_execution_for_workflow(
                run_id, {"environment_id": 1}
            )
            self.assertIsNotNone(result)
            self.assertIn("error", result)
            self.assertEqual(result["error"]["code"], "WORKFLOW_NO_SCENARIOS")
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["payload"]["execution_batches"], [])

            # execution_runs 仍为 0
            runs_after = db.execute(
                text("SELECT COUNT(*) FROM execution_runs")
            ).scalar()
            self.assertEqual(runs_after, 0)
        finally:
            db.close()

    def test_plan_execution_filters_scenarios_to_cumulative(self):
        """显式传入 scenario_ids 时应与 cumulative 取交集，排除非本 workflow 场景。"""
        db = _make_session()
        try:
            # 累计采纳的场景只有 101
            cumulative = [101]
            self._insert_scenarios(
                db,
                [
                    {"id": 101, "name": "本 workflow 场景", "priority": "P0"},
                    # 999 故意不纳入 cumulative，模拟别的 workflow 采纳的
                    {"id": 999, "name": "外部场景", "priority": "P1"},
                ],
            )
            run_id = self._build_run_with_adoption(db, cumulative)

            # 显式请求 101 + 999（外部）
            result = self._svc(db).plan_execution_for_workflow(
                run_id,
                {"environment_id": 1, "scenario_ids": [101, 999]},
            )
            self.assertIsNotNone(result)
            self.assertNotIn("error", result)

            # 收集所有 batch 的 scenario_ids
            all_ids: set = set()
            for batch in result["payload"]["execution_batches"]:
                all_ids.update(batch.get("scenario_ids") or [])
            # 999 必须在 allowed 之外
            self.assertNotIn(999, all_ids)
            # 101 应被包含
            self.assertIn(101, all_ids)
        finally:
            db.close()

    def test_confirm_rejects_when_no_plan(self):
        """没有执行计划时直接 confirm 必须返回 WORKFLOW_EXECUTION_PLAN_MISSING。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [{"id": 201, "name": "没有计划直接确认", "priority": "P0"}],
            )
            run_id = self._build_run_with_adoption(db, scenario_ids)

            # 跳过 plan 直接 confirm
            result = self._svc(db).confirm_execution_plan_for_workflow(
                run_id, {"environment_id": 1}
            )
            self.assertIsNotNone(result)
            self.assertIn("error", result)
            self.assertEqual(
                result["error"]["code"], "WORKFLOW_EXECUTION_PLAN_MISSING"
            )
            self.assertEqual(result["execution_run_ids"], [])

            # execution_runs 仍为 0
            runs_after = db.execute(
                text("SELECT COUNT(*) FROM execution_runs")
            ).scalar()
            self.assertEqual(runs_after, 0)
        finally:
            db.close()

    def test_confirm_execution_creates_runs_for_plan_scenarios(self):
        """confirm 后必须真正写入 execution_runs，且 confirmation 记录在 result_payload。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [
                    {"id": 301, "name": "执行场景 A", "priority": "P0"},
                    {"id": 302, "name": "执行场景 B", "priority": "P1"},
                ],
            )
            run_id = self._build_run_with_adoption(db, scenario_ids)

            # 1) 先生成执行计划
            plan_result = self._svc(db).plan_execution_for_workflow(
                run_id, {"environment_id": 1}
            )
            self.assertIsNotNone(plan_result)
            self.assertNotIn("error", plan_result)

            # 计划阶段不该产生 execution_runs
            runs_before_confirm = db.execute(
                text("SELECT COUNT(*) FROM execution_runs")
            ).scalar()
            self.assertEqual(runs_before_confirm, 0)

            # 2) patch _run_scenario_background 以免触发真实 HTTP 调用
            from app.services import ai_workflow_service as wf_module

            with patch.object(
                wf_module,
                "_run_scenario_background",
                new=lambda run_id, scenario_id: None,
            ):
                confirm = self._svc(db).confirm_execution_plan_for_workflow(
                    run_id,
                    {"environment_id": 1},
                )

            # 返回值断言
            self.assertIsNotNone(confirm)
            self.assertNotIn("error", confirm)
            self.assertEqual(confirm["run_id"], run_id)
            self.assertEqual(confirm["status"], "started")
            self.assertEqual(confirm["environment_id"], 1)
            self.assertEqual(
                sorted(confirm["scenario_ids"]), sorted(scenario_ids)
            )
            self.assertEqual(len(confirm["execution_run_ids"]), len(scenario_ids))

            # 真实落库：execution_runs 行数 == scenario 数
            run_rows = db.execute(
                text(
                    "SELECT id, run_type, target_id, environment_id, status "
                    "FROM execution_runs ORDER BY id"
                )
            ).mappings().all()
            self.assertEqual(len(run_rows), len(scenario_ids))
            for row in run_rows:
                self.assertEqual(row["run_type"], "scenario")
                self.assertIn(row["target_id"], scenario_ids)
                self.assertEqual(row["environment_id"], 1)
                # start_execution 立即置为 running
                self.assertEqual(row["status"], "running")

            # confirmation 记录应写回 result_payload.execution_confirmation
            refreshed = self._svc(db).get_run(run_id)
            confirmation = (
                refreshed["result_payload"].get("execution_confirmation") or {}
            )
            self.assertEqual(confirmation.get("status"), "started")
            self.assertEqual(
                sorted(confirmation.get("scenario_ids") or []),
                sorted(scenario_ids),
            )
            self.assertEqual(confirmation.get("environment_id"), 1)
            self.assertEqual(
                sorted(confirmation.get("execution_run_ids") or []),
                sorted(confirm["execution_run_ids"]),
            )
            self.assertIn("confirmed_at", confirmation)
        finally:
            db.close()

    def test_confirm_execution_supports_batch_index_filter(self):
        """通过 batch_indexes 选择性执行：只执行所选 batch 内的场景。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [
                    {"id": 401, "name": "P0 场景", "priority": "P0"},
                    {"id": 402, "name": "P2 场景", "priority": "P2"},
                ],
            )
            run_id = self._build_run_with_adoption(db, scenario_ids)

            plan_result = self._svc(db).plan_execution_for_workflow(
                run_id, {"environment_id": 1}
            )
            self.assertIsNotNone(plan_result)
            batches = plan_result["payload"]["execution_batches"]
            # 找到只含 P0 场景的 batch 索引
            p0_batch_index = None
            for idx, batch in enumerate(batches):
                if 401 in (batch.get("scenario_ids") or []):
                    p0_batch_index = idx
                    break
            self.assertIsNotNone(p0_batch_index)

            from app.services import ai_workflow_service as wf_module

            with patch.object(
                wf_module,
                "_run_scenario_background",
                new=lambda run_id, scenario_id: None,
            ):
                confirm = self._svc(db).confirm_execution_plan_for_workflow(
                    run_id,
                    {
                        "environment_id": 1,
                        "batch_indexes": [p0_batch_index],
                    },
                )

            self.assertIsNotNone(confirm)
            self.assertNotIn("error", confirm)
            # 只应启动 P0 场景
            self.assertEqual(confirm["scenario_ids"], [401])
            self.assertEqual(len(confirm["execution_run_ids"]), 1)

            run_rows = db.execute(
                text("SELECT target_id FROM execution_runs ORDER BY id")
            ).mappings().all()
            self.assertEqual(len(run_rows), 1)
            self.assertEqual(run_rows[0]["target_id"], 401)
        finally:
            db.close()

    def test_confirm_execution_dedupes_scenario_ids_across_batches(self):
        """同一 scenario_id 出现在多个 batch 时，confirm 只能创建一条 execution_run。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [
                    {"id": 501, "name": "重复场景", "priority": "P0"},
                    {"id": 502, "name": "独立场景", "priority": "P1"},
                ],
            )
            run_id = self._build_run_with_adoption(db, scenario_ids)

            # 先正常生成 plan（fallback 不会让 501 重复出现，需要手工注入一个跨 batch 重复的 plan）
            self._svc(db).plan_execution_for_workflow(run_id, {"environment_id": 1})

            from app.models.ai import AIWorkflowRun
            import json as _json

            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            payload = _json.loads(run_row.result_payload)
            # 手工构造：501 同时出现在 batch 0 / batch 1；验证 confirm 后只剩一条 run
            payload["execution_plan"] = {
                "suggestion_id": 9001,
                "agent_type": "execution-planner",
                "status": "pending_confirm",
                "payload": {
                    "summary": "跨 batch 重复场景测试。",
                    "execution_batches": [
                        {
                            "name": "P0 主路径批次",
                            "priority": "P0",
                            "run_mode": "sequential",
                            "scenario_ids": [501, 502],
                            "rationale": "覆盖重复场景",
                        },
                        {
                            "name": "P0 重复批次",
                            "priority": "P0",
                            "run_mode": "sequential",
                            "scenario_ids": [501],
                            "rationale": "故意重复",
                        },
                    ],
                    "pre_checks": [],
                    "risks": [],
                    "warnings": [],
                },
            }
            run_row.result_payload = _json.dumps(payload, ensure_ascii=False)
            db.commit()

            from app.services import ai_workflow_service as wf_module

            with patch.object(
                wf_module,
                "_run_scenario_background",
                new=lambda run_id, scenario_id: None,
            ):
                confirm = self._svc(db).confirm_execution_plan_for_workflow(
                    run_id, {"environment_id": 1}
                )

            self.assertIsNotNone(confirm)
            self.assertNotIn("error", confirm)
            # scenario_ids 必须去重：顺序为 [501, 502]
            self.assertEqual(confirm["scenario_ids"], [501, 502])
            self.assertEqual(len(confirm["execution_run_ids"]), 2)

            # 业务表真实行数也必须是 2，不能出现 501 重复
            run_rows = db.execute(
                text(
                    "SELECT target_id, status FROM execution_runs ORDER BY id"
                )
            ).mappings().all()
            self.assertEqual(len(run_rows), 2)
            target_ids = [row["target_id"] for row in run_rows]
            self.assertEqual(sorted(target_ids), [501, 502])
            for row in run_rows:
                self.assertEqual(row["status"], "running")
        finally:
            db.close()

    def test_confirm_execution_dedupes_when_selecting_overlapping_batches(self):
        """显式选择两个包含同一 scenario_id 的 batch 时也应去重。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [
                    {"id": 601, "name": "重复 A", "priority": "P0"},
                    {"id": 602, "name": "重复 B", "priority": "P1"},
                ],
            )
            run_id = self._build_run_with_adoption(db, scenario_ids)

            self._svc(db).plan_execution_for_workflow(run_id, {"environment_id": 1})

            from app.models.ai import AIWorkflowRun
            import json as _json

            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            payload = _json.loads(run_row.result_payload)
            payload["execution_plan"] = {
                "suggestion_id": 9002,
                "agent_type": "execution-planner",
                "status": "pending_confirm",
                "payload": {
                    "summary": "显式选择重复 batch 测试。",
                    "execution_batches": [
                        {
                            "name": "批次 1",
                            "priority": "P0",
                            "run_mode": "sequential",
                            "scenario_ids": [601, 602],
                        },
                        {
                            "name": "批次 2",
                            "priority": "P1",
                            "run_mode": "sequential",
                            "scenario_ids": [601],
                        },
                    ],
                    "pre_checks": [],
                    "risks": [],
                    "warnings": [],
                },
            }
            run_row.result_payload = _json.dumps(payload, ensure_ascii=False)
            db.commit()

            from app.services import ai_workflow_service as wf_module

            with patch.object(
                wf_module,
                "_run_scenario_background",
                new=lambda run_id, scenario_id: None,
            ):
                confirm = self._svc(db).confirm_execution_plan_for_workflow(
                    run_id,
                    {"environment_id": 1, "batch_indexes": [0, 1]},
                )

            self.assertIsNotNone(confirm)
            self.assertNotIn("error", confirm)
            # 顺序：601 (在 batch 0 先出现) → 602 → 601 被去重
            self.assertEqual(confirm["scenario_ids"], [601, 602])
            self.assertEqual(len(confirm["execution_run_ids"]), 2)

            run_rows = db.execute(
                text("SELECT target_id FROM execution_runs ORDER BY id")
            ).mappings().all()
            self.assertEqual(len(run_rows), 2)
            self.assertEqual(
                sorted(row["target_id"] for row in run_rows), [601, 602]
            )
        finally:
            db.close()

    def test_unique_ints_helper_preserves_first_occurrence(self):
        """_unique_ints 静态助手应保持首次出现顺序、跳过非整数。"""
        from app.services.ai_workflow_service import AIWorkflowService

        result = AIWorkflowService._unique_ints(
            [501, "501", 502, None, "oops", 503, 501, 502]
        )
        self.assertEqual(result, [501, 502, 503])

        # None / 空 / 非可迭代输入应安全回落
        self.assertEqual(AIWorkflowService._unique_ints(None), [])
        self.assertEqual(AIWorkflowService._unique_ints([]), [])


    # ── Phase 6: Execution Result Analyst Agent ─────────────────────────────

    @staticmethod
    def _insert_execution_runs(db, run_records):
        """直接往 execution_runs 插入行，返回 (id, scenario_id) 列表。"""
        inserted = []
        for record in run_records:
            db.execute(
                text(
                    """
                    INSERT INTO execution_runs
                      (id, run_type, target_id, environment_id, status,
                       started_at, finished_at, duration_ms, summary)
                    VALUES
                      (:id, :run_type, :target_id, :environment_id, :status,
                       :started_at, :finished_at, :duration_ms, :summary)
                    """
                ),
                {
                    "id": record["id"],
                    "run_type": record.get("run_type", "scenario"),
                    "target_id": record["target_id"],
                    "environment_id": record.get("environment_id", 1),
                    "status": record.get("status", "running"),
                    "started_at": record.get("started_at"),
                    "finished_at": record.get("finished_at"),
                    "duration_ms": record.get("duration_ms"),
                    "summary": record.get("summary", "{}"),
                },
            )
            inserted.append((record["id"], record["target_id"]))
        db.commit()
        return inserted

    def _seed_run_with_confirmation(
        self, db, scenario_ids, execution_run_records
    ):
        """构造一个已 completed + 含 execution_confirmation 的 workflow run。

        返回 (run_id, confirmation_execution_run_ids)。
        """
        run_id = self._build_run_with_adoption(db, scenario_ids)
        from app.models.ai import AIWorkflowRun
        import json as _json

        run_row = (
            db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
        )
        confirmation_run_ids = [
            record["id"] for record in execution_run_records
        ]
        self._insert_execution_runs(db, execution_run_records)
        payload = _json.loads(run_row.result_payload)
        payload["execution_confirmation"] = {
            "status": "started",
            "confirmed_at": "2026-06-02T00:00:00Z",
            "confirmed_by": None,
            "environment_id": 1,
            "execution_run_ids": confirmation_run_ids,
            "scenario_ids": list(scenario_ids),
        }
        run_row.result_payload = _json.dumps(payload, ensure_ascii=False)
        db.commit()
        return run_id, confirmation_run_ids

    def test_analyze_execution_returns_none_for_missing_run(self):
        """run 不存在时直接返回 None，便于 router 转 404。"""
        db = _make_session()
        try:
            self.assertIsNone(
                self._svc(db).analyze_execution_results_for_workflow(
                    99999, {"include_running": True}
                )
            )
        finally:
            db.close()

    def test_analyze_execution_rejects_run_without_confirmation(self):
        """没有 execution_confirmation 时必须返回 WORKFLOW_EXECUTION_CONFIRMATION_MISSING。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [{"id": 801, "name": "未确认的场景", "priority": "P2"}],
            )
            # _build_run_with_adoption 不写 execution_confirmation
            run_id = self._build_run_with_adoption(db, scenario_ids)

            result = self._svc(db).analyze_execution_results_for_workflow(
                run_id, {"include_running": True}
            )
            self.assertIsNotNone(result)
            self.assertIn("error", result)
            self.assertEqual(
                result["error"]["code"],
                "WORKFLOW_EXECUTION_CONFIRMATION_MISSING",
            )
            self.assertEqual(result["status"], "error")
            # execution_analysis 不应被写回
            refreshed = self._svc(db).get_run(run_id)
            self.assertNotIn(
                "execution_analysis", refreshed.get("result_payload") or {}
            )
        finally:
            db.close()

    def test_analyze_execution_rejects_run_with_other_workflow_type(self):
        """非 requirement_to_test_design 类型必须返回 WORKFLOW_TYPE_MISMATCH。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            from datetime import datetime
            run = AIWorkflowRun(
                workflow_type="requirement_to_release",
                status="completed",
                source_name="x",
                source_type="prd",
                input_payload="{}",
                result_payload="{}",
                current_step="completed",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            result = self._svc(db).analyze_execution_results_for_workflow(
                run.id, {"include_running": True}
            )
            self.assertIsNotNone(result)
            self.assertEqual(
                result["error"]["code"], "WORKFLOW_TYPE_MISMATCH"
            )
        finally:
            db.close()

    def test_analyze_execution_filters_to_workflow_confirmation_runs(self):
        """显式 execution_run_ids 不在白名单时必须返回 TARGET_EMPTY。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [{"id": 901, "name": "白名单场景", "priority": "P0"}],
            )
            run_id, confirmation_run_ids = self._seed_run_with_confirmation(
                db,
                scenario_ids,
                [
                    {
                        "id": 1001,
                        "target_id": 901,
                        "status": "passed",
                        "summary": "{}",
                    }
                ],
            )

            # 9999 是别的 workflow 启动的，不在本白名单
            result = self._svc(db).analyze_execution_results_for_workflow(
                run_id,
                {"execution_run_ids": [9999], "include_running": True},
            )
            self.assertIsNotNone(result)
            self.assertEqual(
                result["error"]["code"],
                "WORKFLOW_EXECUTION_ANALYSIS_TARGET_EMPTY",
            )
            # 不应写回 execution_analysis
            refreshed = self._svc(db).get_run(run_id)
            self.assertNotIn(
                "execution_analysis", refreshed.get("result_payload") or {}
            )

            # 显式白名单内的 id 应可正常分析
            ok = self._svc(db).analyze_execution_results_for_workflow(
                run_id,
                {"execution_run_ids": [1001], "include_running": True},
            )
            self.assertIsNotNone(ok)
            self.assertNotIn("error", ok)
            self.assertEqual(ok["status"], "completed")
        finally:
            db.close()

    def test_analyze_execution_persists_result_payload_execution_analysis(self):
        """必须采集 execution_runs + scenarios + reports 写回 execution_analysis。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [
                    {
                        "id": 1001,
                        "name": "登录主流程",
                        "scenario_type": "functional",
                        "priority": "P0",
                    },
                    {
                        "id": 1002,
                        "name": "登录异常分支",
                        "scenario_type": "api",
                        "priority": "P1",
                    },
                ],
            )
            run_id, confirmation_run_ids = self._seed_run_with_confirmation(
                db,
                scenario_ids,
                [
                    {
                        "id": 2001,
                        "target_id": 1001,
                        "status": "passed",
                        "duration_ms": 1500,
                        "summary": '{"passed_steps":3,"failed_steps":0,"total_steps":3}',
                    },
                    {
                        "id": 2002,
                        "target_id": 1002,
                        "status": "failed",
                        "duration_ms": 800,
                        "summary": '{"passed_steps":1,"failed_steps":2,"total_steps":3,"error_message":"assertion failed"}',
                    },
                ],
            )

            # 写一条关联 report
            db.execute(
                text(
                    """
                    INSERT INTO reports
                      (name, report_type, target_id, target_name, summary, metrics)
                    VALUES
                      (:name, :report_type, :target_id, :target_name, :summary, :metrics)
                    """
                ),
                {
                    "name": "2001 report",
                    "report_type": "execution",
                    "target_id": 2001,
                    "target_name": "登录主流程",
                    "summary": '{"total":3,"passed":3,"failed":0,"pass_rate":1.0}',
                    "metrics": "{}",
                },
            )
            db.commit()

            result = self._svc(db).analyze_execution_results_for_workflow(
                run_id, {"include_running": True}
            )
            self.assertIsNotNone(result)
            self.assertNotIn("error", result)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(
                result["agent_type"], "execution-result-analyst"
            )
            self.assertIsNotNone(result.get("suggestion_id"))

            payload = result["payload"]
            self.assertEqual(
                payload["overall_status"], "failed"
            )  # 存在 failed
            # 1/2 = 50% failed ratio → 触发 critical 阈值；保留 medium/high 是为
            # 了兼容后续 ratio 调整或阈值变更
            self.assertIn(payload["risk_level"], {"medium", "high", "critical"})
            self.assertGreaterEqual(payload["pass_rate"], 0.0)
            self.assertLessEqual(payload["pass_rate"], 1.0)
            self.assertEqual(len(payload["failed_scenarios"]), 1)
            failed = payload["failed_scenarios"][0]
            self.assertEqual(failed["scenario_id"], 1002)
            self.assertEqual(failed["execution_run_id"], 2002)
            self.assertEqual(payload["report_ids"], [1])

            # 关键断言：写回 result_payload.execution_analysis
            refreshed = self._svc(db).get_run(run_id)
            analysis = refreshed["result_payload"].get("execution_analysis") or {}
            self.assertEqual(
                analysis.get("agent_type"), "execution-result-analyst"
            )
            self.assertEqual(analysis.get("status"), "completed")
            self.assertEqual(
                analysis.get("suggestion_id"), result["suggestion_id"]
            )
            self.assertEqual(
                analysis.get("payload", {}).get("overall_status"),
                payload["overall_status"],
            )

            # 关键：业务表不应被修改（无新 execution_runs、无新 requirement_items / test_cases / scenarios / defects）
            runs_count = db.execute(
                text("SELECT COUNT(*) FROM execution_runs")
            ).scalar()
            self.assertEqual(runs_count, len(confirmation_run_ids))
            self.assertEqual(
                db.execute(text("SELECT COUNT(*) FROM requirement_items")).scalar(),
                0,
            )
            self.assertEqual(
                db.execute(text("SELECT COUNT(*) FROM test_cases")).scalar(), 0
            )
        finally:
            db.close()

    def test_analyze_execution_excludes_running_when_include_running_false(self):
        """include_running=False 应过滤掉 running/pending run。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [
                    {
                        "id": 1101,
                        "name": "P0 场景",
                        "priority": "P0",
                    },
                    {
                        "id": 1102,
                        "name": "P1 场景",
                        "priority": "P1",
                    },
                ],
            )
            run_id, _ = self._seed_run_with_confirmation(
                db,
                scenario_ids,
                [
                    {
                        "id": 3001,
                        "target_id": 1101,
                        "status": "running",
                        "summary": "{}",
                    },
                    {
                        "id": 3002,
                        "target_id": 1102,
                        "status": "passed",
                        "summary": "{}",
                    },
                ],
            )

            # 默认 include_running=True：两条都会进 Agent 输入
            result_all = self._svc(db).analyze_execution_results_for_workflow(
                run_id, {"include_running": True}
            )
            self.assertIsNotNone(result_all)
            self.assertNotIn("error", result_all)

            # include_running=False：3001 仍可能被 Agent 看到（filter 发生在 service
            # 之前的 _collect_execution_runs_payload 路径上），但 fallback 仍基于
            # 实际采集到的 runs 计数。检查 _collect 行为：只把非 running 传给 Agent。
            from app.services.ai_workflow_service import AIWorkflowService

            collected = self._svc(db)._collect_execution_runs_payload(
                execution_run_ids=[3001, 3002],
                include_running=False,
            )
            self.assertEqual(
                [item["execution_run_id"] for item in collected], [3002]
            )

            collected_with_running = self._svc(db)._collect_execution_runs_payload(
                execution_run_ids=[3001, 3002],
                include_running=True,
            )
            self.assertEqual(
                sorted(item["execution_run_id"] for item in collected_with_running),
                [3001, 3002],
            )
        finally:
            db.close()

    def test_analyze_execution_falls_back_when_no_ai_config(self):
        """无 AI 配置时仍能基于 passed/failed/running 计算结果。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [{"id": 1201, "name": "全失败场景", "priority": "P0"}],
            )
            run_id, _ = self._seed_run_with_confirmation(
                db,
                scenario_ids,
                [
                    {
                        "id": 4001,
                        "target_id": 1201,
                        "status": "failed",
                        "summary": '{"error_message":"boom"}',
                    },
                    {
                        "id": 4002,
                        "target_id": 1201,
                        "status": "failed",
                        "summary": '{"error_message":"still boom"}',
                    },
                ],
            )

            result = self._svc(db).analyze_execution_results_for_workflow(
                run_id, {"include_running": True}
            )
            self.assertIsNotNone(result)
            self.assertNotIn("error", result)
            payload = result["payload"]
            # 全部失败 → failed / critical
            self.assertEqual(payload["overall_status"], "failed")
            self.assertEqual(payload["risk_level"], "critical")
            self.assertEqual(payload["pass_rate"], 0.0)
            self.assertEqual(len(payload["failed_scenarios"]), 2)
            # 包含 create_defect 的建议
            action_types = {a["type"] for a in payload["recommended_actions"]}
            self.assertIn("create_defect", action_types)
        finally:
            db.close()

    def test_collect_execution_runs_payload_includes_report_metrics(self):
        """_collect_execution_runs_payload 必须把 report.metrics 一并传给 Agent。"""
        db = _make_session()
        try:
            scenario_ids = self._insert_scenarios(
                db,
                [
                    {
                        "id": 1301,
                        "name": "场景 M",
                        "scenario_type": "functional",
                        "priority": "P1",
                    }
                ],
            )
            run_id, _ = self._seed_run_with_confirmation(
                db,
                scenario_ids,
                [
                    {
                        "id": 5001,
                        "target_id": 1301,
                        "status": "failed",
                        "duration_ms": 1200,
                        "summary": '{"passed_steps":1,"failed_steps":1,"total_steps":2}',
                    }
                ],
            )
            db.execute(
                text(
                    """
                    INSERT INTO reports
                      (name, report_type, target_id, target_name, summary, metrics)
                    VALUES
                      (:name, :report_type, :target_id, :target_name, :summary, :metrics)
                    """
                ),
                {
                    "name": "5001 report",
                    "report_type": "execution",
                    "target_id": 5001,
                    "target_name": "场景 M",
                    "summary": '{"total":2,"passed":1,"failed":1}',
                    "metrics": '{"duration_distribution":{"p50":120,"p95":1500},"failure_breakdown":{"assertion":1}}',
                },
            )
            db.commit()

            payload = self._svc(db)._collect_execution_runs_payload(
                execution_run_ids=[5001],
                include_running=True,
            )
            self.assertEqual(len(payload), 1)
            run_payload = payload[0]
            self.assertEqual(run_payload["report_id"], 1)
            self.assertIn("report_metrics", run_payload)
            self.assertEqual(
                run_payload["report_metrics"]["failure_breakdown"]["assertion"], 1
            )
            self.assertEqual(
                run_payload["report_metrics"]["duration_distribution"]["p50"], 120
            )
        finally:
            db.close()

    def test_analyze_execution_agent_service_filters_out_of_bounds_references(self):
        """Service 层兜底：AIAgentService._normalize_execution_analysis_payload 必须
        复用 AIService 白名单规则，过滤 LLM 幻觉的 execution_run_id / report_id。"""
        from unittest.mock import MagicMock
        from app.services.ai_agent_service import AIAgentService

        runs = [
            {
                "execution_run_id": 7001,
                "scenario_id": 8001,
                "scenario_name": "A",
                "status": "failed",
                "report_id": 91,
            }
        ]
        # 模拟 LLM 越界输出（execution_run_id 6000 / report_id 80 都不在白名单）
        llm_payload = {
            "summary": "x",
            "overall_status": "failed",
            "risk_level": "high",
            "pass_rate": 0.0,
            "failed_scenarios": [
                {
                    "scenario_id": 8001,
                    "scenario_name": "A",
                    "execution_run_id": 7001,
                    "reason": "ok",
                },
                {
                    "scenario_id": 9999,
                    "scenario_name": "ghost",
                    "execution_run_id": 6000,
                    "reason": "out of bounds",
                },
            ],
            "report_ids": [91, 80],
            "warnings": [],
        }
        # mock ai_service 仅暴露必要方法
        ai_service = MagicMock()
        result = AIAgentService._normalize_execution_analysis_payload(
            llm_payload, runs=runs
        )
        # 8001 命中 allowed_scenario_ids 保留；6000 越界丢弃
        self.assertEqual(len(result["failed_scenarios"]), 1)
        self.assertEqual(result["failed_scenarios"][0]["execution_run_id"], 7001)
        # 80 不在 allowed_report_ids 内
        self.assertEqual(result["report_ids"], [91])

    # ── 七期 A：origin 追踪 / 按来源查询 / 从需求启动 ─────────────────

    def test_workflow_persists_origin_in_input_payload(self):
        """origin_* 字段必须写入 AIWorkflowRun.input_payload 摘要。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "需求管理-登录",
                    "source_type": "requirement_item",
                    "content": "登录需求。",
                    "project_id": 7,
                    "origin_module": "requirement",
                    "origin_type": "requirement_item",
                    "origin_ids": [101, 102],
                    "origin_meta": {"requirement_count": 2, "titles": ["登录", "退出"]},
                }
            )
            run_id = result["id"]
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            input_payload = _json.loads(run_row.input_payload)
            self.assertEqual(input_payload["origin_module"], "requirement")
            self.assertEqual(input_payload["origin_type"], "requirement_item")
            self.assertEqual(input_payload["origin_ids"], [101, 102])
            self.assertEqual(input_payload["origin_meta"]["requirement_count"], 2)
        finally:
            db.close()

    def test_workflow_writes_trace_meta_with_origin_in_result_payload(self):
        """result_payload.trace_meta 必须包含 workflow_run_id + origin 字段。"""
        db = _make_session()
        try:
            import json as _json

            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "需求管理",
                    "source_type": "requirement_item",
                    "content": "登录需求。",
                    "origin_module": "requirement",
                    "origin_type": "requirement_item",
                    "origin_ids": [201],
                    "origin_meta": {"requirement_count": 1, "titles": ["登录"]},
                }
            )
            trace_meta = result["result_payload"].get("trace_meta") or {}
            self.assertEqual(trace_meta.get("workflow_run_id"), result["id"])
            self.assertEqual(trace_meta.get("origin_module"), "requirement")
            self.assertEqual(trace_meta.get("origin_type"), "requirement_item")
            self.assertEqual(trace_meta.get("origin_ids"), [201])
            self.assertEqual(trace_meta.get("origin_meta", {}).get("requirement_count"), 1)
        finally:
            db.close()

    def test_step_inputs_preserve_origin_context(self):
        """三个 step input payload 都应保留 origin 字段。"""
        db = _make_session()
        try:
            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "需求管理",
                    "source_type": "requirement_item",
                    "content": "登录需求。",
                    "origin_module": "requirement",
                    "origin_type": "requirement_item",
                    "origin_ids": [301, 302],
                    "origin_meta": {"requirement_count": 2},
                }
            )
            steps = result["steps"]
            for step in steps:
                inp = step["input_payload"]
                self.assertEqual(inp.get("origin_module"), "requirement")
                self.assertEqual(inp.get("origin_type"), "requirement_item")
                self.assertEqual(inp.get("origin_ids"), [301, 302])
        finally:
            db.close()

    def test_input_summary_origin_validator_silently_drops_invalid_values(self):
        """白名单外的 origin_module/origin_type 必须静默置空。"""
        from app.schemas.ai import StartRequirementWorkflowRequest

        req = StartRequirementWorkflowRequest(
            source_name="x",
            source_type="prd",
            content="y",
            origin_module="case",  # 合法
            origin_type="garbage",  # 非法 → 置空
            origin_ids=[1, 2],
        )
        self.assertEqual(req.origin_module, "case")
        self.assertIsNone(req.origin_type)

    def _insert_requirement(self, db, **overrides):
        """通过 SQL 直插一条 requirement_item，绕开 create_requirement 校验。"""
        import json as _json

        defaults = {
            "project_id": 1,
            "version_id": None,
            "iteration_id": None,
            "title": "默认需求",
            "description": "",
            "source_type": "user_story",
            "source_key": "REQ-1",
            "priority": "P2",
            "status": "open",
            "owner_id": None,
        }
        defaults.update(overrides)
        row = db.execute(
            text(
                """
                INSERT INTO requirement_items
                  (project_id, version_id, iteration_id, title, description,
                   source_type, source_key, priority, status, owner_id, created_at, updated_at)
                VALUES
                  (:project_id, :version_id, :iteration_id, :title, :description,
                   :source_type, :source_key, :priority, :status, :owner_id,
                   CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            defaults,
        )
        db.commit()
        return row.lastrowid

    def test_start_workflow_from_requirements_success(self):
        """正常路径：单条需求 → 启动 workflow，input/origin 正确写入。"""
        db = _make_session()
        try:
            from app.models.ai import AIWorkflowRun
            import json as _json

            req_id = self._insert_requirement(
                db,
                project_id=1,
                title="登录主流程",
                description="手机号+密码登录",
                source_type="user_story",
                source_key="REQ-LOGIN-1",
                priority="P0",
                status="open",
            )

            result = self._svc(db).start_workflow_from_requirements(
                {"requirement_ids": [req_id]}
            )
            self.assertIsNone(result.get("error"))
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(result["steps"]), 3)

            run_row = (
                db.query(AIWorkflowRun)
                .filter(AIWorkflowRun.id == result["id"])
                .first()
            )
            input_payload = _json.loads(run_row.input_payload)
            self.assertEqual(input_payload["origin_module"], "requirement")
            self.assertEqual(input_payload["origin_type"], "requirement_item")
            self.assertEqual(input_payload["origin_ids"], [req_id])
            self.assertEqual(input_payload["origin_meta"]["requirement_count"], 1)
            self.assertIn("登录主流程", input_payload["origin_meta"]["titles"])

            # trace_meta
            trace_meta = result["result_payload"].get("trace_meta") or {}
            self.assertEqual(trace_meta.get("origin_ids"), [req_id])
            self.assertEqual(trace_meta.get("origin_module"), "requirement")

            # 关键：不直接写业务表（无新增 requirement_items / test_cases）
            self.assertEqual(
                db.execute(text("SELECT COUNT(*) FROM requirement_items")).scalar(),
                1,
            )
            self.assertEqual(
                db.execute(text("SELECT COUNT(*) FROM test_cases")).scalar(), 0
            )
        finally:
            db.close()

    def test_start_workflow_from_requirements_missing_id_returns_error(self):
        """缺失 ID → REQUIREMENT_NOT_FOUND。"""
        db = _make_session()
        try:
            result = self._svc(db).start_workflow_from_requirements(
                {"requirement_ids": [99999]}
            )
            self.assertIn("error", result)
            self.assertEqual(
                result["error"]["code"], "REQUIREMENT_NOT_FOUND"
            )
            self.assertIn("99999", result["error"]["message"])
        finally:
            db.close()

    def test_start_workflow_from_requirements_cross_project_returns_error(self):
        """跨 project_id → REQUIREMENT_PROJECT_MISMATCH。"""
        db = _make_session()
        try:
            rid_a = self._insert_requirement(
                db, project_id=1, title="A 项目需求", source_key="A-1"
            )
            rid_b = self._insert_requirement(
                db, project_id=2, title="B 项目需求", source_key="B-1"
            )
            result = self._svc(db).start_workflow_from_requirements(
                {"requirement_ids": [rid_a, rid_b]}
            )
            self.assertIn("error", result)
            self.assertEqual(
                result["error"]["code"], "REQUIREMENT_PROJECT_MISMATCH"
            )
        finally:
            db.close()

    def test_start_workflow_from_requirements_consistent_versions(self):
        """同一项目多条需求可正常合并到 workflow。"""
        db = _make_session()
        try:
            rid_a = self._insert_requirement(
                db, project_id=1, title="登录", source_key="L-1", priority="P0"
            )
            rid_b = self._insert_requirement(
                db, project_id=1, title="退出", source_key="L-2", priority="P1"
            )
            result = self._svc(db).start_workflow_from_requirements(
                {"requirement_ids": [rid_a, rid_b]}
            )
            self.assertIsNone(result.get("error"))
            self.assertEqual(result["result_payload"]["trace_meta"]["origin_ids"], [rid_a, rid_b])
        finally:
            db.close()

    def test_list_workflows_by_source_returns_matching_runs(self):
        """按 origin 查到对应 run。"""
        db = _make_session()
        try:
            run_a = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "需求A",
                    "source_type": "requirement_item",
                    "content": "A 需求",
                    "origin_module": "requirement",
                    "origin_type": "requirement_item",
                    "origin_ids": [501],
                }
            )
            run_b = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "需求B",
                    "source_type": "requirement_item",
                    "content": "B 需求",
                    "origin_module": "requirement",
                    "origin_type": "requirement_item",
                    "origin_ids": [502],
                }
            )
            run_c = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "其它来源",
                    "source_type": "prd",
                    "content": "C 需求",
                    "origin_module": "case",
                    "origin_type": "test_case",
                    "origin_ids": [503],
                }
            )

            data = self._svc(db).list_workflows_by_source(
                origin_module="requirement",
                origin_type="requirement_item",
                origin_id=501,
                limit=10,
            )
            self.assertEqual(data["total"], 1)
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["id"], run_a["id"])

            # origin_id 不命中 → 空
            empty = self._svc(db).list_workflows_by_source(
                origin_module="requirement",
                origin_type="requirement_item",
                origin_id=99999,
            )
            self.assertEqual(empty["total"], 0)
            self.assertEqual(empty["items"], [])
        finally:
            db.close()

    def test_list_workflows_by_source_limit_clamped_and_ordering(self):
        """limit 被钳制 + 倒序。"""
        db = _make_session()
        try:
            for idx in range(3):
                self._svc(db).start_requirement_to_test_design(
                    {
                        "source_name": f"需求{idx}",
                        "source_type": "requirement_item",
                        "content": "x",
                        "origin_module": "requirement",
                        "origin_type": "requirement_item",
                        "origin_ids": [900],
                    }
                )
            # limit=2 显式截断
            data = self._svc(db).list_workflows_by_source(
                origin_module="requirement",
                origin_type="requirement_item",
                origin_id=900,
                limit=2,
            )
            self.assertEqual(data["total"], 3)
            self.assertEqual(len(data["items"]), 2)
            # 倒序：items 第一个是最后创建的 run
            ids = [item["id"] for item in data["items"]]
            self.assertGreater(ids[0], ids[1])

            # limit=99 钳制到 20；3 条全部返回
            data_full = self._svc(db).list_workflows_by_source(
                origin_module="requirement",
                origin_type="requirement_item",
                origin_id=900,
                limit=99,  # 超过 20 上限 → 钳制
            )
            self.assertEqual(data_full["total"], 3)
            self.assertEqual(len(data_full["items"]), 3)

            # 不传 limit → 走默认 5
            data_default = self._svc(db).list_workflows_by_source(
                origin_module="requirement",
                origin_type="requirement_item",
                origin_id=900,
            )
            self.assertEqual(len(data_default["items"]), 3)
        finally:
            db.close()

    def test_list_workflows_by_source_skips_legacy_runs_without_origin(self):
        """旧 run（无 origin 字段）不能被命中。"""
        db = _make_session()
        try:
            legacy = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "老数据",
                    "source_type": "prd",
                    "content": "x",
                    # 无 origin_*
                }
            )
            data = self._svc(db).list_workflows_by_source(
                origin_module="requirement",
                origin_type="requirement_item",
                origin_id=legacy["id"],
            )
            self.assertEqual(data["total"], 0)
        finally:
            db.close()

    def test_resolve_async_payload_rebuilds_full_content_from_requirement_ids(self):
        """异步入口: 入参 ``{requirement_ids: [...]}`` 时, 后台必须重建完整
        content/source_name/project_id/version_id/iteration_id/origin_*,不能
        用空 payload 跑 Agent."""
        from app.services.ai_workflow_service import AIWorkflowService

        db = _make_session()
        try:
            db.execute(text("INSERT INTO quality_projects (id, name, code) VALUES (1, 'P1', 'P1')"))
            db.execute(text(
                "INSERT INTO quality_versions (id, project_id, name, code) VALUES (1, 1, 'V1', 'V1')"
            ))
            db.execute(text(
                "INSERT INTO quality_iterations (id, project_id, version_id, name) VALUES (1, 1, 1, 'I1')"
            ))
            db.execute(text(
                "INSERT INTO requirement_items (id, project_id, version_id, iteration_id, "
                "title, description, priority, status) "
                "VALUES (101, 1, 1, 1, 'E2E登录', '真实手机号+密码', 'P0', 'open')"
            ))
            db.commit()

            stored_input = {"origin_module": "requirement", "origin_type": "requirement_item"}
            payload, err = AIWorkflowService._resolve_async_workflow_payload(
                {"requirement_ids": [101]}, stored_input, db
            )
            self.assertIsNone(err, f"重建不应失败: {err}")
            self.assertIsInstance(payload, dict)
            # 重建必须含原需求正文
            self.assertIn("E2E登录", payload.get("content", ""))
            self.assertIn("真实手机号+密码", payload.get("content", ""))
            # 重建必须含 project_id / version_id / iteration_id
            self.assertEqual(payload.get("project_id"), 1)
            self.assertEqual(payload.get("version_id"), 1)
            self.assertEqual(payload.get("iteration_id"), 1)
            # 重建必须含 source_name / source_type
            self.assertTrue(payload.get("source_name"), "source_name 不能为空")
            self.assertEqual(payload.get("source_type"), "requirement_item")
            # 重建必须含 origin
            self.assertEqual(payload.get("origin_module"), "requirement")
            self.assertEqual(payload.get("origin_type"), "requirement_item")
            self.assertIn(101, payload.get("origin_ids") or [])
            # origin_meta 应含原需求元数据
            origin_meta = payload.get("origin_meta") or {}
            self.assertEqual(origin_meta.get("requirement_count"), 1)
            self.assertIn("E2E登录", origin_meta.get("titles") or [])
        finally:
            db.close()

    def test_resolve_async_payload_returns_error_when_requirement_missing(self):
        """异步入口: 重建阶段发现 requirement_ids 缺失时, 必须返回 error,
        不应让 Agent 拿到空 payload 继续跑。"""
        from app.services.ai_workflow_service import AIWorkflowService

        db = _make_session()
        try:
            db.execute(text("INSERT INTO quality_projects (id, name, code) VALUES (1, 'P1', 'P1')"))
            db.execute(text(
                "INSERT INTO quality_versions (id, project_id, name, code) VALUES (1, 1, 'V1', 'V1')"
            ))
            db.execute(text(
                "INSERT INTO quality_iterations (id, project_id, version_id, name) VALUES (1, 1, 1, 'I1')"
            ))
            db.commit()

            payload, err = AIWorkflowService._resolve_async_workflow_payload(
                {"requirement_ids": [99999]}, {}, db
            )
            self.assertIsNone(payload)
            self.assertIsNotNone(err)
            self.assertEqual(err["error"]["code"], "REQUIREMENT_NOT_FOUND")
        finally:
            db.close()

    def test_resolve_async_payload_merges_origin_when_payload_has_content(self):
        """异步入口兼容: payload 已含 content 时, 不重建但合并 origin_* 兜底。"""
        from app.services.ai_workflow_service import AIWorkflowService

        db = _make_session()
        try:
            stored_input = {
                "origin_module": "requirement",
                "origin_type": "requirement_item",
                "origin_ids": [101],
                "origin_meta": {"requirement_count": 1},
            }
            payload = {
                "source_name": "已存在",
                "content": "已是 workflow_payload",
                "requirement_ids": [101],
            }
            result, err = AIWorkflowService._resolve_async_workflow_payload(
                payload, stored_input, db
            )
            self.assertIsNone(err)
            # content 保留原值(未走重建分支)
            self.assertEqual(result.get("content"), "已是 workflow_payload")
            # origin_* 从 stored_input 合并
            self.assertEqual(result.get("origin_module"), "requirement")
            self.assertEqual(result.get("origin_ids"), [101])
            self.assertEqual(result.get("origin_meta"), {"requirement_count": 1})
        finally:
            db.close()

    def test_async_execute_passes_rebuilt_content_to_requirement_analyst(self):
        """端到端: ``create_workflow_run_from_requirements`` 创建的 pending run,
        通过 ``execute_workflow_steps_async`` 后, requirement-analyst 收到的 input
        必须含原需求正文/project_id/version_id/iteration_id/origin_ids,
        不能只拿到 ``{requirement_ids: [...]}`` 空跑。"""
        from app.services import ai_workflow_service as aws_module
        from app.services.ai_agent_service import AIAgentService
        import app.services.ai_workflow_service as aws_module_for_session
        # SessionLocal 是函数内 ``from app.database import SessionLocal``,
        # patch ``app.database.SessionLocal`` 即可影响后续 import。

        db = _make_session()
        try:
            db.execute(text("INSERT INTO quality_projects (id, name, code) VALUES (1, 'P1', 'P1')"))
            db.execute(text(
                "INSERT INTO quality_versions (id, project_id, name, code) VALUES (1, 1, 'V1', 'V1')"
            ))
            db.execute(text(
                "INSERT INTO quality_iterations (id, project_id, version_id, name) VALUES (1, 1, 1, 'I1')"
            ))
            db.execute(text(
                "INSERT INTO requirement_items (id, project_id, version_id, iteration_id, "
                "title, description, priority, status) "
                "VALUES (101, 1, 1, 1, 'E2E登录正文', '真实需求描述内容', 'P0', 'open')"
            ))
            db.commit()

            # 1. 创建 pending run (走真实 service)
            svc = self._svc(db)
            result = svc.create_workflow_run_from_requirements({"requirement_ids": [101]})
            self.assertEqual(result["status"], "pending")
            run_id = result["id"]

            captured: list = []

            def fake_run_analyze(self, payload, created_by=None):
                captured.append(dict(payload))
                return {
                    "suggestion_id": 9001,
                    "agent_type": "requirement-analyst",
                    "status": "completed",
                    "payload": {"summary": "ok", "requirements": []},
                }

            from app.repositories import ai_repository as ai_repo_module
            from app import database as database_module
            with patch.object(AIAgentService, "run_analyze_requirements", fake_run_analyze), \
                 patch.object(database_module, "SessionLocal", return_value=db), \
                 patch.object(ai_repo_module.AIRepository, "get_config", return_value=None):
                aws_module.AIWorkflowService.execute_workflow_steps_async(
                    run_id, {"requirement_ids": [101]}
                )

            self.assertGreaterEqual(len(captured), 1, "requirement-analyst 必须被调用")
            input_payload = captured[0]
            self.assertIn("E2E登录正文", input_payload.get("content", ""))
            self.assertIn("真实需求描述内容", input_payload.get("content", ""))
            self.assertEqual(input_payload.get("project_id"), 1)
            self.assertEqual(input_payload.get("version_id"), 1)
            self.assertEqual(input_payload.get("iteration_id"), 1)
            self.assertIn(101, input_payload.get("origin_ids") or [])
            self.assertEqual(input_payload.get("origin_module"), "requirement")
            self.assertTrue(input_payload.get("source_name"))
        finally:
            db.close()

    def test_async_execute_marks_run_failed_when_rebuild_invalid(self):
        """端到端: 异步 payload 重建失败时, run 必须 status='failed',
        result_payload 含 error 字段, 不能继续空跑 Agent。"""
        from app.services import ai_workflow_service as aws_module
        from app import database as database_module

        db = _make_session()
        try:
            db.execute(text("INSERT INTO quality_projects (id, name, code) VALUES (1, 'P1', 'P1')"))
            db.execute(text(
                "INSERT INTO quality_versions (id, project_id, name, code) VALUES (1, 1, 'V1', 'V1')"
            ))
            db.execute(text(
                "INSERT INTO quality_iterations (id, project_id, version_id, name) VALUES (1, 1, 1, 'I1')"
            ))
            # 不插入 requirement_items, 让 requirement_ids=[99999] 重建失败
            db.commit()

            from app.models.ai import AIWorkflowRun
            run = AIWorkflowRun(
                workflow_type="requirement_to_test_design",
                status="pending",
                source_name="fake",
                source_type="other",
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            run_id = run.id

            with patch.object(database_module, "SessionLocal", return_value=db):
                aws_module.AIWorkflowService.execute_workflow_steps_async(
                    run_id, {"requirement_ids": [99999]}
                )

            # 后台 commit 后 instance 可能过期, 用新 query 拿最新值
            from app.models.ai import AIWorkflowRun as _AWR
            latest = (
                db.query(_AWR)
                .filter(_AWR.id == run_id)
                .one()
            )
            self.assertEqual(latest.status, "failed")
            self.assertEqual(latest.current_step, "failed:async_payload_rebuild")
            import json as _json
            payload = _json.loads(latest.result_payload or "{}")
            self.assertIn("error", payload)
            self.assertEqual(
                (payload.get("error") or {}).get("code"),
                "REQUIREMENT_NOT_FOUND",
            )
        finally:
            db.close()

    # ── Phase 8: 真实模型空输出 / 上游空用例 / current_step 起始更新 ─────────

    def test_scenario_designer_skips_llm_when_test_design_has_no_cases(self):
        """``scenario-designer``: 上游 functional_cases + api_cases 都为空时,
        不应调用 LLM, 直接走 fallback。

        单元层测试: 直接构造一个 ai_service (mock _call_llm) 接到
        ``AIAgentService._build_scenario_design_payload``, 验证 LLM 未被调用。
        """
        from app.services.ai_agent_service import AIAgentService
        from app.services.ai_service import AIService

        db = _make_session()
        try:
            real_ai_service = AIService.__new__(AIService)

            def fake_call_llm(*args, **kwargs):
                raise AssertionError("scenario LLM 不应被调用")

            real_ai_service._call_llm = fake_call_llm
            agent = AIAgentService(db, real_ai_service)
            # 上游 requirement_analysis 提供 1 条 requirement, 但 functional_cases/api_cases 都空
            payload = {
                "source_name": "登录",
                "source_type": "prd",
                "project_id": 1,
                "requirement_analysis": {
                    "payload": {
                        "requirements": [
                            {"title": "登录", "source_key": "REQ-LOGIN-1",
                             "source_type": "prd", "priority": "P0"}
                        ]
                    }
                },
                "test_design": {
                    "payload": {
                        "summary": "AI 返回结构不可用",
                        "test_points": [],
                        "functional_cases": [],
                        "api_cases": [],
                    }
                },
            }
            result = agent._build_scenario_design_payload(payload)
            # 必须有 scenario_draft, 且 LLM 未被调用
            self.assertGreaterEqual(len(result["scenario_drafts"]), 1)
        finally:
            db.close()

    def test_workflow_generates_minimum_cases_and_scenarios_when_test_designer_llm_empty(self):
        """端到端: LLM test-designer 真实空输出时, workflow 必须产出
        >=1 functional_case + >=1 scenario_draft, 不再以 completed + 0 收尾。

        通过给 ``AIService`` 注入 mock _call_llm (返回未闭合 <think>),
        触发 ``_parse_test_design`` 的业务兜底分支, 验证 workflow 三步结果。
        """
        from app.services.ai_workflow_service import AIWorkflowService
        from app.services.ai_service import AIService
        from app.repositories import ai_repository as ai_repo_module
        from app import database as database_module

        db = _make_session()
        try:
            real_ai_service = AIService.__new__(AIService)
            # step 1 正常返回, step 2 模拟真实模型空输出, step 3 不应再调用
            call_log: list = []

            def fake_call_llm(self_or_prompt, *args, **kwargs):
                # AIService._call_llm signature: (prompt, system_prompt="", timeout=None)
                # self bound via instance; call_log 用 prompt 长度区分
                if isinstance(self_or_prompt, AIService):
                    prompt = args[0] if args else kwargs.get("prompt", "")
                else:
                    prompt = self_or_prompt
                call_log.append(prompt[:50])
                if len(call_log) == 1:
                    # step 1 requirement-analyst 正常返回
                    return json.dumps(
                        {
                            "summary": "搜索需求已结构化。",
                            "requirements": [
                                {"title": "支持关键字模糊搜索",
                                 "source_key": "REQ-SEARCH-1",
                                 "source_type": "prd", "priority": "P1"},
                            ],
                            "acceptance_criteria": [
                                {"criteria": "空关键字返回空列表", "priority": "P1"},
                            ],
                            "test_suggestions": [],
                            "ambiguities": [],
                            "risks": [],
                        }
                    )
                # step 2/3 返回未闭合 think, 触发 _parse_test_design 兜底
                return "<think> 模型推理中, 未闭合 tag..."

            # bind: 因为 _call_llm 是 instance method, 用 types.MethodType
            from types import MethodType
            real_ai_service._call_llm = MethodType(fake_call_llm, real_ai_service)
            real_ai_service.model = "fake"

            svc = AIWorkflowService(db, real_ai_service)
            with patch.object(
                ai_repo_module.AIRepository, "get_config", return_value=None
            ), patch.object(database_module, "SessionLocal", return_value=db):
                result = svc.start_requirement_to_test_design(
                    {
                        "source_name": "搜索",
                        "source_type": "prd",
                        "content": "支持关键字模糊搜索。",
                    }
                )

            self.assertEqual(result["status"], "completed")
            # step 2 test-designer 兜底后必须产生 test_points + functional_cases
            design_step = result["steps"][1]
            design_payload = design_step["output_payload"]["payload"]
            self.assertGreaterEqual(len(design_payload["test_points"]), 1)
            self.assertGreaterEqual(len(design_payload["functional_cases"]), 1)
            fc = design_payload["functional_cases"][0]
            self.assertIn("name", fc)
            self.assertIn("priority", fc)
            self.assertIn("steps", fc)
            # functional_cases 不为空时, step 3 仍允许调 LLM
            # (但本次因为 functional_cases 非空, _build_scenario_design_payload 会进 LLM 分支)
            # step 3 scenario-designer 应至少 1 个 scenario_draft
            scenario_step = result["steps"][2]
            drafts = scenario_step["output_payload"]["payload"]["scenario_drafts"]
            self.assertGreaterEqual(len(drafts), 1)
        finally:
            db.close()

    def test_adopt_after_fallback_design_creates_case_and_scenario(self):
        """端到端: test-designer 兜底生成 functional_case + scenario_designer
        兜底 scenario_draft 后, adopt 路径应能落地需求 + 用例 + 场景。"""
        from app.services import ai_workflow_service as wf_module
        from app.services.test_case_service import TestCaseService
        from app.services.ai_agent_service import AIAgentService
        from app.models.ai import AIWorkflowRun
        import json as _json

        db = _make_session()
        try:
            # 准备真实 project / version / iteration, 让 adopt 路径完整写入
            db.execute(text("INSERT INTO quality_projects (id, name, code) VALUES (1, 'P1', 'P1')"))
            db.execute(text(
                "INSERT INTO quality_versions (id, project_id, name, code) VALUES (1, 1, 'V1', 'V1')"
            ))
            db.execute(text(
                "INSERT INTO quality_iterations (id, project_id, version_id, name) VALUES (1, 1, 1, 'I1')"
            ))
            db.commit()

            # 1. 创建一次 workflow, 拿到一个 completed run + run_id
            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "登录",
                    "source_type": "prd",
                    "content": "支持手机号+密码登录。",
                }
            )
            run_id = result["id"]

            # 2. 覆盖 result_payload 为 LLM 空输出但被业务兜底后的产物
            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
            )
            run_row.result_payload = _json.dumps(
                {
                    "requirement_analysis": {
                        "suggestion_id": 11,
                        "agent_type": "requirement-analyst",
                        "status": "pending_review",
                        "payload": {
                            "summary": "登录需求已结构化。",
                            "requirements": [
                                {
                                    "title": "支持手机号+密码登录",
                                    "description": "登录主路径",
                                    "source_type": "prd",
                                    "source_key": "REQ-LOGIN-1",
                                    "priority": "P0",
                                }
                            ],
                            "acceptance_criteria": [
                                {"criteria": "密码错误3次后锁定", "priority": "P0"},
                            ],
                            "test_suggestions": [],
                            "ambiguities": [],
                            "risks": [],
                        },
                        "trace_meta": {},
                    },
                    "test_design": {
                        "suggestion_id": 22,
                        "agent_type": "test-designer",
                        "status": "pending_review",
                        "payload": {
                            "summary": (
                                "AI 返回结构不可用, 已基于需求分析生成兜底测试设计。"
                            ),
                            "test_points": ["覆盖需求点：支持手机号+密码登录"],
                            "functional_cases": [
                                {
                                    "name": "验证登录 - 主路径",
                                    "description": "主路径功能用例",
                                    "priority": "P0",
                                    "steps": [
                                        "准备符合前置条件的数据",
                                        "执行主路径操作",
                                        "验证系统响应与验收点一致",
                                    ],
                                    "expected_result": "登录成功",
                                }
                            ],
                            "api_cases": [],
                            "scenario_drafts": [],
                        },
                        "trace_meta": {},
                    },
                    "scenario_design": {
                        "suggestion_id": 33,
                        "agent_type": "scenario-designer",
                        "status": "pending_review",
                        "payload": {
                            "summary": "AI 未配置, 已基于测试设计草稿生成占位场景。",
                            "scenario_drafts": [
                                {
                                    "name": "登录主路径回归",
                                    "description": "AI 兜底生成的回归场景",
                                    "scenario_type": "e2e",
                                    "priority": "P1",
                                    "steps": [
                                        {
                                            "name": "执行验证登录 - 主路径",
                                            "case_index": 0,
                                            "case_name": "验证登录 - 主路径",
                                            "failure_strategy": "stop",
                                            "timeout_ms": 30000,
                                        }
                                    ],
                                    "expected_outcome": "全部步骤通过",
                                }
                            ],
                        },
                        "trace_meta": {},
                    },
                },
                ensure_ascii=False,
            )
            db.commit()

            requirement_calls: list = []
            case_calls: list = []
            next_requirement_id = [7001]

            def fake_create_requirement(db, data):
                payload = (
                    data.model_dump() if hasattr(data, "model_dump") else dict(data)
                )
                requirement_calls.append(payload)
                rid = next_requirement_id[0]
                next_requirement_id[0] += 1
                return SimpleNamespace(id=rid, **payload)

            def fake_create_case(self, data):
                case_calls.append(dict(data))
                case_id = 8000 + len(case_calls)
                data = dict(data)
                data["id"] = case_id
                return data

            with patch.object(
                wf_module, "create_requirement", new=fake_create_requirement
            ), patch.object(
                TestCaseService, "create_case", new=fake_create_case
            ):
                adopt = self._svc(db).adopt_requirement_to_test_design(
                    run_id,
                    {
                        "project_id": 1,
                        "version_id": 1,
                        "iteration_id": 1,
                        "adopt_requirements": True,
                        "adopt_functional_cases": True,
                        "adopt_api_cases": True,
                        "adopt_scenario_drafts": True,
                        "link_cases_to_requirements": True,
                        "link_scenario_steps_to_cases": True,
                    },
                )

            self.assertIsNotNone(adopt)
            self.assertEqual(
                adopt["summary"]["error_count"], 0,
                f"adopt 不应有 error: {adopt.get('errors')}",
            )
            self.assertEqual(adopt["summary"]["requirements_created"], 1)
            self.assertEqual(adopt["summary"]["cases_created"], 1)
            self.assertEqual(adopt["summary"]["scenarios_created"], 1)
        finally:
            db.close()

    def test_run_step_updates_current_step_when_step_starts(self):
        """``_run_step``: step 启动时必须立即把 ``run.current_step`` 推进到
        当前 agent_type + ``run.status='running'``, 不应停留在上一步状态。"""
        from app.services.ai_workflow_service import AIWorkflowService
        from app.services.ai_agent_service import AIAgentService

        db = _make_session()
        try:
            # 启动一个真实 workflow, 拿到 run row
            result = self._svc(db).start_requirement_to_test_design(
                {
                    "source_name": "下单",
                    "source_type": "prd",
                    "content": "买家下单成功后看到订单详情。",
                }
            )
            run_id = result["id"]
            # 重置 run 状态, 模拟上一轮已 completed 之后再次进入 step
            from app.models.ai import AIWorkflowRun
            from datetime import datetime as _dt

            db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).update(
                {
                    "current_step": "requirement-analyst",
                    "status": "pending",
                }
            )
            db.commit()

            captured: list = []

            def fake_run_design(self, payload, created_by=None):
                # 在 step 内部断言 run.current_step 已是 "test-designer"
                latest = (
                    db.query(AIWorkflowRun)
                    .filter(AIWorkflowRun.id == run_id)
                    .one()
                )
                captured.append(
                    {
                        "current_step": latest.current_step,
                        "status": latest.status,
                    }
                )
                return {
                    "suggestion_id": 909,
                    "agent_type": "test-designer",
                    "status": "pending_review",
                    "payload": {"summary": "ok", "test_points": ["t"]},
                    "trace_meta": {},
                }

            run_row = (
                db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).one()
            )
            with patch.object(
                AIAgentService, "run_design_tests", new=fake_run_design
            ):
                AIWorkflowService._run_step(
                    self._svc(db),
                    run_row,
                    step_order=2,
                    agent_type="test-designer",
                    input_payload={},
                )

            # 抓取的 current_step 应是 test-designer, 而非上一步的 requirement-analyst
            self.assertEqual(captured[0]["current_step"], "test-designer")
            self.assertEqual(captured[0]["status"], "running")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
