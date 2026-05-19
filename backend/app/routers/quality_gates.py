from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
from app.database import get_db
from app.models import QualityGate, QualityGateResult, CoverageRecord, Defect, TestCase

router = APIRouter(prefix="/api/quality-gates", tags=["质量门禁"])


class GateRuleCreate(BaseModel):
    id: str
    type: str  # coverage / test_pass_rate / response_time / critical_defects
    metric: Optional[str] = None
    operator: str  # gte / lte / eq
    threshold: float
    scope: Optional[str] = "overall"  # overall / file:xxx / case:xxx / scenario:xxx


class QualityGateCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    rules: List[dict] = []
    enabled: Optional[bool] = True


class QualityGateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[List[dict]] = None
    enabled: Optional[bool] = None


@router.get("")
def list_gates(db: Session = Depends(get_db)):
    gates = db.query(QualityGate).order_by(QualityGate.id.desc()).all()
    return {"code": 0, "data": gates}


@router.post("")
def create_gate(data: QualityGateCreate, db: Session = Depends(get_db)):
    gate = QualityGate(
        name=data.name,
        description=data.description,
        rules=json.dumps(data.rules),
        enabled=data.enabled,
    )
    db.add(gate)
    db.commit()
    db.refresh(gate)
    return {"code": 0, "data": gate}


@router.get("/{gate_id}")
def get_gate(gate_id: int, db: Session = Depends(get_db)):
    gate = db.query(QualityGate).filter(QualityGate.id == gate_id).first()
    if not gate:
        raise HTTPException(status_code=404, detail="门禁不存在")
    return {"code": 0, "data": gate}


@router.put("/{gate_id}")
def update_gate(gate_id: int, data: QualityGateUpdate, db: Session = Depends(get_db)):
    gate = db.query(QualityGate).filter(QualityGate.id == gate_id).first()
    if not gate:
        raise HTTPException(status_code=404, detail="门禁不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if k == "rules":
            v = json.dumps(v)
        setattr(gate, k, v)
    db.commit()
    db.refresh(gate)
    return {"code": 0, "data": gate}


@router.delete("/{gate_id}")
def delete_gate(gate_id: int, db: Session = Depends(get_db)):
    gate = db.query(QualityGate).filter(QualityGate.id == gate_id).first()
    if not gate:
        raise HTTPException(status_code=404, detail="门禁不存在")
    db.query(QualityGateResult).filter(QualityGateResult.gate_id == gate_id).delete()
    db.delete(gate)
    db.commit()
    return {"code": 0, "message": "删除成功"}


@router.post("/{gate_id}/evaluate")
def evaluate_gate(gate_id: int, trigger_type: str = "manual", trigger_ref: str = "", db: Session = Depends(get_db)):
    """执行门禁评估"""
    gate = db.query(QualityGate).filter(QualityGate.id == gate_id).first()
    if not gate:
        raise HTTPException(status_code=404, detail="门禁不存在")

    rules = json.loads(gate.rules or "[]")
    rule_results = []
    overall_status = "passed"

    for rule in rules:
        result = _evaluate_rule(rule, db)
        rule_results.append(result)
        if result["status"] == "failed":
            overall_status = "failed"
        elif result["status"] == "warning" and overall_status == "passed":
            overall_status = "warning"

    # 记录结果
    gate_result = QualityGateResult(
        gate_id=gate_id,
        trigger_type=trigger_type,
        trigger_ref=trigger_ref,
        status=overall_status,
        rule_results=json.dumps(rule_results),
        summary=f"{sum(1 for r in rule_results if r['status']=='passed')} 项通过，{sum(1 for r in rule_results if r['status']=='failed')} 项失败",
    )
    db.add(gate_result)
    db.commit()
    db.refresh(gate_result)

    return {"code": 0, "data": {
        "gate_id": gate_id,
        "status": overall_status,
        "rule_results": rule_results,
        "summary": gate_result.summary,
        "triggered_at": gate_result.triggered_at.isoformat() if gate_result.triggered_at else None,
    }}


def _evaluate_rule(rule: dict, db: Session) -> dict:
    r_type = rule.get("type", "")
    operator = rule.get("operator", "gte")
    threshold = float(rule.get("threshold", 0))
    actual = 0.0
    message = ""
    status = "passed"

    try:
        if r_type == "coverage":
            metric = rule.get("metric", "line_coverage")
            # 获取最新覆盖率
            latest = db.query(CoverageRecord).order_by(CoverageRecord.report_date.desc()).first()
            if not latest:
                actual = 0
                message = "无覆盖率数据"
                status = "warning"
            else:
                repo_cov = db.query(CoverageRecord).filter(
                    CoverageRecord.repository_id == latest.repository_id
                ).all()
                if metric == "line_coverage":
                    total = sum(r.total_lines for r in repo_cov)
                    covered = sum(r.covered_lines for r in repo_cov)
                    actual = round(covered / total * 100, 2) if total > 0 else 0
                if operator == "gte" and actual < threshold:
                    status = "failed"
                    message = f"覆盖率 {actual}% < {threshold}%，不通过"
                elif operator == "lte" and actual > threshold:
                    status = "failed"
                    message = f"覆盖率 {actual}% > {threshold}%，不通过"
                elif operator == "eq" and abs(actual - threshold) > 0.1:
                    status = "failed"
                    message = f"覆盖率 {actual}% != {threshold}%，不通过"
                else:
                    message = f"覆盖率 {actual}% >= {threshold}%，通过"

        elif r_type == "test_pass_rate":
            # 从执行记录统计通过率
            from app.models import ExecutionLog
            logs = db.query(ExecutionLog).limit(100).all()
            if not logs:
                actual = 100
                message = "无执行记录，视为通过"
                status = "warning"
            else:
                passed = sum(1 for log in logs if log.status == "success")
                actual = round(passed / len(logs) * 100, 2)
                if operator == "gte" and actual < threshold:
                    status = "failed"
                    message = f"通过率 {actual}% < {threshold}%，不通过"
                else:
                    message = f"通过率 {actual}% >= {threshold}%，通过"

        elif r_type == "critical_defects":
            count = db.query(Defect).filter(
                Defect.severity.in_(["critical", "high"]),
                Defect.status.in_(["open", "in_progress", "reopened"])
            ).count()
            actual = count
            if operator == "eq" and count != int(threshold):
                status = "failed"
                message = f"严重缺陷 {count} != {int(threshold)}，不通过"
            elif operator == "lte" and count > int(threshold):
                status = "failed"
                message = f"严重缺陷 {count} > {int(threshold)}，不通过"
            else:
                message = f"严重缺陷 {count}，通过"

        else:
            message = f"未知规则类型: {r_type}"
            status = "warning"

    except Exception as e:
        message = f"评估异常: {str(e)}"
        status = "warning"

    return {
        "id": rule.get("id", ""),
        "type": r_type,
        "status": status,
        "actual": actual,
        "threshold": threshold,
        "message": message,
    }


@router.get("/{gate_id}/results")
def get_gate_results(gate_id: int, db: Session = Depends(get_db)):
    results = db.query(QualityGateResult).filter(
        QualityGateResult.gate_id == gate_id
    ).order_by(QualityGateResult.triggered_at.desc()).limit(50).all()
    return {"code": 0, "data": results}
