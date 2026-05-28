"""
Quality Analytics Service — 质量分析服务

提供版本质量评分、通过率趋势、缺陷趋势、需求覆盖率、发布门禁结论等指标。
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.models.report import Report, Defect, QualityGate
from app.models.quality_foundation import RequirementItem


class QualityAnalyticsService:
    """Service for quality analytics."""

    def __init__(self, db: Session):
        self.db = db

    # ── Overview ─────────────────────────────────────────────────────────────

    def get_overview(
        self,
        project_id: Optional[int] = None,
        version_id: Optional[int] = None,
        iteration_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        scope_note = self._build_scope_note(project_id, version_id, iteration_id)

        # Report stats
        report_query = self.db.query(Report)
        report_filters = self._apply_filters(project_id, version_id, iteration_id, start_date, end_date)
        report_query = report_query.filter(*report_filters)

        report_count = report_query.count()

        # Execution stats from reports
        total_cases = 0
        passed_cases = 0
        failed_cases = 0
        execution_count = 0

        reports = report_query.all()
        for r in reports:
            summary = self._safe_json_loads(r.summary, {})
            passed = summary.get("passed", 0) or 0
            failed = summary.get("failed", 0) or 0
            total = summary.get("total", 0) or 0
            if total > 0 or passed > 0 or failed > 0:
                execution_count += 1
                total_cases += total
                passed_cases += passed
                failed_cases += failed

        avg_pass_rate = 0.0
        if total_cases > 0:
            avg_pass_rate = round(passed_cases / total_cases * 100, 2)

        # Defect stats
        defect_query = self.db.query(Defect)
        defect_filters = self._defect_filters(project_id, version_id, iteration_id)
        defect_query = defect_query.filter(*defect_filters)

        defect_total = defect_query.count()
        defect_p0p1 = defect_query.filter(
            Defect.priority.in_(["P0", "P1"])
        ).count()
        defect_open = defect_query.filter(
            Defect.status.in_(["open", "confirmed"])
        ).count()

        # Requirement coverage
        req_query = self.db.query(RequirementItem)
        if project_id:
            req_query = req_query.filter(RequirementItem.project_id == project_id)
        if version_id:
            req_query = req_query.filter(RequirementItem.version_id == version_id)
        if iteration_id:
            req_query = req_query.filter(RequirementItem.iteration_id == iteration_id)

        requirement_total = req_query.count()
        # Join RequirementItem → TestCase (via requirement_id) → FunctionalTestCase (via testcase_id)
        from app.models.functional_test_case import FunctionalTestCase
        from app.models.test_case import TestCase
        covered_subq = (
            self.db.query(RequirementItem.id)
            .join(TestCase, TestCase.requirement_id == RequirementItem.id)
            .join(FunctionalTestCase, FunctionalTestCase.testcase_id == TestCase.id)
            .filter(RequirementItem.project_id == project_id if project_id else True)
            .filter(RequirementItem.version_id == version_id if version_id else True)
            .filter(RequirementItem.iteration_id == iteration_id if iteration_id else True)
            .distinct()
        )
        requirement_covered = covered_subq.count()

        # Quality score: weighted formula
        # 60% pass rate + 25% defect closure + 15% requirement coverage
        pass_rate_score = avg_pass_rate * 0.6
        closure_score = 0.0
        if defect_total > 0:
            closure_score = (defect_total - defect_open) / defect_total * 100 * 0.25
        else:
            closure_score = 100.0 * 0.25
        coverage_score = 0.0
        if requirement_total > 0:
            coverage_score = requirement_covered / requirement_total * 100 * 0.15
        quality_score = round(pass_rate_score + closure_score + coverage_score, 1)

        return {
            "metrics": {
                "report_count": report_count,
                "execution_count": execution_count,
                "total_cases": total_cases,
                "passed_cases": passed_cases,
                "failed_cases": failed_cases,
                "average_pass_rate": avg_pass_rate,
                "defect_total": defect_total,
                "defect_p0p1": defect_p0p1,
                "defect_open": defect_open,
                "requirement_total": requirement_total,
                "requirement_covered": requirement_covered,
                "quality_score": quality_score,
            },
            "scope_note": scope_note,
        }

    # ── Trends ───────────────────────────────────────────────────────────────

    def get_trends(
        self,
        project_id: Optional[int] = None,
        version_id: Optional[int] = None,
        iteration_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=days)

        scope_note = self._build_scope_note(project_id, version_id, iteration_id)

        report_query = self.db.query(Report)
        report_filters = self._apply_filters(project_id, version_id, iteration_id, start_date, end_date)
        report_query = report_query.filter(*report_filters)

        reports = report_query.order_by(Report.executed_at).all()

        # Group by date
        date_points: Dict[str, Dict[str, Any]] = {}
        for r in reports:
            date_str = r.executed_at.strftime("%Y-%m-%d") if r.executed_at else ""
            if not date_str:
                continue
            if date_str not in date_points:
                date_points[date_str] = {"passed": 0, "failed": 0, "total": 0, "executions": 0}

            summary = self._safe_json_loads(r.summary, {})
            passed = summary.get("passed", 0) or 0
            failed = summary.get("failed", 0) or 0
            total = summary.get("total", 0) or 0

            date_points[date_str]["passed"] += passed
            date_points[date_str]["failed"] += failed
            date_points[date_str]["total"] += total
            date_points[date_str]["executions"] += 1

        defect_query = self.db.query(Defect)
        defect_filters = self._defect_filters(project_id, version_id, iteration_id, start_date, end_date)
        defect_query = defect_query.filter(*defect_filters)
        defect_by_date: Dict[str, int] = {}
        defects = defect_query.all()
        for d in defects:
            date_str = d.opened_at.strftime("%Y-%m-%d") if d.opened_at else ""
            if date_str:
                defect_by_date[date_str] = defect_by_date.get(date_str, 0) + 1

        points = []
        current = start_date
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            dp = date_points.get(date_str, {})
            total = dp.get("total", 0)
            passed = dp.get("passed", 0)
            pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0

            points.append({
                "date": date_str,
                "pass_rate": pass_rate,
                "defect_count": defect_by_date.get(date_str, 0),
                "execution_count": dp.get("executions", 0),
            })
            current += timedelta(days=1)

        return {"points": points, "scope_note": scope_note}

    # ── Defect Distribution ───────────────────────────────────────────────────

    def get_defect_distribution(
        self,
        project_id: Optional[int] = None,
        version_id: Optional[int] = None,
        iteration_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        scope_note = self._build_scope_note(project_id, version_id, iteration_id)

        defect_query = self.db.query(Defect)
        defect_filters = self._defect_filters(project_id, version_id, iteration_id, start_date, end_date)
        defect_query = defect_query.filter(*defect_filters)

        defects = defect_query.all()
        severities = ["critical", "high", "medium", "low"]
        items = []
        for sev in severities:
            sev_defects = [d for d in defects if d.severity == sev]
            open_count = sum(1 for d in sev_defects if d.status in ("open", "confirmed"))
            items.append({
                "severity": sev,
                "count": len(sev_defects),
                "open_count": open_count,
            })

        return {"items": items, "scope_note": scope_note}

    # ── Requirement Coverage ───────────────────────────────────────────────────

    def get_requirement_coverage(
        self,
        project_id: Optional[int] = None,
        version_id: Optional[int] = None,
        iteration_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        scope_note = None
        if not project_id:
            scope_note = "未指定项目，统计范围为全部项目，结果仅供参考"

        req_query = self.db.query(RequirementItem)
        if project_id:
            req_query = req_query.filter(RequirementItem.project_id == project_id)
        if version_id:
            req_query = req_query.filter(RequirementItem.version_id == version_id)
        if iteration_id:
            req_query = req_query.filter(RequirementItem.iteration_id == iteration_id)

        requirements = req_query.all()
        items = []
        covered_count = 0
        from app.models.functional_test_case import FunctionalTestCase as FT
        from app.models.test_case import TestCase as TC
        for req in requirements:
            tc_count = self.db.query(FT).join(TC, TC.id == FT.testcase_id).filter(
                TC.requirement_id == req.id
            ).count()
            covered = tc_count > 0
            if covered:
                covered_count += 1

            items.append({
                "requirement_id": req.id,
                "title": req.title or "",
                "status": req.status or "",
                "covered": covered,
                "defect_count": 0,
            })

        total = len(requirements)
        coverage_rate = round(covered_count / total * 100, 2) if total > 0 else 0.0

        return {
            "items": items[:100],  # Limit to 100 for response size
            "coverage_rate": coverage_rate,
            "scope_note": scope_note,
        }

    # ── Release Gate ─────────────────────────────────────────────────────────

    def get_release_gate(
        self,
        project_id: Optional[int] = None,
        version_id: Optional[int] = None,
        iteration_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        scope_note = None
        if not project_id:
            scope_note = "未指定项目，使用全局门禁（结果可能不准确）"

        # Get all enabled gates; filter to scoping rules in Python below
        gate_query = self.db.query(QualityGate).filter(QualityGate.enabled == True)

        gates = gate_query.all()
        gates_checked = len(gates)

        # Aggregate gate evaluation
        conditions_passed = 0
        conditions_failed = 0
        blockers = []
        overall_pass = True
        gate_level = "warning"

        for gate in gates:
            conditions = self._safe_json_loads(gate.conditions, [])
            scope_filter = self._safe_json_loads(gate.scope_filter, {})

            # Filter by project/version/iteration if scope_filter specified
            if scope_filter:
                sf_project = scope_filter.get("project_id")
                sf_version = scope_filter.get("version_id")
                sf_iteration = scope_filter.get("iteration_id")
                if sf_project and sf_project != project_id:
                    continue
                if sf_version and sf_version != version_id:
                    continue
                if sf_iteration and sf_iteration != iteration_id:
                    continue

            # Evaluate each condition
            for cond in conditions:
                metric = cond.get("metric", "")
                operator = cond.get("operator", ">=")
                threshold = float(cond.get("threshold", 0))

                current_value = self._get_metric_value(metric, project_id, version_id, iteration_id)
                cond_pass = self._evaluate_condition(current_value, operator, threshold)
                if cond_pass:
                    conditions_passed += 1
                else:
                    conditions_failed += 1
                    blockers.append(f"{gate.name}: {metric} {operator} {threshold} (当前: {current_value})")

            last_result = gate.last_result or "skipped"
            if last_result in ("fail", "warning"):
                overall_pass = False
                gate_level = gate.gate_level or "warning"

        if conditions_failed > 0:
            overall_pass = False

        return {
            "result": {
                "overall_pass": overall_pass,
                "gate_name": "综合质量门禁" if gates_checked > 0 else "无门禁配置",
                "gate_level": gate_level,
                "conditions_passed": conditions_passed,
                "conditions_failed": conditions_failed,
                "blockers": blockers[:10],
            },
            "gates_checked": gates_checked,
            "scope_note": scope_note,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _apply_filters(
        self,
        project_id: Optional[int],
        version_id: Optional[int],
        iteration_id: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[Any]:
        filters = []
        if project_id:
            filters.append(Report.project_id == project_id)
        if version_id:
            filters.append(Report.version_id == version_id)
        if iteration_id:
            filters.append(Report.iteration_id == iteration_id)
        if start_date:
            filters.append(Report.executed_at >= start_date)
        if end_date:
            filters.append(Report.executed_at <= end_date)
        return filters

    def _defect_filters(
        self,
        project_id: Optional[int],
        version_id: Optional[int],
        iteration_id: Optional[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Any]:
        filters = []
        if project_id:
            filters.append(Defect.project_id == project_id)
        if version_id:
            filters.append(Defect.version_id == version_id)
        if iteration_id:
            filters.append(Defect.iteration_id == iteration_id)
        if start_date:
            filters.append(Defect.opened_at >= start_date)
        if end_date:
            filters.append(Defect.opened_at <= end_date)
        return filters

    def _build_scope_note(
        self,
        project_id: Optional[int],
        version_id: Optional[int],
        iteration_id: Optional[int],
    ) -> Optional[str]:
        if not any([project_id, version_id, iteration_id]):
            return "未指定筛选条件，统计范围为全部数据"
        return None

    def _safe_json_loads(self, text: Any, fallback: Any = None) -> Any:
        import json
        if text is None:
            return fallback if fallback is not None else {}
        # Already parsed by SQLAlchemy JSON column — return as-is
        if isinstance(text, (dict, list)):
            return text
        if not isinstance(text, str):
            return fallback if fallback is not None else {}
        try:
            return json.loads(text)
        except Exception:
            return fallback if fallback is not None else {}

    def _get_metric_value(
        self,
        metric: str,
        project_id: Optional[int],
        version_id: Optional[int],
        iteration_id: Optional[int],
    ) -> float:
        if metric == "pass_rate":
            overview = self.get_overview(project_id, version_id, iteration_id)
            return overview["metrics"]["average_pass_rate"]
        elif metric == "defect_count":
            defect_query = self.db.query(Defect)
            defect_filters = self._defect_filters(project_id, version_id, iteration_id)
            return float(defect_query.filter(*defect_filters).count())
        elif metric == "critical_defects":
            defect_query = self.db.query(Defect)
            defect_filters = self._defect_filters(project_id, version_id, iteration_id)
            return float(defect_query.filter(
                *defect_filters,
                Defect.priority.in_(["P0", "P1"])
            ).count())
        elif metric == "avg_duration":
            report_query = self.db.query(Report)
            report_filters = self._apply_filters(project_id, version_id, iteration_id, None, None)
            reports = report_query.filter(*report_filters).all()
            durations = [r.duration_ms for r in reports if r.duration_ms]
            return sum(durations) / len(durations) if durations else 0.0
        return 0.0

    def _evaluate_condition(self, current_value: float, operator: str, threshold: float) -> bool:
        ops = {
            ">=": lambda c, t: c >= t,
            "<=": lambda c, t: c <= t,
            ">": lambda c, t: c > t,
            "<": lambda c, t: c < t,
            "==": lambda c, t: c == t,
            "!=": lambda c, t: c != t,
        }
        fn = ops.get(operator, lambda c, t: False)
        return fn(current_value, threshold)