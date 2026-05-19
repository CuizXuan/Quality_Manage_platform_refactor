from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import init_db
from app.routers import cases, environments, scenarios, logs, folders, proxy, datasets, schedules, mocks, reports, loadtest, repositories, coverage, defects, quality_gates, integrations, case_folders
from app.routers import auth, tenant, projects, versions, share, templates, ai, dashboard, openapi  # Phase 4
from app.routers.ai_gen import router as ai_gen_router  # Phase 5 AI 生成
from app.routers.traffic import router as traffic_router  # Phase 5 全链路压测
from app.routers.chaos import router as chaos_router  # Phase 5 混沌工程
from app.routers.testdata import router as testdata_router  # Phase 5 测试数据工厂
from app.routers.marketplace import router as marketplace_router  # Phase 5 插件市场
from app.routers.audit import router as audit_router  # Phase 5 审计日志
from app.routers.ai_models import router as ai_models_router  # Phase 5 AI模型配置
from app.middleware.tenant_middleware import TenantMiddleware  # Phase 4 租户中间件
from app.middleware.audit_middleware import AuditLoggerMiddleware  # Phase 5 审计日志

app = FastAPI(title="Quality Manage Platform - API Debug Tool")

# 全局异常处理器：确保所有异常返回 JSON 格式
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获所有未处理异常，返回 JSON 格式错误"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if __import__("os").getenv("DEBUG") else "Internal Server Error"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 5 审计日志中间件（必须在 TenantMiddleware 之前注册，这样执行时它在租户中间件之后）
# FastAPI 中间件执行顺序是反向的——最后注册的先执行
# 所以 TenantMiddleware 最后注册 → 最先执行 → 先设置 user_id/tenant_id
# → AuditLoggerMiddleware 后注册 → 第二执行 → 能读到 state
app.add_middleware(AuditLoggerMiddleware)
# Phase 4 租户中间件（最后注册，最先执行）
app.add_middleware(TenantMiddleware)

# 注册路由
app.include_router(proxy.router, prefix="/proxy", tags=["Proxy"])
app.include_router(cases.router)
app.include_router(environments.router)
app.include_router(scenarios.router)
app.include_router(logs.router)
app.include_router(folders.router)
app.include_router(case_folders.router)
app.include_router(datasets.router)
app.include_router(schedules.router)
app.include_router(mocks.router)
app.include_router(mocks.mock_entry_router)
app.include_router(reports.router_templates)
app.include_router(reports.router)
app.include_router(loadtest.router)
# Phase 3 路由
app.include_router(repositories.router)
app.include_router(coverage.router)
app.include_router(coverage.router_upload)
app.include_router(defects.router)
app.include_router(quality_gates.router)
app.include_router(integrations.router)
# Phase 4 路由
app.include_router(auth.router)
app.include_router(tenant.router)
app.include_router(projects.router)
app.include_router(versions.router)
app.include_router(share.router)
app.include_router(templates.router)
app.include_router(ai.router)
app.include_router(dashboard.router)
app.include_router(openapi.router)
# Phase 5 AI 生成路由
app.include_router(ai_gen_router)
# Phase 5 全链路压测路由
app.include_router(traffic_router)
# Phase 5 混沌工程路由
app.include_router(chaos_router)
# Phase 5 测试数据工厂路由
app.include_router(testdata_router)
# Phase 5 插件市场路由
app.include_router(marketplace_router)
# Phase 5 审计日志路由
app.include_router(audit_router)
# Phase 5 AI 模型配置路由
app.include_router(ai_models_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Quality Manage Platform API", "version": "1.5.0 (Phase 5)"}
