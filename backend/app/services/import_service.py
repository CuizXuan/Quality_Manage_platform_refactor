import json
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.api_asset import ApiDefinition, ApiGroup
from app.models.import_asset import ImportIssue, ImportJob


def _json_loads(value: str, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, source_type: str, source_name: str, source_ref: str, project_id=None, created_by=None) -> ImportJob:
        job = ImportJob(
            project_id=project_id,
            source_type=source_type,
            source_name=source_name or source_type.upper(),
            source_ref=source_ref,
            status="running",
            created_by=created_by,
            summary=json.dumps({}),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_jobs(self) -> List[Dict]:
        jobs = self.db.query(ImportJob).order_by(ImportJob.created_at.desc()).all()
        return [self.serialize_job(job) for job in jobs]

    def import_document(self, request: dict, created_by=None) -> Dict:
        source_type = request["source_type"]
        source_name = request.get("source_name") or f"{source_type} import"
        source_ref = request.get("source_url") or source_name
        raw_content = request.get("raw_content") or ""
        if not raw_content and request.get("source_url"):
            import httpx

            response = httpx.get(request["source_url"], timeout=30)
            response.raise_for_status()
            raw_content = response.text

        job = self.create_job(source_type, source_name, source_ref, request.get("project_id"), created_by)
        spec = self._parse_source(source_type, raw_content)
        normalized = self._normalize_apis(source_type, spec)
        issues = self._collect_issues(normalized)
        imported = self._save_normalized_assets(normalized, request.get("project_id"))

        job.total_count = len(normalized)
        job.imported_count = imported
        job.issue_count = len(issues)
        job.status = "success"
        job.summary = json.dumps(
            {
                "coverage_rate": round(imported / len(normalized) * 100, 2) if normalized else 0,
                "conflict_count": sum(1 for issue in issues if issue["issue_type"] == "conflict"),
                "missing_example_count": sum(1 for issue in issues if issue["issue_type"] == "missing_example"),
            },
            ensure_ascii=False,
        )
        self.db.commit()

        for issue in issues:
            self.db.add(ImportIssue(job_id=job.id, **issue))
        self.db.commit()
        self.db.refresh(job)
        return self.serialize_job(job)

    def _parse_source(self, source_type: str, raw_content: str):
        parsed = _json_loads(raw_content, {})
        if not parsed:
            raise ValueError("导入文档解析失败")
        return parsed

    def _normalize_apis(self, source_type: str, spec: dict) -> List[Dict]:
        if source_type == "openapi":
            return self._normalize_openapi(spec)
        if source_type == "postman":
            return self._normalize_postman(spec)
        if source_type == "apifox":
            return self._normalize_apifox(spec)
        raise ValueError("不支持的导入类型")

    def _normalize_openapi(self, spec: dict) -> List[Dict]:
        title = spec.get("info", {}).get("title", "Imported API")
        base_url = ""
        servers = spec.get("servers") or []
        if servers and isinstance(servers[0], dict):
            base_url = servers[0].get("url", "")
        items = []
        for path, methods in (spec.get("paths") or {}).items():
            if not isinstance(methods, dict):
                continue
            for method, operation in methods.items():
                if method.lower() not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                    continue
                if not isinstance(operation, dict):
                    continue
                tags = operation.get("tags") or [title]
                request_body = operation.get("requestBody") or {}
                items.append(
                    {
                        "service_name": title,
                        "group_name": tags[0],
                        "name": operation.get("summary") or f"{method.upper()} {path}",
                        "method": method.upper(),
                        "path": path,
                        "base_url": base_url,
                        "summary": operation.get("summary") or "",
                        "description": operation.get("description") or "",
                        "tags": tags,
                        "parameters": operation.get("parameters") or [],
                        "request_body": request_body,
                        "responses": operation.get("responses") or {},
                    }
                )
        return items

    def _normalize_postman(self, spec: dict) -> List[Dict]:
        items = []
        collection_name = spec.get("info", {}).get("name", "Postman Collection")
        for item in spec.get("item") or []:
            request = item.get("request") or {}
            url = request.get("url") or {}
            raw_url = url.get("raw") if isinstance(url, dict) else str(url)
            path_parts = url.get("path") or [] if isinstance(url, dict) else []
            path = "/" + "/".join(path_parts) if path_parts else raw_url
            items.append(
                {
                    "service_name": collection_name,
                    "group_name": item.get("name") or collection_name,
                    "name": item.get("name") or "Imported Request",
                    "method": (request.get("method") or "GET").upper(),
                    "path": path,
                    "base_url": "",
                    "summary": item.get("name") or "",
                    "description": "",
                    "tags": [collection_name],
                    "parameters": [],
                    "request_body": request.get("body") or {},
                    "responses": {},
                }
            )
        return items

    def _normalize_apifox(self, spec: dict) -> List[Dict]:
        apis = spec.get("apis") or spec.get("items") or []
        title = spec.get("name") or spec.get("info", {}).get("name", "Apifox Import")
        items = []
        for api in apis:
            method = (api.get("method") or "GET").upper()
            path = api.get("path") or api.get("url") or "/"
            items.append(
                {
                    "service_name": title,
                    "group_name": api.get("folderName") or title,
                    "name": api.get("name") or f"{method} {path}",
                    "method": method,
                    "path": path,
                    "base_url": api.get("baseUrl") or "",
                    "summary": api.get("name") or "",
                    "description": api.get("description") or "",
                    "tags": api.get("tags") or [title],
                    "parameters": api.get("parameters") or [],
                    "request_body": api.get("requestBody") or {},
                    "responses": api.get("responses") or {},
                }
            )
        return items

    def _collect_issues(self, normalized: List[Dict]) -> List[Dict]:
        issues = []
        for item in normalized:
            if not item.get("request_body"):
                issues.append(
                    {
                        "issue_type": "missing_example",
                        "severity": "warning",
                        "endpoint_path": item["path"],
                        "method": item["method"],
                        "message": "缺少请求示例，生成用例时会退化为基础模板",
                        "details": json.dumps({"name": item["name"]}, ensure_ascii=False),
                    }
                )
            if "{{" in (item.get("base_url") or ""):
                issues.append(
                    {
                        "issue_type": "unresolved_variable",
                        "severity": "warning",
                        "endpoint_path": item["path"],
                        "method": item["method"],
                        "message": "检测到未解析环境变量，请补充环境配置",
                        "details": json.dumps({"base_url": item.get("base_url")}, ensure_ascii=False),
                    }
                )
            existing = (
                self.db.query(ApiDefinition)
                .filter(ApiDefinition.method == item["method"], ApiDefinition.path == item["path"])
                .first()
            )
            if existing:
                issues.append(
                    {
                        "issue_type": "conflict",
                        "severity": "info",
                        "endpoint_path": item["path"],
                        "method": item["method"],
                        "message": "接口已存在，将保留新版本并可用于后续差异比较",
                        "details": json.dumps({"existing_id": existing.id}, ensure_ascii=False),
                    }
                )
        return issues

    def _save_normalized_assets(self, normalized: List[Dict], project_id=None) -> int:
        group_cache: Dict[Tuple[str, str], ApiGroup] = {}
        imported = 0
        for item in normalized:
            group_key = (item["service_name"], item["group_name"])
            if group_key not in group_cache:
                parent = self._ensure_group(item["service_name"], project_id=project_id)
                group_cache[group_key] = self._ensure_group(
                    item["group_name"],
                    parent_id=parent.id,
                    project_id=project_id,
                )
            group = group_cache[group_key]
            api = ApiDefinition(
                project_id=project_id,
                group_id=group.id,
                name=item["name"],
                method=item["method"],
                path=item["path"],
                base_url=item.get("base_url"),
                summary=item.get("summary") or "",
                description=item.get("description") or "",
                tags=json.dumps(item.get("tags") or [], ensure_ascii=False),
                parameters=json.dumps(item.get("parameters") or [], ensure_ascii=False),
                request_body=json.dumps(item.get("request_body") or {}, ensure_ascii=False),
                responses=json.dumps(item.get("responses") or {}, ensure_ascii=False),
                version="1.0.0",
                status="active",
            )
            self.db.add(api)
            imported += 1
        self.db.commit()
        return imported

    def _ensure_group(self, name: str, parent_id=None, project_id=None) -> ApiGroup:
        existing = (
            self.db.query(ApiGroup)
            .filter(ApiGroup.name == name, ApiGroup.parent_id == parent_id, ApiGroup.project_id == project_id)
            .first()
        )
        if existing:
            return existing
        group = ApiGroup(name=name, parent_id=parent_id, project_id=project_id)
        self.db.add(group)
        self.db.flush()
        return group

    def serialize_job(self, job: ImportJob) -> Dict:
        return {
            "id": job.id,
            "project_id": job.project_id,
            "source_type": job.source_type,
            "source_name": job.source_name,
            "source_ref": job.source_ref,
            "status": job.status,
            "total_count": job.total_count or 0,
            "imported_count": job.imported_count or 0,
            "issue_count": job.issue_count or 0,
            "summary": _json_loads(job.summary, {}),
            "issues": [
                {
                    "id": issue.id,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "endpoint_path": issue.endpoint_path or "",
                    "method": issue.method or "",
                    "message": issue.message or "",
                    "details": _json_loads(issue.details, {}),
                }
                for issue in job.issues
            ],
        }
