from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers import platform_auth, platform_system
from app.routers.terminal import router as terminal_router
from app.routers.testcase import router as testcase_router
from app.routers.case_folder import router as case_folder_router
from app.routers.scenario import router as scenario_router
from app.routers.report import router as report_router
from app.routers.dictionary import router as dictionary_router

app = FastAPI(title="Quality Manage Platform", version="2.0.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(platform_auth.router)
app.include_router(platform_system.router)
app.include_router(terminal_router)
app.include_router(case_folder_router)
app.include_router(testcase_router)
app.include_router(scenario_router)
app.include_router(report_router)
app.include_router(dictionary_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
def root():
    return {"message": "Quality Manage Platform API", "version": "2.0.0"}
