#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线答题系统 - 主入口
"""
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db
from routes import register_routes
import os

# ==================== 初始化应用 ====================
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# 初始化扩展
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.auth_login'

# 注册路由
register_routes(app)

# ==================== 模板初始化 ====================
TEMPLATES_DIR = 'templates'
ADMIN_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'admin')

def ensure_templates():
    """确保模板目录存在"""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(ADMIN_TEMPLATES_DIR, exist_ok=True)

# ==================== 用户加载器 ====================
@login_manager.user_loader
def load_user(user_id):
    from models import db, User
    return db.session.get(User, int(user_id))

# ==================== 启动 ====================
if __name__ == '__main__':
    ensure_templates()
    with app.app_context():
        from utils import init_db
        init_db()
    print(f"服务器运行在 http://127.0.0.1:5000")
    from config import ADMIN_USERNAME, ADMIN_PASSWORD
    print(f"默认管理员：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    app.run(debug=True, host='0.0.0.0', port=5000)
