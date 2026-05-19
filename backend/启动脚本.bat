@echo off
chcp 65001 >nul
title API Debug Tool - 后台服务

cd /d "%~dp0\backend"

:menu
echo ========================================
echo   API Debug Tool - 后台服务管理
echo ========================================
echo [1] 启动后台服务 (端口 8000)
echo [2] 停止后台服务
echo [3] 查看服务状态
echo [4] 重启后台服务
echo [5] 安装依赖 (阿里镜像)
echo [6] 退出
echo.

set /p choice=请输入选项 (1-6):

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto status
if "%choice%"=="4" goto restart
if "%choice%"=="5" goto install
if "%choice%"=="6" goto end

:start
echo.
echo 正在启动后台服务 (端口 8000)...
start "API Debug Tool - 后台" cmd /k "cd /d "%~dp0\backend" && python3.11 -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=False)""
echo 服务已启动
goto menu

:stop
echo.
echo 正在停止后台服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 停止进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo 后台服务已停止
goto menu

:status
echo.
curl -s -o nul -w "HTTP状态: %%{http_code}\n" http://localhost:8000/ --connect-timeout 3
if errorlevel 1 echo 服务未运行
goto menu

:restart
echo.
echo 正在重启后台服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 >nul
start "API Debug Tool - 后台" cmd /k "cd /d "%~dp0\backend" && python3.11 -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=False)""
echo 后台服务已重启
goto menu

:install
echo.
echo 正在安装依赖 (阿里镜像)...
python3.11 -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
echo 依赖安装完成
goto menu

:end
exit
