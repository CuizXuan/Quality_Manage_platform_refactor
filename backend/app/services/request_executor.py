"""
Request Executor - 统一 HTTP 请求执行器
"""
import json
import time
import logging
import httpx
from typing import Optional
from app.services.variable_engine import VariableEngine
from app.services.assertion_engine import AssertionEngine
from app.services.extract_engine import ExtractEngine

logger = logging.getLogger(__name__)


class RequestExecutor:
    """请求执行器，协调变量替换、请求发送、断言、提取"""

    def __init__(self):
        self.var_engine = VariableEngine()
        self.assert_engine = AssertionEngine()
        self.extract_engine = ExtractEngine()

    async def _prepare_variables(self, case_data: dict, env_vars: dict,
                                 temp_vars: dict) -> tuple[str, str, dict, dict, str]:
        """准备变量替换后的请求数据"""
        self.var_engine.build_from_sources(
            global_vars={},
            env_vars=env_vars or {},
            scenario_vars={},
            step_vars={},
            temp_vars=temp_vars or {},
        )
        method = self.var_engine.replace(case_data.get("method", "GET"))
        url = self.var_engine.replace(case_data.get("url", ""))
        headers = self.var_engine.replace_dict(case_data.get("headers", {}))
        params = self.var_engine.replace_dict(case_data.get("params", {}))
        body = self.var_engine.replace(case_data.get("body", ""))
        return method, url, headers, params, body

    def _run_assertions(self, assertions: list, response: dict) -> list:
        """执行断言"""
        return self.assert_engine.execute(assertions, response)

    async def execute_case(self, case_data: dict, env_vars: dict = None,
                           temp_vars: dict = None) -> dict:
        """执行单个用例"""
        start = time.time()
        case_id = case_data.get("id")
        logger.info(f"[execute_case] start case_id={case_id}, url={case_data.get('url')}")

        try:
            method, url, headers, params, body = self._prepare_variables(
                case_data, env_vars, temp_vars
            )
            headers = self._apply_auth(
                headers, case_data.get("auth_type", "none"),
                case_data.get("auth_config", {})
            )
            response = await self._send_request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                body=body,
                body_type=case_data.get("body_type", "json"),
                timeout=case_data.get("timeout", 30),
                follow_redirects=case_data.get("follow_redirects", True),
                verify_ssl=case_data.get("verify_ssl", True),
            )

            assertion_results = self._run_assertions(
                case_data.get("assertions", []), response
            )

            extracted = {}
            post_script = case_data.get("post_script", "")
            if post_script:
                extracted = self._run_script(post_script, response)

            status = "success" if all(r.get("passed", False) for r in assertion_results) else "failure"
            logger.info(f"[execute_case] done case_id={case_id} status={status} in {time.time()-start:.2f}s")
            return {
                "execution_id": f"exec_{int(time.time()*1000)}",
                "case_id": case_id,
                "status": status,
                "response": response,
                "assertion_results": assertion_results,
                "extracted_variables": extracted,
            }
        except Exception as e:
            logger.error(f"[execute_case] failed case_id={case_id}: {type(e).__name__}: {e}")
            raise

    async def _send_request(self, method: str, url: str, headers: dict,
                            params: dict, body: str, body_type: str,
                            timeout: int, follow_redirects: bool,
                            verify_ssl: bool) -> dict:
        # 如果 URL 是相对路径，拒绝执行避免死循环
        if not url.startswith(("http://", "https://")):
            return {
                "status_code": 0,
                "headers": {},
                "body": "",
                "size": 0,
                "time_ms": 0,
                "error": f"URL 必须是完整地址，当前值「{url}」是相对路径",
            }
        """发送 HTTP 请求并返回标准化响应"""
        start_time = time.time()
        status_code = 0
        response_headers = {}
        response_body = ""
        error_message = ""

        try:
            req_headers = {}
            for k, v in headers.items():
                if v:  # 过滤空值
                    req_headers[str(k)] = str(v)

            req_params = {}
            for k, v in params.items():
                if v:  # 过滤空值
                    req_params[str(k)] = str(v)

            request_kwargs = {
                "method": method.upper(),
                "url": url,
                "headers": req_headers,
                "timeout": timeout,
                "follow_redirects": follow_redirects,
            }

            if method.upper() in ("POST", "PUT", "PATCH"):
                content_type = req_headers.get("Content-Type", req_headers.get("content-type", ""))
                if body_type == "json" and "application/json" in content_type:
                    try:
                        request_kwargs["json"] = json.loads(body)
                    except json.JSONDecodeError:
                        request_kwargs["content"] = body
                elif body_type == "form":
                    form_data = {}
                    try:
                        fd = json.loads(body)
                        for k, v in fd.items():
                            form_data[k] = str(v)
                    except json.JSONDecodeError:
                        form_data = {"data": body}
                    request_kwargs["data"] = form_data
                else:
                    request_kwargs["content"] = body

            if req_params:
                request_kwargs["params"] = req_params

            async with httpx.AsyncClient(verify=verify_ssl) as client:
                resp = await client.request(**request_kwargs)
                status_code = resp.status_code
                response_headers = dict(resp.headers)
                try:
                    response_body = resp.json()
                except Exception:
                    response_body = resp.text

        except httpx.TimeoutException:
            status_code = 0
            error_message = f"请求超时 ({timeout}s)"
        except httpx.ConnectError as e:
            status_code = 0
            error_message = f"连接失败: {str(e)}"
        except Exception as e:
            status_code = 0
            error_message = f"请求异常: {str(e)}"

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "status_code": status_code,
            "headers": response_headers,
            "body": response_body,
            "size": len(json.dumps(response_body)) if response_body else 0,
            "time_ms": elapsed_ms,
            "error": error_message,
        }

    def _apply_auth(self, headers: dict, auth_type: str, auth_config: dict) -> dict:
        """应用认证配置到请求头"""
        if auth_type == "bearer":
            token = auth_config.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "basic":
            import base64
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            if username:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        elif auth_type == "api_key":
            key_name = auth_config.get("key_name", "X-API-Key")
            key_value = auth_config.get("key_value", "")
            add_to = auth_config.get("add_to", "header")
            if key_value:
                if add_to == "header":
                    headers[key_name] = key_value
                # params 的情况在 _send_request 里通过 params 处理
        return headers

    def _run_script(self, script: str, response: dict) -> dict:
        """执行后置脚本（沙箱版本，返回空字典）"""
        # Phase 1 暂时不实现完整沙箱脚本，先留空
        # 后续可用 RestrictedPython 实现
        return {}
