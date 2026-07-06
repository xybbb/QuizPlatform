#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证路由：登录、注册、退出
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def auth_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('auth.auth_register'))
        user = User(username=username, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('auth.auth_login'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.status:
                flash('账号已被禁用')
                return redirect(url_for('auth.auth_login'))
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('quiz.index'))
        flash('用户名或密码错误')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def auth_logout():
    logout_user()
    return redirect(url_for('quiz.index'))
