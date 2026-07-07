#!/bin/bash
# 在线答题系统 - 一键配置运行 (Linux/macOS)

echo "============================================"
echo "   在线答题系统 - 一键配置运行"
echo "============================================"
echo ""

# ==================== 检查 Python ====================
echo "[1/5] 检查 Python 环境..."

if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

echo "  Python 版本: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo "[错误] Python 版本过低，需要 Python 3.8+，当前为 $PYTHON_VERSION"
    exit 1
fi
echo "  Python 版本符合要求 (>=3.8)"
echo ""

# ==================== 检查 pip ====================
echo "[2/5] 检查 pip 版本..."

if ! command -v pip3 &> /dev/null; then
    echo "[警告] 未检测到 pip3，正在尝试安装..."
    python3 -m ensurepip --upgrade
    if [ $? -ne 0 ]; then
        echo "[错误] pip 安装失败，请手动安装 pip"
        exit 1
    fi
fi

PIP_VERSION=$(pip3 --version 2>/dev/null | awk '{print $2}')
echo "  pip 版本: $PIP_VERSION"
echo ""

# ==================== 创建虚拟环境 ====================
echo "[3/5] 配置虚拟环境 (.venv)..."
if [ ! -d ".venv" ]; then
    echo "  正在创建虚拟环境..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[错误] 虚拟环境创建失败"
        exit 1
    fi
    echo "  虚拟环境创建成功"
else
    echo "  虚拟环境已存在，跳过创建"
fi
echo ""

# ==================== 激活虚拟环境并安装依赖 ====================
echo "[4/5] 安装依赖包..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[错误] 虚拟环境激活失败"
    exit 1
fi

pip install -r requirements.txt --only-binary :all: -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[警告] 清华源安装失败，尝试默认源..."
    pip install -r requirements.txt --only-binary :all:
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败，请检查网络连接"
        exit 1
    fi
fi
echo ""

# ==================== 启动应用 ====================
echo "[5/5] 启动应用..."
echo ""
echo "============================================"
echo "  服务器运行在 http://127.0.0.1:5000"
echo "  默认管理员: admin / admin123"
echo "  按 Ctrl+C 停止服务器"
echo "============================================"
echo ""
python3 app.py