import json
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.config import DEBUG_API_ORIGIN, DEBUG_PROXY_ORIGIN
from app.models.terminal import DebugRequest, DebugResult


class TerminalService:
    def __init__(self, db: Session):
        self.db = db

    def create_debug_request(
        self,
        method: str,
        url: str,
        query_params: Dict[str, Any],
        headers: Dict[str, Any],
        cookies: Dict[str, Any],
        auth_config: Dict[str, Any],
        body_type: str,
        body: str,
        environment_id: Optional[int],
        created_by: Optional[int],
        source_type: str = "manual",
    ) -> DebugRequest:
        req = DebugRequest(
            method=method.upper(),
            url=url,
            query_params=json.dumps(query_params),
            headers=json.dumps(headers),
            cookies=json.dumps(cookies),
            auth_config=json.dumps(auth_config),
            body_type=body_type,
            body=body,
            environment_id=environment_id,
            created_by=created_by,
            source_type=source_type,
            status="active",
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def execute_debug(self, request_id: int) -> DebugResult:
        req = self.db.query(DebugRequest).filter(DebugRequest.id == request_id).first()
        if not req:
            raise ValueError(f"Debug request {request_id} not found")

        query_params = json.loads(req.query_params)
        headers = json.loads(req.headers)
        cookies = json.loads(req.cookies)

        # Apply auth config
        auth_config = json.loads(req.auth_config)
        if auth_config.get("type") == "bearer":
            headers["Authorization"] = f"Bearer {auth_config.get('token', '')}"
        elif auth_config.get("type") == "basic":
            import base64
            creds = f"{auth_config.get('username', '')}:{auth_config.get('password', '')}"
            headers["Authorization"] = f"Basic {base64.b64encode(creds.encode()).decode()}"

        # Build URL with query params
        url = self._normalize_debug_url(req.url)
        if query_params:
            separator = "&" if "?" in url else "?"
            url += separator + urlencode(query_params, doseq=True)

        start_time = time.time()
        result = DebugResult(debug_request_id=request_id)

        try:
            request_kwargs = {
                "method": req.method,
                "url": url,
                "headers": headers,
                "cookies": cookies,
            }

            if req.body:
                if req.body_type == "json":
                    try:
                        request_kwargs["json"] = json.loads(req.body)
                    except json.JSONDecodeError:
                        request_kwargs["content"] = req.body
                elif req.body_type == "form":
                    try:
                        request_kwargs["data"] = json.loads(req.body)
                    except json.JSONDecodeError:
                        request_kwargs["content"] = req.body
                else:
                    request_kwargs["content"] = req.body

            with httpx.Client(timeout=30.0) as client:
                response = client.request(**request_kwargs)
                result.status_code = response.status_code
                result.response_headers = json.dumps(dict(response.headers))
                result.response_body = response.text
                result.duration_ms = int((time.time() - start_time) * 1000)
        except httpx.TimeoutException:
            result.status_code = 0
            result.error_message = "Request timeout"
            result.duration_ms = int((time.time() - start_time) * 1000)
        except httpx.RequestError as e:
            result.status_code = 0
            result.error_message = f"RequestError: {e}"
            result.duration_ms = int((time.time() - start_time) * 1000)
        except Exception as e:
            result.status_code = 0
            result.error_message = str(e)
            result.duration_ms = int((time.time() - start_time) * 1000)

        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def _normalize_debug_url(self, url: str) -> str:
        if not url:
            return url
        if url.startswith(f"{DEBUG_PROXY_ORIGIN}/api/"):
            return url.replace(DEBUG_PROXY_ORIGIN, DEBUG_API_ORIGIN, 1)
        return url

    def get_history(
        self,
        page: int = 1,
        page_size: int = 20,
        created_by: Optional[int] = None,
    ) -> Tuple[list, int]:
        query = self.db.query(DebugRequest).filter(DebugRequest.status == "active")
        if created_by:
            query = query.filter(DebugRequest.created_by == created_by)
        query = query.order_by(DebugRequest.created_at.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_request_with_result(self, request_id: int) -> Optional[DebugRequest]:
        return self.db.query(DebugRequest).filter(DebugRequest.id == request_id).first()

    def toggle_favorite(self, request_id: int) -> DebugRequest:
        req = self.db.query(DebugRequest).filter(DebugRequest.id == request_id).first()
        if not req:
            raise ValueError(f"Debug request {request_id} not found")
        req.status = "favorite" if req.status == "active" else "active"
        self.db.commit()
        self.db.refresh(req)
        return req

    def delete_request(self, request_id: int) -> bool:
        req = self.db.query(DebugRequest).filter(DebugRequest.id == request_id).first()
        if not req:
            return False
        self.db.delete(req)
        self.db.commit()
        return True

    def import_openapi_document(
        self,
        *,
        source_url: str = "",
        raw_content: str = "",
    ) -> list[dict]:
        content = raw_content.strip()
        if source_url:
            with httpx.Client(timeout=20.0) as client:
                response = client.get(source_url)
                response.raise_for_status()
                content = response.text

        if not content:
            return []

        document = json.loads(content)
        paths = document.get("paths", {})
        items = []

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, config in methods.items():
                if method.lower() not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                    continue
                summary = ""
                if isinstance(config, dict):
                    summary = config.get("summary") or config.get("operationId") or ""
                items.append({
                    "method": method.upper(),
                    "url": path,
                    "summary": summary,
                })

        return items
