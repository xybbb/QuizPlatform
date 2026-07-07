@echo off
chcp 65001 >nul
title 在线答题系统 - 一键配置运行

echo ============================================
echo    在线答题系统 - 一键配置运行
echo ============================================
echo.

:: ==================== 检查 Python ====================
echo [1/5] 检查 Python 环境...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 获取 Python 版本号
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo   Python 版本: %PYTHON_VERSION%

:: 解析主版本号和次版本号
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

:: 检查 Python >= 3.8
if %MAJOR% LSS 3 (
    echo [错误] Python 版本过低，需要 Python 3.8+，当前为 %PYTHON_VERSION%
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 8 (
    echo [错误] Python 版本过低，需要 Python 3.8+，当前为 %PYTHON_VERSION%
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   Python 版本符合要求 (>=3.8)
echo.

:: ==================== 检查 pip ====================
echo [2/5] 检查 pip 版本...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到 pip，正在尝试安装...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo [错误] pip 安装失败，请手动安装 pip
        pause
        exit /b 1
    )
)

for /f "tokens=2" %%v in ('pip --version 2^>^&1') do set PIP_VERSION=%%v
echo   pip 版本: %PIP_VERSION%
echo.

:: ==================== 创建虚拟环境 ====================
echo [3/5] 配置虚拟环境 (.venv)...
if not exist ".venv\" (
    echo   正在创建虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo   虚拟环境创建成功
) else (
    echo   虚拟环境已存在，跳过创建
)
echo.

:: ==================== 激活虚拟环境并安装依赖 ====================
echo [4/5] 安装依赖包（优先使用预编译包，避免需要 C++ 编译器）...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)

pip install -r requirements.txt --only-binary :all: -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [警告] 清华源安装失败，尝试默认源...
    pip install -r requirements.txt --only-binary :all:
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)
echo.

:: ==================== 启动应用 ====================
echo [5/5] 启动应用...
echo.
echo ============================================
echo   服务器运行在 http://127.0.0.1:5000
echo   默认管理员: admin / admin123
echo   按 Ctrl+C 停止服务器
echo ============================================
echo.
python app.py

pause