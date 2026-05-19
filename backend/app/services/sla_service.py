# -*- coding: utf-8 -*-
"""
Phase 5 - SLA 监控服务
"""
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.base import Base, get_engine
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, func


class SLAMetric(Base):
    """SLA 指标表"""
    __tablename__ = "sla_metric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(50), nullable=False)  # uptime/response_time/error_rate
    metric_value = Column(Float, nullable=False)
    target_value = Column(Float)  # 目标值
    period = Column(String(20), nullable=False)  # daily/weekly/monthly
    endpoint = Column(String(200))  # 相关端点（可选）
    dimension = Column(String(50))  # 维度标签，如 region/tenant
    metadata = Column(JSON)
    recorded_at = Column(DateTime, server_default=func.now())


class SLAReport(Base):
    """SLA 报告表"""
    __tablename__ = "sla_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    uptime = Column(Float)  # 可用性百分比
    avg_response_time_ms = Column(Float)
    p95_response_time_ms = Column(Float)
    error_rate = Column(Float)  # 错误率百分比
    total_requests = Column(Integer)
    failed_requests = Column(Integer)
    sla_breaches = Column(Integer)  # SLA 违规次数
    report_data = Column(JSON)  # 详细数据
    created_at = Column(DateTime, server_default=func.now())


class SLAService:
    """
    SLA 监控服务

    SLA 目标:
    - 可用性: 99.99% (年停机 < 52 分钟)
    - 响应时间: P95 < 500ms
    - 错误率: < 0.01%
    """

    TARGETS = {
        "uptime": 99.99,       # %
        "response_time_p95": 500,  # ms
        "error_rate": 0.01,    # %
    }

    def __init__(self, db: Session):
        self.db = db

    def record_metric(
        self,
        metric_name: str,
        value: float,
        period: str = "daily",
        target_value: float = None,
        endpoint: str = None,
        dimension: str = None,
    ):
        """记录一个 SLA 指标"""
        metric = SLAMetric(
            metric_name=metric_name,
            metric_value=value,
            target_value=target_value,
            period=period,
            endpoint=endpoint,
            dimension=dimension,
        )
        self.db.add(metric)
        self.db.commit()

    def check_sla_breach(self, metric_name: str, value: float) -> bool:
        """检查是否违反 SLA 目标"""
        target = self.TARGETS.get(metric_name)
        if target is None:
            return False

        if metric_name == "uptime":
            # 可用性：实际值 < 目标值 = 违反
            return value < target
        elif "response_time" in metric_name:
            # 响应时间：实际值 > 目标值 = 违反
            return value > target
        elif metric_name == "error_rate":
            # 错误率：实际值 > 目标值 = 违反
            return value > target
        return False

    def get_current_status(self, period: str = "daily") -> dict:
        """获取当前 SLA 状态"""
        now = datetime.now()
        since = now - timedelta(hours=24)

        # 查询最近的指标
        uptime_metrics = self.db.query(SLAMetric).filter(
            SLAMetric.metric_name == "uptime",
            SLAMetric.period == period,
            SLAMetric.recorded_at >= since,
        ).all()

        response_metrics = self.db.query(SLAMetric).filter(
            SLAMetric.metric_name.in_(["response_time_p95", "response_time_avg"]),
            SLAMetric.period == period,
            SLAMetric.recorded_at >= since,
        ).all()

        error_metrics = self.db.query(SLAMetric).filter(
            SLAMetric.metric_name == "error_rate",
            SLAMetric.period == period,
            SLAMetric.recorded_at >= since,
        ).all()

        # 计算当前值（取最新）
        current_uptime = uptime_metrics[-1].metric_value if uptime_metrics else None
        current_response = (
            response_metrics[-1].metric_value if response_metrics else None
        )
        current_error = (
            error_metrics[-1].metric_value if error_metrics else None
        )

        return {
            "period": period,
            "checked_at": now.isoformat(),
            "uptime": {
                "current": current_uptime,
                "target": self.TARGETS["uptime"],
                "breach": self.check_sla_breach("uptime", current_uptime)
                if current_uptime else None,
            },
            "response_time_p95": {
                "current": current_response,
                "target": self.TARGETS["response_time_p95"],
                "breach": self.check_sla_breach("response_time_p95", current_response)
                if current_response else None,
            },
            "error_rate": {
                "current": current_error,
                "target": self.TARGETS["error_rate"],
                "breach": self.check_sla_breach("error_rate", current_error)
                if current_error else None,
            },
        }

    def generate_report(self, period_start: datetime, period_end: datetime) -> dict:
        """生成 SLA 报告"""
        # 查询期间内的指标
        metrics = self.db.query(SLAMetric).filter(
            SLAMetric.recorded_at >= period_start,
            SLAMetric.recorded_at <= period_end,
        ).all()

        if not metrics:
            return {"error": "No metrics in period"}

        # 计算各项指标
        uptime_values = [m.metric_value for m in metrics if m.metric_name == "uptime"]
        response_values = [
            m.metric_value
            for m in metrics
            if "response_time" in m.metric_name
        ]
        error_values = [m.metric_value for m in metrics if m.metric_name == "error_rate"]
        total_requests = sum(
            m.metadata.get("total_requests", 0)
            for m in metrics
            if m.metadata
        )
        failed_requests = sum(
            m.metadata.get("failed_requests", 0)
            for m in metrics
            if m.metadata
        )

        # 计算 SLA 违规次数
        sla_breaches = 0
        for m in metrics:
            if self.check_sla_breach(m.metric_name, m.metric_value):
                sla_breaches += 1

        avg_uptime = sum(uptime_values) / len(uptime_values) if uptime_values else None
        avg_response = sum(response_values) / len(response_values) if response_values else None
        p95_response = (
            sorted(response_values)[int(len(response_values) * 0.95)]
            if response_values else None
        )
        avg_error = sum(error_values) / len(error_values) if error_values else None

        report = SLAReport(
            period_start=period_start,
            period_end=period_end,
            uptime=avg_uptime,
            avg_response_time_ms=avg_response,
            p95_response_time_ms=p95_response,
            error_rate=avg_error,
            total_requests=total_requests,
            failed_requests=failed_requests,
            sla_breaches=sla_breaches,
            report_data={
                "sample_count": len(metrics),
                "uptime_samples": len(uptime_values),
                "response_samples": len(response_values),
                "error_samples": len(error_values),
            },
        )
        self.db.add(report)
        self.db.commit()

        return {
            "report_id": report.id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "uptime": avg_uptime,
            "avg_response_time_ms": avg_response,
            "p95_response_time_ms": p95_response,
            "error_rate": avg_error,
            "total_requests": total_requests,
            "sla_breaches": sla_breaches,
            "meets_sla": sla_breaches == 0,
        }
