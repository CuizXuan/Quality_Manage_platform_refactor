# -*- coding: utf-8 -*-
"""
Phase 5 - 审计日志中间件
记录所有 API 操作，提供合规审计追踪
"""
import json
import time
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件
    记录所有 HTTP 请求的详细信息
    """

    # 不需要记录日志的路径
    EXCLUDED_PATHS = {
        "/",
        "/api/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    # 敏感操作类型
    SENSITIVE_OPERATIONS = {
        "POST": {
            "/api/auth/login": "user_login",
            "/api/auth/register": "user_register",
            "/api/users": "user_create",
            "/api/users/delete": "user_delete",
            "/api/projects": "project_create",
            "/api/projects/delete": "project_delete",
            "/api/tenant": "tenant_create",
            "/api/marketplace/plugins": "plugin_publish",
            "/api/marketplace/plugins/{id}/install": "plugin_install",
            "/api/cli/keys": "cli_key_create",
        },
        "PUT": {
            "/api/users/{id}": "user_update",
            "/api/projects/{id}": "project_update",
        },
        "DELETE": {
            "/api/users/{id}": "user_delete",
            "/api/projects/{id}": "project_delete",
            "/api/marketplace/plugins/{id}": "plugin_delete",
            "/api/cli/keys/{id}": "cli_key_delete",
        },
    }

    # 高敏感操作
    HIGH_SENSITIVITY = {
        "user_login", "user_register", "user_delete",
        "tenant_create", "cli_key_create",
        "plugin_publish", "plugin_delete",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        """处理每个请求并记录审计日志"""
        # 跳过排除路径
        if self._is_excluded(request.url.path):
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()
        method = request.method
        path = request.url.path
        client_ip = self._get_client_ip(request)

        # 提取用户信息
        user_id = getattr(request.state, "user_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        # 确定操作类型
        operation = self._classify_operation(method, path)

        # 处理请求体（如果有）
        request_body = None
        if method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    # 脱敏处理
                    request_body = self._sanitize_body(body.decode("utf-8", errors="ignore"))
            except Exception:
                pass

        # 执行请求
        response = await call_next(request)

        # 计算耗时
        duration_ms = int((time.time() - start_time) * 1000)
        status_code = response.status_code

        # 异步记录审计日志（不阻塞响应）
        try:
            self._log_audit(
                method=method,
                path=path,
                operation=operation,
                user_id=user_id,
                tenant_id=tenant_id,
                client_ip=client_ip,
                status_code=status_code,
                duration_ms=duration_ms,
                request_body=request_body,
                is_sensitive=operation in self.HIGH_SENSITIVITY,
            )
        except Exception as e:
            # 审计日志失败不应该影响业务
            print(f"[AuditLog] Failed to write audit log: {e}")

        return response

    def _is_excluded(self, path: str) -> bool:
        """判断路径是否需要排除"""
        if path in self.EXCLUDED_PATHS:
            return True
        # 排除静态资源和文档路径
        if path.startswith("/static") or path.startswith("/assets"):
            return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        # 优先从 X-Forwarded-For 获取（反向代理场景）
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # 其次从 X-Real-IP 获取
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        # 最后使用直接连接的 IP
        if request.client:
            return request.client.host
        return "unknown"

    def _classify_operation(self, method: str, path: str) -> str:
        """对操作进行分类"""
        op_map = self.SENSITIVE_OPERATIONS.get(method, {})

        # 精确匹配
        if path in op_map:
            return op_map[path]

        # 路径参数匹配（如 /api/users/123）
        for pattern, op_name in op_map.items():
            if self._match_path_pattern(pattern, path):
                return op_name

        # 根据路径自动分类
        if path.startswith("/api/"):
            parts = path.strip("/").split("/")
            if len(parts) >= 2:
                resource = parts[1]  # 如 "users", "projects"
                action = {
                    "POST": f"{resource}_create",
                    "GET": f"{resource}_read",
                    "PUT": f"{resource}_update",
                    "DELETE": f"{resource}_delete",
                }.get(method, "unknown")
                return action

        return "unknown"

    def _match_path_pattern(self, pattern: str, path: str) -> bool:
        """匹配路径模式（支持 /{id} 占位符）"""
        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")

        if len(pattern_parts) != len(path_parts):
            return False

        for p, a in zip(pattern_parts, path_parts):
            if p.startswith("{") and p.endswith("}"):
                continue  # 占位符匹配任意值
            if p != a:
                return False
        return True

    def _sanitize_body(self, body: str) -> str:
        """对请求体进行脱敏处理"""
        try:
            data = json.loads(body)
            sensitive_fields = [
                "password", "secret", "token", "api_key", "apikey",
                "access_key", "accesskey", "private_key", "credential",
                "authorization", "refresh_token", "session_id",
            ]
            self._mask_sensitive_fields(data, sensitive_fields)
            return json.dumps(data, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            # 非 JSON 内容，尝试简单脱敏
            return self._simple_mask(body)

    def _mask_sensitive_fields(self, obj, fields: list):
        """递归掩码敏感字段"""
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                if any(f in key.lower() for f in fields):
                    obj[key] = "***MASKED***"
                elif isinstance(obj[key], (dict, list)):
                    self._mask_sensitive_fields(obj[key], fields)
        elif isinstance(obj, list):
            for item in obj:
                self._mask_sensitive_fields(item, fields)

    def _simple_mask(self, text: str) -> str:
        """简单脱敏（针对非 JSON 内容）"""
        import re
        # 掩码常见的 key=value 形式
        patterns = [
            (r'(password|secret|token|api_key|apikey)\s*[:=]\s*["\']?([^"\'&\s]+)', r'\1=***MASKED***'),
        ]
        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    def _log_audit(
        self,
        method: str,
        path: str,
        operation: str,
        user_id: int,
        tenant_id: int,
        client_ip: str,
        status_code: int,
        duration_ms: int,
        request_body: str,
        is_sensitive: bool,
    ):
        """写入审计日志到数据库"""
        # 延迟导入避免循环依赖
        from app.models.audit_models import AuditLog

        db_gen = get_db()
        db = next(db_gen)

        try:
            audit = AuditLog(
                method=method,
                path=path,
                operation=operation,
                user_id=user_id,
                tenant_id=tenant_id,
                client_ip=client_ip,
                status_code=status_code,
                duration_ms=duration_ms,
                request_body=request_body,
                is_sensitive=is_sensitive,
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[AuditLog] DB write failed: {e}")
        finally:
            db.close()
