# -*- coding: utf-8 -*-
"""
Phase 5 - 混沌实验服务
"""
import json
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.chaos_models import ChaosExperiment, FaultInjection, FaultType, ChaosMetric, ResilienceScore


class ChaosExperimentService:
    """混沌实验服务"""

    STATUS_MAP = {
        "draft": "草稿",
        "running": "运行中",
        "paused": "已暂停",
        "completed": "已完成",
        "aborted": "已中止",
    }

    def __init__(self, db: Session):
        self.db = db

    def create_experiment(
        self,
        name: str,
        target_type: str,
        project_id: int,
        user_id: int,
        description: Optional[str] = None,
        target_id: Optional[str] = None,
        hypothesis: Optional[str] = None,
        steady_state: Optional[dict] = None,
        blast_radius: int = 0,
        auto_rollback: bool = True,
        rollback_condition: Optional[dict] = None,
    ) -> dict:
        """创建混沌实验"""
        experiment = ChaosExperiment(
            name=name,
            description=description,
            target_type=target_type,
            target_id=target_id,
            hypothesis=hypothesis,
            steady_state=json.dumps(steady_state, ensure_ascii=False) if steady_state else None,
            blast_radius=blast_radius,
            auto_rollback=auto_rollback,
            rollback_condition=json.dumps(rollback_condition, ensure_ascii=False) if rollback_condition else None,
            status="draft",
            project_id=project_id,
            created_by=user_id,
        )

        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)

        return {"success": True, "experiment_id": experiment.id}

    def start_experiment(self, experiment_id: int) -> dict:
        """启动实验"""
        experiment = self.db.query(ChaosExperiment).filter(ChaosExperiment.id == experiment_id).first()
        if not experiment:
            return {"success": False, "error": "Experiment not found"}

        if experiment.status == "running":
            return {"success": False, "error": "Experiment already running"}

        experiment.status = "running"
        experiment.started_at = datetime.utcnow()
        self.db.commit()

        return {
            "success": True,
            "experiment_id": experiment.id,
            "status": experiment.status,
            "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
        }

    def pause_experiment(self, experiment_id: int) -> dict:
        """暂停实验"""
        experiment = self.db.query(ChaosExperiment).filter(ChaosExperiment.id == experiment_id).first()
        if not experiment:
            return {"success": False, "error": "Experiment not found"}

        experiment.status = "paused"
        self.db.commit()

        return {"success": True, "status": experiment.status}

    def stop_experiment(self, experiment_id: int) -> dict:
        """停止实验"""
        experiment = self.db.query(ChaosExperiment).filter(ChaosExperiment.id == experiment_id).first()
        if not experiment:
            return {"success": False, "error": "Experiment not found"}

        experiment.status = "aborted"
        experiment.ended_at = datetime.utcnow()

        # 停止所有关联的故障注入
        for fault in experiment.faults:
            if fault.status == "running":
                fault.status = "rolled_back"
                fault.ended_at = datetime.utcnow()

        self.db.commit()

        return {"success": True, "status": experiment.status}

    def get_experiment(self, experiment_id: int) -> Optional[dict]:
        """获取实验详情"""
        experiment = self.db.query(ChaosExperiment).filter(ChaosExperiment.id == experiment_id).first()
        if not experiment:
            return None
        return self._experiment_to_dict(experiment)

    def list_experiments(
        self, project_id: int, page: int = 1, page_size: int = 20
    ) -> dict:
        """获取实验列表"""
        query = (
            self.db.query(ChaosExperiment)
            .filter(ChaosExperiment.project_id == project_id)
            .order_by(ChaosExperiment.created_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [self._experiment_to_dict(e) for e in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def delete_experiment(self, experiment_id: int) -> dict:
        """删除实验"""
        experiment = self.db.query(ChaosExperiment).filter(ChaosExperiment.id == experiment_id).first()
        if not experiment:
            return {"success": False, "error": "Experiment not found"}

        # 删除关联的故障注入
        self.db.query(FaultInjection).filter(FaultInjection.experiment_id == experiment_id).delete()

        self.db.delete(experiment)
        self.db.commit()

        return {"success": True}

    def _experiment_to_dict(self, exp: ChaosExperiment) -> dict:
        """转换实验为字典"""
        return {
            "id": exp.id,
            "name": exp.name,
            "description": exp.description,
            "target_type": exp.target_type,
            "target_id": exp.target_id,
            "hypothesis": exp.hypothesis,
            "steady_state": json.loads(exp.steady_state) if exp.steady_state else None,
            "status": exp.status,
            "status_text": self.STATUS_MAP.get(exp.status, exp.status),
            "blast_radius": exp.blast_radius,
            "auto_rollback": exp.auto_rollback,
            "rollback_condition": json.loads(exp.rollback_condition) if exp.rollback_condition else None,
            "started_at": exp.started_at.isoformat() if exp.started_at else None,
            "ended_at": exp.ended_at.isoformat() if exp.ended_at else None,
            "project_id": exp.project_id,
            "created_by": exp.created_by,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "faults": [self._fault_to_dict(f) for f in exp.faults] if exp.faults else [],
        }

    def _fault_to_dict(self, fault: FaultInjection) -> dict:
        """转换故障为字典"""
        return {
            "id": fault.id,
            "experiment_id": fault.experiment_id,
            "fault_type": fault.fault_type,
            "target_service": fault.target_service,
            "fault_config": json.loads(fault.fault_config) if fault.fault_config else None,
            "blast_radius": fault.blast_radius,
            "status": fault.status,
            "started_at": fault.started_at.isoformat() if fault.started_at else None,
            "ended_at": fault.ended_at.isoformat() if fault.ended_at else None,
            "error_message": fault.error_message,
        }


class FaultInjectionService:
    """故障注入服务"""

    # 预定义故障类型
    FAULT_TYPES = {
        "cpu-stress": {"name": "CPU 压力", "category": "resource", "risk": "high"},
        "memory-stress": {"name": "内存压力", "category": "resource", "risk": "high"},
        "network-delay": {"name": "网络延迟", "category": "network", "risk": "medium"},
        "network-loss": {"name": "网络丢包", "category": "network", "risk": "high"},
        "pod-kill": {"name": "杀死 Pod", "category": "pod", "risk": "critical"},
        "service-down": {"name": "服务下线", "category": "application", "risk": "critical"},
        "disk-fill": {"name": "磁盘填充", "category": "resource", "risk": "high"},
        "dns-failure": {"name": "DNS 故障", "category": "network", "risk": "medium"},
    }

    def __init__(self, db: Session):
        self.db = db

    def inject_fault(
        self,
        experiment_id: int,
        fault_type: str,
        target_service: str,
        fault_config: dict,
        blast_radius: int = 0,
    ) -> dict:
        """注入故障"""
        # 检查实验是否存在
        experiment = self.db.query(ChaosExperiment).filter(ChaosExperiment.id == experiment_id).first()
        if not experiment:
            return {"success": False, "error": "Experiment not found"}

        # 创建故障注入记录
        fault = FaultInjection(
            experiment_id=experiment_id,
            fault_type=fault_type,
            target_service=target_service,
            fault_config=json.dumps(fault_config, ensure_ascii=False),
            blast_radius=blast_radius,
            status="running",
            started_at=datetime.utcnow(),
        )

        self.db.add(fault)
        experiment.status = "running"
        self.db.commit()
        self.db.refresh(fault)

        # 模拟故障执行
        self._simulate_fault_execution(fault)

        return {
            "success": True,
            "fault_id": fault.id,
            "status": fault.status,
            "started_at": fault.started_at.isoformat() if fault.started_at else None,
        }

    def _simulate_fault_execution(self, fault: FaultInjection):
        """模拟故障执行（实际项目中调用 K8s API 或其他工具）"""
        # 模拟故障执行 3 秒后成功结束
        import time
        time.sleep(0.1)  # 模拟延迟

        fault.status = "success"
        fault.ended_at = datetime.utcnow()

        # 生成模拟指标
        for metric_name, baseline in [
            ("response_time_ms", 100),
            ("error_rate", 0.01),
            ("throughput", 1000),
        ]:
            # 模拟指标值有 20% 偏差
            import random
            value = baseline * random.uniform(0.8, 1.2)
            deviation = (value - baseline) / baseline * 100

            metric = ChaosMetric(
                injection_id=fault.id,
                metric_name=metric_name,
                metric_value=value,
                baseline_value=baseline,
                deviation=deviation,
            )
            self.db.add(metric)

        self.db.commit()

    def rollback_fault(self, fault_id: int) -> dict:
        """回滚故障"""
        fault = self.db.query(FaultInjection).filter(FaultInjection.id == fault_id).first()
        if not fault:
            return {"success": False, "error": "Fault not found"}

        fault.status = "rolled_back"
        fault.ended_at = datetime.utcnow()
        self.db.commit()

        return {"success": True, "status": fault.status}

    def get_fault_types(self) -> List[dict]:
        """获取故障类型列表"""
        return [
            {
                "type": fault_type,
                "name": info["name"],
                "category": info["category"],
                "risk_level": info["risk"],
            }
            for fault_type, info in self.FAULT_TYPES.items()
        ]

    def get_fault_metrics(self, fault_id: int) -> List[dict]:
        """获取故障指标"""
        metrics = self.db.query(ChaosMetric).filter(ChaosMetric.injection_id == fault_id).all()
        return [
            {
                "id": m.id,
                "metric_name": m.metric_name,
                "metric_value": m.metric_value,
                "baseline_value": m.baseline_value,
                "deviation": m.deviation,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in metrics
        ]


class ResilienceScoreService:
    """韧性评分服务"""

    # 评分权重
    WEIGHTS = {
        "redundancy": 0.20,
        "isolation": 0.15,
        "observability": 0.15,
        "recovery": 0.25,
        "fault_tolerance": 0.25,
    }

    def __init__(self, db: Session):
        self.db = db

    def evaluate(self, target_type: str, target_id: str, project_id: int) -> dict:
        """评估韧性"""
        # 模拟评估（实际项目中分析实际指标）
        import random

        metrics = {
            "redundancy": random.uniform(70, 95),
            "isolation": random.uniform(65, 90),
            "observability": random.uniform(75, 95),
            "recovery": random.uniform(70, 90),
            "fault_tolerance": random.uniform(68, 88),
        }

        score = self.calculate_score(metrics)

        # 生成弱点和建议
        weaknesses = []
        recommendations = []

        if metrics["redundancy"] < 80:
            weaknesses.append("副本配置不足，单点故障风险高")
            recommendations.append("增加服务副本数，配置多可用区部署")

        if metrics["isolation"] < 80:
            weaknesses.append("服务隔离不足，故障传播风险")
            recommendations.append("引入熔断器和隔离舱模式")

        if metrics["observability"] < 80:
            weaknesses.append("监控告警覆盖不全面")
            recommendations.append("完善指标采集和告警规则")

        if metrics["recovery"] < 80:
            weaknesses.append("故障恢复时间较长")
            recommendations.append("优化自动扩缩容和故障转移策略")

        if metrics["fault_tolerance"] < 80:
            weaknesses.append("容错机制不完善")
            recommendations.append("增加重试、降级和限流配置")

        # 保存评估结果
        score_record = ResilienceScore(
            target_type=target_type,
            target_id=target_id,
            score=score,
            metrics=json.dumps(metrics, ensure_ascii=False),
            weaknesses=json.dumps(weaknesses, ensure_ascii=False),
            recommendations=json.dumps(recommendations, ensure_ascii=False),
            project_id=project_id,
        )
        self.db.add(score_record)
        self.db.commit()

        return {
            "score": round(score, 1),
            "metrics": {k: round(v, 1) for k, v in metrics.items()},
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    def calculate_score(self, metrics: dict) -> float:
        """计算综合评分"""
        total = 0
        for key, weight in self.WEIGHTS.items():
            value = metrics.get(key, 0)
            total += value * weight
        return total

    def get_latest_score(self, target_type: str, target_id: str) -> Optional[dict]:
        """获取最新评分"""
        score = (
            self.db.query(ResilienceScore)
            .filter(
                ResilienceScore.target_type == target_type,
                ResilienceScore.target_id == target_id,
            )
            .order_by(ResilienceScore.evaluated_at.desc())
            .first()
        )

        if not score:
            return None

        return {
            "score": score.score,
            "metrics": json.loads(score.metrics) if score.metrics else {},
            "weaknesses": json.loads(score.weaknesses) if score.weaknesses else [],
            "recommendations": json.loads(score.recommendations) if score.recommendations else [],
            "evaluated_at": score.evaluated_at.isoformat() if score.evaluated_at else None,
        }

    def get_score_history(
        self, target_type: str, target_id: str, limit: int = 10
    ) -> List[dict]:
        """获取评分历史"""
        scores = (
            self.db.query(ResilienceScore)
            .filter(
                ResilienceScore.target_type == target_type,
                ResilienceScore.target_id == target_id,
            )
            .order_by(ResilienceScore.evaluated_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": s.id,
                "score": s.score,
                "evaluated_at": s.evaluated_at.isoformat() if s.evaluated_at else None,
            }
            for s in scores
        ]
