"""
Report Generator - 报告生成引擎
基于 Jinja2 模板生成 HTML 格式报告
"""
import json
from datetime import datetime, timedelta
from typing import Optional
from jinja2 import Environment, FileSystemLoader, Template, BaseLoader
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.execution_log import ExecutionLog


class ReportGenerator:
    """报告生成引擎"""

    def __init__(self):
        self._env = None

    def _get_jinja_env(self) -> Environment:
        """获取 Jinja2 环境"""
        if self._env is None:
            self._env = Environment(loader=BaseLoader())
            # 注册自定义过滤器
            self._env.filters["json_dumps"] = lambda v: json.dumps(v, ensure_ascii=False)
            self._env.filters["format_time"] = lambda v: datetime.fromisoformat(v).strftime("%Y-%m-%d %H:%M:%S") if v else "-"
        return self._env

    def generate_report(
        self,
        report_type: str,
        data: dict,
        template_content: str = None
    ) -> str:
        """
        生成报告
        report_type: 报告类型 (summary, trend, execution, custom)
        data: 报告数据
        template_content: 自定义模板内容（可选）
        返回: HTML 报告字符串
        """
        if template_content:
            template = self._get_jinja_env().from_string(template_content)
        else:
            template = self._get_jinja_env().from_string(self._get_default_template(report_type))

        html = template.render(
            report_type=report_type,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **data
        )
        return html

    def _get_default_template(self, report_type: str) -> str:
        """获取默认模板"""
        base_css = """
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #333; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; overflow: hidden; }
            .card-header { padding: 16px 20px; border-bottom: 1px solid #eee; font-weight: 600; font-size: 16px; background: #fafafa; }
            .card-body { padding: 20px; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
            .metric { background: white; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
            .metric-value { font-size: 32px; font-weight: 700; color: #2196F3; }
            .metric-label { font-size: 14px; color: #666; margin-top: 4px; }
            .metric.success .metric-value { color: #4CAF50; }
            .metric.warning .metric-value { color: #FF9800; }
            .metric.danger .metric-value { color: #F44336; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #eee; }
            th { background: #fafafa; font-weight: 600; font-size: 13px; color: #666; text-transform: uppercase; }
            tr:hover { background: #fafafa; }
            .status { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
            .status.success { background: #E8F5E9; color: #2E7D32; }
            .status.failure { background: #FFEBEE; color: #C62828; }
            .status.error { background: #FFF3E0; color: #EF6C00; }
            .status.pending { background: #E3F2FD; color: #1565C0; }
            .chart-placeholder { height: 300px; background: #fafafa; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
            .header h1 { font-size: 24px; color: #333; }
            .header .meta { font-size: 13px; color: #999; }
            .empty { text-align: center; padding: 40px; color: #999; }
        </style>
        """

        if report_type == "summary":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>测试摘要报告</title>
    {base_css}
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📊 测试摘要报告</h1>
        <span class="meta">生成时间: {{{{ generated_at }}}}</span>
    </div>
    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{{{{ total }}}}</div>
            <div class="metric-label">总执行数</div>
        </div>
        <div class="metric success">
            <div class="metric-value">{{{{ passed }}}}</div>
            <div class="metric-label">通过数</div>
        </div>
        <div class="metric danger">
            <div class="metric-value">{{{{ failed }}}}</div>
            <div class="metric-label">失败数</div>
        </div>
        <div class="metric {{'success' if pass_rate >= 80 else 'warning' if pass_rate >= 60 else 'danger'}}">
            <div class="metric-value">{{{{ pass_rate }}}}%</div>
            <div class="metric-label">通过率</div>
        </div>
    </div>
    <div class="card">
        <div class="card-header">📈 执行趋势</div>
        <div class="card-body">
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>执行数</th>
                        <th>通过数</th>
                        <th>失败数</th>
                        <th>通过率</th>
                        <th>平均响应时间 (ms)</th>
                    </tr>
                </thead>
                <tbody>
                    {{{{ each trend_data }}}}
                    <tr>
                        <td>{{{{ this.date }}}}</td>
                        <td>{{{{ this.total }}}}</td>
                        <td>{{{{ this.passed }}}}</td>
                        <td>{{{{ this.failed }}}}</td>
                        <td>{{{{ this.pass_rate }}}}%</td>
                        <td>{{{{ this.avg_rt }}}}</td>
                    </tr>
                    {{{{ /each }}}}
                </tbody>
            </table>
        </div>
    </div>
    <div class="card">
        <div class="card-header">❌ 错误分类</div>
        <div class="card-body">
            <table>
                <thead>
                    <tr>
                        <th>错误类型</th>
                        <th>错误信息</th>
                        <th>出现次数</th>
                    </tr>
                </thead>
                <tbody>
                    {{{{ each error_stats }}}}
                    <tr>
                        <td>{{{{ this.type }}}}</td>
                        <td>{{{{ this.message }}}}</td>
                        <td>{{{{ this.count }}}}</td>
                    </tr>
                    {{{{ /each }}}}
                </tbody>
            </table>
        </div>
    </div>
</div>
</body>
</html>
            """
        elif report_type == "trend":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>趋势分析报告</title>
    {base_css}
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📈 趋势分析报告</h1>
        <span class="meta">生成时间: {{{{ generated_at }}}}</span>
    </div>
    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{{{{ total_tests }}}}</div>
            <div class="metric-label">总测试数</div>
        </div>
        <div class="metric success">
            <div class="metric-value">{{{{ overall_pass_rate }}}}%</div>
            <div class="metric-label">总通过率</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{{{ avg_response_time }}}}</div>
            <div class="metric-label">平均响应时间 (ms)</div>
        </div>
    </div>
    <div class="card">
        <div class="card-header">📊 每日执行统计</div>
        <div class="card-body">
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>用例数</th>
                        <th>通过</th>
                        <th>失败</th>
                        <th>通过率</th>
                        <th>平均 RT</th>
                    </tr>
                </thead>
                <tbody>
                    {{{{ each daily_stats }}}}
                    <tr>
                        <td>{{{{ this.date }}}}</td>
                        <td>{{{{ this.total }}}}</td>
                        <td class="status success">{{{{ this.passed }}}}</td>
                        <td class="status failure">{{{{ this.failed }}}}</td>
                        <td>{{{{ this.pass_rate }}}}%</td>
                        <td>{{{{ this.avg_rt }}}} ms</td>
                    </tr>
                    {{{{ /each }}}}
                </tbody>
            </table>
        </div>
    </div>
    <div class="card">
        <div class="card-header">🔝 Top 失败用例</div>
        <div class="card-body">
            {{{{ if top_failures }}}}
            <table>
                <thead>
                    <tr>
                        <th>用例 ID</th>
                        <th>URL</th>
                        <th>失败次数</th>
                    </tr>
                </thead>
                <tbody>
                    {{{{ each top_failures }}}}
                    <tr>
                        <td>{{{{ this.case_id }}}}</td>
                        <td>{{{{ this.url }}}}</td>
                        <td class="status failure">{{{{ this.count }}}}</td>
                    </tr>
                    {{{{ /each }}}}
                </tbody>
            </table>
            {{{{ else }}}}
            <div class="empty">暂无失败记录</div>
            {{{{ /if }}}}
        </div>
    </div>
</div>
</body>
</html>
            """
        elif report_type == "execution":
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>执行详情报告</title>
    {base_css}
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📋 执行详情报告</h1>
        <span class="meta">生成时间: {{{{ generated_at }}}}</span>
    </div>
    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{{{{ total }}}}</div>
            <div class="metric-label">总执行数</div>
        </div>
        <div class="metric success">
            <div class="metric-value">{{{{ passed }}}}</div>
            <div class="metric-label">成功</div>
        </div>
        <div class="metric danger">
            <div class="metric-value">{{{{ failed }}}}</div>
            <div class="metric-label">失败</div>
        </div>
    </div>
    <div class="card">
        <div class="card-header">📝 执行记录</div>
        <div class="card-body">
            <table>
                <thead>
                    <tr>
                        <th>执行 ID</th>
                        <th>用例</th>
                        <th>方法</th>
                        <th>URL</th>
                        <th>状态</th>
                        <th>响应时间</th>
                        <th>状态码</th>
                    </tr>
                </thead>
                <tbody>
                    {{{{ each executions }}}}
                    <tr>
                        <td>{{{{ this.execution_id }}}}</td>
                        <td>{{{{ this.case_id }}}}</td>
                        <td><span class="status">{{{{ this.method }}}}</span></td>
                        <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">{{{{ this.url }}}}</td>
                        <td><span class="status {{this.status}}">{{{{ this.status }}}}</span></td>
                        <td>{{{{ this.response_time }}}} ms</td>
                        <td>{{{{ this.status_code }}}}</td>
                    </tr>
                    {{{{ /each }}}}
                </tbody>
            </table>
        </div>
    </div>
</div>
</body>
</html>
            """
        else:
            # 自定义报告
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>测试报告</title>
    {base_css}
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📊 测试报告</h1>
        <span class="meta">生成时间: {{{{ generated_at }}}}</span>
    </div>
    <div class="card">
        <div class="card-body">
            {{{{ content | safe }}}}
        </div>
    </div>
</div>
</body>
</html>
            """

    def generate_trend_report(
        self,
        start_date: datetime,
        end_date: datetime,
        db: Session = None
    ) -> str:
        """
        生成趋势报告
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        """
        if db is None:
            db = SessionLocal()

        try:
            # 查询执行日志
            logs = db.query(ExecutionLog).filter(
                ExecutionLog.created_at >= start_date,
                ExecutionLog.created_at <= end_date
            ).order_by(ExecutionLog.created_at).all()

            # 按日期分组统计
            daily_data = {}
            for log in logs:
                date_key = log.created_at.strftime("%Y-%m-%d")
                if date_key not in daily_data:
                    daily_data[date_key] = {
                        "date": date_key,
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "total_rt": 0,
                    }
                daily_data[date_key]["total"] += 1
                daily_data[date_key]["total_rt"] += log.response_time_ms or 0
                if log.status == "success":
                    daily_data[date_key]["passed"] += 1
                else:
                    daily_data[date_key]["failed"] += 1

            # 计算每日通过率和平均响应时间
            daily_stats = []
            for date_key in sorted(daily_data.keys()):
                d = daily_data[date_key]
                total = d["total"]
                d["pass_rate"] = round(d["passed"] / total * 100, 2) if total > 0 else 0
                d["avg_rt"] = round(d["total_rt"] / total, 2) if total > 0 else 0
                del d["total_rt"]
                daily_stats.append(d)

            # 错误统计
            error_stats = {}
            for log in logs:
                if log.status != "success" and log.error_message:
                    key = log.error_message[:100]  # 截断长错误信息
                    if key not in error_stats:
                        error_stats[key] = {"type": "Error", "message": key, "count": 0}
                    error_stats[key]["count"] += 1

            error_list = list(error_stats.values())
            error_list.sort(key=lambda x: x["count"], reverse=True)

            data = {
                "total_tests": len(logs),
                "overall_pass_rate": round(
                    sum(d["passed"] for d in daily_stats) / sum(d["total"] for d in daily_stats) * 100
                    if sum(d["total"] for d in daily_stats) > 0 else 0, 2
                ),
                "avg_response_time": round(
                    sum(d["avg_rt"] * d["total"] for d in daily_stats) / sum(d["total"] for d in daily_stats)
                    if sum(d["total"] for d in daily_stats) > 0 else 0, 2
                ),
                "daily_stats": daily_stats,
                "error_stats": error_list[:20],  # 只取前 20 条
                "top_failures": [],  # 简化版不包含
            }

            return self.generate_report("trend", data)

        finally:
            if db:
                db.close()

    def generate_execution_report(
        self,
        execution_ids: list,
        db: Session = None
    ) -> str:
        """生成执行详情报告"""
        if db is None:
            db = SessionLocal()

        try:
            logs = db.query(ExecutionLog).filter(
                ExecutionLog.execution_id.in_(execution_ids)
            ).all()

            total = len(logs)
            passed = sum(1 for log in logs if log.status == "success")
            failed = total - passed

            executions = []
            for log in logs:
                executions.append({
                    "execution_id": log.execution_id,
                    "case_id": log.case_id,
                    "method": log.request_method,
                    "url": log.request_url[:100],
                    "status": log.status,
                    "response_time": log.response_time_ms,
                    "status_code": log.response_status,
                })

            data = {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
                "executions": executions,
            }

            return self.generate_report("execution", data)

        finally:
            if db:
                db.close()

    def generate_summary_stats(
        self,
        db: Session = None,
        filters: dict = None
    ) -> dict:
        """
        生成汇总统计数据
        filters: 筛选条件 {case_id, scenario_id, status, start_date, end_date}
        """
        if db is None:
            db = SessionLocal()
        filters = filters or {}

        try:
            query = db.query(ExecutionLog)

            if filters.get("case_id"):
                query = query.filter(ExecutionLog.case_id == filters["case_id"])
            if filters.get("scenario_id"):
                query = query.filter(ExecutionLog.scenario_id == filters["scenario_id"])
            if filters.get("status"):
                query = query.filter(ExecutionLog.status == filters["status"])
            if filters.get("start_date"):
                query = query.filter(ExecutionLog.created_at >= filters["start_date"])
            if filters.get("end_date"):
                query = query.filter(ExecutionLog.created_at <= filters["end_date"])

            logs = query.all()

            total = len(logs)
            passed = sum(1 for log in logs if log.status == "success")
            failed = total - passed

            # 按日期分组
            daily_stats = {}
            for log in logs:
                date_key = log.created_at.strftime("%Y-%m-%d")
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"date": date_key, "total": 0, "passed": 0, "failed": 0, "total_rt": 0}
                daily_stats[date_key]["total"] += 1
                daily_stats[date_key]["total_rt"] += log.response_time_ms or 0
                if log.status == "success":
                    daily_stats[date_key]["passed"] += 1
                else:
                    daily_stats[date_key]["failed"] += 1

            # 计算趋势数据
            trend_data = []
            for date_key in sorted(daily_stats.keys()):
                d = daily_stats[date_key]
                total_d = d["total"]
                trend_data.append({
                    "date": date_key,
                    "total": total_d,
                    "passed": d["passed"],
                    "failed": d["failed"],
                    "pass_rate": round(d["passed"] / total_d * 100, 2) if total_d > 0 else 0,
                    "avg_rt": round(d["total_rt"] / total_d, 2) if total_d > 0 else 0,
                })

            # 错误分类统计
            error_stats = {}
            for log in logs:
                if log.status != "success" and log.error_message:
                    key = log.error_message[:100]
                    if key not in error_stats:
                        error_stats[key] = {"type": "Error", "message": key, "count": 0}
                    error_stats[key]["count"] += 1

            error_list = list(error_stats.values())
            error_list.sort(key=lambda x: x["count"], reverse=True)

            return {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
                "avg_response_time": round(
                    sum(log.response_time_ms for log in logs) / total, 2
                ) if total > 0 else 0,
                "trend_data": trend_data,
                "error_stats": error_list[:20],
            }

        finally:
            if db:
                db.close()
