"""
DocGen Router — 文档生成中心所有 API 端点
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.docgen import DocGenerationTask, DocGenerationRule, DocGenerationTemplate
from app.schemas.docgen import (
    DocGenTaskCreate, DocGenTaskUpdate, DocGenTaskResponse, DocGenTaskListResponse,
    DocGenRuleCreate, DocGenRuleUpdate, DocGenRuleResponse, DocGenRuleListResponse,
    DocGenTemplateResponse, DocGenTemplateListResponse,
    DocGenRequirementGenerateRequest, DocGenDatabaseGenerateRequest, DocGenApiGenerateRequest,
    DocGenRequirementPreview, DocGenApiPreview, DocGenDatabasePreview,
)
from app.services.docgen import (
    DocParser, DocBuilder, OpenApiParser, DbConverter, SqliteConnector,
    DocumentTree, Platform, Section, Group, Leaf,
)
from app.services.docgen.storage import (
    save_upload, get_upload_path, save_output, get_output_path,
    get_templates_dir, get_rules_dir,
)


router = APIRouter(prefix="/api/docgen", tags=["docgen"])


# ── Dependency ────────────────────────────────────────────────────────────────

def _get_db():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


# ── Task Endpoints ────────────────────────────────────────────────────────────

@router.get("/tasks", response_model=dict)
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(_get_db),
):
    """查询文档生成任务列表"""
    query = db.query(DocGenerationTask)
    if task_type:
        query = query.filter(DocGenerationTask.task_type == task_type)
    if status:
        query = query.filter(DocGenerationTask.status == status)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (DocGenerationTask.name.ilike(pattern)) |
            (DocGenerationTask.source_filename.ilike(pattern)) |
            (DocGenerationTask.output_filename.ilike(pattern))
        )
    total = query.count()
    items = query.order_by(DocGenerationTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_serialize_task(t) for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/tasks/{task_id}", response_model=dict)
def get_task(task_id: int, db: Session = Depends(_get_db)):
    task = db.query(DocGenerationTask).filter(DocGenerationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _serialize_task(task)


@router.get("/tasks/download/{task_id}")
def download_task_file(task_id: int, db: Session = Depends(_get_db)):
    """下载任务生成的文件"""
    task = db.query(DocGenerationTask).filter(DocGenerationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not task.output_path:
        raise HTTPException(status_code=404, detail="文件未生成")
    try:
        path = get_output_path(task.output_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(path=path, filename=task.output_filename or "output.docx", media_type='application/octet-stream')
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")


# ── Rule Endpoints ─────────────────────────────────────────────────────────────

@router.get("/rules", response_model=dict)
def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    doc_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(_get_db),
):
    """查询规则列表"""
    query = db.query(DocGenerationRule)
    if doc_type:
        query = query.filter(DocGenerationRule.doc_type == doc_type)
    if enabled is not None:
        query = query.filter(DocGenerationRule.enabled == enabled)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (DocGenerationRule.name.ilike(pattern)) |
            (DocGenerationRule.filename.ilike(pattern)) |
            (DocGenerationRule.doc_type.ilike(pattern))
        )
    total = query.count()
    items = query.order_by(DocGenerationRule.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_serialize_rule(r) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/rules", response_model=dict)
def create_rule(data: DocGenRuleCreate, db: Session = Depends(_get_db)):
    """创建规则"""
    # 验证 JSON 内容
    try:
        json.loads(data.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="规则内容必须是有效的 JSON")
    rule = DocGenerationRule(
        name=data.name,
        doc_type=data.doc_type,
        filename=data.filename,
        content=data.content,
        enabled=data.enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _serialize_rule(rule)


@router.get("/rules/{rule_id}", response_model=dict)
def get_rule(rule_id: int, db: Session = Depends(_get_db)):
    rule = db.query(DocGenerationRule).filter(DocGenerationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return _serialize_rule(rule)


@router.put("/rules/{rule_id}", response_model=dict)
def update_rule(rule_id: int, data: DocGenRuleUpdate, db: Session = Depends(_get_db)):
    rule = db.query(DocGenerationRule).filter(DocGenerationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    if data.name is not None:
        rule.name = data.name
    if data.content is not None:
        try:
            json.loads(data.content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="规则内容必须是有效的 JSON")
        rule.content = data.content
    if data.enabled is not None:
        rule.enabled = data.enabled
    db.commit()
    db.refresh(rule)
    return _serialize_rule(rule)


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(_get_db)):
    rule = db.query(DocGenerationRule).filter(DocGenerationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    db.delete(rule)
    db.commit()
    return {"ok": True}


# ── Template Endpoints ────────────────────────────────────────────────────────

@router.get("/templates", response_model=dict)
def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(_get_db),
):
    """查询模板列表"""
    query = db.query(DocGenerationTemplate)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (DocGenerationTemplate.name.ilike(pattern)) |
            (DocGenerationTemplate.filename.ilike(pattern))
        )
    total = query.count()
    items = query.order_by(DocGenerationTemplate.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_serialize_template(t) for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/templates/upload", response_model=dict)
async def upload_template(file: UploadFile = File(...), db: Session = Depends(_get_db)):
    """上传模板文件"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    content = await file.read()
    safe_path = save_upload(content, file.filename)
    filename = os.path.basename(safe_path)
    dest = get_templates_dir() / filename
    shutil.copyfile(get_upload_path(safe_path), dest)
    tmpl = DocGenerationTemplate(
        name=file.filename,
        filename=filename,
        file_path=str(dest),
        file_size=len(content),
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return _serialize_template(tmpl)


@router.post("/uploads/upload")
def upload_file(file: UploadFile = File(...)):
    """上传文件到 uploads 目录"""
    import tempfile
    content = file.file.read()
    safe_path = save_upload(content, file.filename)
    return {'path': safe_path, 'name': file.filename}


@router.get("/uploads")
def list_uploads():
    """列出 uploads 目录下的文件"""
    from app.services.docgen.storage import UPLOADS_DIR, _ensure_dirs
    _ensure_dirs()
    files = []
    for f in UPLOADS_DIR.iterdir():
        if f.is_file():
            files.append({
                'name': f.name,
                'size': f.stat().st_size,
            })
    return files


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(_get_db)):
    tmpl = db.query(DocGenerationTemplate).filter(DocGenerationTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.delete(tmpl)
    db.commit()
    return {"ok": True}


# ── Requirement Doc Generation ───────────────────────────────────────────────

@router.post("/requirement/preview")
def preview_requirement(req: DocGenRequirementGenerateRequest, db: Session = Depends(_get_db)):
    """预览需求文档结构"""
    try:
        path = get_upload_path(req.source_file_path)
        parser = DocParser(str(path))
        tree = parser.parse()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败: {str(e)}")

    platforms = [p.name for p in tree.platforms]
    sections = {}
    for plat in tree.platforms:
        for sec in plat.sections:
            if sec.name not in sections:
                sections[sec.name] = []
            for grp in sec.groups:
                if grp.name not in sections[sec.name]:
                    sections[sec.name].append(grp.name)

    return {
        "total_leaves": tree.total_leaves,
        "platforms": platforms,
        "sections": sections,
    }


@router.post("/requirement/generate")
def generate_requirement(req: DocGenRequirementGenerateRequest, db: Session = Depends(_get_db)):
    """生成需求设计文档"""
    task = DocGenerationTask(
        name=req.output_filename or "需求设计文档",
        task_type="requirement_design",
        status="running",
        source_filename=os.path.basename(req.source_file_path),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        path = get_upload_path(req.source_file_path)
        parser = DocParser(str(path))
        tree = parser.parse()

        rule_content = None
        if req.rule_ids:
            rule_obj = db.query(DocGenerationRule).filter(
                DocGenerationRule.id.in_(req.rule_ids),
                DocGenerationRule.enabled == True
            ).first()
            if rule_obj:
                rule_content = json.loads(rule_obj.content)

        if not rule_content:
            rules_dir = get_rules_dir()
            default_rule = rules_dir / "概要设计.json"
            if default_rule.exists():
                with open(default_rule, "r", encoding="utf-8") as f:
                    rule_content = json.load(f)

        if not rule_content:
            raise HTTPException(status_code=400, detail="未找到可用规则")

        template_path = None
        if req.template_id:
            tmpl = db.query(DocGenerationTemplate).filter(DocGenerationTemplate.id == req.template_id).first()
            if tmpl and os.path.exists(tmpl.file_path):
                template_path = tmpl.file_path

        if not template_path:
            templates_dir = get_templates_dir()
            default_tmpl = templates_dir / "概要设计说明书-模板.docx"
            if default_tmpl.exists():
                template_path = str(default_tmpl)

        if not template_path:
            raise HTTPException(status_code=400, detail="未找到可用模板")

        builder = DocBuilder(template_path, rule_content)
        builder.build(tree)

        output_name = req.output_filename or f"需求设计_{task.id}.docx"
        output_path = save_output(b"", output_name)
        builder.save(get_output_path(output_path))

        task.status = "success"
        task.output_filename = output_name
        task.output_path = output_path
        task.finished_at = task.created_at
    except HTTPException:
        raise
    except Exception as e:
        task.status = "failed"
        task.message = str(e)

    db.commit()
    db.refresh(task)
    return _serialize_task(task)


# ── Database Design Generation ────────────────────────────────────────────────

@router.post("/database/preview")
def preview_database(req: DocGenDatabaseGenerateRequest, db: Session = Depends(_get_db)):
    """预览数据库表结构"""
    try:
        if req.db_type == "sqlite":
            if not req.file_path:
                raise HTTPException(status_code=400, detail="SQLite 文件路径不能为空")
            path = get_upload_path(req.file_path)
            connector = SqliteConnector(str(path))
            converter = DbConverter(connector)
            tables = converter.get_tables()
            table_infos = []
            for t in tables:
                info = connector.get_table_info(t)
                table_infos.append({
                    "name": info.name,
                    "column_count": len(info.columns),
                    "index_count": len(info.indexes),
                })
            return {"total_tables": len(tables), "tables": table_infos}
        else:
            raise HTTPException(status_code=400, detail=f"{req.db_type} 连接暂不支持")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"预览失败: {str(e)}")


@router.post("/database/generate")
def generate_database(req: DocGenDatabaseGenerateRequest, db: Session = Depends(_get_db)):
    """生成数据库设计文档"""
    task = DocGenerationTask(
        name=req.output_filename or "数据库设计文档",
        task_type="database_design",
        status="running",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        if req.db_type != "sqlite":
            raise HTTPException(status_code=400, detail="仅支持 SQLite")

        if not req.file_path:
            raise HTTPException(status_code=400, detail="SQLite 文件路径不能为空")

        path = get_upload_path(req.file_path)
        connector = SqliteConnector(str(path))
        converter = DbConverter(connector)

        selected = req.selected_tables or converter.get_tables()
        leaf_datas = converter.to_leaf_datas(selected)

        rules_dir = get_rules_dir()
        rule_file = rules_dir / "数据库设计.json"
        if not rule_file.exists():
            raise HTTPException(status_code=400, detail="数据库设计规则文件不存在")

        with open(rule_file, "r", encoding="utf-8") as f:
            rule = json.load(f)

        templates_dir = get_templates_dir()
        default_tmpl = templates_dir / "概要设计说明书-模板.docx"
        if not default_tmpl.exists():
            raise HTTPException(status_code=400, detail="模板文件不存在")

        builder = DocBuilder(str(default_tmpl), rule)
        builder.set_external_data(leaf_datas)

        from app.services.docgen.datamodel import DocumentTree, Platform, Section, Group, Leaf
        tree = DocumentTree(platforms=[])
        plat = Platform(name="数据库设计")
        sec = Section(name="数据表")
        for table_name in selected:
            grp = Group(name=table_name, heading_level=4)
            leaf = Leaf(name=table_name, heading_level=5)
            if table_name in leaf_datas:
                leaf.data = leaf_datas[table_name]
            grp.children.append(leaf)
            sec.groups.append(grp)
        plat.sections.append(sec)
        tree.platforms.append(plat)

        builder.build(tree)

        output_name = req.output_filename or f"数据库设计_{task.id}.docx"
        output_path = save_output(b"", output_name)
        builder.save(get_output_path(output_path))

        task.status = "success"
        task.output_filename = output_name
        task.output_path = output_path
        task.finished_at = task.created_at
    except HTTPException:
        raise
    except Exception as e:
        task.status = "failed"
        task.message = str(e)

    db.commit()
    db.refresh(task)
    return _serialize_task(task)


# ── API Design Generation ─────────────────────────────────────────────────────

@router.post("/api/preview")
def preview_api(req: DocGenApiGenerateRequest, db: Session = Depends(_get_db)):
    """预览 API 接口列表"""
    try:
        if req.source_type == "system":
            import httpx
            resp = httpx.get("http://localhost:8000/openapi.json", timeout=10)
            spec = resp.json()
        elif req.source_type == "url":
            if not req.openapi_url:
                raise HTTPException(status_code=400, detail="OpenAPI URL 不能为空")
            parser = OpenApiParser.from_url(req.openapi_url)
            spec = parser.spec
        elif req.source_type == "file":
            if not req.openapi_file_path:
                raise HTTPException(status_code=400, detail="OpenAPI 文件路径不能为空")
            path = get_upload_path(req.openapi_file_path)
            parser = OpenApiParser.from_file(str(path))
            spec = parser.spec
        else:
            raise HTTPException(status_code=400, detail="无效的来源类型")

        openapi_parser = OpenApiParser(spec)
        openapi_parser.parse()
        tags = openapi_parser.get_tags()

        endpoint_summaries = []
        for ep in openapi_parser._endpoints:
            endpoint_summaries.append({
                "method": ep.method,
                "path": ep.path,
                "summary": ep.summary,
                "tag": ep.tag,
                "param_count": len(ep.parameters),
            })

        return {
            "total_endpoints": len(openapi_parser._endpoints),
            "tags": tags,
            "endpoints": endpoint_summaries,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"预览失败: {str(e)}")


@router.post("/api/generate")
def generate_api(req: DocGenApiGenerateRequest, db: Session = Depends(_get_db)):
    """生成 API 设计文档"""
    task = DocGenerationTask(
        name=req.output_filename or "接口设计文档",
        task_type="api_design",
        status="running",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        if req.source_type == "system":
            import httpx
            resp = httpx.get("http://localhost:8000/openapi.json", timeout=10)
            spec = resp.json()
        elif req.source_type == "url":
            if not req.openapi_url:
                raise HTTPException(status_code=400, detail="OpenAPI URL 不能为空")
            parser = OpenApiParser.from_url(req.openapi_url)
            spec = parser.spec
        elif req.source_type == "file":
            if not req.openapi_file_path:
                raise HTTPException(status_code=400, detail="OpenAPI 文件路径不能为空")
            path = get_upload_path(req.openapi_file_path)
            parser = OpenApiParser.from_file(str(path))
            spec = parser.spec
        else:
            raise HTTPException(status_code=400, detail="无效的来源类型")

        openapi_parser = OpenApiParser(spec)
        openapi_parser.parse()

        if req.output_format == "markdown":
            selected_tags = req.selected_tags or openapi_parser.get_tags()
            content = openapi_parser.to_markdown(selected_tags)
            output_name = req.output_filename or f"接口设计_{task.id}.md"
            output_path = save_output(content.encode("utf-8"), output_name)
            task.status = "success"
            task.output_filename = output_name
            task.output_path = output_path
            task.finished_at = task.created_at
        else:
            raise HTTPException(status_code=400, detail="暂不支持 docx 格式的 API 文档生成")

    except HTTPException:
        raise
    except Exception as e:
        task.status = "failed"
        task.message = str(e)

    db.commit()
    db.refresh(task)
    return _serialize_task(task)


# ── Background generation tasks ──────────────────────────────────────────────

def _generate_requirement_background(task_id: int, req_dict: dict) -> None:
    """后台生成需求设计文档"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        task = db.query(DocGenerationTask).filter(DocGenerationTask.id == task_id).first()
        if not task:
            return

        path = get_upload_path(req_dict["source_file_path"])
        parser = DocParser(str(path))
        tree = parser.parse()

        rule_content = None
        if req_dict.get("rule_ids"):
            rule_obj = db.query(DocGenerationRule).filter(
                DocGenerationRule.id.in_(req_dict["rule_ids"]),
                DocGenerationRule.enabled == True
            ).first()
            if rule_obj:
                rule_content = json.loads(rule_obj.content)

        if not rule_content:
            rules_dir = get_rules_dir()
            default_rule = rules_dir / "概要设计.json"
            if default_rule.exists():
                with open(default_rule, "r", encoding="utf-8") as f:
                    rule_content = json.load(f)

        if not rule_content:
            task.status = "failed"
            task.message = "未找到可用规则"
            db.commit()
            return

        template_path = None
        if req_dict.get("template_id"):
            tmpl = db.query(DocGenerationTemplate).filter(DocGenerationTemplate.id == req_dict["template_id"]).first()
            if tmpl and os.path.exists(tmpl.file_path):
                template_path = tmpl.file_path

        if not template_path:
            templates_dir = get_templates_dir()
            default_tmpl = templates_dir / "概要设计说明书-模板.docx"
            if default_tmpl.exists():
                template_path = str(default_tmpl)

        if not template_path:
            task.status = "failed"
            task.message = "未找到可用模板"
            db.commit()
            return

        builder = DocBuilder(template_path, rule_content)
        builder.build(tree)

        output_name = req_dict.get("output_filename") or f"需求设计_{task.id}.docx"
        output_path = save_output(b"", output_name)
        builder.save(get_output_path(output_path))

        task.status = "success"
        task.output_filename = output_name
        task.output_path = output_path
        task.finished_at = task.created_at
    except Exception as e:
        task.status = "failed"
        task.message = str(e)
    finally:
        db.commit()
        db.close()


def _generate_database_background(task_id: int, req_dict: dict) -> None:
    """后台生成数据库设计文档"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        task = db.query(DocGenerationTask).filter(DocGenerationTask.id == task_id).first()
        if not task:
            return

        if req_dict["db_type"] != "sqlite":
            task.status = "failed"
            task.message = "仅支持 SQLite"
            db.commit()
            return

        path = get_upload_path(req_dict["file_path"])
        connector = SqliteConnector(str(path))
        converter = DbConverter(connector)

        selected = req_dict.get("selected_tables") or converter.get_tables()
        leaf_datas = converter.to_leaf_datas(selected)

        rules_dir = get_rules_dir()
        rule_file = rules_dir / "数据库设计.json"
        if not rule_file.exists():
            task.status = "failed"
            task.message = "数据库设计规则文件不存在"
            db.commit()
            return

        with open(rule_file, "r", encoding="utf-8") as f:
            rule = json.load(f)

        templates_dir = get_templates_dir()
        default_tmpl = templates_dir / "概要设计说明书-模板.docx"
        if not default_tmpl.exists():
            task.status = "failed"
            task.message = "模板文件不存在"
            db.commit()
            return

        builder = DocBuilder(str(default_tmpl), rule)
        builder.set_external_data(leaf_datas)

        tree = DocumentTree(platforms=[])
        plat = Platform(name="数据库设计")
        sec = Section(name="数据表")
        for table_name in selected:
            grp = Group(name=table_name, heading_level=4)
            leaf = Leaf(name=table_name, heading_level=5)
            if table_name in leaf_datas:
                leaf.data = leaf_datas[table_name]
            grp.children.append(leaf)
            sec.groups.append(grp)
        plat.sections.append(sec)
        tree.platforms.append(plat)

        builder.build(tree)

        output_name = req_dict.get("output_filename") or f"数据库设计_{task.id}.docx"
        output_path = save_output(b"", output_name)
        builder.save(get_output_path(output_path))

        task.status = "success"
        task.output_filename = output_name
        task.output_path = output_path
        task.finished_at = task.created_at
    except Exception as e:
        task.status = "failed"
        task.message = str(e)
    finally:
        db.commit()
        db.close()


def _generate_api_background(task_id: int, req_dict: dict) -> None:
    """后台生成 API 设计文档"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        task = db.query(DocGenerationTask).filter(DocGenerationTask.id == task_id).first()
        if not task:
            return

        if req_dict["source_type"] == "system":
            import httpx
            resp = httpx.get("http://localhost:8000/openapi.json", timeout=30)
            spec = resp.json()
        elif req_dict["source_type"] == "url":
            parser = OpenApiParser.from_url(req_dict["openapi_url"])
            spec = parser.spec
        elif req_dict["source_type"] == "file":
            path = get_upload_path(req_dict["openapi_file_path"])
            parser = OpenApiParser.from_file(str(path))
            spec = parser.spec
        else:
            task.status = "failed"
            task.message = "无效的来源类型"
            db.commit()
            return

        openapi_parser = OpenApiParser(spec)
        openapi_parser.parse()

        if req_dict.get("output_format") == "markdown":
            selected_tags = req_dict.get("selected_tags") or openapi_parser.get_tags()
            content = openapi_parser.to_markdown(selected_tags)
            output_name = req_dict.get("output_filename") or f"接口设计_{task.id}.md"
            output_path = save_output(content.encode("utf-8"), output_name)
            task.status = "success"
            task.output_filename = output_name
            task.output_path = output_path
            task.finished_at = task.created_at
        else:
            task.status = "failed"
            task.message = "暂不支持 docx 格式的 API 文档生成"
    except Exception as e:
        task.status = "failed"
        task.message = str(e)
    finally:
        db.commit()
        db.close()


# ── Async generate endpoints ──────────────────────────────────────────────────

@router.post("/requirement/generate-async")
def generate_requirement_async(
    req: DocGenRequirementGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(_get_db),
):
    """异步生成需求设计文档（立即返回任务，后台执行）"""
    task = DocGenerationTask(
        name=req.output_filename or "需求设计文档",
        task_type="requirement_design",
        status="running",
        source_filename=os.path.basename(req.source_file_path),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    req_dict = {
        "source_file_path": req.source_file_path,
        "rule_ids": req.rule_ids,
        "template_id": req.template_id,
        "output_filename": req.output_filename,
    }
    background_tasks.add_task(_generate_requirement_background, task.id, req_dict)
    return _serialize_task(task)


@router.post("/database/generate-async")
def generate_database_async(
    req: DocGenDatabaseGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(_get_db),
):
    """异步生成数据库设计文档（立即返回任务，后台执行）"""
    task = DocGenerationTask(
        name=req.output_filename or "数据库设计文档",
        task_type="database_design",
        status="running",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    req_dict = {
        "db_type": req.db_type,
        "file_path": req.file_path,
        "selected_tables": req.selected_tables,
        "output_filename": req.output_filename,
    }
    background_tasks.add_task(_generate_database_background, task.id, req_dict)
    return _serialize_task(task)


@router.post("/api/generate-async")
def generate_api_async(
    req: DocGenApiGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(_get_db),
):
    """异步生成 API 设计文档（立即返回任务，后台执行）"""
    task = DocGenerationTask(
        name=req.output_filename or "接口设计文档",
        task_type="api_design",
        status="running",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    req_dict = {
        "source_type": req.source_type,
        "openapi_url": req.openapi_url,
        "openapi_file_path": req.openapi_file_path,
        "output_format": req.output_format,
        "selected_tags": req.selected_tags,
        "output_filename": req.output_filename,
    }
    background_tasks.add_task(_generate_api_background, task.id, req_dict)
    return _serialize_task(task)


# ── Serializers ────────────────────────────────────────────────────────────────

def _serialize_task(t: DocGenerationTask) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "task_type": t.task_type,
        "status": t.status,
        "source_filename": t.source_filename,
        "output_filename": t.output_filename,
        "output_path": t.output_path,
        "message": t.message or "",
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "finished_at": t.finished_at.isoformat() if t.finished_at else None,
    }


def _serialize_rule(r: DocGenerationRule) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "doc_type": r.doc_type,
        "filename": r.filename,
        "content": r.content,
        "enabled": bool(r.enabled),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _serialize_template(t: DocGenerationTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "doc_type": t.doc_type,
        "filename": t.filename,
        "file_path": t.file_path,
        "file_size": t.file_size,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }