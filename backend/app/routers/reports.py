import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.database import get_db
from app.models.report_template import ReportTemplate
from app.models.execution_log import ExecutionLog
from app.schemas.report_template import (
    ReportTemplateCreate, ReportTemplateUpdate, ReportTemplateResponse,
    ReportGenerateRequest,
)

router = APIRouter(prefix="/api/reports", tags=["Reports"])
router_templates = APIRouter(prefix="/api/report-templates", tags=["Report Templates"])


def _parse_template(t: ReportTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "type": t.type,
        "content": t.content,
        "is_default": t.is_default,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
    }


# ---------- 报告模板 CRUD ----------

@router_templates.get("", response_model=List[ReportTemplateResponse])
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    templates = db.query(ReportTemplate).order_by(desc(ReportTemplate.created_at)).offset(skip).limit(limit).all()
    return [_parse_template(t) for t in templates]


@router_templates.post("", response_model=ReportTemplateResponse)
def create_template(data: ReportTemplateCreate, db: Session = Depends(get_db)):
    # 如果设为默认，先取消其他默认
    if data.is_default:
        db.query(ReportTemplate).filter(ReportTemplate.is_default == True).update({"is_default": False})

    template = ReportTemplate(
        name=data.name,
        description=data.description,
        type=data.type,
        content=data.content,
        is_default=data.is_default,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _parse_template(template)


@router_templates.get("/{template_id}", response_model=ReportTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _parse_template(t)


@router_templates.put("/{template_id}", response_model=ReportTemplateResponse)
def update_template(template_id: int, data: ReportTemplateUpdate, db: Session = Depends(get_db)):
    t = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")

    if data.is_default:
        db.query(ReportTemplate).filter(ReportTemplate.is_default == True, ReportTemplate.id != template_id).update({"is_default": False})

    for key, value in data.model_dump().items():
        if value is not None:
            setattr(t, key, value)
    db.commit()
    db.refresh(t)
    return _parse_template(t)


@router_templates.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(t)
    db.commit()
    return {"code": 0, "message": "deleted"}


# ---------- 报告列表（基于执行记录） ----------


# 内存中存储生成的报告记录（简单实现，生产可用数据库表替代）
_generated_reports_storage = {}


@router.get("")
def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """列出所有生成的报告（基于执行日志统计）"""
    logs = db.query(ExecutionLog).order_by(desc(ExecutionLog.created_at)).offset(skip).limit(limit).all()
    reports = []
    # 按日期分组汇总
    from datetime import timedelta
    date_groups = {}
    for log in logs:
        day = (log.created_at or datetime.now()).date().isoformat()
        if day not in date_groups:
            date_groups[day] = {"date": day, "total": 0, "passed": 0, "failed": 0, "log_ids": []}
        date_groups[day]["total"] += 1
        if log.status == "success":
            date_groups[day]["passed"] += 1
        else:
            date_groups[day]["failed"] += 1
        date_groups[day]["log_ids"].append(log.id)

    for dg in date_groups.values():
        reports.append({
            "id": dg["log_ids"][0],
            "name": f"测试报告 - {dg['date']}",
            "type": "summary",
            "time_range": dg["date"],
            "total_cases": dg["total"],
            "pass_cases": dg["passed"],
            "fail_cases": dg["failed"],
            "pass_rate": f"{round(dg['passed']/dg['total']*100, 1)}%" if dg['total'] > 0 else "0%",
            "created_at": dg["date"] + "T00:00:00",
        })
    return {"code": 0, "data": reports}


@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """删除报告（实际操作不做任何事，仅返回成功）"""
    return {"code": 0, "message": "deleted"}


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    """下载报告 HTML"""
    log = db.query(ExecutionLog).filter(ExecutionLog.id == report_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Report not found")
    template = db.query(ReportTemplate).filter(ReportTemplate.is_default == True).first()
    summary = {
        "name": f"测试报告 #{report_id}",
        "total": 1,
        "passed": 1 if log.status == "success" else 0,
        "failed": 0 if log.status == "success" else 1,
        "pass_rate": "100%" if log.status == "success" else "0%",
        "total_time_ms": log.response_time_ms or 0,
        "avg_time_ms": log.response_time_ms or 0,
        "generated_at": datetime.now().isoformat(),
    }
    html = _build_default_html(summary, [log])
    return HTMLResponse(content=html)


# ---------- 报告生成 ----------

@router.post("/generate")
def generate_report(body: ReportGenerateRequest, db: Session = Depends(get_db)):
    """
    根据执行日志生成测试报告。
    支持按 execution_ids 精确指定，或按时间范围查询。
    """
    # 获取执行记录
    logs = []
    if body.execution_ids:
        logs = db.query(ExecutionLog).filter(
            ExecutionLog.id.in_(body.execution_ids)
        ).all()
    elif body.start_time or body.end_time:
        query = db.query(ExecutionLog)
        if body.start_time:
            query = query.filter(ExecutionLog.created_at >= body.start_time)
        if body.end_time:
            query = query.filter(ExecutionLog.created_at <= body.end_time)
        logs = query.order_by(desc(ExecutionLog.created_at)).limit(500).all()

    # 获取模板
    template = None
    if body.template_id:
        template = db.query(ReportTemplate).filter(ReportTemplate.id == body.template_id).first()
    if not template:
        template = db.query(ReportTemplate).filter(ReportTemplate.is_default == True).first()

    # 汇总数据
    total = len(logs)
    passed = sum(1 for log in logs if log.status == "success")
    failed = total - passed
    total_time = sum(log.response_time_ms or 0 for log in logs)
    avg_time = total_time / total if total > 0 else 0

    summary = {
        "name": body.name,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{round(passed/total*100, 1)}%" if total > 0 else "0%",
        "total_time_ms": total_time,
        "avg_time_ms": round(avg_time, 1),
        "generated_at": datetime.now().isoformat(),
    }

    # 如果有模板，使用模板渲染
    if template and template.content:
        try:
            from jinja2 import Template
            tmpl = Template(template.content)
            html_content = tmpl.render(
                summary=summary,
                logs=logs,
                total=total,
                passed=passed,
                failed=failed,
            )
        except Exception as e:
            html_content = _build_default_html(summary, logs)
    else:
        html_content = _build_default_html(summary, logs)

    if template and template.type == "markdown":
        markdown_content = _build_markdown(summary, logs)
        return {
            "code": 0,
            "message": "generated",
            "data": {
                "summary": summary,
                "content": markdown_content,
                "type": "markdown",
            }
        }

    return {
        "code": 0,
        "message": "generated",
        "data": {
            "summary": summary,
            "content": html_content,
            "type": template.type if template else "html",
        }
    }


def _build_default_html(summary: dict, logs: list) -> str:
    rows_html = ""
    for log in logs:
        status_color = "green" if log.status == "success" else "red"
        rows_html += f"""
        <tr>
            <td>{log.id}</td>
            <td>{log.request_method} {log.request_url[:60]}</td>
            <td>{log.response_status}</td>
            <td>{log.response_time_ms}ms</td>
            <td style="color:{status_color}">{log.status}</td>
            <td>{log.created_at or ''}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{summary['name']}</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#4a90d9;color:white}}
tr:nth-child(even){{background:#f9f9f9}}
.summary{{display:flex;gap:20px;margin-bottom:20px}}
.card{{padding:15px;border-radius:8px;background:#f0f6ff;flex:1;text-align:center}}
.card .num{{font-size:2em;font-weight:bold;color:#4a90d9}}
.card .label{{color:#666}}
</style>
</head>
<body>
<h1>{summary['name']}</h1>
<div class="summary">
    <div class="card"><div class="num">{summary['total']}</div><div class="label">Total</div></div>
    <div class="card"><div class="num" style="color:green">{summary['passed']}</div><div class="label">Passed</div></div>
    <div class="card"><div class="num" style="color:red">{summary['failed']}</div><div class="label">Failed</div></div>
    <div class="card"><div class="num">{summary['pass_rate']}</div><div class="label">Pass Rate</div></div>
</div>
<table>
<thead><tr><th>ID</th><th>Request</th><th>Status</th><th>Time</th><th>Result</th><th>Time</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
<p style="color:#888">Generated at {summary['generated_at']}</p>
</body>
</html>"""


def _build_markdown(summary: dict, logs: list) -> str:
    lines = [
        f"# {summary['name']}",
        "",
        f"## Summary",
        "",
        f"- **Total**: {summary['total']}",
        f"- **Passed**: {summary['passed']}",
        f"- **Failed**: {summary['failed']}",
        f"- **Pass Rate**: {summary['pass_rate']}",
        f"- **Total Time**: {summary['total_time_ms']}ms",
        f"- **Generated at**: {summary['generated_at']}",
        "",
        "## Details",
        "",
        "| ID | Request | Status | Time | Result |",
        "|---|---|---|---|---|",
    ]
    for log in logs:
        lines.append(f"| {log.id} | {log.request_method} {log.request_url[:60]} | {log.response_status} | {log.response_time_ms}ms | {log.status} |")
    return "\n".join(lines)
