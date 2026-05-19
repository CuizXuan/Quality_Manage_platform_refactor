# -*- coding: utf-8 -*-
"""
Phase 5 - 数据脱敏服务
"""
import re
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.data_factory_models import DataMaskRule


class DataMaskService:
    """数据脱敏服务"""

    # 内置脱敏类型
    MASK_TYPES = {
        "phone": "手机号",
        "email": "邮箱",
        "id_card": "身份证",
        "bank_card": "银行卡",
        "password": "密码",
        "token": "Token",
        "custom": "自定义",
    }

    def __init__(self, db: Session):
        self.db = db

    def create_rule(
        self,
        name: str,
        field_pattern: str,
        mask_type: str,
        project_id: int,
        mask_config: Optional[dict] = None,
        priority: int = 0,
    ) -> dict:
        """创建脱敏规则"""
        if mask_type not in self.MASK_TYPES:
            return {"success": False, "error": f"Invalid mask type: {mask_type}"}

        rule = DataMaskRule(
            name=name,
            field_pattern=field_pattern,
            mask_type=mask_type,
            mask_config=json.dumps(mask_config, ensure_ascii=False) if mask_config else None,
            priority=priority,
            project_id=project_id,
            enabled=True,
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return {"success": True, "id": rule.id}

    def update_rule(
        self,
        rule_id: int,
        name: Optional[str] = None,
        field_pattern: Optional[str] = None,
        mask_type: Optional[str] = None,
        mask_config: Optional[dict] = None,
        priority: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> dict:
        """更新脱敏规则"""
        rule = self.db.query(DataMaskRule).filter(DataMaskRule.id == rule_id).first()
        if not rule:
            return {"success": False, "error": "Rule not found"}

        if name is not None:
            rule.name = name
        if field_pattern is not None:
            rule.field_pattern = field_pattern
        if mask_type is not None:
            if mask_type not in self.MASK_TYPES:
                return {"success": False, "error": f"Invalid mask type: {mask_type}"}
            rule.mask_type = mask_type
        if mask_config is not None:
            rule.mask_config = json.dumps(mask_config, ensure_ascii=False)
        if priority is not None:
            rule.priority = priority
        if enabled is not None:
            rule.enabled = enabled

        self.db.commit()
        return {"success": True}

    def delete_rule(self, rule_id: int) -> dict:
        """删除规则"""
        rule = self.db.query(DataMaskRule).filter(DataMaskRule.id == rule_id).first()
        if not rule:
            return {"success": False, "error": "Rule not found"}

        self.db.delete(rule)
        self.db.commit()
        return {"success": True}

    def list_rules(self, project_id: int) -> List[dict]:
        """获取规则列表"""
        rules = (
            self.db.query(DataMaskRule)
            .filter(DataMaskRule.project_id == project_id)
            .order_by(DataMaskRule.priority.desc())
            .all()
        )

        return [self._rule_to_dict(r) for r in rules]

    def get_rule(self, rule_id: int) -> Optional[dict]:
        """获取规则详情"""
        rule = self.db.query(DataMaskRule).filter(DataMaskRule.id == rule_id).first()
        if not rule:
            return None
        return self._rule_to_dict(rule)

    def _rule_to_dict(self, rule: DataMaskRule) -> dict:
        """转换规则为字典"""
        return {
            "id": rule.id,
            "name": rule.name,
            "field_pattern": rule.field_pattern,
            "mask_type": rule.mask_type,
            "mask_type_name": self.MASK_TYPES.get(rule.mask_type, rule.mask_type),
            "mask_config": json.loads(rule.mask_config) if rule.mask_config else None,
            "enabled": rule.enabled,
            "priority": rule.priority,
            "project_id": rule.project_id,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
        }

    def apply_mask(self, data: Any, rules: List[dict]) -> Any:
        """
        应用脱敏规则到数据

        Args:
            data: 输入数据 (dict, list, or str)
            rules: 脱敏规则列表

        Returns:
            脱敏后的数据
        """
        if isinstance(data, dict):
            return self._mask_dict(data, rules)
        elif isinstance(data, list):
            return [self.apply_mask(item, rules) for item in data]
        elif isinstance(data, str):
            # 尝试解析 JSON
            try:
                parsed = json.loads(data)
                masked = self.apply_mask(parsed, rules)
                return json.dumps(masked, ensure_ascii=False)
            except json.JSONDecodeError:
                return data
        return data

    def _mask_dict(self, data: dict, rules: List[dict]) -> dict:
        """对字典应用脱敏"""
        result = data.copy()

        for rule in rules:
            if not rule.get("enabled", True):
                continue

            field_pattern = rule.get("field_pattern", "")
            mask_type = rule.get("mask_type", "")
            mask_config = rule.get("mask_config", {})

            # 匹配字段
            matched_fields = self._match_fields(result, field_pattern)
            for field in matched_fields:
                result[field] = self._mask_value(result[field], mask_type, mask_config)

        return result

    def _match_fields(self, data: dict, pattern: str) -> List[str]:
        """根据模式匹配字段"""
        matched = []

        # 支持 JSONPath 简化版 (e.g., $.phone, $..name)
        if pattern.startswith("$.."):
            # 递归匹配
            key = pattern[3:]
            for k, v in data.items():
                if key.lower() in k.lower():
                    matched.append(k)
        elif pattern.startswith("$."):
            # 直接匹配
            key = pattern[2:]
            if key in data:
                matched.append(key)
        else:
            # 正则匹配
            try:
                regex = re.compile(pattern)
                for key in data.keys():
                    if regex.match(key):
                        matched.append(key)
            except re.error:
                # 无效正则，当作字段名匹配
                if pattern in data:
                    matched.append(pattern)

        return matched

    def _mask_value(self, value: Any, mask_type: str, config: dict) -> str:
        """根据类型脱敏"""
        if value is None:
            return None

        value_str = str(value)

        if mask_type == "phone":
            return self._mask_phone(value_str)
        elif mask_type == "email":
            return self._mask_email(value_str)
        elif mask_type == "id_card":
            return self._mask_id_card(value_str)
        elif mask_type == "bank_card":
            return self._mask_bank_card(value_str)
        elif mask_type == "password":
            return "******"
        elif mask_type == "token":
            return self._mask_token(value_str)
        elif mask_type == "custom":
            return self._mask_custom(value_str, config)
        else:
            return value_str

    def _mask_phone(self, value: str) -> str:
        """手机号脱敏: 138****1234"""
        if len(value) >= 11:
            return value[:3] + "****" + value[-4:]
        return value[:3] + "****" if len(value) > 3 else "****"

    def _mask_email(self, value: str) -> str:
        """邮箱脱敏: t***@example.com"""
        if "@" in value:
            parts = value.split("@")
            if len(parts[0]) > 1:
                return parts[0][0] + "***@" + parts[1]
            return "***@" + parts[1]
        return value[:1] + "***" if len(value) > 1 else "***"

    def _mask_id_card(self, value: str) -> str:
        """身份证脱敏: 110***********1234"""
        if len(value) >= 8:
            return value[:3] + "***********" + value[-4:]
        return value[:3] + "***********" if len(value) > 3 else "************"

    def _mask_bank_card(self, value: str) -> str:
        """银行卡脱敏: 6222********1234"""
        if len(value) >= 8:
            return value[:4] + "********" + value[-4:]
        return value[:4] + "********" if len(value) > 4 else "********"

    def _mask_token(self, value: str) -> str:
        """Token 脱敏: eyJ***..."""
        if len(value) > 10:
            return value[:5] + "***" + value[-5:]
        return "***"

    def _mask_custom(self, value: str, config: dict) -> str:
        """自定义正则脱敏"""
        pattern = config.get("pattern", "")
        replacement = config.get("replacement", "***")

        if pattern:
            try:
                return re.sub(pattern, replacement, value)
            except re.error:
                return value
        return replacement

    def preview_mask(self, data: dict, rule_id: int) -> dict:
        """预览单条规则的脱敏结果"""
        rule = self.get_rule(rule_id)
        if not rule:
            return {"success": False, "error": "Rule not found"}

        original = {}
        matched_fields = self._match_fields(data, rule["field_pattern"])
        for field in matched_fields:
            original[field] = data.get(field)

        masked_data = self.apply_mask(data, [rule])

        result = {}
        for field in matched_fields:
            result[field] = {
                "original": original[field],
                "masked": masked_data.get(field),
            }

        return {
            "success": True,
            "rule": rule,
            "preview": result,
        }
