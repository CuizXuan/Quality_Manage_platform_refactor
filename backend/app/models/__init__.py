from app.models.base import Base
from .case import TestCase
from .environment import Environment
from .scenario import Scenario, ScenarioStep
from .execution_log import ExecutionLog
from .dataset import DataSet, DataSetRow
from .schedule import Schedule
from .mock_rule import MockRule
from .report_template import ReportTemplate
from .repository import CodeRepository, CodeFile, CodeMethod
from .coverage import CoverageRecord
from .defect import Defect, DefectAttachment, DefectComment
from .quality_gate import QualityGate, QualityGateResult
from .integration import IntegrationConfig

# Phase 4 新增模型
from .tenant import (
    Tenant,
    User,
    Role,
    Permission,
    UserRole,
    Project,
    ProjectMember,
    Version,
    SharedAsset,
    AssetTemplate,
    FailureCluster,
    ChangeImpact,
    PerformanceBaseline,
    AlertRule,
    Dashboard,
    DashboardWidget,
)

# Phase 5 新增模型
from .ai_models import (
    AIGenHistory,
    VectorDoc,
    EmbeddingCache,
    SelfHealLog,
    SmartOrchRule,
    AIAdvisorChat,
)
from .traffic_models import (
    TrafficRecord,
    TrafficReplay,
    TrafficTag,
    DiffReport,
    CompareResult,
)
from .chaos_models import (
    ChaosExperiment,
    FaultInjection,
    FaultType,
    ChaosMetric,
    ResilienceScore,
)
from .data_factory_models import (
    DataMaskRule,
    DataGenTemplate,
    DataSnapshot,
    DataCloneTask,
)
from .plugin_models import (
    Plugin,
    PluginVersion,
    PluginReview,
    PluginInstall,
    CLIKey,
    CLIUsageLog,
)
from .audit_models import (
    AuditLog,
    SecurityEvent,
)
from .ai_model_config import AIModelConfig
from .case_folder import CaseFolder

__all__ = [
    # Phase 1-3
    "Base",
    "TestCase",
    "Environment",
    "Scenario",
    "ScenarioStep",
    "ExecutionLog",
    "DataSet",
    "DataSetRow",
    "Schedule",
    "MockRule",
    "ReportTemplate",
    "CodeRepository",
    "CodeFile",
    "CodeMethod",
    "CoverageRecord",
    "Defect",
    "DefectAttachment",
    "DefectComment",
    "QualityGate",
    "QualityGateResult",
    "IntegrationConfig",
    # Phase 4
    "Tenant",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "Project",
    "ProjectMember",
    "Version",
    "SharedAsset",
    "AssetTemplate",
    "FailureCluster",
    "ChangeImpact",
    "PerformanceBaseline",
    "AlertRule",
    "Dashboard",
    "DashboardWidget",
    # Phase 5
    "AIGenHistory",
    "VectorDoc",
    "EmbeddingCache",
    "SelfHealLog",
    "SmartOrchRule",
    "AIAdvisorChat",
    # Phase 5 - Traffic
    "TrafficRecord",
    "TrafficReplay",
    "TrafficTag",
    "DiffReport",
    "CompareResult",
    # Phase 5 - Chaos
    "ChaosExperiment",
    "FaultInjection",
    "FaultType",
    "ChaosMetric",
    "ResilienceScore",
    # Phase 5 - Data Factory
    "DataMaskRule",
    "DataGenTemplate",
    "DataSnapshot",
    "DataCloneTask",
    # Phase 5 - Plugin
    "Plugin",
    "PluginVersion",
    "PluginReview",
    "PluginInstall",
    "CLIKey",
    "CLIUsageLog",
    # Phase 5 - Audit
    "AuditLog",
    "SecurityEvent",
    # Phase 5 - AI Model Config
    "AIModelConfig",
    # Case Folder
    "CaseFolder",
]
