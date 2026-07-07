#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助函数
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from models import db, User
from config import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL
from werkzeug.security import generate_password_hash

# ==================== 装饰器 ====================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('需要管理员权限')
            return redirect(url_for('quiz.index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== 业务逻辑 ====================
def check_answer(question, user_answer):
    """根据题型判断答案是否正确"""
    if question.type == 'single':
        return user_answer == question.answer
    elif question.type == 'multiple':
        correct = set(question.answer.replace(' ', '').split(','))
        if isinstance(user_answer, str):
            user = set(user_answer.replace(' ', '').split(','))
        else:
            user = set(user_answer)
        return user == correct
    elif question.type == 'judge':
        return user_answer == question.answer
    elif question.type == 'fill':
        correct_answers = [ans.strip().lower() for ans in question.answer.split('|')]
        user = user_answer.strip().lower() if user_answer else ''
        return user in correct_answers
    return False

def init_db():
    """创建数据库和默认管理员"""
    db.create_all()
    
    # 迁移：为 Group 表添加新字段（如果不存在）
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    if 'group' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('group')]
        if 'study_content' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE [group] ADD COLUMN study_content TEXT"))
                conn.commit()
            print("已添加 group.study_content 列")
        if 'unlock_order' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE [group] ADD COLUMN unlock_order INTEGER DEFAULT 0"))
                conn.commit()
            print("已添加 group.unlock_order 列")
        if 'background_image' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE [group] ADD COLUMN background_image VARCHAR(255)"))
                conn.commit()
            print("已添加 group.background_image 列")
    
    if 'question' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('question')]
        if 'image' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE question ADD COLUMN image VARCHAR(255)"))
                conn.commit()
            print("已添加 question.image 列")
    
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"默认管理员已创建：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
