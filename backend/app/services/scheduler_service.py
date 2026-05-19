"""
Scheduler Service - 定时调度服务
基于 APScheduler AsyncIOScheduler 实现
"""
import logging
import json
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.database import SessionLocal
from app.models.schedule import Schedule

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时调度服务"""

    _instance: Optional["SchedulerService"] = None
    _scheduler: Optional[AsyncIOScheduler] = None
    _running_tests: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._scheduler is None:
            self._init_scheduler()

    def _init_scheduler(self):
        """初始化 APScheduler"""
        jobstores = {
            "default": MemoryJobStore()
        }
        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60
        }
        self._scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults=job_defaults,
            timezone="Asia/Shanghai"
        )
        # 注册事件监听
        self._scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

    @staticmethod
    def _job_executed_listener(event):
        """任务执行完成回调"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} completed successfully")

    def init_scheduler(self):
        """初始化并启动调度器（已自动调用，可手动触发）"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def add_job(
        self,
        schedule_id: int,
        name: str,
        target_type: str,
        target_id: int,
        cron_expr: str,
        env_id: Optional[int] = None,
        notify_on: str = "never",
        notify_channels: str = "[]"
    ) -> bool:
        """
        添加定时任务
        schedule_id: 数据库中的调度记录 ID
        name: 任务名称
        target_type: "case" 或 "scenario"
        target_id: 目标用例/场景 ID
        cron_expr: cron 表达式，如 "0 8 * * *" 表示每天 8 点
        env_id: 环境 ID
        返回: 是否成功
        """
        job_id = f"schedule_{schedule_id}"

        # 解析 cron 表达式
        try:
            parts = cron_expr.split()
            if len(parts) == 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            else:
                raise ValueError(f"Invalid cron expression: {cron_expr}")
        except Exception as e:
            logger.error(f"Failed to parse cron expression: {e}")
            return False

        # 移除已存在的同名任务
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

        try:
            self._scheduler.add_job(
                func=self._execute_scheduled_job,
                trigger=trigger,
                job_id=job_id,
                name=name,
                kwargs={
                    "schedule_id": schedule_id,
                    "target_type": target_type,
                    "target_id": target_id,
                    "env_id": env_id,
                    "notify_on": notify_on,
                    "notify_channels": notify_channels
                },
                replace_existing=True
            )
            logger.info(f"Added scheduled job: {job_id} ({name})")
            return True
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {e}")
            return False

    def remove_job(self, schedule_id: int) -> bool:
        """移除定时任务"""
        job_id = f"schedule_{schedule_id}"
        try:
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
                logger.info(f"Removed scheduled job: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False

    def pause_job(self, schedule_id: int) -> bool:
        """暂停定时任务"""
        job_id = f"schedule_{schedule_id}"
        try:
            self._scheduler.pause_job(job_id)
            logger.info(f"Paused scheduled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False

    def resume_job(self, schedule_id: int) -> bool:
        """恢复定时任务"""
        job_id = f"schedule_{schedule_id}"
        try:
            self._scheduler.resume_job(job_id)
            logger.info(f"Resumed scheduled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False

    def run_now(self, schedule_id: int) -> bool:
        """立即执行一次定时任务"""
        job_id = f"schedule_{schedule_id}"
        try:
            job = self._scheduler.get_job(job_id)
            if job:
                self._scheduler.modify_job(job_id, next_run_time=datetime.now())
                logger.info(f"Triggered immediate run for job: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to run job now {job_id}: {e}")
            return False

    def sync_from_db(self):
        """从数据库同步任务到调度器"""
        db = SessionLocal()
        try:
            schedules = db.query(Schedule).filter(Schedule.enabled == True).all()
            for schedule in schedules:
                self.add_job(
                    schedule_id=schedule.id,
                    name=schedule.name,
                    target_type=schedule.target_type,
                    target_id=schedule.target_id,
                    cron_expr=schedule.cron_expression,
                    env_id=schedule.environment_id,
                    notify_on=schedule.notify_on,
                    notify_channels=schedule.notify_channels
                )
            logger.info(f"Synced {len(schedules)} schedules from database")
        except Exception as e:
            logger.error(f"Failed to sync schedules from db: {e}")
        finally:
            db.close()

    @staticmethod
    async def _execute_scheduled_job(
        schedule_id: int,
        target_type: str,
        target_id: int,
        env_id: Optional[int],
        notify_on: str,
        notify_channels: str
    ):
        """
        执行调度的任务
        这是一个异步函数，由 APScheduler 调用
        """
        from app.services.notify_service import NotifyService
        from app.services.request_executor import RequestExecutor
        from app.services.scenario_executor import ScenarioExecutor
        import asyncio

        db = SessionLocal()
        try:
            # 获取调度记录
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule:
                logger.error(f"Schedule {schedule_id} not found in database")
                return

            # 更新最后运行时间
            schedule.last_run_at = datetime.now()
            schedule.run_count += 1
            db.commit()

            # 获取环境变量
            env_vars = {}
            if env_id:
                from app.models.environment import Environment
                env = db.query(Environment).filter(Environment.id == env_id).first()
                if env:
                    env_vars = json.loads(env.variables or "{}")

            # 执行目标
            status = "success"
            error_message = ""

            if target_type == "case":
                from app.models.case import TestCase
                case = db.query(TestCase).filter(TestCase.id == target_id).first()
                if case:
                    case_data = {
                        "id": case.id,
                        "name": case.name,
                        "method": case.method,
                        "url": case.url,
                        "headers": json.loads(case.headers or "{}"),
                        "params": json.loads(case.params or "{}"),
                        "body": case.body,
                        "body_type": case.body_type,
                        "auth_type": case.auth_type,
                        "auth_config": json.loads(case.auth_config or "{}"),
                        "assertions": json.loads(case.assertions or "[]"),
                        "timeout": case.timeout,
                        "follow_redirects": case.follow_redirects,
                        "verify_ssl": case.verify_ssl,
                    }
                    executor = RequestExecutor()
                    result = await executor.execute_case(case_data, env_vars)
                    status = result.get("status", "unknown")
                    if status != "success":
                        error_message = "Assertion failed or request error"
            elif target_type == "scenario":
                from app.models.scenario import Scenario, ScenarioStep
                scenario = db.query(Scenario).filter(Scenario.id == target_id).first()
                if scenario:
                    steps = db.query(ScenarioStep).filter(
                        ScenarioStep.scenario_id == target_id
                    ).order_by(ScenarioStep.step_order).all()

                    steps_data = []
                    for step in steps:
                        case = db.query(TestCase).filter(TestCase.id == step.case_id).first()
                        if case:
                            case_data = {
                                "id": case.id,
                                "name": case.name,
                                "method": case.method,
                                "url": case.url,
                                "headers": json.loads(case.headers or "{}"),
                                "params": json.loads(case.params or "{}"),
                                "body": case.body,
                                "body_type": case.body_type,
                                "auth_type": case.auth_type,
                                "auth_config": json.loads(case.auth_config or "{}"),
                                "assertions": json.loads(case.assertions or "[]"),
                                "timeout": case.timeout,
                                "follow_redirects": case.follow_redirects,
                                "verify_ssl": case.verify_ssl,
                            }
                            steps_data.append({
                                "step_order": step.step_order,
                                "case_id": step.case_id,
                                "case_data": case_data,
                                "extract_rules": json.loads(step.extract_rules or "[]"),
                                "skip_on_failure": step.skip_on_failure,
                                "enabled": step.enabled,
                            })

                    scenario_data = {
                        "id": scenario.id,
                        "name": scenario.name,
                        "variables": json.loads(scenario.variables or "{}"),
                        "steps": steps_data,
                    }
                    executor = ScenarioExecutor()
                    result = await executor.execute_scenario(scenario_data, env_vars)
                    status = result.get("status", "unknown")
                    if status != "success":
                        error_message = "One or more steps failed"

            # 更新调度统计
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if schedule:
                if status == "success":
                    schedule.success_count += 1
                else:
                    schedule.failure_count += 1
                db.commit()

            # 发送通知
            notify_channels_list = json.loads(notify_channels or "[]")
            if notify_channels_list and (
                notify_on == "always" or
                (notify_on == "failure" and status != "success")
            ):
                from app.models.execution_log import ExecutionLog
                summary = {
                    "total": 1,
                    "passed": 1 if status == "success" else 0,
                    "failed": 1 if status != "success" else 0,
                    "rate": 100 if status == "success" else 0
                }
                message = {
                    "title": f"定时任务执行结果: {schedule.name}",
                    "status": status,
                    "summary": summary,
                    "details": error_message,
                    "report_url": ""
                }
                notify_service = NotifyService()
                asyncio.create_task(
                    notify_service.notify_execution_result(message, notify_channels_list)
                )

            logger.info(f"Scheduled job {schedule_id} executed with status: {status}")

        except Exception as e:
            logger.error(f"Error executing scheduled job {schedule_id}: {e}")
            # 更新失败计数
            try:
                schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
                if schedule:
                    schedule.failure_count += 1
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    def shutdown(self):
        """关闭调度器"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler shutdown")


# 全局实例（延迟初始化）
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """获取调度服务单例"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
