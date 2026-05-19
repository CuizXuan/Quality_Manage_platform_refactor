# -*- coding: utf-8 -*-
"""
Phase 4 - AI分析服务
包括：失败聚类、变更影响分析、智能告警、性能基线
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from app.models.tenant import FailureCluster, ChangeImpact, AlertRule, PerformanceBaseline
from app.models.execution_log import ExecutionLog
import re
import json


class AIFailureService:
    """失败聚类分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_clusters(self, project_id: int, 
                    page: int = 1, page_size: int = 20,
                    resolved: bool = None) -> Tuple[List[dict], int]:
        """获取失败聚类列表"""
        query = self.db.query(FailureCluster).filter(
            FailureCluster.project_id == project_id
        )
        
        if resolved is not None:
            query = query.filter(FailureCluster.resolved == resolved)
        
        total = query.count()
        clusters = query.order_by(FailureCluster.last_seen_at.desc())\
                       .offset((page - 1) * page_size)\
                       .limit(page_size)\
                       .all()
        
        return [self._cluster_to_dict(c) for c in clusters], total
    
    def get_cluster_by_id(self, cluster_id: int) -> Optional[dict]:
        """获取聚类详情"""
        cluster = self.db.query(FailureCluster).filter(
            FailureCluster.id == cluster_id
        ).first()
        return self._cluster_to_dict(cluster) if cluster else None
    
    def analyze_failure(self, project_id: int, execution_logs: List[dict]) -> dict:
        """
        分析失败用例，进行聚类
        execution_logs: [{"case_id": 1, "case_name": "...", "error": "...", "timestamp": "..."}]
        """
        # 1. 提取错误模式
        error_patterns = {}
        for log in execution_logs:
            if log.get("status") == "failed" and log.get("error"):
                pattern = self._extract_error_pattern(log["error"])
                if pattern not in error_patterns:
                    error_patterns[pattern] = {
                        "pattern": pattern,
                        "count": 0,
                        "cases": [],
                        "error_type": self._classify_error_type(pattern)
                    }
                error_patterns[pattern]["count"] += 1
                error_patterns[pattern]["cases"].append({
                    "case_id": log.get("case_id"),
                    "case_name": log.get("case_name", ""),
                    "error": log.get("error", "")[:500]
                })
        
        # 2. 创建或更新聚类
        created_clusters = []
        for pattern, info in error_patterns.items():
            # 检查是否已存在相似聚类
            existing = self.db.query(FailureCluster).filter(
                FailureCluster.project_id == project_id,
                FailureCluster.error_pattern == pattern,
                FailureCluster.resolved == False
            ).first()
            
            if existing:
                # 更新已有聚类
                existing.occurrence_count += info["count"]
                existing.affected_cases = json.dumps(info["cases"])
                existing.last_seen_at = datetime.utcnow()
                cluster = existing
            else:
                # 创建新聚类
                cluster = FailureCluster(
                    project_id=project_id,
                    cluster_name=f"Failure-{info['error_type']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    error_pattern=pattern,
                    error_type=info["error_type"],
                    occurrence_count=info["count"],
                    affected_cases=json.dumps(info["cases"]),
                    first_seen_at=datetime.utcnow(),
                    last_seen_at=datetime.utcnow()
                )
                self.db.add(cluster)
            
            created_clusters.append(cluster)
        
        self.db.commit()
        
        return {
            "total_failures": len(execution_logs),
            "clusters_created": len(created_clusters),
            "clusters": [self._cluster_to_dict(c) for c in created_clusters]
        }
    
    def analyze_root_cause(self, cluster_id: int) -> dict:
        """
        根因分析（简化版）
        实际生产中应调用外部AI服务
        """
        cluster = self.db.query(FailureCluster).filter(
            FailureCluster.id == cluster_id
        ).first()
        
        if not cluster:
            return None
        
        # 简化版根因分析 - 基于错误类型
        root_cause_map = {
            "timeout": "请求超时，可能原因：网络延迟、服务响应慢、服务器负载高",
            "assertion": "断言失败，可能原因：预期结果与实际结果不符、测试数据问题",
            "connection": "连接失败，可能原因：服务不可达、连接池满、网络故障",
            "parse": "解析错误，可能原因：响应格式不符合预期、编码问题",
            "auth": "认证失败，可能原因：Token过期、权限不足",
            "unknown": "未知错误，需要进一步调查"
        }
        
        error_type = cluster.error_type or "unknown"
        root_cause = root_cause_map.get(error_type, root_cause_map["unknown"])
        
        # 建议修复方案
        fix_suggestions = {
            "timeout": "1. 检查服务端性能 2. 增加超时时间 3. 使用重试机制",
            "assertion": "1. 检查预期值 2. 验证测试数据 3. 更新断言逻辑",
            "connection": "1. 检查服务状态 2. 验证网络连通性 3. 检查连接配置",
            "parse": "1. 检查响应格式 2. 验证JSON/XML结构 3. 处理编码问题",
            "auth": "1. 刷新Token 2. 检查权限配置 3. 验证登录状态",
            "unknown": "1. 收集更多日志 2. 联系开发人员 3. 创建缺陷工单"
        }
        
        suggested_fix = fix_suggestions.get(error_type, fix_suggestions["unknown"])
        
        # 更新聚类信息
        cluster.root_cause = root_cause
        cluster.suggested_fix = suggested_fix
        self.db.commit()
        
        return {
            "cluster_id": cluster.id,
            "error_type": error_type,
            "root_cause": root_cause,
            "suggested_fix": suggested_fix,
            "confidence": 0.85
        }
    
    def resolve_cluster(self, cluster_id: int) -> Tuple[bool, str]:
        """标记聚类为已解决"""
        cluster = self.db.query(FailureCluster).filter(
            FailureCluster.id == cluster_id
        ).first()
        
        if not cluster:
            return False, "聚类不存在"
        
        cluster.resolved = True
        cluster.resolved_at = datetime.utcnow()
        self.db.commit()
        return True, ""
    
    def ignore_cluster(self, cluster_id: int) -> Tuple[bool, str]:
        """忽略聚类"""
        return self.resolve_cluster(cluster_id)
    
    def _extract_error_pattern(self, error: str) -> str:
        """提取错误特征模式"""
        # 移除具体数值，保留错误结构
        pattern = re.sub(r'\d{4,}', '{NUMBER}', error)
        pattern = re.sub(r'0x[0-9a-fA-F]+', '{HEX}', pattern)
        pattern = re.sub(r'http[s]?://[^\s]+', '{URL}', pattern)
        pattern = re.sub(r'[\w.-]+@[\w.-]+', '{EMAIL}', pattern)
        # 保留前200字符
        return pattern[:200]
    
    def _classify_error_type(self, error: str) -> str:
        """分类错误类型"""
        error_lower = error.lower()
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return 'timeout'
        elif 'assert' in error_lower or 'expected' in error_lower:
            return 'assertion'
        elif 'connect' in error_lower or 'connection' in error_lower or 'refused' in error_lower:
            return 'connection'
        elif 'json' in error_lower or 'parse' in error_lower or 'xml' in error_lower:
            return 'parse'
        elif 'auth' in error_lower or 'token' in error_lower or '401' in error_lower or '403' in error_lower:
            return 'auth'
        else:
            return 'unknown'
    
    def _cluster_to_dict(self, cluster: FailureCluster) -> dict:
        if not cluster:
            return None
        try:
            affected_cases = json.loads(cluster.affected_cases) if isinstance(cluster.affected_cases, str) else (cluster.affected_cases or [])
        except:
            affected_cases = []
        
        return {
            "id": cluster.id,
            "project_id": cluster.project_id,
            "cluster_name": cluster.cluster_name,
            "error_pattern": cluster.error_pattern,
            "error_type": cluster.error_type,
            "root_cause": cluster.root_cause,
            "suggested_fix": cluster.suggested_fix,
            "occurrence_count": cluster.occurrence_count,
            "affected_cases": affected_cases,
            "first_seen_at": cluster.first_seen_at.isoformat() if cluster.first_seen_at else None,
            "last_seen_at": cluster.last_seen_at.isoformat() if cluster.last_seen_at else None,
            "resolved": cluster.resolved,
            "resolved_at": cluster.resolved_at.isoformat() if cluster.resolved_at else None,
            "created_at": cluster.created_at.isoformat() if cluster.created_at else None
        }


class AIChangeImpactService:
    """变更影响分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def predict_impact(self, project_id: int, commit_hash: str, 
                     changed_files: List[str]) -> dict:
        """
        预测变更影响
        简化版：基于文件路径匹配用例
        """
        # 查找相关的测试用例
        impacted_cases = []
        impacted_scenarios = []
        
        # 简化逻辑：根据文件路径猜测相关用例
        for file_path in changed_files:
            # 查找包含文件路径关键词的用例
            keywords = file_path.split('/')[-1].split('.')[0]
            # 这里简化处理，实际应该关联代码仓库分析
            if keywords:
                impacted_cases.append({
                    "file": file_path,
                    "predicted_cases": [],
                    "risk_level": "medium"
                })
        
        # 计算风险等级
        risk_level = "low"
        if len(changed_files) > 10:
            risk_level = "high"
        elif len(changed_files) > 5:
            risk_level = "medium"
        
        # 建议执行的测试
        recommendations = self._generate_recommendations(changed_files, risk_level)
        
        # 保存预测结果
        impact = ChangeImpact(
            project_id=project_id,
            commit_hash=commit_hash,
            changed_files=json.dumps(changed_files),
            impacted_cases=json.dumps(impacted_cases),
            impacted_scenarios=json.dumps(impacted_scenarios),
            risk_level=risk_level,
            recommendation=recommendations,
            prediction_accuracy=0.75
        )
        self.db.add(impact)
        self.db.commit()
        self.db.refresh(impact)
        
        return self._impact_to_dict(impact)
    
    def get_impact_history(self, project_id: int,
                          page: int = 1, page_size: int = 20) -> Tuple[List[dict], int]:
        """获取预测历史"""
        query = self.db.query(ChangeImpact).filter(
            ChangeImpact.project_id == project_id
        )
        
        total = query.count()
        impacts = query.order_by(ChangeImpact.created_at.desc())\
                      .offset((page - 1) * page_size)\
                      .limit(page_size)\
                      .all()
        
        return [self._impact_to_dict(i) for i in impacts], total
    
    def get_impact_by_id(self, impact_id: int) -> Optional[dict]:
        """获取预测详情"""
        impact = self.db.query(ChangeImpact).filter(
            ChangeImpact.id == impact_id
        ).first()
        return self._impact_to_dict(impact) if impact else None
    
    def _generate_recommendations(self, changed_files: List[str], risk_level: str) -> str:
        """生成测试建议"""
        recommendations = []
        
        if risk_level == "high":
            recommendations.append("建议执行全套回归测试")
        elif risk_level == "medium":
            recommendations.append("建议执行相关模块测试")
        else:
            recommendations.append("建议执行变更文件相关测试")
        
        # 根据文件类型建议
        for file in changed_files[:3]:
            if 'api' in file.lower():
                recommendations.append("API接口测试")
            if 'auth' in file.lower():
                recommendations.append("认证授权测试")
            if 'db' in file.lower() or 'model' in file.lower():
                recommendations.append("数据库相关测试")
        
        return "; ".join(recommendations[:5])
    
    def _impact_to_dict(self, impact: ChangeImpact) -> dict:
        if not impact:
            return None
        try:
            changed_files = json.loads(impact.changed_files) if isinstance(impact.changed_files, str) else (impact.changed_files or [])
            impacted_cases = json.loads(impact.impacted_cases) if isinstance(impact.impacted_cases, str) else (impact.impacted_cases or [])
            impacted_scenarios = json.loads(impact.impacted_scenarios) if isinstance(impact.impacted_scenarios, str) else (impact.impacted_scenarios or [])
        except:
            changed_files, impacted_cases, impacted_scenarios = [], [], []
        
        return {
            "id": impact.id,
            "project_id": impact.project_id,
            "commit_hash": impact.commit_hash,
            "changed_files": changed_files,
            "impacted_cases": impacted_cases,
            "impacted_scenarios": impacted_scenarios,
            "risk_level": impact.risk_level,
            "recommendation": impact.recommendation,
            "actual_failures": impact.actual_failures,
            "prediction_accuracy": impact.prediction_accuracy,
            "created_at": impact.created_at.isoformat() if impact.created_at else None
        }


class AIAlertService:
    """智能告警服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_alert_rules(self, project_id: int = None) -> List[dict]:
        """获取告警规则列表"""
        query = self.db.query(AlertRule)
        if project_id:
            query = query.filter(AlertRule.project_id == project_id)
        
        rules = query.order_by(AlertRule.created_at.desc()).all()
        return [self._rule_to_dict(r) for r in rules]
    
    def create_alert_rule(self, project_id: int, user_id: int,
                        name: str, rule_type: str, threshold: float,
                        severity: str = "medium",
                        notify_channels: List[str] = None,
                        scope: dict = None) -> Tuple[AlertRule, bool, str]:
        """创建告警规则"""
        valid_types = ["failure_rate", "rt_spike", "coverage_drop", "defect_backlog", "custom"]
        if rule_type not in valid_types:
            return None, False, f"不支持的规则类型: {rule_type}"
        
        valid_severity = ["critical", "high", "medium", "low", "info"]
        if severity not in valid_severity:
            return None, False, f"无效的严重级别"
        
        try:
            rule = AlertRule(
                name=name,
                type=rule_type,
                project_id=project_id,
                threshold=threshold,
                severity=severity,
                notify_channels=json.dumps(notify_channels or ["email"]),
                scope=json.dumps(scope or {}),
                enabled=True,
                cooldown_minutes=30,
                created_by=user_id
            )
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            return rule, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_alert_rule(self, rule_id: int, **kwargs) -> Tuple[AlertRule, bool, str]:
        """更新告警规则"""
        rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return None, False, "规则不存在"
        
        for key, value in kwargs.items():
            if value is not None and hasattr(rule, key):
                if key in ["notify_channels", "scope"]:
                    setattr(rule, key, json.dumps(value) if isinstance(value, list) else value)
                else:
                    setattr(rule, key, value)
        
        self.db.commit()
        self.db.refresh(rule)
        return rule, True, ""
    
    def delete_alert_rule(self, rule_id: int) -> Tuple[bool, str]:
        """删除告警规则"""
        rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return False, "规则不存在"
        
        self.db.delete(rule)
        self.db.commit()
        return True, ""
    
    def toggle_alert_rule(self, rule_id: int) -> Tuple[bool, str]:
        """启用/禁用规则"""
        rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return False, "规则不存在"
        
        rule.enabled = not rule.enabled
        self.db.commit()
        return True, ""
    
    def check_alerts(self, project_id: int, metrics: dict) -> List[dict]:
        """
        检查告警
        metrics: {"failure_rate": 0.15, "avg_rt": 250, "coverage": 0.85}
        """
        triggered = []
        
        rules = self.db.query(AlertRule).filter(
            AlertRule.project_id == project_id,
            AlertRule.enabled == True
        ).all()
        
        for rule in rules:
            if self._check_rule(rule, metrics):
                triggered.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "type": rule.type,
                    "severity": rule.severity,
                    "message": f"触发告警: {rule.name}",
                    "threshold": rule.threshold,
                    "current_value": metrics.get(rule.type.replace("_", "_"))
                })
        
        return triggered
    
    def _check_rule(self, rule: AlertRule, metrics: dict) -> bool:
        """检查单个规则"""
        metric_key = rule.type.replace("_spike", "_rt").replace("_drop", "_coverage").replace("_rate", "")
        current_value = metrics.get(metric_key, 0)
        
        if rule.type == "failure_rate":
            return current_value > rule.threshold
        elif rule.type == "rt_spike":
            return current_value > rule.threshold
        elif rule.type == "coverage_drop":
            return current_value < rule.threshold
        
        return False
    
    def _rule_to_dict(self, rule: AlertRule) -> dict:
        if not rule:
            return None
        try:
            notify_channels = json.loads(rule.notify_channels) if isinstance(rule.notify_channels, str) else (rule.notify_channels or [])
            scope = json.loads(rule.scope) if isinstance(rule.scope, str) else (rule.scope or {})
        except:
            notify_channels, scope = [], {}
        
        return {
            "id": rule.id,
            "name": rule.name,
            "type": rule.type,
            "project_id": rule.project_id,
            "scope": scope,
            "threshold": rule.threshold,
            "severity": rule.severity,
            "enabled": rule.enabled,
            "notify_channels": notify_channels,
            "cooldown_minutes": rule.cooldown_minutes,
            "created_at": rule.created_at.isoformat() if rule.created_at else None
        }


class AIPerformanceService:
    """性能基线服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_baselines(self, project_id: int, 
                     case_id: int = None,
                     scenario_id: int = None) -> List[dict]:
        """获取性能基线"""
        query = self.db.query(PerformanceBaseline).filter(
            PerformanceBaseline.project_id == project_id
        )
        
        if case_id:
            query = query.filter(PerformanceBaseline.case_id == case_id)
        if scenario_id:
            query = query.filter(PerformanceBaseline.scenario_id == scenario_id)
        
        baselines = query.all()
        return [self._baseline_to_dict(b) for b in baselines]
    
    def create_baseline(self, project_id: int,
                       metric_name: str, baseline_value: float,
                       upper_bound: float = None, lower_bound: float = None,
                       case_id: int = None, scenario_id: int = None,
                       environment_id: int = None) -> Tuple[PerformanceBaseline, bool, str]:
        """创建性能基线"""
        try:
            baseline = PerformanceBaseline(
                project_id=project_id,
                case_id=case_id,
                scenario_id=scenario_id,
                environment_id=environment_id,
                metric_name=metric_name,
                baseline_value=baseline_value,
                upper_bound=upper_bound,
                lower_bound=lower_bound,
                sample_count=0
            )
            self.db.add(baseline)
            self.db.commit()
            self.db.refresh(baseline)
            return baseline, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_baseline(self, baseline_id: int, 
                       baseline_value: float = None,
                       upper_bound: float = None, lower_bound: float = None) -> Tuple[bool, str]:
        """更新基线"""
        baseline = self.db.query(PerformanceBaseline).filter(
            PerformanceBaseline.id == baseline_id
        ).first()
        
        if not baseline:
            return False, "基线不存在"
        
        if baseline_value is not None:
            baseline.baseline_value = baseline_value
        if upper_bound is not None:
            baseline.upper_bound = upper_bound
        if lower_bound is not None:
            baseline.lower_bound = lower_bound
        
        self.db.commit()
        return True, ""
    
    def collect_baseline_data(self, baseline_id: int, new_value: float) -> dict:
        """采集新数据更新基线"""
        baseline = self.db.query(PerformanceBaseline).filter(
            PerformanceBaseline.id == baseline_id
        ).first()
        
        if not baseline:
            return {"error": "基线不存在"}
        
        # 简化：更新基线值
        baseline.baseline_value = (baseline.baseline_value * baseline.sample_count + new_value) / (baseline.sample_count + 1)
        baseline.sample_count += 1
        
        # 检查是否超出范围
        is_anomaly = False
        if baseline.upper_bound and new_value > baseline.upper_bound:
            is_anomaly = True
        if baseline.lower_bound and new_value < baseline.lower_bound:
            is_anomaly = True
        
        self.db.commit()
        
        return {
            "baseline_id": baseline.id,
            "new_value": new_value,
            "updated_baseline": baseline.baseline_value,
            "is_anomaly": is_anomaly
        }
    
    def delete_baseline(self, baseline_id: int) -> Tuple[bool, str]:
        """删除基线"""
        baseline = self.db.query(PerformanceBaseline).filter(
            PerformanceBaseline.id == baseline_id
        ).first()
        
        if not baseline:
            return False, "基线不存在"
        
        self.db.delete(baseline)
        self.db.commit()
        return True, ""
    
    def _baseline_to_dict(self, baseline: PerformanceBaseline) -> dict:
        if not baseline:
            return None
        return {
            "id": baseline.id,
            "project_id": baseline.project_id,
            "case_id": baseline.case_id,
            "scenario_id": baseline.scenario_id,
            "environment_id": baseline.environment_id,
            "metric_name": baseline.metric_name,
            "baseline_value": baseline.baseline_value,
            "upper_bound": baseline.upper_bound,
            "lower_bound": baseline.lower_bound,
            "sample_count": baseline.sample_count,
            "std_deviation": baseline.std_deviation,
            "updated_at": baseline.updated_at.isoformat() if baseline.updated_at else None
        }
