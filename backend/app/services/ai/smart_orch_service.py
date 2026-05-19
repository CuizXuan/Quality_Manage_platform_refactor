# -*- coding: utf-8 -*-
"""
Phase 5 - 智能编排服务
"""
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.ai_models import SmartOrchRule


class SmartOrchService:
    """智能编排服务"""

    # 预定义条件模板
    CONDITION_TEMPLATES = {
        "failure_type_is": {
            "type": "failure_type",
            "values": ["locator_not_found", "assertion_error", "timeout"],
        },
        "response_status_is": {"type": "response_status", "values": [400, 401, 500]},
        "error_contains": {"type": "error_keyword", "keywords": []},
        "project_changed": {"type": "project_change", "enabled": True},
    }

    # 预定义动作模板
    ACTION_TEMPLATES = {
        "update_locator": {
            "type": "update_locator",
            "strategy": "relative_position",
            "description": "使用相对定位重新查找元素",
        },
        "update_assertion": {
            "type": "update_assertion",
            "auto_adjust": True,
            "description": "自动调整断言期望值",
        },
        "add_wait": {
            "type": "add_wait",
            "wait_seconds": 5,
            "description": "增加等待时间",
        },
        "retry_with_backoff": {
            "type": "retry_with_backoff",
            "max_retries": 3,
            "backoff_factor": 2,
            "description": "指数退避重试",
        },
        "notify_team": {
            "type": "notify",
            "channel": "dingtalk",
            "template": "failure_alert",
            "description": "通知团队",
        },
        "create_defect": {
            "type": "create_defect",
            "priority": "medium",
            "assignee": "auto",
            "description": "自动创建缺陷",
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def get_rules(
        self, project_id: int, page: int = 1, page_size: int = 20
    ) -> dict:
        """获取规则列表"""
        query = (
            self.db.query(SmartOrchRule)
            .filter(SmartOrchRule.project_id == project_id)
            .order_by(SmartOrchRule.priority.desc(), SmartOrchRule.created_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [self._rule_to_dict(rule) for rule in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def get_rule(self, rule_id: int) -> Optional[dict]:
        """获取单个规则"""
        rule = self.db.query(SmartOrchRule).filter(SmartOrchRule.id == rule_id).first()
        if not rule:
            return None
        return self._rule_to_dict(rule)

    def _rule_to_dict(self, rule: SmartOrchRule) -> dict:
        """规则转字典"""
        try:
            condition = json.loads(rule.condition) if rule.condition else {}
            action = json.loads(rule.action) if rule.action else {}
        except json.JSONDecodeError:
            condition = {}
            action = {}

        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "condition": condition,
            "action": action,
            "priority": rule.priority,
            "usage_count": rule.usage_count,
            "success_rate": rule.success_rate,
            "enabled": rule.enabled,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
        }

    def create_rule(
        self,
        name: str,
        condition: dict,
        action: dict,
        project_id: int,
        description: Optional[str] = None,
        priority: int = 0,
    ) -> dict:
        """创建规则"""
        # 验证条件
        if not self._validate_condition(condition):
            return {"success": False, "error": "Invalid condition format"}

        # 验证动作
        if not self._validate_action(action):
            return {"success": False, "error": "Invalid action format"}

        rule = SmartOrchRule(
            name=name,
            description=description,
            condition=json.dumps(condition, ensure_ascii=False),
            action=json.dumps(action, ensure_ascii=False),
            priority=priority,
            project_id=project_id,
            enabled=True,
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return {"success": True, "id": rule.id, "rule": self._rule_to_dict(rule)}

    def update_rule(
        self,
        rule_id: int,
        name: Optional[str] = None,
        condition: Optional[dict] = None,
        action: Optional[dict] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> dict:
        """更新规则"""
        rule = self.db.query(SmartOrchRule).filter(SmartOrchRule.id == rule_id).first()
        if not rule:
            return {"success": False, "error": "Rule not found"}

        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if priority is not None:
            rule.priority = priority
        if enabled is not None:
            rule.enabled = enabled
        if condition is not None:
            if not self._validate_condition(condition):
                return {"success": False, "error": "Invalid condition format"}
            rule.condition = json.dumps(condition, ensure_ascii=False)
        if action is not None:
            if not self._validate_action(action):
                return {"success": False, "error": "Invalid action format"}
            rule.action = json.dumps(action, ensure_ascii=False)

        self.db.commit()
        self.db.refresh(rule)

        return {"success": True, "rule": self._rule_to_dict(rule)}

    def delete_rule(self, rule_id: int) -> dict:
        """删除规则"""
        rule = self.db.query(SmartOrchRule).filter(SmartOrchRule.id == rule_id).first()
        if not rule:
            return {"success": False, "error": "Rule not found"}

        self.db.delete(rule)
        self.db.commit()

        return {"success": True}

    def toggle_rule(self, rule_id: int) -> dict:
        """启用/禁用规则"""
        rule = self.db.query(SmartOrchRule).filter(SmartOrchRule.id == rule_id).first()
        if not rule:
            return {"success": False, "error": "Rule not found"}

        rule.enabled = not rule.enabled
        self.db.commit()

        return {"success": True, "enabled": rule.enabled}

    def _validate_condition(self, condition: dict) -> bool:
        """验证条件格式"""
        if not condition:
            return False

        # 支持简单条件
        valid_types = [
            "failure_type",
            "failure_types",
            "response_status",
            "error_keyword",
            "project_change",
            "time_range",
        ]

        cond_type = condition.get("type", "")
        if cond_type and cond_type not in valid_types:
            return False

        return True

    def _validate_action(self, action: dict) -> bool:
        """验证动作格式"""
        if not action:
            return False

        # 支持的动作类型
        valid_types = [
            "update_locator",
            "update_assertion",
            "add_wait",
            "retry_with_backoff",
            "skip_step",
            "notify",
            "create_defect",
            "webhook",
        ]

        action_type = action.get("type", "")
        if action_type and action_type not in valid_types:
            return False

        return True

    def test_rule(
        self, rule_id: int, test_context: dict
    ) -> dict:
        """测试规则"""
        rule = self.db.query(SmartOrchRule).filter(SmartOrchRule.id == rule_id).first()
        if not rule:
            return {"success": False, "error": "Rule not found"}

        try:
            condition = json.loads(rule.condition)
            action = json.loads(rule.action)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid rule format"}

        # 检查条件是否匹配
        matched = self._evaluate_condition(condition, test_context)

        return {
            "success": True,
            "matched": matched,
            "condition": condition,
            "action": action,
            "test_context": test_context,
        }

    def _evaluate_condition(self, condition: dict, context: dict) -> bool:
        """评估条件是否匹配上下文"""
        cond_type = condition.get("type", "")

        if cond_type == "failure_type":
            return context.get("failure_type") in condition.get("values", [])

        if cond_type == "failure_types":
            return context.get("failure_type") in condition.get("failure_types", [])

        if cond_type == "response_status":
            return context.get("response_status") in condition.get("values", [])

        if cond_type == "error_keyword":
            error_msg = context.get("error_message", "").lower()
            keywords = condition.get("keywords", [])
            return any(kw.lower() in error_msg for kw in keywords)

        # 默认匹配
        return True

    def get_templates(self) -> dict:
        """获取规则模板"""
        return {
            "conditions": self.CONDITION_TEMPLATES,
            "actions": self.ACTION_TEMPLATES,
        }

    def optimize_rule(self, rule_id: int) -> dict:
        """优化规则（基于历史数据）"""
        rule = self.db.query(SmartOrchRule).filter(SmartOrchRule.id == rule_id).first()
        if not rule:
            return {"success": False, "error": "Rule not found"}

        # 基于成功率调整优先级
        if rule.success_rate is not None:
            if rule.success_rate < 0.5:
                rule.priority = max(0, rule.priority - 1)
                suggestion = "检测到成功率较低，建议降低优先级或调整条件"
            elif rule.success_rate > 0.8:
                rule.priority = rule.priority + 1
                suggestion = "检测到成功率高，可以考虑提高优先级"
            else:
                suggestion = "当前策略运行良好"

            self.db.commit()
            return {
                "success": True,
                "suggestion": suggestion,
                "new_priority": rule.priority,
                "success_rate": rule.success_rate,
            }

        return {"success": False, "suggestion": "暂无足够数据进行分析"}
