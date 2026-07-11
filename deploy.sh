#!/bin/bash
# QuizPlatform 自动部署脚本
# 由 GitHub Actions SSH 远程调用

set -e

PROJECT_DIR="/opt/QuizPlatform"
SCREEN_NAME="project"

echo "====== 开始部署 QuizPlatform ======"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 1. 拉取最新代码
echo "[1/4] 拉取最新代码..."
cd "$PROJECT_DIR"
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "代码已是最新，无需更新"
else
    git pull origin main
    echo "代码已更新"
fi

# 2. 安装依赖
echo "[2/4] 安装依赖..."
source .venv/bin/activate
pip install -r requirements.txt --only-binary :all: -q 2>/dev/null || \
    pip install -r requirements.txt --only-binary :all: -q || true

# 3. 停止旧进程
echo "[3/4] 重启服务..."
if screen -list | grep -q "\.$SCREEN_NAME"; then
    screen -S "$SCREEN_NAME" -X quit
    echo "旧 screen 会话已关闭"
fi

# 4. 启动新进程
sleep 1
screen -dmS "$SCREEN_NAME" bash -c "source .venv/bin/activate && gunicorn -w 4 -b 0.0.0.0:5000 app:app 2>&1 | tee -a /opt/QuizPlatform/gunicorn.log"

if screen -list | grep -q "\.$SCREEN_NAME"; then
    echo "服务已重新启动"
else
    echo "[错误] 服务启动失败！"
    exit 1
fi

echo "====== 部署完成 ======"
echo ""