#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由模块
"""
from .auth import auth_bp
from .quiz import quiz_bp
from .admin import admin_bp

def register_routes(app):
    """注册所有路由蓝图"""
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(quiz_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
