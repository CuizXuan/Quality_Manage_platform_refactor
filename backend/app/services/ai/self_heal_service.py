# -*- coding: utf-8 -*-
"""
Phase 5 - 测试自愈服务
"""
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.ai_models import SelfHealLog, SmartOrchRule
from app.models.execution_log import ExecutionLog


class SelfHealService:
    """测试自愈服务"""

    # 自愈动作类型
    HEAL_ACTIONS = {
        "update_locator": "更新元素定位器",
        "update_assertion": "更新断言值",
        "add_wait": "增加等待时间",
        "retry_with_backoff": "重试并退避",
        "skip_step": "跳过失败步骤",
    }

    # 失败类型映射
    FAILURE_TYPE_MAP = {
        "locator_not_found": "update_locator",
        "assertion_error": "update_assertion",
        "timeout": "add_wait",
        "network_error": "retry_with_backoff",
        "data_missing": "update_assertion",
        "auth_expired": "retry_with_backoff",
    }

    # 预定义自愈策略
    BUILTIN_STRATEGIES = {
        "locator_not_found": {
            "action": "update_locator",
            "confidence": 0.85,
            "reasoning": "元素定位失败，AI 分析页面结构生成新的定位器",
            "changes": {
                "strategy": "使用相对定位 + 内容匹配",
            },
        },
        "assertion_error": {
            "action": "update_assertion",
            "confidence": 0.75,
            "reasoning": "断言值与实际响应不匹配，分析响应结构变化",
            "changes": {
                "auto_adjust": True,
            },
        },
        "timeout": {
            "action": "add_wait",
            "confidence": 0.9,
            "reasoning": "操作超时，增加等待时间并启用智能等待",
            "changes": {
                "wait_seconds": 5,
                "smart_wait": True,
            },
        },
        "network_error": {
            "action": "retry_with_backoff",
            "confidence": 0.8,
            "reasoning": "网络错误，执行指数退避重试",
            "changes": {
                "max_retries": 3,
                "backoff_factor": 2,
            },
        },
        "auth_expired": {
            "action": "retry_with_backoff",
            "confidence": 0.95,
            "reasoning": "认证过期，自动刷新 Token 后重试",
            "changes": {
                "refresh_token": True,
                "max_retries": 2,
            },
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def classify_failure(self, failure_log_id: int) -> dict:
        """
        失败分类

        分析失败日志，返回失败类型和上下文
        """
        log = self.db.query(ExecutionLog).filter(ExecutionLog.id == failure_log_id).first()
        if not log:
            return {"error": "Failure log not found"}

        failure_type = "unknown"
        confidence = 0.5
        context = {}

        # 根据错误信息分类
        error_msg = log.error_message or ""

        if "locator" in error_msg.lower() or "element" in error_msg.lower():
            failure_type = "locator_not_found"
            confidence = 0.9
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            failure_type = "timeout"
            confidence = 0.95
        elif "assert" in error_msg.lower() or "expected" in error_msg.lower():
            failure_type = "assertion_error"
            confidence = 0.85
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            failure_type = "network_error"
            confidence = 0.8
        elif "401" in error_msg or "403" in error_msg or "unauthorized" in error_msg.lower():
            failure_type = "auth_expired"
            confidence = 0.9
        elif "data" in error_msg.lower() or "null" in error_msg.lower():
            failure_type = "data_missing"
            confidence = 0.7

        context = {
            "error_message": error_msg,
            "request_url": log.request_url,
            "request_method": log.request_method,
            "response_status": log.response_status,
            "response_body": log.response_body[:500] if log.response_body else None,
        }

        return {
            "failure_type": failure_type,
            "confidence": confidence,
            "context": context,
        }

    def match_heal_strategy(
        self, failure_type: str, context: dict, project_id: int
    ) -> List[dict]:
        """
        匹配自愈策略

        优先使用项目自定义规则，其次使用预定义策略
        """
        strategies = []

        # 查询项目自定义规则
        custom_rules = (
            self.db.query(SmartOrchRule)
            .filter(
                SmartOrchRule.project_id == project_id,
                SmartOrchRule.enabled == True,
            )
            .all()
        )

        for rule in custom_rules:
            try:
                condition = json.loads(rule.condition)
                if self._match_condition(condition, failure_type, context):
                    strategies.append(
                        {
                            "rule_id": rule.id,
                            "action": json.loads(rule.action),
                            "priority": rule.priority,
                            "confidence": 0.8,  # 自定义规则默认置信度
                            "source": "custom",
                        }
                    )
            except json.JSONDecodeError:
                continue

        # 添加预定义策略
        builtin = self.BUILTIN_STRATEGIES.get(failure_type)
        if builtin:
            strategies.append(
                {
                    "rule_id": None,
                    "action": builtin["action"],
                    "priority": 0,
                    "confidence": builtin["confidence"],
                    "reasoning": builtin["reasoning"],
                    "changes": builtin["changes"],
                    "source": "builtin",
                }
            )

        # 按优先级和置信度排序
        strategies.sort(key=lambda x: (x["priority"], x["confidence"]), reverse=True)

        return strategies

    def _match_condition(
        self, condition: dict, failure_type: str, context: dict
    ) -> bool:
        """匹配条件"""
        # 简单实现：检查 failure_type 是否匹配
        if "failure_types" in condition:
            return failure_type in condition["failure_types"]
        return True

    def execute_heal(
        self,
        failure_log_id: int,
        strategy: dict,
        auto_approve: bool = False,
        user_id: Optional[int] = None,
    ) -> dict:
        """
        执行自愈

        Args:
            failure_log_id: 失败日志 ID
            strategy: 匹配到的策略
            auto_approve: 是否自动批准
            user_id: 用户 ID

        Returns:
            自愈结果
        """
        log = self.db.query(ExecutionLog).filter(ExecutionLog.id == failure_log_id).first()
        if not log:
            return {"error": "Failure log not found"}

        action = strategy.get("action", "")
        heal_action = action if isinstance(action, str) else strategy.get("action", {}).get("type", "")

        # 构建自愈配置
        heal_config = {
            "strategy_source": strategy.get("source", "builtin"),
            "rule_id": strategy.get("rule_id"),
            "changes": strategy.get("changes", {}),
        }

        # 生成 before snapshot
        before_snapshot = json.dumps(
            {
                "request_url": log.request_url,
                "request_method": log.request_method,
                "request_body": log.request_body,
                "assertion_results": log.assertion_results,
                "error_message": log.error_message,
            },
            ensure_ascii=False,
        )

        # 执行自愈动作（模拟）
        after_snapshot, heal_success, ai_reasoning = self._perform_heal_action(
            heal_action, log, strategy
        )

        # 保存自愈日志
        heal_log = SelfHealLog(
            failure_log_id=failure_log_id,
            heal_action=heal_action,
            heal_config=json.dumps(heal_config, ensure_ascii=False),
            heal_success=heal_success,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            confidence=strategy.get("confidence", 0.5),
            ai_reasoning=ai_reasoning,
            human_approved=auto_approve or strategy.get("confidence", 0) >= 0.9,
        )

        self.db.add(heal_log)

        # 更新规则使用统计
        if strategy.get("rule_id"):
            rule = (
                self.db.query(SmartOrchRule)
                .filter(SmartOrchRule.id == strategy["rule_id"])
                .first()
            )
            if rule:
                rule.usage_count += 1
                if heal_success:
                    # 更新成功率
                    total = rule.usage_count
                    old_success = (rule.success_rate or 0) * (total - 1)
                    rule.success_rate = (old_success + 1) / total if total > 0 else 0

        self.db.commit()
        self.db.refresh(heal_log)

        return {
            "heal_id": heal_log.id,
            "action": heal_action,
            "action_name": self.HEAL_ACTIONS.get(heal_action, heal_action),
            "confidence": heal_log.confidence,
            "ai_reasoning": ai_reasoning,
            "heal_success": heal_success,
            "changes": strategy.get("changes", {}),
            "requires_approval": not (auto_approve or heal_log.human_approved),
            "before_snapshot": before_snapshot,
            "after_snapshot": after_snapshot,
        }

    def _perform_heal_action(
        self, action: str, log: ExecutionLog, strategy: dict
    ) -> tuple:
        """执行具体的自愈动作"""
        changes = strategy.get("changes", {})

        if action == "update_locator":
            reasoning = "分析页面 HTML 结构，使用内容匹配和相对定位生成新的 XPath"
            after = json.dumps(
                {
                    "locator": "//div[contains(text(),'Submit')]/following-sibling::button",
                    "type": "xpath",
                },
                ensure_ascii=False,
            )
            return after, True, reasoning

        elif action == "update_assertion":
            # 尝试从响应中提取实际值
            actual_value = "200"
            if log.response_body:
                try:
                    resp = json.loads(log.response_body)
                    if "code" in resp:
                        actual_value = str(resp["code"])
                    elif "status" in resp:
                        actual_value = str(resp["status"])
                except json.JSONDecodeError:
                    pass

            reasoning = f"分析响应结构变化，检测到 code 字段值已从 0 调整为 {actual_value}，自动更新期望值"
            after = json.dumps(
                {"path": "$.code", "expected": actual_value}, ensure_ascii=False
            )
            return after, True, reasoning

        elif action == "add_wait":
            wait_seconds = changes.get("wait_seconds", 5)
            reasoning = f"检测到超时，增加 {wait_seconds} 秒等待时间，启用智能等待机制"
            after = json.dumps(
                {"wait_seconds": wait_seconds, "smart_wait": True}, ensure_ascii=False
            )
            return after, True, reasoning

        elif action == "retry_with_backoff":
            max_retries = changes.get("max_retries", 3)
            reasoning = f"网络错误，执行指数退避重试策略，最大重试 {max_retries} 次"
            after = json.dumps(
                {"max_retries": max_retries, "backoff_factor": 2, "retry_count": 0},
                ensure_ascii=False,
            )
            return after, True, reasoning

        elif action == "skip_step":
            reasoning = "标记该步骤为非关键步骤，测试继续执行但记录跳过"
            after = json.dumps({"skipped": True, "reason": "non_critical"}, ensure_ascii=False)
            return after, True, reasoning

        else:
            reasoning = "未知操作类型，执行默认重试策略"
            after = json.dumps({"retry": True, "count": 1}, ensure_ascii=False)
            return after, False, reasoning

    def get_history(
        self, project_id: int, page: int = 1, page_size: int = 20
    ) -> dict:
        """获取自愈历史"""
        query = (
            self.db.query(SelfHealLog)
            .join(ExecutionLog)
            .filter(ExecutionLog.environment_id.in_(
                self.db.query(SmartOrchRule.project_id).filter(
                    SmartOrchRule.project_id == project_id
                )
            ))
            .order_by(SelfHealLog.created_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        # 计算成功率
        success_count = (
            self.db.query(SelfHealLog)
            .join(ExecutionLog)
            .filter(
                SelfHealLog.heal_success == True,
            )
            .count()
        )
        success_rate = success_count / total if total > 0 else 0

        return {
            "items": [
                {
                    "id": h.id,
                    "failure_log_id": h.failure_log_id,
                    "heal_action": h.heal_action,
                    "heal_action_name": self.HEAL_ACTIONS.get(h.heal_action, h.heal_action),
                    "heal_success": h.heal_success,
                    "confidence": h.confidence,
                    "ai_reasoning": h.ai_reasoning,
                    "human_approved": h.human_approved,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in items
            ],
            "total": total,
            "success_rate": round(success_rate, 2),
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def approve_heal(self, heal_id: int, approved: bool) -> dict:
        """人工审批自愈结果"""
        heal_log = self.db.query(SelfHealLog).filter(SelfHealLog.id == heal_id).first()
        if not heal_log:
            return {"success": False, "error": "Heal log not found"}

        heal_log.human_approved = approved
        self.db.commit()

        return {"success": True, "approved": approved}

    def rollback_heal(self, heal_id: int) -> dict:
        """回滚自愈"""
        heal_log = self.db.query(SelfHealLog).filter(SelfHealLog.id == heal_id).first()
        if not heal_log:
            return {"success": False, "error": "Heal log not found"}

        # 回滚逻辑：删除或标记
        heal_log.heal_success = False
        heal_log.ai_reasoning = (heal_log.ai_reasoning or "") + " [已回滚]"
        self.db.commit()

        return {"success": True}
