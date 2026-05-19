from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import json
from app.database import get_db
from app.models import CoverageRecord

router = APIRouter(prefix="/api/coverage", tags=["覆盖率"])
router_upload = APIRouter(prefix="/api/coverage", tags=["覆盖率"])


class CoverageUploadData(BaseModel):
    repository_id: int
    commit_hash: str
    report_format: Optional[str] = "lcov"


@router_upload.post("/upload")
async def upload_coverage_report(
    repository_id: int,
    commit_hash: str,
    report_format: Optional[str] = "lcov",
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传并解析覆盖率报告"""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    if report_format == "lcov":
        records = _parse_lcov(text, repository_id, commit_hash)
    elif report_format == "cobertura":
        records = _parse_cobertura(text, repository_id, commit_hash)
    else:
        records = _parse_lcov(text, repository_id, commit_hash)

    created = []
    for rec in records:
        db_rec = CoverageRecord(**rec)
        db.add(db_rec)
        created.append(rec)

    db.commit()

    total_lines = sum(r["total_lines"] for r in created)
    covered_lines = sum(r["covered_lines"] for r in created)
    overall = round(covered_lines / total_lines * 100, 2) if total_lines > 0 else 0

    return {"code": 0, "data": {
        "summary": {
            "total_files": len(created),
            "total_lines": total_lines,
            "covered_lines": covered_lines,
            "line_coverage": overall,
        },
        "files": created,
    }}


def _parse_lcov(text: str, repository_id: int, commit_hash: str) -> List[dict]:
    records = []
    current_file = None
    total_lines = 0
    covered_lines = 0
    uncovered = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("SF:"):
            if current_file:
                records.append({
                    "repository_id": repository_id,
                    "commit_hash": commit_hash,
                    "file_path": current_file,
                    "total_lines": total_lines,
                    "covered_lines": covered_lines,
                    "line_coverage": round(covered_lines / total_lines * 100, 2) if total_lines > 0 else 0,
                    "uncovered_lines": json.dumps(uncovered),
                    "report_format": "lcov",
                    "report_date": date.today(),
                    "branch_coverage": 0,
                    "function_coverage": 0,
                })
            current_file = line[3:]
            total_lines = covered_lines = 0
            uncovered = []
        elif line.startswith("DA:"):
            parts = line[3:].split(",")
            if len(parts) >= 2:
                ln = int(parts[0])
                hits = int(parts[1])
                total_lines += 1
                if hits > 0:
                    covered_lines += 1
                else:
                    uncovered.append(ln)
        elif line.startswith("end_of_record"):
            if current_file:
                records.append({
                    "repository_id": repository_id,
                    "commit_hash": commit_hash,
                    "file_path": current_file,
                    "total_lines": total_lines,
                    "covered_lines": covered_lines,
                    "line_coverage": round(covered_lines / total_lines * 100, 2) if total_lines > 0 else 0,
                    "uncovered_lines": json.dumps(uncovered),
                    "report_format": "lcov",
                    "report_date": date.today(),
                    "branch_coverage": 0,
                    "function_coverage": 0,
                })
            current_file = None

    if current_file:
        records.append({
            "repository_id": repository_id,
            "commit_hash": commit_hash,
            "file_path": current_file,
            "total_lines": total_lines,
            "covered_lines": covered_lines,
            "line_coverage": round(covered_lines / total_lines * 100, 2) if total_lines > 0 else 0,
            "uncovered_lines": json.dumps(uncovered),
            "report_format": "lcov",
            "report_date": date.today(),
            "branch_coverage": 0,
            "function_coverage": 0,
        })
    return records


def _parse_cobertura(text: str, repository_id: int, commit_hash: str) -> List[dict]:
    import xml.etree.ElementTree as ET
    records = []
    try:
        root = ET.fromstring(text)
        ns = {"c": "http://www.mavendev.com/cobertura"}
        for cl in root.findall(".//c:class", ns) or root.findall(".//class"):
            fpath = cl.get("name", "")
            pl = cl.find(".//c:line-rate", ns) or cl.find("line-rate")
            br = cl.find(".//c:branch-rate", ns) or cl.find("branch-rate")
            lc = float(pl.text) * 100 if pl is not None and pl.text else 0
            bc = float(br.text) * 100 if br is not None and br.text else 0
            lines_el = cl.findall(".//c:line", ns) or cl.findall("line")
            total_lines = len(lines_el)
            covered_lines = sum(1 for ln in lines_el if (ln.get("hits") or "0") != "0")
            uncovered = [int(ln.get("number")) for ln in lines_el if (ln.get("hits") or "0") == "0"]
            records.append({
                "repository_id": repository_id,
                "commit_hash": commit_hash,
                "file_path": fpath,
                "total_lines": total_lines,
                "covered_lines": covered_lines,
                "line_coverage": round(lc, 2),
                "branch_coverage": round(bc, 2),
                "uncovered_lines": json.dumps(uncovered),
                "report_format": "cobertura",
                "report_date": date.today(),
                "function_coverage": 0,
            })
    except Exception:
        pass
    return records


@router.get("/summary")
def get_coverage_summary(
    repository_id: Optional[int] = None,
    commit_hash: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CoverageRecord)
    if repository_id:
        query = query.filter(CoverageRecord.repository_id == repository_id)
    if commit_hash:
        query = query.filter(CoverageRecord.commit_hash == commit_hash)

    records = query.all()
    if not records:
        return {"code": 0, "data": {"line_coverage": 0, "total_lines": 0, "covered_lines": 0, "files": []}}

    total_lines = sum(r.total_lines for r in records)
    covered_lines = sum(r.covered_lines for r in records)
    files_data = [{
        "file_path": r.file_path,
        "line_coverage": r.line_coverage,
        "branch_coverage": r.branch_coverage,
        "total_lines": r.total_lines,
        "covered_lines": r.covered_lines,
        "uncovered_lines": json.loads(r.uncovered_lines or "[]"),
    } for r in records]

    return {"code": 0, "data": {
        "line_coverage": round(covered_lines / total_lines * 100, 2) if total_lines > 0 else 0,
        "total_lines": total_lines,
        "covered_lines": covered_lines,
        "files": files_data,
    }}


@router.get("/files")
def get_file_coverage_list(
    repository_id: int,
    db: Session = Depends(get_db)
):
    """获取文件覆盖率列表（最新一次提交）"""
    from sqlalchemy import func, desc
    sub = db.query(
        CoverageRecord.file_path,
        func.max(CoverageRecord.report_date).label("latest_date")
    ).filter(
        CoverageRecord.repository_id == repository_id
    ).group_by(CoverageRecord.file_path).subquery()

    records = db.query(CoverageRecord).join(
        sub,
        (CoverageRecord.file_path == sub.c.file_path) &
        (CoverageRecord.report_date == sub.c.latest_date)
    ).filter(CoverageRecord.repository_id == repository_id).all()

    return {"code": 0, "data": [{
        "id": r.id,
        "file_path": r.file_path,
        "line_coverage": r.line_coverage,
        "branch_coverage": r.branch_coverage,
        "total_lines": r.total_lines,
        "covered_lines": r.covered_lines,
        "commit_hash": r.commit_hash,
        "report_date": r.report_date,
    } for r in records]}
