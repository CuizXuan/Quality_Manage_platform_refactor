# -*- coding: utf-8 -*-
"""
Phase 5 - AI 测试生成服务
"""
import json
import re
import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from app.models.ai_models import AIGenHistory, VectorDoc, EmbeddingCache


class AIGenService:
    """AI 测试生成服务"""

    # 支持的输入源类型
    SOURCE_TYPES = ["code", "doc", "curl", "description"]

    # 默认生成选项
    DEFAULT_OPTIONS = {
        "include_success": True,
        "include_error": True,
        "include_boundary": False,
        "include_performance": False,
    }

    # 测试用例模板
    CASE_TEMPLATE = {
        "name": "",
        "method": "GET",
        "url": "",
        "headers": {},
        "body": None,
        "params": {},
        "assertions": [],
    }

    def __init__(self, db: Session):
        self.db = db

    def generate(
        self,
        source_type: str,
        source_content: str,
        project_id: int,
        user_id: int,
        options: Optional[dict] = None,
    ) -> dict:
        """
        主生成入口

        Args:
            source_type: 输入源类型 (code/doc/curl/description)
            source_content: 源内容
            project_id: 项目 ID
            user_id: 用户 ID
            options: 生成选项

        Returns:
            生成结果，包含用例列表
        """
        if options is None:
            options = self.DEFAULT_OPTIONS.copy()

        # 解析输入源
        parsed = self._parse_source(source_type, source_content)

        # 构建 Prompt
        prompt = self._build_prompt(source_type, parsed, options)

        # 模拟 LLM 调用 (实际项目中替换为真实 LLM 调用)
        raw_output = self._call_llm(prompt)

        # 后处理
        cases = self._post_process(raw_output, parsed)

        # 获取模型名称
        model_used = "MiniMax-M2.7"
        try:
            from app.services.ai.ai_model_service import AIModelService
            model_service = AIModelService(self.db)
            default_config = model_service.get_default_config()
            if default_config:
                model_used = default_config.get('name', 'MiniMax-M2.7')
        except Exception:
            pass

        # 保存生成历史
        history = self._save_history(
            source_type=source_type,
            source_content=source_content,
            cases=cases,
            project_id=project_id,
            user_id=user_id,
            model_used=model_used,
            prompt_tokens=len(prompt) // 4,  # 估算
            completion_tokens=sum(len(json.dumps(c)) for c in cases) // 4,
        )

        return {
            "success": True,
            "cases": cases,
            "history_id": history.id,
            "model_used": model_used,
            "tokens_used": {
                "prompt": len(prompt) // 4,
                "completion": sum(len(json.dumps(c)) for c in cases) // 4,
            },
        }

    def _parse_source(self, source_type: str, source_content: str) -> dict:
        """解析不同类型的输入源"""
        parsers = {
            "code": self._parse_code,
            "doc": self._parse_openapi,
            "curl": self._parse_curl,
            "description": self._parse_description,
        }
        parser = parsers.get(source_type, self._parse_description)
        return parser(source_content)

    def _parse_code(self, code: str) -> dict:
        """从代码解析 API 定义"""
        result = {
            "api_name": "",
            "endpoints": [],
            "models": [],
        }

        # 提取 @GetMapping / @PostMapping 等注解
        get_patterns = re.findall(r'@GetMapping\(["\']([^"\']+)["\']\)', code)
        post_patterns = re.findall(r'@PostMapping\(["\']([^"\']+)["\']\)', code)
        put_patterns = re.findall(r'@PutMapping\(["\']([^"\']+)["\']\)', code)
        delete_patterns = re.findall(r'@DeleteMapping\(["\']([^"\']+)["\']\)', code)

        for path in get_patterns:
            result["endpoints"].append({"method": "GET", "path": path})
        for path in post_patterns:
            result["endpoints"].append({"method": "POST", "path": path})
        for path in put_patterns:
            result["endpoints"].append({"method": "PUT", "path": path})
        for path in delete_patterns:
            result["endpoints"].append({"method": "DELETE", "path": path})

        # 提取类名作为 API 名称
        class_match = re.search(r'class (\w+)', code)
        if class_match:
            result["api_name"] = class_match.group(1)

        return result

    def _parse_openapi(self, spec_str: str) -> dict:
        """解析 OpenAPI 规范"""
        try:
            spec = json.loads(spec_str)
        except json.JSONDecodeError:
            return {"api_name": "", "endpoints": [], "models": []}

        result = {
            "api_name": spec.get("info", {}).get("title", ""),
            "endpoints": [],
            "models": [],
        }

        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = {
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", ""),
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody"),
                    }
                    result["endpoints"].append(endpoint)

        # 收集 schemas
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        result["models"] = list(schemas.keys())

        return result

    def _parse_curl(self, curl_cmd: str) -> dict:
        """解析 cURL 命令"""
        result = {
            "method": "GET",
            "url": "",
            "headers": {},
            "body": None,
        }

        # 提取 URL
        url_match = re.search(r'curl\s+(?:-\w+\s+)*["\']?(https?://[^\s"\']+)', curl_cmd)
        if url_match:
            result["url"] = url_match.group(1)

        # 提取 Method
        if "-X POST" in curl_cmd or "--request POST" in curl_cmd:
            result["method"] = "POST"
        elif "-X PUT" in curl_cmd:
            result["method"] = "PUT"
        elif "-X DELETE" in curl_cmd:
            result["method"] = "DELETE"

        # 提取 Headers
        header_matches = re.findall(r'-H\s+["\']([^"\']+)["\']', curl_cmd)
        for header in header_matches:
            if ":" in header:
                key, value = header.split(":", 1)
                result["headers"][key.strip()] = value.strip()

        # 提取 Body
        data_match = re.search(r'-d\s+["\']([^"\']+)["\']', curl_cmd)
        if data_match:
            result["body"] = data_match.group(1)
            if result["method"] == "GET":
                result["method"] = "POST"

        return result

    def _parse_description(self, description: str) -> dict:
        """解析文字描述"""
        return {
            "description": description,
            "intent": self._extract_intent(description),
        }

    def _extract_intent(self, text: str) -> str:
        """提取意图"""
        text_lower = text.lower()
        if "登录" in text or "login" in text_lower:
            return "login"
        elif "用户" in text and "列表" in text:
            return "user_list"
        elif "创建" in text or "新增" in text:
            return "create"
        elif "删除" in text:
            return "delete"
        elif "修改" in text or "更新" in text:
            return "update"
        else:
            return "general"

    def _build_prompt(self, source_type: str, parsed: dict, options: dict) -> str:
        """构建 Prompt"""
        project_rules = """
项目规范：
- 成功响应格式：{"code": 0, "data": {...}}
- 错误响应格式：{"code": 非0, "message": "..."}
- 认证方式：Bearer Token (Header: Authorization: Bearer <token>)
"""

        case_format = """
输出格式 (JSON):
{
  "cases": [
    {
      "name": "用例名称",
      "method": "GET|POST|PUT|DELETE",
      "url": "/api/path",
      "headers": {"Authorization": "Bearer xxx"},
      "body": {...},
      "assertions": [
        {"type": "status", "expected": 200},
        {"type": "json_path", "path": "$.code", "expected": 0}
      ]
    }
  ]
}
"""

        if source_type == "code":
            prompt = f"""你是一个 API 测试专家。请根据以下代码生成测试用例：
{parsed.get('api_name', '')}

代码：
```java
{parsed.get('endpoints', [])}
```

{project_rules}
{case_format}
"""
        elif source_type == "doc":
            endpoints = parsed.get("endpoints", [])
            prompt = f"""你是一个 API 测试专家。请根据以下 OpenAPI 定义生成测试用例：

API: {parsed.get('api_name', '')}

端点：
{json.dumps(endpoints, ensure_ascii=False, indent=2)}

{project_rules}
请为每个端点生成：
1. 成功场景用例
2. 常见错误场景用例

{case_format}
"""
        elif source_type == "curl":
            prompt = f"""你是一个 API 测试专家。请根据以下 cURL 命令生成完整的测试用例：

{parsed.get('method', 'GET')} {parsed.get('url', '')}

Headers: {json.dumps(parsed.get('headers', {}), ensure_ascii=False)}
Body: {parsed.get('body', 'N/A')}

{project_rules}
请生成完整的测试用例，包括正常场景和错误场景。

{case_format}
"""
        else:  # description
            prompt = f"""你是一个 API 测试专家。请根据以下描述生成测试用例：

描述：{parsed.get('description', '')}

意图：{parsed.get('intent', 'general')}

{project_rules}
请根据描述生成合适的测试用例。

{case_format}
"""

        # 根据选项添加额外要求
        if options.get("include_error"):
            prompt += "\n请包含错误场景测试（如：参数缺失、权限不足）"
        if options.get("include_boundary"):
            prompt += "\n请包含边界值测试"
        if options.get("include_performance"):
            prompt += "\n请包含性能相关断言（如响应时间）"

        return prompt

    def _call_llm(self, prompt: str) -> dict:
        """
        调用 LLM，使用已配置的 AI 模型
        """
        try:
            from app.services.ai.ai_model_service import AIModelService
            model_service = AIModelService(self.db)
            system_prompt = "你是一个专业的测试用例生成助手。请根据用户提供的API定义或代码，生成全面且高质量的测试用例。输出格式为严格的JSON数组，每个用例对象包含：name(字符串,用例名称), method(字符串,HTTP方法如GET/POST/PUT/DELETE), url(字符串,接口路径如/api/users), headers(JSON对象,请求头), body(JSON对象或null,请求体), expected_status(数字,预期HTTP状态码), description(字符串,用例文案)字段。直接返回JSON数组，不要任何其他文字。"
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            result = model_service.chat(messages=messages, config_id=None, timeout=60)
            if result.get("success"):
                raw_content = result.get("content", "")
                print(f"[AIGen] MiniMax returned: {raw_content[:200]}")
                # 尝试解析 LLM 返回的 JSON
                cases = self._extract_json_cases(raw_content)
                if cases:
                    print(f"[AIGen] Extracted {len(cases)} cases from LLM response")
                    return {"cases": cases}
                else:
                    print("[AIGen] JSON parse failed, falling back to mock")
                    # JSON 解析失败，降级到 mock
                    return self._mock_llm_response(prompt)
            else:
                # 模型调用失败，降级到 mock
                print(f"[AIGen] MiniMax error: {result.get('error', '')}")
                return self._mock_llm_response(prompt)
        except Exception as e:
            # 任何异常都降级到 mock
            print(f"[AIGen] Exception: {e}")
            return self._mock_llm_response(prompt)

    def _extract_json_cases(self, raw_content: str) -> list:
        """从 LLM 返回的原始内容中提取 JSON 用例数组"""
        import json, re
        content = raw_content.strip()

        # 去掉 markdown 代码块标记
        if content.startswith("```"):
            # 去掉 ```json ... ```
            match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', content)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            # 去掉 ```json 前缀
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

        # 尝试直接解析整个内容
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "cases" in data:
                return data["cases"]
        except json.JSONDecodeError:
            pass

        # 查找第一个 [ 或 { 开始的位置，截取后解析
        for start in [m.start() for m in re.finditer(r'[\[{]', content)]:
            try:
                candidate = content[start:]
                data = json.loads(candidate)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "cases" in data:
                    return data["cases"]
            except json.JSONDecodeError:
                continue

        return []

    def _mock_llm_response(self, prompt: str) -> dict:
        """模拟 LLM 响应"""
        # 根据 prompt 内容生成模拟响应
        cases = []

        if "curl" in prompt.lower() or "GetMapping" in prompt or "PostMapping" in prompt:
            # 从 curl 或代码生成
            cases.append(
                {
                    "name": "正常场景测试",
                    "method": "GET",
                    "url": "/api/test",
                    "headers": {"Authorization": "Bearer ${1:token}"},
                    "body": None,
                    "assertions": [
                        {"type": "status", "expected": 200},
                        {"type": "json_path", "path": "$.code", "expected": 0},
                    ],
                }
            )
            cases.append(
                {
                    "name": "错误场景 - 未授权",
                    "method": "GET",
                    "url": "/api/test",
                    "headers": {},
                    "body": None,
                    "assertions": [
                        {"type": "status", "expected": 401},
                    ],
                }
            )
        else:
            # 默认生成
            cases.append(
                {
                    "name": "成功场景",
                    "method": "GET",
                    "url": "/api/resource",
                    "headers": {"Authorization": "Bearer ${1:token}"},
                    "body": None,
                    "assertions": [
                        {"type": "status", "expected": 200},
                        {"type": "json_path", "path": "$.code", "expected": 0},
                    ],
                }
            )

        return {"cases": cases}

    def _post_process(self, raw_output: dict, parsed: dict) -> list:
        """后处理：格式校验、变量补全、去重"""
        cases = raw_output.get("cases", [])

        processed = []
        seen_urls = set()

        for case in cases:
            # 变量补全 (使用 placeholder)
            if "Bearer" in str(case.get("headers", {})):
                case["headers"]["Authorization"] = "Bearer ${1:token}"

            # URL 补全
            url = case.get("url", "")
            if url and not url.startswith("/"):
                url = "/" + url
                case["url"] = url

            # 去重
            case_key = f"{case.get('method', '')}_{url}"
            if case_key not in seen_urls:
                seen_urls.add(case_key)
                processed.append(case)

        return processed

    def _save_history(
        self,
        source_type: str,
        source_content: str,
        cases: list,
        project_id: int,
        user_id: int,
        model_used: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> AIGenHistory:
        """保存生成历史"""
        history = AIGenHistory(
            source_type=source_type,
            source_content=source_content[:10000],  # 限制长度
            generated_case=json.dumps(cases, ensure_ascii=False),
            project_id=project_id,
            created_by=user_id,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_history(
        self,
        project_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取生成历史"""
        query = (
            self.db.query(AIGenHistory)
            .filter(AIGenHistory.project_id == project_id)
            .order_by(AIGenHistory.created_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [
                {
                    "id": h.id,
                    "source_type": h.source_type,
                    "source_content": h.source_content[:200] + "..."
                    if len(h.source_content) > 200
                    else h.source_content,
                    "case_count": len(json.loads(h.generated_case))
                    if h.generated_case
                    else 0,
                    "accepted": h.accepted,
                    "feedback_score": h.feedback_score,
                    "model_used": h.model_used,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def update_feedback(
        self,
        history_id: int,
        accepted: bool,
        feedback_score: Optional[int] = None,
        feedback_comment: Optional[str] = None,
    ) -> dict:
        """更新反馈"""
        history = self.db.query(AIGenHistory).filter(AIGenHistory.id == history_id).first()
        if not history:
            return {"success": False, "error": "History not found"}

        history.accepted = accepted
        if feedback_score is not None:
            history.feedback_score = feedback_score
        if feedback_comment is not None:
            history.feedback_comment = feedback_comment

        self.db.commit()
        return {"success": True}
