"""
Phase 4 - 租户管理模块
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="租户名称")
    code = Column(String(50), unique=True, nullable=False, comment="租户编码")
    description = Column(Text, comment="租户描述")
    status = Column(String(20), default="active", comment="active/suspended/expired")
    logo_url = Column(String(500), comment="Logo地址")
    quota_config = Column(JSON, comment="资源配额配置")
    subscription_plan = Column(String(50), comment="free/pro/enterprise")
    subscription_expires = Column(DateTime, comment="订阅过期时间")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    users = relationship("User", back_populates="tenant")
    projects = relationship("Project", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.code}>"


class User(Base):
    """用户表（Phase 4扩展）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="所属租户")
    username = Column(String(100), unique=True, nullable=False, comment="用户名")
    email = Column(String(200), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(200), nullable=False, comment="密码哈希")
    avatar = Column(String(500), comment="头像地址")
    phone = Column(String(20), comment="手机号")
    status = Column(String(20), default="active", comment="active/disabled/invited")
    last_login_at = Column(DateTime, comment="最后登录时间")
    last_login_ip = Column(String(50), comment="最后登录IP")
    settings = Column(JSON, comment="用户偏好设置")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tenant = relationship("Tenant", back_populates="users")
    roles = relationship("UserRole", back_populates="user")
    project_members = relationship("ProjectMember", back_populates="user")
    # Phase 5
    ai_gen_history = relationship("AIGenHistory", back_populates="creator")
    ai_advisor_chats = relationship("AIAdvisorChat", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="角色名称")
    description = Column(Text, comment="角色描述")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), comment="所属租户，null表示系统角色")
    is_system = Column(Boolean, default=False, comment="是否系统内置角色")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    tenant = relationship("Tenant", back_populates="roles")
    permissions = relationship("Permission", back_populates="role")
    user_roles = relationship("UserRole", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    resource = Column(String(100), nullable=False, comment="资源类型")
    action = Column(String(50), nullable=False, comment="操作类型")
    scope = Column(String(20), default="all", comment="all/own/project/tenant")

    # 关系
    role = relationship("Role", back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.resource}:{self.action}>"


class UserRole(Base):
    """用户角色关联表"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="user_roles")

    def __repr__(self):
        return f"<UserRole user={self.user_id} role={self.role_id}>"


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(200), nullable=False, comment="项目名称")
    key = Column(String(20), unique=True, comment="项目唯一标识")
    description = Column(Text, comment="项目描述")
    avatar = Column(String(500), comment="项目图标")
    status = Column(String(20), default="active", comment="active/archived/deleted")
    repository_id = Column(Integer, ForeignKey("code_repository.id"), comment="关联的代码仓库")
    settings = Column(JSON, comment="项目配置")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tenant = relationship("Tenant", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project")
    versions = relationship("Version", back_populates="project")
    # Phase 5
    ai_gen_history = relationship("AIGenHistory", back_populates="project")
    vector_docs = relationship("VectorDoc", back_populates="project")
    smart_orch_rules = relationship("SmartOrchRule", back_populates="project")

    def __repr__(self):
        return f"<Project {self.key}>"


class ProjectMember(Base):
    """项目成员表"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False, comment="项目内角色：admin/developer/tester/viewer")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_members")

    def __repr__(self):
        return f"<ProjectMember project={self.project_id} user={self.user_id}>"


class Version(Base):
    """版本表"""
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="版本名称")
    tag = Column(String(50), comment="Git Tag")
    commit_hash = Column(String(64), comment="关联的Git Commit")
    description = Column(Text, comment="版本描述")
    baseline_id = Column(Integer, comment="关联的基准版本ID")
    quality_report_id = Column(String(100), comment="关联的质量报告")
    test_summary = Column(JSON, comment="测试摘要")
    status = Column(String(20), default="draft", comment="draft/testing/released/archived")
    released_at = Column(DateTime, comment="发布时间")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    project = relationship("Project", back_populates="versions")

    def __repr__(self):
        return f"<Version {self.name}>"


class SharedAsset(Base):
    """共享资产表"""
    __tablename__ = "shared_assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), nullable=False, comment="case/scenario/environment/template")
    asset_id = Column(Integer, nullable=False, comment="资产原始ID")
    owner_tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    owner_project_id = Column(Integer, comment="所有者项目")
    shared_to_tenant_id = Column(Integer, ForeignKey("tenants.id"), comment="共享目标租户，null表示公开")
    shared_to_project_id = Column(Integer, comment="共享目标项目")
    permission = Column(String(20), default="read", comment="read/copy/execute")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, comment="过期时间")

    def __repr__(self):
        return f"<SharedAsset {self.asset_type}:{self.asset_id}>"


class AssetTemplate(Base):
    """资产模板表"""
    __tablename__ = "asset_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="模板名称")
    type = Column(String(50), nullable=False, comment="case/scenario/report/environment")
    content = Column(Text, nullable=False, comment="模板内容JSON")
    description = Column(Text, comment="模板描述")
    tags = Column(JSON, comment="标签数组")
    icon = Column(String(500), comment="图标")
    usage_count = Column(Integer, default=0, comment="使用次数")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), comment="所属租户，null表示系统模板")
    created_by = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False, comment="是否公开")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AssetTemplate {self.name}>"


class FailureCluster(Base):
    """失败聚类表"""
    __tablename__ = "failure_clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    cluster_name = Column(String(200), nullable=False, comment="聚类名称")
    error_pattern = Column(Text, nullable=False, comment="错误特征模式")
    error_type = Column(String(50), comment="timeout/assertion/connection/parse/...")
    root_cause = Column(Text, comment="根因分析结果")
    suggested_fix = Column(Text, comment="建议修复方案")
    occurrence_count = Column(Integer, default=1, comment="发生次数")
    affected_cases = Column(JSON, comment="受影响的用例ID列表")
    first_seen_at = Column(DateTime, comment="首次出现时间")
    last_seen_at = Column(DateTime, comment="最后出现时间")
    resolved = Column(Boolean, default=False, comment="是否已解决")
    resolved_at = Column(DateTime, comment="解决时间")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FailureCluster {self.cluster_name}>"


class ChangeImpact(Base):
    """变更影响分析表"""
    __tablename__ = "change_impacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    commit_hash = Column(String(64), nullable=False, comment="变更Commit")
    changed_files = Column(JSON, comment="变更文件列表")
    impacted_cases = Column(JSON, comment="受影响的用例ID列表")
    impacted_scenarios = Column(JSON, comment="受影响的场景ID列表")
    risk_level = Column(String(20), comment="low/medium/high/critical")
    recommendation = Column(Text, comment="建议执行的测试")
    actual_failures = Column(Text, comment="实际失败的用例")
    prediction_accuracy = Column(Float, comment="预测准确率")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChangeImpact {self.commit_hash}>"


class PerformanceBaseline(Base):
    """性能基线表"""
    __tablename__ = "performance_baselines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("test_case.id"), comment="关联用例")
    scenario_id = Column(Integer, ForeignKey("scenario.id"), comment="关联场景")
    environment_id = Column(Integer, ForeignKey("environment.id"), comment="环境")
    metric_name = Column(String(50), nullable=False, comment="rt/tps/error_rate/...")
    baseline_value = Column(Float, nullable=False, comment="基准值")
    upper_bound = Column(Float, comment="上界（告警阈值）")
    lower_bound = Column(Float, comment="下界")
    sample_count = Column(Integer, comment="样本数量")
    std_deviation = Column(Float, comment="标准差")
    version_id = Column(Integer, ForeignKey("versions.id"), comment="关联版本")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PerformanceBaseline {self.metric_name}>"


class AlertRule(Base):
    """智能告警规则表"""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="规则名称")
    type = Column(String(50), nullable=False, comment="failure_rate/rt_spike/coverage_drop/...")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="所属项目")
    scope = Column(JSON, comment="作用范围（用例/场景ID列表）")
    condition = Column(JSON, comment="触发条件")
    threshold = Column(Float, comment="阈值")
    duration = Column(Integer, comment="持续时间（秒）")
    severity = Column(String(20), comment="critical/high/medium/low/info")
    enabled = Column(Boolean, default=True, comment="是否启用")
    notify_channels = Column(JSON, comment="通知渠道")
    cooldown_minutes = Column(Integer, default=30, comment="冷却时间（分钟）")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AlertRule {self.name}>"


class Dashboard(Base):
    """仪表盘表"""
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="仪表盘名称")
    type = Column(String(20), nullable=False, comment="personal/project/tenant/system")
    owner_id = Column(Integer, comment="所有者ID（用户/项目/租户）")
    is_default = Column(Boolean, default=False, comment="是否默认仪表盘")
    layout_config = Column(JSON, comment="布局配置")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    widgets = relationship("DashboardWidget", back_populates="dashboard")

    def __repr__(self):
        return f"<Dashboard {self.name}>"


class DashboardWidget(Base):
    """仪表盘组件表"""
    __tablename__ = "dashboard_widgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"), nullable=False)
    widget_type = Column(String(50), nullable=False, comment="组件类型")
    title = Column(String(200), comment="组件标题")
    config = Column(JSON, comment="组件配置")
    position = Column(JSON, comment="位置 {x, y, w, h}")
    refresh_interval = Column(Integer, comment="刷新间隔（秒）")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    dashboard = relationship("Dashboard", back_populates="widgets")

    def __repr__(self):
        return f"<DashboardWidget {self.widget_type}>"
