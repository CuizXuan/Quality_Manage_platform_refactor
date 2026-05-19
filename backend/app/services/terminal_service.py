import json
import time
from typing import Any, Dict, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

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
        url = req.url
        if query_params:
            separator = "&" if "?" in url else "?"
            query_parts = [f"{k}={v}" for k, v in query_params.items()]
            url += separator + "&".join(query_parts)

        start_time = time.time()
        result = DebugResult(debug_request_id=request_id)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=req.method,
                    url=url,
                    headers=headers,
                    cookies=cookies,
                    content=req.body if req.body else None,
                )
                result.status_code = response.status_code
                result.response_headers = json.dumps(dict(response.headers))
                result.response_body = response.text
                result.duration_ms = int((time.time() - start_time) * 1000)
        except httpx.TimeoutException:
            result.error_message = "Request timeout"
            result.duration_ms = int((time.time() - start_time) * 1000)
        except Exception as e:
            result.error_message = str(e)
            result.duration_ms = int((time.time() - start_time) * 1000)

        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

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
