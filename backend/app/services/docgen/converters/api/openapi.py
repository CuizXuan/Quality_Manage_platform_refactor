"""
API文档转换器 — 从 OpenAPI/Swagger 解析接口定义
从 doc-generator 迁入
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from app.services.docgen.datamodel import LeafData, FlowRow


@dataclass
class ApiEndpoint:
    """接口端点"""
    method: str
    path: str
    summary: str
    tag: str
    parameters: List[dict] = field(default_factory=list)
    request_body: Optional[dict] = None
    responses: dict = field(default_factory=dict)


class OpenApiParser:
    """OpenAPI 解析器"""

    def __init__(self, spec: dict):
        self.spec = spec
        self._endpoints: List[ApiEndpoint] = []

    @classmethod
    def from_file(cls, filepath: str) -> "OpenApiParser":
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)

    @classmethod
    def from_url(cls, url: str) -> "OpenApiParser":
        import httpx
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        return cls(resp.json())

    @classmethod
    def from_dict(cls, spec: dict) -> "OpenApiParser":
        return cls(spec)

    def parse(self) -> list[ApiEndpoint]:
        endpoints = []
        paths = self.spec.get("paths", {})

        for path, methods in paths.items():
            for method, detail in methods.items():
                if method in ("parameters",):
                    continue
                tag = (detail.get("tags") or ["其他"])[0]
                endpoints.append(ApiEndpoint(
                    method=method.upper(),
                    path=path,
                    summary=detail.get("summary", detail.get("description", "")),
                    tag=tag,
                    parameters=self._parse_parameters(detail),
                    request_body=self._parse_request_body(detail),
                    responses=self._parse_responses(detail),
                ))

        self._endpoints = endpoints
        return endpoints

    def get_tags(self) -> List[str]:
        tags = set()
        for ep in self._endpoints:
            tags.add(ep.tag)
        return sorted(tags)

    def get_endpoints_by_tag(self, tag: str) -> List[ApiEndpoint]:
        return [ep for ep in self._endpoints if ep.tag == tag]

    def to_leaf_data(self, tag: str) -> LeafData:
        endpoints = self.get_endpoints_by_tag(tag)
        if not endpoints:
            return LeafData(desc=f"{tag} 暂无接口", flow=[])

        desc_lines = [f"模块: {tag}", f"接口数: {len(endpoints)}"]
        flow = []

        for ep in endpoints:
            flow.append(FlowRow(
                action=f"{ep.method} {ep.path}",
                response=ep.summary,
            ))
            if ep.parameters:
                flow.append(FlowRow(
                    action=f"  请求参数 ({len(ep.parameters)}个)",
                    response="",
                ))
                for param in ep.parameters:
                    name = param.get("name", "")
                    required = "必填" if param.get("required") else "可选"
                    schema = param.get("schema", {})
                    ptype = schema.get("type", "string")
                    pdesc = param.get("description", "")
                    flow.append(FlowRow(
                        action=f"    {name} ({ptype})",
                        response=f"{required}  {pdesc}",
                    ))
            if ep.responses:
                status_codes = list(ep.responses.keys())
                flow.append(FlowRow(
                    action=f"  响应: {', '.join(status_codes)}",
                    response="",
                ))

        return LeafData(desc="\n".join(desc_lines), flow=flow)

    def to_leaf_datas(self, tags: Optional[List[str]] = None) -> Dict[str, LeafData]:
        if tags is None:
            tags = self.get_tags()
        return {tag: self.to_leaf_data(tag) for tag in tags}

    def _parse_parameters(self, detail: dict) -> List[dict]:
        params = []
        for p in detail.get("parameters", []):
            schema = p.get("schema", {})
            params.append({
                "name": p.get("name", ""),
                "in": p.get("in", ""),
                "required": p.get("required", False),
                "type": schema.get("type", "string"),
                "description": p.get("description", ""),
            })
        return params

    def _parse_request_body(self, detail: dict) -> Optional[dict]:
        rb = detail.get("requestBody")
        if rb:
            content = rb.get("content", {})
            for media_type, media in content.items():
                schema = media.get("schema", {})
                return {
                    "required": rb.get("required", False),
                    "media_type": media_type,
                    "schema": schema,
                }
        return None

    def _parse_responses(self, detail: dict) -> dict:
        responses = {}
        for code, resp in detail.get("responses", {}).items():
            responses[code] = {"description": resp.get("description", "")}
        return responses

    def to_markdown(self, tags: Optional[List[str]] = None) -> str:
        if not self._endpoints:
            self.parse()

        if tags is None:
            tags = self.get_tags()

        lines = []
        lines.append("# API 接口文档")
        lines.append("")
        lines.append(f"> 共 {len(self._endpoints)} 个接口，{len(tags)} 个模块")
        lines.append("")

        for tag in tags:
            endpoints = self.get_endpoints_by_tag(tag)
            if not endpoints:
                continue

            lines.append(f"## {tag}")
            lines.append("")
            lines.append(f"共 {len(endpoints)} 个接口")
            lines.append("")

            for ep in endpoints:
                method_tag = f"`{ep.method}`"
                lines.append(f"### {method_tag} {ep.path}")
                lines.append("")
                if ep.summary:
                    lines.append(f"{ep.summary}")
                    lines.append("")

                if ep.parameters:
                    lines.append("**请求参数**")
                    lines.append("")
                    lines.append("| 参数名 | 位置 | 类型 | 必填 | 说明 |")
                    lines.append("|--------|------|------|------|------|")
                    for p in ep.parameters:
                        required = "是" if p.get("required") else "否"
                        lines.append(f"| {p['name']} | {p.get('in', '')} | {p.get('type', '')} | {required} | {p.get('description', '')} |")
                    lines.append("")

                if ep.request_body:
                    lines.append("**请求体**")
                    lines.append("")
                    schema = ep.request_body.get("schema", {})
                    if "properties" in schema:
                        lines.append("| 字段 | 类型 | 说明 |")
                        lines.append("|------|------|------|")
                        for prop_name, prop in schema["properties"].items():
                            lines.append(f"| {prop_name} | {prop.get('type', '')} | {prop.get('description', '')} |")
                        lines.append("")
                    else:
                        lines.append(f"```json\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n```")
                        lines.append("")

                if ep.responses:
                    lines.append("**响应**")
                    lines.append("")
                    for code, resp in ep.responses.items():
                        desc = resp.get("description", "")
                        lines.append(f"- `{code}`: {desc}")
                    lines.append("")

        return "\n".join(lines)