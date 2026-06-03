import json
import re
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.environment_asset import Environment, SecretVariable, VariableSet


VARIABLE_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_\-\.]+)\}\}")


def _mask_value(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * max(len(value) - 4, 2) + value[-2:]


class EnvironmentService:
    def __init__(self, db: Session):
        self.db = db

    def create_environment(self, data: dict) -> Dict:
        payload = dict(data)
        variable_sets = payload.pop("variable_sets", [])
        env = Environment(**payload)
        self.db.add(env)
        self.db.flush()
        for variable_set_data in variable_sets:
            variables = variable_set_data.pop("variables", [])
            variable_set = VariableSet(environment_id=env.id, **variable_set_data)
            self.db.add(variable_set)
            self.db.flush()
            for variable in variables:
                value = variable.get("value", "")
                self.db.add(
                    SecretVariable(
                        variable_set_id=variable_set.id,
                        key=variable["key"],
                        value=value,
                        is_secret=bool(variable.get("is_secret")),
                        masked_value=_mask_value(value) if variable.get("is_secret") else value,
                    )
                )
        self.db.commit()
        self.db.refresh(env)
        return self.serialize_environment(env)

    def list_environments(self, project_id: Optional[int] = None) -> list[Dict]:
        query = self.db.query(Environment)
        if project_id:
            query = query.filter(Environment.project_id == project_id)
        items = query.order_by(Environment.updated_at.desc()).all()
        return [self.serialize_environment(item) for item in items]

    def build_variable_map(self, environment_id: Optional[int]) -> Dict[str, str]:
        if not environment_id:
            return {}
        env = self.db.query(Environment).filter(Environment.id == environment_id).first()
        if not env:
            return {}
        resolved: Dict[str, str] = {}
        for variable_set in env.variable_sets:
            if not variable_set.enabled:
                continue
            for variable in variable_set.variables:
                resolved[variable.key] = variable.value or ""
        if env.base_url and "base_url" not in resolved:
            resolved["base_url"] = env.base_url
        return resolved

    def render_request(self, payload: dict) -> Dict:
        variables = self.build_variable_map(payload.get("environment_id"))
        rendered = {
            "method": payload.get("method", "GET"),
            "url": self._render_string(payload.get("url", ""), variables),
            "query_params": self._render_mapping(payload.get("query_params", {}), variables),
            "headers": self._render_mapping(payload.get("headers", {}), variables),
            "cookies": self._render_mapping(payload.get("cookies", {}), variables),
            "auth_config": self._render_mapping(payload.get("auth_config", {}), variables),
            "body_type": payload.get("body_type", "none"),
            "body": self._render_body(payload.get("body", ""), variables),
            "resolved_variables": variables,
        }
        return rendered

    def _render_body(self, body: str, variables: Dict[str, str]) -> str:
        if not body:
            return ""
        try:
            body_obj = json.loads(body)
        except json.JSONDecodeError:
            return self._render_string(body, variables)
        return json.dumps(self._render_mapping(body_obj, variables), ensure_ascii=False)

    def _render_mapping(self, value, variables: Dict[str, str]):
        if isinstance(value, dict):
            return {key: self._render_mapping(item, variables) for key, item in value.items()}
        if isinstance(value, list):
            return [self._render_mapping(item, variables) for item in value]
        if isinstance(value, str):
            return self._render_string(value, variables)
        return value

    def _render_string(self, value: str, variables: Dict[str, str]) -> str:
        def replace(match):
            key = match.group(1)
            return variables.get(key, match.group(0))

        return VARIABLE_PATTERN.sub(replace, value or "")

    def serialize_environment(self, env: Environment) -> Dict:
        return {
            "id": env.id,
            "project_id": env.project_id,
            "name": env.name,
            "code": env.code or "",
            "base_url": env.base_url,
            "description": env.description or "",
            "enabled": bool(env.enabled),
            "variable_sets": [
                {
                    "id": variable_set.id,
                    "name": variable_set.name,
                    "scope": variable_set.scope,
                    "sort_order": variable_set.sort_order,
                    "enabled": bool(variable_set.enabled),
                    "variables": [
                        {
                            "id": variable.id,
                            "key": variable.key,
                            "value": variable.masked_value if variable.is_secret else variable.value,
                            "is_secret": bool(variable.is_secret),
                        }
                        for variable in variable_set.variables
                    ],
                }
                for variable_set in env.variable_sets
            ],
        }
